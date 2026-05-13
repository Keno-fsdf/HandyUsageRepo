"""
Verifiziert, dass die hartgecodeten SCALER_MEAN/SCALER_SCALE in
android/.../BatteryPredictor.kt mit der aktuellen models/scaler.joblib
uebereinstimmen.

Wird das vergessen, sind die On-Device-Vorhersagen systematisch verzerrt.

Exit-Code 0 = synchron, 1 = divergiert (in CI / Pre-Build verwenden).

Aufruf:
    python -m methods.tinyml.check_scaler_sync
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import joblib
import yaml


KOTLIN_PATH = Path("android/app/src/main/java/com/batterypredictor/datacollector/BatteryPredictor.kt")
TOLERANCE = 1e-4  # Kotlin speichert mit 6 Nachkommastellen, das passt locker


def parse_kotlin_array(text: str, name: str) -> list[float]:
    """Extrahiert ein floatArrayOf(...) Array nach Variablen-Namen."""
    pattern = rf"private val {name}\s*=\s*floatArrayOf\(([^)]*)\)"
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        raise RuntimeError(f"konnte {name} in {KOTLIN_PATH} nicht finden")
    raw = m.group(1)
    nums = re.findall(r"-?\d+\.\d+f?", raw)
    return [float(n.rstrip("f")) for n in nums]


def main(config_path: str = "configs/default.yaml") -> int:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    scaler_path = Path(cfg["paths"]["models_dir"]) / "scaler.joblib"
    if not scaler_path.exists():
        print(f"[check_scaler_sync] {scaler_path} existiert nicht -- "
              f"Pipeline noch nicht gelaufen? Skip.")
        return 0

    scaler = joblib.load(scaler_path)
    py_mean = list(scaler.mean_)
    py_scale = list(scaler.scale_)

    if not KOTLIN_PATH.exists():
        print(f"[check_scaler_sync] {KOTLIN_PATH} nicht gefunden", file=sys.stderr)
        return 1
    text = KOTLIN_PATH.read_text(encoding="utf-8")
    kt_mean = parse_kotlin_array(text, "SCALER_MEAN")
    kt_scale = parse_kotlin_array(text, "SCALER_SCALE")

    problems: list[str] = []
    if len(py_mean) != len(kt_mean):
        problems.append(
            f"laenge MEAN: python={len(py_mean)} kotlin={len(kt_mean)}"
        )
    if len(py_scale) != len(kt_scale):
        problems.append(
            f"laenge SCALE: python={len(py_scale)} kotlin={len(kt_scale)}"
        )
    if not problems:
        for i, (a, b) in enumerate(zip(py_mean, kt_mean)):
            if abs(a - b) > TOLERANCE:
                problems.append(f"MEAN[{i}]: python={a:.6f} kotlin={b:.6f} diff={a-b:+.6f}")
        for i, (a, b) in enumerate(zip(py_scale, kt_scale)):
            if abs(a - b) > TOLERANCE:
                problems.append(f"SCALE[{i}]: python={a:.6f} kotlin={b:.6f} diff={a-b:+.6f}")

    if problems:
        print("[check_scaler_sync] DIVERGENZ:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print("\nFix:  python -m methods.tinyml.export_scaler_for_android", file=sys.stderr)
        print("      und Output in BatteryPredictor.kt einsetzen.", file=sys.stderr)
        return 1

    print(f"[check_scaler_sync] OK: {len(py_mean)} Features, alle Werte im Toleranz-Bereich (<{TOLERANCE})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml"))
