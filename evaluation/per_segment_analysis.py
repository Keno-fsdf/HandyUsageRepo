"""
Per-Segment / Per-Bucket-Analyse.

Zerlegt die Test-Punkte in Buckets nach
    (a) Battery-Level zum Test-Zeitpunkt   (0-25, 25-50, 50-75, 75-100)
    (b) Segment-Laenge in Stunden          (<2h, 2-5h, >5h)
    (c) y_real-Bucket                      (<1h, 1-3h, >3h)

und reportet pro Bucket die MAE / C-Index aller Methoden.

Argument fuer's Paper: zeigt WO die Methoden gut/schlecht sind.
Hypothese: Google API liefert konsistente Ranking-Qualitaet (C-Index),
TinyML/Conv1D dagegen ist auf allen Buckets nahe Zufall - weiteres
Indiz, dass es nicht segment-spezifisch versagt sondern grundsaetzlich
keine Feature->Output-Beziehung gelernt hat.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from evaluation.accuracy import all_metrics


METHODS = ("tinyml", "random_forest", "mean_const", "linear", "exponential", "google")


def _load_predictions(processed: Path) -> dict[str, dict]:
    files = {
        "tinyml": "predictions_tinyml.npz",
        "random_forest": "predictions_random_forest.npz",
        "mean_const": "predictions_mean_const.npz",
        "linear": "predictions_linear.npz",
        "exponential": "predictions_exponential.npz",
        "google": "predictions_google.npz",
    }
    out: dict[str, dict] = {}
    for name, fname in files.items():
        path = processed / fname
        if not path.exists():
            continue
        d = dict(np.load(path, allow_pickle=True))
        if "valid" not in d:
            d["valid"] = (~np.isnan(d["y_pred"])).astype(bool)
        else:
            d["valid"] = d["valid"].astype(bool)
        out[name] = d
    return out


def _segment_lengths_hours(test: dict, raw_csv: Path) -> np.ndarray:
    """Pro Test-Punkt die Laenge des zugehoerigen Discharge-Segments (in h)."""
    df = pd.read_csv(raw_csv).sort_values(["session_id", "timestamp"]).reset_index(drop=True)
    df_idx = df.set_index("timestamp")

    # Lookup pro session + position
    by_session = {sid: g.reset_index(drop=True) for sid, g in df.groupby("session_id")}

    out = np.full(len(test["timestamp_ms"]), np.nan, dtype=np.float32)
    for i, ts in enumerate(test["timestamp_ms"]):
        try:
            row = df_idx.loc[int(ts)]
        except KeyError:
            continue
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]
        sid = row["session_id"]
        sess_df = by_session[sid]
        pos_arr = np.where(sess_df["timestamp"].values == int(ts))[0]
        if len(pos_arr) == 0:
            continue
        pos = int(pos_arr[0])

        # Vorwaerts und rueckwaerts in der Session laufen, solange charging=0
        # und timestamp-Differenzen <= max_gap.
        max_gap = 300_000  # gleicher Wert wie data_prep
        # rueckwaerts
        start = pos
        while start > 0:
            prev = start - 1
            if sess_df.iloc[prev]["charging"] == 0 and \
               (sess_df.iloc[start]["timestamp"] - sess_df.iloc[prev]["timestamp"]) <= max_gap:
                start = prev
            else:
                break
        # vorwaerts
        end = pos
        while end < len(sess_df) - 1:
            nxt = end + 1
            if sess_df.iloc[nxt]["charging"] == 0 and \
               (sess_df.iloc[nxt]["timestamp"] - sess_df.iloc[end]["timestamp"]) <= max_gap:
                end = nxt
            else:
                break
        t0 = int(sess_df.iloc[start]["timestamp"])
        t1 = int(sess_df.iloc[end]["timestamp"])
        out[i] = (t1 - t0) / 3_600_000.0
    return out


def _bucket_table(preds: dict[str, dict], y_true: np.ndarray, mask: np.ndarray, label: str, tols) -> dict:
    out = {"_label": label, "_n": int(mask.sum())}
    if mask.sum() < 5:
        return out
    for name, p in preds.items():
        m = mask & p["valid"] & ~np.isnan(p["y_pred"])
        if m.sum() < 5:
            out[name] = {"n": int(m.sum())}
            continue
        out[name] = all_metrics(y_true[m], p["y_pred"][m], tols_h=tols)
    return out


def main(config_path: str = "configs/default.yaml") -> None:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    processed = Path(cfg["paths"]["processed_dir"])
    raw_csv = Path(cfg["paths"]["raw_csv"])
    reports = Path(cfg["paths"]["reports_dir"])
    tols = list(cfg["evaluation"]["accuracy_tolerances_h"])

    preds = _load_predictions(processed)
    if not preds:
        raise RuntimeError("no predictions found")
    test = dict(np.load(processed / "test.npz"))
    y_extrap = test["y_extrap"]
    y_real = test["y_real"]
    bat = test["battery_level"]

    # Bucket (a) by battery level
    bat_buckets = [
        ("battery_0_25", (bat >= 0) & (bat < 25)),
        ("battery_25_50", (bat >= 25) & (bat < 50)),
        ("battery_50_75", (bat >= 50) & (bat < 75)),
        ("battery_75_100", (bat >= 75) & (bat <= 100)),
    ]

    # Bucket (b) by segment length
    seg_h = _segment_lengths_hours(test, raw_csv)
    seg_buckets = [
        ("segment_under_2h", seg_h < 2),
        ("segment_2_5h", (seg_h >= 2) & (seg_h < 5)),
        ("segment_over_5h", seg_h >= 5),
    ]

    # Bucket (c) by y_real
    real_buckets = [
        ("y_real_under_1h", y_real < 1),
        ("y_real_1_3h", (y_real >= 1) & (y_real < 3)),
        ("y_real_over_3h", y_real >= 3),
    ]

    out = {
        "_meta": {
            "n_test": int(len(y_real)),
            "y_real_mean_h": float(y_real.mean()),
            "y_extrap_mean_h": float(y_extrap.mean()),
            "segment_length_mean_h": float(np.nanmean(seg_h)),
            "segment_length_max_h": float(np.nanmax(seg_h)),
        },
        "by_battery_level_vs_extrap": {},
        "by_segment_length_vs_extrap": {},
        "by_y_real_bucket_vs_real": {},
    }
    for name, m in bat_buckets:
        out["by_battery_level_vs_extrap"][name] = _bucket_table(preds, y_extrap, m, name, tols)
    for name, m in seg_buckets:
        out["by_segment_length_vs_extrap"][name] = _bucket_table(preds, y_extrap, m, name, tols)
    for name, m in real_buckets:
        out["by_y_real_bucket_vs_real"][name] = _bucket_table(preds, y_real, m, name, tols)

    reports.mkdir(parents=True, exist_ok=True)
    (reports / "per_segment_analysis.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[per-segment] wrote {reports / 'per_segment_analysis.json'}")
    print(json.dumps(out["_meta"], indent=2))


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml")
