"""
Druckt die StandardScaler-Werte als Kotlin-Snippet fuer BatteryPredictor.kt.

Aufruf:
    python -m methods.tinyml.export_scaler_for_android

Ausgabe in stdout - direkt in den Companion-Object-Block kopieren.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import yaml


def main(config_path: str = "configs/default.yaml") -> None:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    scaler = joblib.load(Path(cfg["paths"]["models_dir"]) / "scaler.joblib")
    features = cfg["features"]

    print("// AUTO-GENERATED from models/scaler.joblib via export_scaler_for_android.py")
    print("// Reihenfolge muss exakt der CSV-Feature-Reihenfolge entsprechen.")
    print("// Features:")
    for feat in features:
        print(f"//   - {feat}")
    print()
    print("private val SCALER_MEAN = floatArrayOf(")
    print("    " + ", ".join(f"{m:.6f}f" for m in scaler.mean_))
    print(")")
    print("private val SCALER_SCALE = floatArrayOf(")
    print("    " + ", ".join(f"{s:.6f}f" for s in scaler.scale_))
    print(")")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml")
