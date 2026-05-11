"""
Triviale "Mean Predictor"-Baseline.

Gibt fuer jeden Test-Punkt einfach den Trainings-Mittelwert von y_extrap
zurueck. Dient als Floor fuer den Vergleich:

    Wenn ein lernendes Modell einen schlechteren oder vergleichbaren MAE
    hat wie diese Baseline, hat es nichts ueber die Features gelernt.
    Wenn der C-Index dieser Baseline 0.5 ist (definitionsgemaess) und das
    lernende Modell auch 0.5 hat, lernt es keine Reihenfolge.

Wird in der Auswertung als "mean_const" gefuehrt.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml


def predict_test(config_path: str = "configs/default.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    processed = Path(cfg["paths"]["processed_dir"])
    train = dict(np.load(processed / "train.npz"))
    test = dict(np.load(processed / "test.npz"))

    mean_extrap = float(train["y_extrap"].mean())
    print(f"[mean-pred] using train mean of y_extrap = {mean_extrap:.3f}h")

    y_pred = np.full(len(test["y_extrap"]), mean_extrap, dtype=np.float32)
    return {
        "y_pred": y_pred,
        "y_extrap": test["y_extrap"],
        "y_real": test["y_real"],
        "system_estimate_min": test["system_estimate_min"],
        "battery_level": test["battery_level"],
        "timestamp_ms": test["timestamp_ms"],
        "segment_idx": test["segment_idx"],
        "constant_value_h": np.float32(mean_extrap),
    }


def main(config_path: str = "configs/default.yaml") -> None:
    out = predict_test(config_path)
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    out_dir = Path(cfg["paths"]["processed_dir"])
    np.savez_compressed(out_dir / "predictions_mean_const.npz", **out)
    print(f"[mean-pred] wrote {out_dir / 'predictions_mean_const.npz'}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml")
