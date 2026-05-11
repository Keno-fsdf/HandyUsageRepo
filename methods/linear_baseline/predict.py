"""
Naive lineare Baseline.

Konzept (entspricht der MIUI/Settings-Logik):
    drain_rate = (battery[t-N] - battery[t]) / (time[t] - time[t-N])    [%/h]
    remaining_h = battery[t] / drain_rate

Die Baseline nutzt fuer die Drain-Rate ein gleitendes Fenster der letzten N
realen Datenpunkte (drain_window in der Config).

Wichtig fuer Fairness:
- Vorhersagen werden auf demselben Test-Split wie TinyML berechnet.
- Wir nutzen den Roh-Akkustand und Timestamp aus dem Sliding-Window
  (nicht das skalierte X). Das macht die Baseline reproduzierbar.

Ausgabe analog zu predictions_tinyml.npz unter
data/processed/predictions_linear.npz.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml


def _drain_rates_for_test(
    raw_csv: Path,
    timestamps: np.ndarray,
    segment_idx: np.ndarray,
    drain_window: int,
) -> np.ndarray:
    """
    Fuer jeden Test-Punkt: Drain-Rate aus den letzten drain_window Eintraegen
    DESSELBEN Segments im Roh-CSV.

    Ergebnis: %/h. NaN wenn nicht berechenbar (z.B. Segmentbeginn).
    """
    df = pd.read_csv(raw_csv)
    df = df.sort_values(["session_id", "timestamp"]).reset_index(drop=True)

    # Per-Punkt Lookup ueber timestamp_ms (eindeutig auf 1ms-Aufloesung).
    df_indexed = df.set_index("timestamp")

    out = np.full(len(timestamps), np.nan, dtype=np.float32)
    # Index pro Session, damit wir die "letzten N im selben Segment" kennen
    # ohne zwischen Sessions zu wandern.
    by_session = {sid: g.reset_index(drop=True) for sid, g in df.groupby("session_id")}

    for i, ts in enumerate(timestamps):
        try:
            row = df_indexed.loc[int(ts)]
        except KeyError:
            continue
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]
        sid = row["session_id"]
        sess_df = by_session[sid]
        # Position im Session-DataFrame
        pos_arr = np.where(sess_df["timestamp"].values == int(ts))[0]
        if len(pos_arr) == 0:
            continue
        pos = int(pos_arr[0])
        start = max(0, pos - drain_window)
        window = sess_df.iloc[start : pos + 1]
        # Nur Punkte im aktuellen Discharge-Block (charging=0)
        window = window[window["charging"] == 0]
        if len(window) < 2:
            continue
        b0 = float(window["battery_level"].iloc[0])
        b1 = float(window["battery_level"].iloc[-1])
        t0 = int(window["timestamp"].iloc[0])
        t1 = int(window["timestamp"].iloc[-1])
        dh = (t1 - t0) / 3_600_000.0
        if dh <= 0:
            continue
        drain = b0 - b1
        if drain <= 0:
            continue
        out[i] = drain / dh
    return out


def predict_test(config_path: str = "configs/default.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    processed = Path(cfg["paths"]["processed_dir"])
    raw_csv = Path(cfg["paths"]["raw_csv"])
    drain_window = int(cfg["baselines"]["linear"]["drain_window"])

    test = dict(np.load(processed / "test.npz"))

    drain_rate = _drain_rates_for_test(
        raw_csv, test["timestamp_ms"], test["segment_idx"], drain_window
    )
    bat = test["battery_level"]

    with np.errstate(divide="ignore", invalid="ignore"):
        y_pred = np.where(drain_rate > 0, bat / drain_rate, np.nan).astype(np.float32)

    valid = ~np.isnan(y_pred)
    print(
        f"[predict-linear] valid {int(valid.sum())}/{len(y_pred)} "
        f"({100.0 * valid.mean():.1f}%)"
    )
    return {
        "y_pred": y_pred,
        "valid": valid,
        "y_extrap": test["y_extrap"],
        "y_real": test["y_real"],
        "system_estimate_min": test["system_estimate_min"],
        "battery_level": test["battery_level"],
        "timestamp_ms": test["timestamp_ms"],
        "segment_idx": test["segment_idx"],
        "drain_rate_pct_h": drain_rate,
    }


def main(config_path: str = "configs/default.yaml") -> None:
    out = predict_test(config_path)
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    out_dir = Path(cfg["paths"]["processed_dir"])
    np.savez_compressed(out_dir / "predictions_linear.npz", **out)
    print(f"[predict-linear] wrote {out_dir / 'predictions_linear.npz'}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml")
