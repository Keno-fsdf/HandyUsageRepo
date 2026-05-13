"""
Google Battery Discharge Prediction wird auf dem Phone berechnet
(PowerManager.getBatteryDischargePrediction()) und in der CSV als
system_estimate_min in Minuten geloggt.

Hier extrahieren wir nur die Werte fuer das Test-Split (zur Vereinheitlichung
mit den anderen Methoden) und konvertieren auf Stunden.

Wichtig:
- system_estimate_min == -1 bedeutet "API hat null zurueckgegeben"
  (z.B. ladend oder Schaetzung noch nicht verfuegbar). Diese Punkte
  markieren wir als invalid.
- Aktuell wird isBatteryDischargePredictionPersonalized NICHT geloggt
  (TODO Android-Side). Wir koennen das hier ohne Code-Aenderung nicht
  rekonstruieren - vermerken im Report.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml


def extract(config_path: str = "configs/default.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    processed = Path(cfg["paths"]["processed_dir"])
    test = dict(np.load(processed / "test.npz"))
    sys_min = test["system_estimate_min"]
    # -1 = Sentinel "API liefert null" (z.B. waehrend Ladens). 0 ist eine
    # legitime Vorhersage ("Akku gleich leer") und wird als valid behalten.
    valid = sys_min > -0.5
    y_pred = np.where(valid, sys_min / 60.0, np.nan).astype(np.float32)

    print(f"[google-api] valid {int(valid.sum())}/{len(y_pred)} ({100.0 * valid.mean():.1f}%)")
    return {
        "y_pred": y_pred,
        "valid": valid,
        "y_extrap": test["y_extrap"],
        "y_real": test["y_real"],
        "system_estimate_min": sys_min,
        "battery_level": test["battery_level"],
        "timestamp_ms": test["timestamp_ms"],
        "segment_idx": test["segment_idx"],
    }


def main(config_path: str = "configs/default.yaml") -> None:
    out = extract(config_path)
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    out_dir = Path(cfg["paths"]["processed_dir"])
    np.savez_compressed(out_dir / "predictions_google.npz", **out)
    print(f"[google-api] wrote {out_dir / 'predictions_google.npz'}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml")
