"""
Konsolidiert mehrere Geraete-CSVs zu einer einzigen
data/processed/combined.csv mit zusaetzlicher device-Spalte.

Behandelt zwei Probleme der Roh-Daten:
    1. Leere session_id-Felder werden durch device-spezifische
       Synthetische IDs ersetzt (sonst gruppiert pandas alles in
       einen Bucket und das ergibt unsinnige Segmente).
    2. Die alte App-Version hat 14 Spalten (system_estimate_min am
       Ende), die neue hat 17 (mit system_personalized,
       own_prediction_h, linear_baseline_h). Wir konsolidieren auf
       die alten 14 Spalten plus device, weil die drei zusaetzlichen
       fuer die hier ausgewerteten Methoden nicht benoetigt werden.

Aufruf:
    python -m methods.tinyml.merge_devices

Liest die in configs/default.yaml unter `devices:` gelisteten Eintraege.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml


REQUIRED_COLS = [
    "session_id",
    "timestamp",
    "datetime",
    "battery_level",
    "screen_on",
    "brightness",
    "active_app_category",
    "wifi_on",
    "mobile_data_on",
    "charging",
    "cpu_usage",
    "temperature",
    "hotspot_on",
    "system_estimate_min",
]


def _load_one(path: Path, device: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = set(REQUIRED_COLS) - set(df.columns)
    if missing:
        raise ValueError(f"{path}: missing required columns {missing}")
    df = df[REQUIRED_COLS].copy()

    # Leere session_id durch synthetische IDs ersetzen
    empty_mask = df["session_id"].isna() | (df["session_id"].astype(str).str.strip() == "")
    n_empty = int(empty_mask.sum())
    if n_empty > 0:
        df.loc[empty_mask, "session_id"] = (
            f"{device}_nosession_" + empty_mask.cumsum().astype(str)
        )
        print(f"[merge] {path.name}: replaced {n_empty} empty session_id values")

    # Device-praefix damit session_ids ueber Geraete hinweg eindeutig sind
    df["session_id"] = device + "__" + df["session_id"].astype(str)
    df["device"] = device
    print(f"[merge] {path.name} -> device={device}: {len(df)} rows, "
          f"{df['session_id'].nunique()} sessions")
    return df


def main(config_path: str = "configs/default.yaml") -> None:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    devices = cfg.get("devices")
    if not devices:
        raise RuntimeError(
            "No `devices:` section in config. Add a list of {name, csv} pairs."
        )
    out_path = Path(cfg["paths"]["raw_csv"])

    frames = []
    for d in devices:
        path = Path(d["csv"])
        if not path.exists():
            print(f"[merge] WARN: {path} missing, skipping")
            continue
        frames.append(_load_one(path, d["name"]))

    if not frames:
        raise RuntimeError("No device CSVs loaded.")

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values(["device", "session_id", "timestamp"]).reset_index(drop=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(out_path, index=False)

    print(f"\n[merge] wrote {out_path}")
    print(f"[merge] total: {len(combined)} rows, {combined['session_id'].nunique()} sessions, "
          f"{combined['device'].nunique()} devices")
    for dev, sub in combined.groupby("device"):
        print(f"  {dev:<25s} n={len(sub):>6d}  sessions={sub['session_id'].nunique():>4d}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml")
