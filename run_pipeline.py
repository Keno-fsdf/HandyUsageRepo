"""
Vollständige Pipeline: Datengenerierung -> Training -> TFLite Conversion.

Führt alle drei Phasen sequentiell aus.
"""

import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

SCRIPTS = [
    ("Phase 1: Datengenerierung",    "generate_data.py"),
    ("Phase 2: Model Training",       "train_model.py"),
    ("Phase 3: TFLite Conversion",    "convert_tflite.py"),
]


def main():
    print("=" * 60)
    print("  BATTERY LIFETIME PREDICTOR - FULL PIPELINE")
    print("=" * 60)

    for phase_name, script in SCRIPTS:
        print(f"\n{'─' * 60}")
        print(f"  {phase_name}: {script}")
        print(f"{'─' * 60}\n")

        result = subprocess.run([sys.executable, script], check=False)
        if result.returncode != 0:
            print(f"\n[ERROR] {script} fehlgeschlagen (exit code {result.returncode})")
            sys.exit(1)

    print(f"\n{'=' * 60}")
    print("  PIPELINE ABGESCHLOSSEN")
    print(f"{'=' * 60}")
    print("\nDateien:")
    print("  data/battery_data.csv         - Rohdaten")
    print("  data/X_sequences.npy          - Feature-Sequenzen")
    print("  data/y_sequences.npy          - Targets")
    print("  model/battery_model.keras     - Keras Modell")
    print("  model/scaler.joblib           - Feature Scaler")
    print("  model/metrics.json            - Evaluation Metrics")
    print("  model/battery_model.tflite    - Finale TFLite Datei")
    print("  model/tflite_results.json     - Conversion Ergebnisse")
    print("  plots/training_results.png    - Visualisierungen")


if __name__ == "__main__":
    main()
