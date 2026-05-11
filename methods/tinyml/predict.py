"""
TinyML-Vorhersagen fuer das Test-Split. Wird von evaluation/ konsumiert.

Verwendet das Keras-Modell (Float32). Die TFLite-Variante hat eigene
Vorhersage-Funktion in tflite_convert.py - hier waehlen wir Keras, weil
die Vergleichsergebnisse so deterministisch reproduzierbar sind.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml


def predict_test(config_path: str = "configs/default.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    processed = Path(cfg["paths"]["processed_dir"])
    models = Path(cfg["paths"]["models_dir"])

    test = dict(np.load(processed / "test.npz"))

    from tensorflow import keras

    model = keras.models.load_model(models / "battery_model.keras")
    y_pred = model.predict(test["X"], verbose=0).flatten().astype(np.float32)
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
    np.savez_compressed(out_dir / "predictions_tinyml.npz", **out)
    print(f"[predict-tinyml] wrote {out_dir / 'predictions_tinyml.npz'}  (n={len(out['y_pred'])})")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml")
