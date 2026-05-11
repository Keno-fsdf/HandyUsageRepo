"""
Random-Forest-Vorhersagen auf dem Test-Split.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import yaml


def predict_test(config_path: str = "configs/default.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    processed = Path(cfg["paths"]["processed_dir"])
    models = Path(cfg["paths"]["models_dir"])
    test = dict(np.load(processed / "test.npz"))

    n_test, seq_len, n_feat = test["X"].shape
    X_test = test["X"].reshape(n_test, seq_len * n_feat)

    rf = joblib.load(models / "random_forest.joblib")
    y_pred = rf.predict(X_test).astype(np.float32)
    return {
        "y_pred": y_pred,
        "y_extrap": test["y_extrap"],
        "y_real": test["y_real"],
        "system_estimate_min": test["system_estimate_min"],
        "battery_level": test["battery_level"],
        "timestamp_ms": test["timestamp_ms"],
        "segment_idx": test["segment_idx"],
    }


def main(config_path: str = "configs/default.yaml") -> None:
    out = predict_test(config_path)
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    out_dir = Path(cfg["paths"]["processed_dir"])
    np.savez_compressed(out_dir / "predictions_random_forest.npz", **out)
    print(f"[predict-rf] wrote {out_dir / 'predictions_random_forest.npz'}  (n={len(out['y_pred'])})")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml")
