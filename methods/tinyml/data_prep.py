"""
Datenvorbereitung fuer Battery-Prediction.

Pipeline:
    raw CSV -> Entladesegmente -> Sliding-Window-Sequenzen -> Train/Val/Test

Methodisch wichtig (im Paper als Methode beschreiben):

1. Entladesegmente: zusammenhaengende Bereiche mit charging=0 innerhalb derselben
   Session, getrennt durch Zeitluecken > max_gap_ms. Mindestlaenge min_segment_length.

2. Targets:
   - target_extrap: Zeit bis Segment-Ende + Extrapolation ueber Drain-Rate
     (= dasselbe Target wie im urspruenglichen Code, fuer Training).
   - target_real: NUR die gemessene Zeit bis Segment-Ende (ohne Extrapolation).
     Dieses Target ist die ehrlichere Ground-Truth fuer den Vergleich gegen
     Google-API und Baselines. Beide werden gespeichert.

3. Split: SEGMENT-LEVEL, NICHT Sequenz-Level.
   Random Shuffle ueber Sliding-Window-Sequenzen ist Data-Leakage in
   Time-Series-Settings (Hidden Leaks in Time Series Forecasting, 2025) -
   Sequenzen aus demselben Segment landen sonst in Train UND Test.
   -> Wir splitten Segmente, dann erzeugen wir Sequenzen nur innerhalb
   eines Splits.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib


@dataclass
class PrepConfig:
    raw_csv: Path
    processed_dir: Path
    models_dir: Path
    features: list[str]
    sequence_length: int
    min_segment_length: int
    max_gap_ms: int
    train_frac: float
    val_frac: float
    test_frac: float
    seed: int

    @classmethod
    def from_yaml(cls, path: str | Path) -> "PrepConfig":
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        split = cfg["data_prep"]["split"]
        return cls(
            raw_csv=Path(cfg["paths"]["raw_csv"]),
            processed_dir=Path(cfg["paths"]["processed_dir"]),
            models_dir=Path(cfg["paths"]["models_dir"]),
            features=list(cfg["features"]),
            sequence_length=int(cfg["data_prep"]["sequence_length"]),
            min_segment_length=int(cfg["data_prep"]["min_segment_length"]),
            max_gap_ms=int(cfg["data_prep"]["max_gap_ms"]),
            train_frac=float(split["train"]),
            val_frac=float(split["val"]),
            test_frac=float(split["test"]),
            seed=int(split["seed"]),
        )


def load_raw(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    required = {"session_id", "timestamp", "battery_level", "charging", "system_estimate_min"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV fehlen Spalten: {missing}")
    return df


def find_discharge_segments(df: pd.DataFrame, min_length: int, max_gap_ms: int) -> list[pd.DataFrame]:
    """Zerlegt CSV in zusammenhaengende Entladesegmente."""
    segments: list[pd.DataFrame] = []

    for _, session_df in df.groupby("session_id"):
        session_df = session_df.sort_values("timestamp").reset_index(drop=True)
        is_discharging = session_df["charging"] == 0
        # Ladevorgaenge teilen die Session
        block_id = (~is_discharging).cumsum()

        for _, block in session_df[is_discharging].groupby(block_id[is_discharging]):
            # Zeitluecken splitten den Block weiter
            time_diffs = block["timestamp"].diff()
            gap_id = (time_diffs > max_gap_ms).cumsum()

            for _, sub in block.groupby(gap_id):
                if len(sub) >= min_length:
                    segments.append(sub.reset_index(drop=True).copy())

    return segments


def compute_segment_targets(seg: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """
    Pro Datenpunkt im Segment zwei Targets:
        target_extrap: Zeit bis Segment-Ende + extrapolierte Restzeit ueber Drain-Rate
        target_real:   NUR Zeit bis Segment-Ende (ohne Extrapolation)
    """
    ts = seg["timestamp"].values.astype(np.int64)
    bat = seg["battery_level"].values.astype(np.float32)

    total_h = (ts[-1] - ts[0]) / 3_600_000.0
    total_drain = float(bat[0] - bat[-1])

    if total_h <= 0 or total_drain <= 0:
        # Kein Drain im Segment -> Targets nicht definierbar
        return None, None  # type: ignore[return-value]

    drain_rate = total_drain / total_h  # %/h
    extra_h = bat[-1] / drain_rate if drain_rate > 0 else 0.0

    time_to_end_h = (ts[-1] - ts) / 3_600_000.0
    target_extrap = (time_to_end_h + extra_h).astype(np.float32)
    target_real = time_to_end_h.astype(np.float32)
    return target_extrap, target_real


def build_sequences(
    segments: list[pd.DataFrame],
    feature_cols: list[str],
    seq_len: int,
) -> dict[str, np.ndarray]:
    """
    Sliding-Window-Sequenzen NUR innerhalb eines Segments.
    Gibt Arrays mit zusaetzlichem Segment-Index zurueck (fuer spaeteres Sanity-Checking).
    Trackt zusaetzlich device-Zugehoerigkeit pro Sample (falls Spalte vorhanden).
    """
    feats: list[np.ndarray] = []
    target_extrap: list[float] = []
    target_real: list[float] = []
    sys_est: list[float] = []
    seg_idx: list[int] = []
    timestamps: list[int] = []
    battery_levels: list[float] = []
    devices: list[str] = []

    for s_idx, seg in enumerate(segments):
        te, tr = compute_segment_targets(seg)
        if te is None:
            continue
        f = seg[feature_cols].values.astype(np.float32)
        sys_e = seg["system_estimate_min"].values.astype(np.float32)
        ts = seg["timestamp"].values.astype(np.int64)
        bat = seg["battery_level"].values.astype(np.float32)
        seg_device = str(seg["device"].iloc[0]) if "device" in seg.columns else "unknown"

        for i in range(len(seg) - seq_len):
            j = i + seq_len - 1
            feats.append(f[i : i + seq_len])
            target_extrap.append(te[j])
            target_real.append(tr[j])
            sys_est.append(sys_e[j])
            seg_idx.append(s_idx)
            timestamps.append(int(ts[j]))
            battery_levels.append(float(bat[j]))
            devices.append(seg_device)

    return {
        "X": np.asarray(feats, dtype=np.float32),
        "y_extrap": np.asarray(target_extrap, dtype=np.float32),
        "y_real": np.asarray(target_real, dtype=np.float32),
        "system_estimate_min": np.asarray(sys_est, dtype=np.float32),
        "segment_idx": np.asarray(seg_idx, dtype=np.int32),
        "timestamp_ms": np.asarray(timestamps, dtype=np.int64),
        "battery_level": np.asarray(battery_levels, dtype=np.float32),
        # Als feste UTF-8 Strings ablegen (nicht object-dtype!), damit np.load
        # ohne allow_pickle=True funktioniert.
        "device": np.asarray(devices, dtype=np.str_),
    }


def split_segments(n_segments: int, train: float, val: float, test: float, seed: int):
    assert abs(train + val + test - 1.0) < 1e-6, "Splits muessen zu 1.0 summieren"
    rng = np.arange(n_segments)
    train_idx, temp_idx = train_test_split(rng, test_size=val + test, random_state=seed, shuffle=True)
    val_share_of_temp = val / (val + test)
    val_idx, test_idx = train_test_split(temp_idx, test_size=1.0 - val_share_of_temp, random_state=seed, shuffle=True)
    return set(train_idx), set(val_idx), set(test_idx)


def filter_by_segment(arrs: dict[str, np.ndarray], keep: set[int]) -> dict[str, np.ndarray]:
    mask = np.isin(arrs["segment_idx"], list(keep))
    return {k: v[mask] for k, v in arrs.items()}


def fit_scaler_and_transform(
    train: dict[str, np.ndarray],
    val: dict[str, np.ndarray],
    test: dict[str, np.ndarray],
    n_features: int,
):
    scaler = StandardScaler()
    n, t, f = train["X"].shape
    scaler.fit(train["X"].reshape(-1, f))

    def _norm(d):
        x = d["X"]
        n_, t_, f_ = x.shape
        d["X"] = scaler.transform(x.reshape(-1, f_)).reshape(n_, t_, f_).astype(np.float32)
        return d

    return _norm(train), _norm(val), _norm(test), scaler


def save_splits(
    cfg: PrepConfig,
    train: dict[str, np.ndarray],
    val: dict[str, np.ndarray],
    test: dict[str, np.ndarray],
    scaler: StandardScaler,
):
    cfg.processed_dir.mkdir(parents=True, exist_ok=True)
    cfg.models_dir.mkdir(parents=True, exist_ok=True)

    for name, d in (("train", train), ("val", val), ("test", test)):
        np.savez_compressed(cfg.processed_dir / f"{name}.npz", **d)

    joblib.dump(scaler, cfg.models_dir / "scaler.joblib")


def write_summary(cfg: PrepConfig, splits: dict[str, dict[str, np.ndarray]], n_segments_total: int):
    lines = [
        "# Data preparation summary",
        "",
        f"Source: `{cfg.raw_csv}`",
        f"Sequence length: {cfg.sequence_length}",
        f"Total discharge segments: {n_segments_total}",
        "",
        "## Split (segment-level, no leakage)",
        "",
        "| Split | Sequences | mean target_extrap (h) | mean target_real (h) |",
        "|-------|-----------|------------------------|----------------------|",
    ]
    for name in ("train", "val", "test"):
        d = splits[name]
        lines.append(
            f"| {name} | {len(d['X'])} | "
            f"{float(d['y_extrap'].mean()):.2f} | {float(d['y_real'].mean()):.2f} |"
        )
    # Per-Device-Counts pro Split (nur wenn device vorhanden)
    if "device" in splits["train"]:
        lines += ["", "## Per-device sequence counts", "",
                  "| Split | " + " | ".join(sorted(set(splits["train"]["device"]) |
                                                   set(splits["val"]["device"]) |
                                                   set(splits["test"]["device"]))) + " |"]
        all_devices = sorted(set(splits["train"]["device"]) |
                            set(splits["val"]["device"]) |
                            set(splits["test"]["device"]))
        lines.append("|---|" + "|".join(["---"] * len(all_devices)) + "|")
        for name in ("train", "val", "test"):
            d = splits[name]
            counts = [str(int((d["device"] == dev).sum())) for dev in all_devices]
            lines.append(f"| {name} | " + " | ".join(counts) + " |")
    cfg.processed_dir.mkdir(parents=True, exist_ok=True)
    (cfg.processed_dir / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(config_path: str = "configs/default.yaml") -> None:
    cfg = PrepConfig.from_yaml(config_path)
    print(f"[data_prep] config: {config_path}")
    print(f"[data_prep] reading {cfg.raw_csv}")

    df = load_raw(cfg.raw_csv)
    print(f"[data_prep] {len(df)} rows, {df['session_id'].nunique()} sessions")

    segments = find_discharge_segments(df, cfg.min_segment_length, cfg.max_gap_ms)
    print(f"[data_prep] {len(segments)} discharge segments")

    train_set, val_set, test_set = split_segments(
        len(segments), cfg.train_frac, cfg.val_frac, cfg.test_frac, cfg.seed
    )
    print(
        f"[data_prep] segment split: train={len(train_set)} val={len(val_set)} test={len(test_set)}"
    )

    arrs = build_sequences(segments, cfg.features, cfg.sequence_length)
    print(f"[data_prep] {len(arrs['X'])} total sequences across all segments")

    train = filter_by_segment(arrs, train_set)
    val = filter_by_segment(arrs, val_set)
    test = filter_by_segment(arrs, test_set)
    print(
        f"[data_prep] sequences: train={len(train['X'])} val={len(val['X'])} test={len(test['X'])}"
    )

    train, val, test, scaler = fit_scaler_and_transform(train, val, test, len(cfg.features))
    save_splits(cfg, train, val, test, scaler)
    write_summary(cfg, {"train": train, "val": val, "test": test}, len(segments))
    print(f"[data_prep] wrote {cfg.processed_dir}/{{train,val,test}}.npz + scaler")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml")
