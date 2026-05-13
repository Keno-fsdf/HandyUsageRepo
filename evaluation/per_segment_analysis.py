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


def _common_mask(preds: dict[str, dict]) -> np.ndarray:
    masks = list(preds.values())
    m = masks[0]["valid"].copy()
    for p in masks[1:]:
        m &= p["valid"]
    return m


def _bucket_table(
    preds: dict[str, dict],
    y_true: np.ndarray,
    bucket_mask: np.ndarray,
    label: str,
    tols,
    common: np.ndarray,
) -> dict:
    """
    Pro Bucket reporten wir BEIDE Subsets:
      - native: Methoden auf ihrer eigenen Validity-Mask (Coverage-Spalte unterscheidet sich)
      - common: nur Punkte, wo alle Methoden valid sind -> direkte Vergleichbarkeit

    Frueher: nur native, was zu n=2915-vs-n=2827-Verwechslungen gefuehrt hat.
    """
    out = {"_label": label, "_n_in_bucket": int(bucket_mask.sum()),
           "_n_common_in_bucket": int((bucket_mask & common).sum())}
    if bucket_mask.sum() < 5:
        return out

    # Common-Subset: alle Methoden auf demselben n -> direkt vergleichbar
    common_in_bucket = bucket_mask & common
    if common_in_bucket.sum() >= 5:
        common_block: dict = {}
        for name, p in preds.items():
            yt = y_true[common_in_bucket]
            yp = p["y_pred"][common_in_bucket]
            common_block[name] = all_metrics(yt, yp, tols_h=tols)
        out["common"] = common_block
    else:
        out["common"] = {"_skipped": "n_common < 5"}

    # Native-Subset: jede Methode auf ihrer eigenen Validity -> Coverage-Vergleich
    native_block: dict = {}
    for name, p in preds.items():
        m = bucket_mask & p["valid"] & ~np.isnan(p["y_pred"])
        if m.sum() < 5:
            native_block[name] = {"n": int(m.sum())}
            continue
        native_block[name] = all_metrics(y_true[m], p["y_pred"][m], tols_h=tols)
    out["native"] = native_block
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

    # Bucket (d) by y_extrap (Trainings-Target; relevant fuer Long-Horizon-Analyse)
    extrap_buckets = [
        ("y_extrap_under_5h", y_extrap < 5),
        ("y_extrap_5_15h", (y_extrap >= 5) & (y_extrap < 15)),
        ("y_extrap_15_30h", (y_extrap >= 15) & (y_extrap < 30)),
        ("y_extrap_over_30h", y_extrap >= 30),
    ]

    common = _common_mask(preds)
    out = {
        "_meta": {
            "n_test": int(len(y_real)),
            "n_common_valid": int(common.sum()),
            "y_real_mean_h": float(y_real.mean()),
            "y_extrap_mean_h": float(y_extrap.mean()),
            "segment_length_mean_h": float(np.nanmean(seg_h)),
            "segment_length_max_h": float(np.nanmax(seg_h)),
            "_note": ("Hauptmetric im Paper: gegen y_real. "
                      "vs_extrap-Block dient nur als Vergleich zum Trainings-Target "
                      "(zirkulaerer Bias zugunsten TinyML/RF). "
                      "Innerhalb jedes Bucket-Eintrags gibt es 'common' "
                      "(alle Methoden gleicher n - direkt vergleichbar) und 'native' "
                      "(jede Methode auf eigener Validity-Mask)."),
        },
        "by_battery_level_vs_real": {},
        "by_segment_length_vs_real": {},
        "by_y_real_bucket_vs_real": {},
        "by_y_extrap_bucket_vs_extrap": {},
        "by_battery_level_vs_extrap": {},
        "by_segment_length_vs_extrap": {},
    }
    for name, m in bat_buckets:
        out["by_battery_level_vs_real"][name] = _bucket_table(preds, y_real, m, name, tols, common)
        out["by_battery_level_vs_extrap"][name] = _bucket_table(preds, y_extrap, m, name, tols, common)
    for name, m in seg_buckets:
        out["by_segment_length_vs_real"][name] = _bucket_table(preds, y_real, m, name, tols, common)
        out["by_segment_length_vs_extrap"][name] = _bucket_table(preds, y_extrap, m, name, tols, common)
    for name, m in real_buckets:
        out["by_y_real_bucket_vs_real"][name] = _bucket_table(preds, y_real, m, name, tols, common)
    for name, m in extrap_buckets:
        out["by_y_extrap_bucket_vs_extrap"][name] = _bucket_table(preds, y_extrap, m, name, tols, common)

    reports.mkdir(parents=True, exist_ok=True)
    (reports / "per_segment_analysis.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[per-segment] wrote {reports / 'per_segment_analysis.json'}")
    print(json.dumps(out["_meta"], indent=2))


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml")
