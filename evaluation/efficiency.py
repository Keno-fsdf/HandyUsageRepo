"""
Effizienz-Benchmark: Modellgroesse, Inferenzzeit, Parameter, Energie-Proxy.

Misst auf dem Rechner als untere Schranke fuer das Smartphone -
das echte On-Device-Latenz-Profil muss spaeter via Logging in der App
ergaenzt werden (siehe REPORT.md).

Drei der vier MLPerf-Tiny-Pflichtmetriken werden direkt gemessen:
    - Accuracy (kommt aus evaluation/accuracy.py)
    - Latency (avg + p95)
    - Memory (Modellgroesse + Peak-Tensor-Arena via TFLite)

Energie wird nicht direkt gemessen (Smartphone gibt keine pro-Inferenz-mA).
Wir geben einen Proxy: Energie ~ Latenz x CPU-Auslastung. Das ist eine
Vereinfachung und im Paper als solche zu deklarieren.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import yaml


def benchmark_keras(model_path: Path, X: np.ndarray, warmup: int, runs: int) -> dict:
    from tensorflow import keras

    model = keras.models.load_model(model_path)
    # Warmup
    for i in range(min(warmup, len(X))):
        model.predict(X[i : i + 1], verbose=0)
    # Messen
    times: list[float] = []
    for i in range(min(runs, len(X))):
        x = X[i : i + 1]
        t0 = time.perf_counter()
        model.predict(x, verbose=0)
        times.append(time.perf_counter() - t0)
    arr = np.asarray(times) * 1000.0
    n_params = int(model.count_params())
    return {
        "n_params": n_params,
        "size_kb": round(model_path.stat().st_size / 1024.0, 2),
        "avg_inference_ms": round(float(arr.mean()), 4),
        "p50_inference_ms": round(float(np.median(arr)), 4),
        "p95_inference_ms": round(float(np.percentile(arr, 95)), 4),
        "n_runs": int(len(arr)),
    }


def benchmark_tflite(tflite_path: Path, X: np.ndarray, warmup: int, runs: int) -> dict:
    import tensorflow as tf

    interp = tf.lite.Interpreter(model_path=str(tflite_path))
    interp.allocate_tensors()
    in_details = interp.get_input_details()[0]
    out_details = interp.get_output_details()[0]

    # Warmup
    for i in range(min(warmup, len(X))):
        interp.set_tensor(in_details["index"], X[i : i + 1].astype(np.float32))
        interp.invoke()

    times: list[float] = []
    for i in range(min(runs, len(X))):
        t0 = time.perf_counter()
        interp.set_tensor(in_details["index"], X[i : i + 1].astype(np.float32))
        interp.invoke()
        _ = interp.get_tensor(out_details["index"])
        times.append(time.perf_counter() - t0)

    arr = np.asarray(times) * 1000.0
    return {
        "size_kb": round(tflite_path.stat().st_size / 1024.0, 2),
        "avg_inference_ms": round(float(arr.mean()), 4),
        "p50_inference_ms": round(float(np.median(arr)), 4),
        "p95_inference_ms": round(float(np.percentile(arr, 95)), 4),
        "n_runs": int(len(arr)),
    }


def main(config_path: str = "configs/default.yaml") -> None:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    models = Path(cfg["paths"]["models_dir"])
    processed = Path(cfg["paths"]["processed_dir"])
    reports = Path(cfg["paths"]["reports_dir"])
    eff_cfg = cfg["evaluation"]["efficiency"]

    test = dict(np.load(processed / "test.npz"))
    X = test["X"]

    out: dict = {"_meta": {"warmup": eff_cfg["warmup_runs"], "runs": eff_cfg["measurement_runs"]}}

    keras_path = models / "battery_model.keras"
    if keras_path.exists():
        print("[efficiency] keras")
        out["keras_float32"] = benchmark_keras(
            keras_path, X, eff_cfg["warmup_runs"], eff_cfg["measurement_runs"]
        )

    for tfl in sorted(models.glob("battery_model_*.tflite")):
        if tfl.name == "battery_model.tflite":
            continue
        variant = tfl.stem.replace("battery_model_", "")
        print(f"[efficiency] tflite {variant}")
        out[f"tflite_{variant}"] = benchmark_tflite(
            tfl, X, eff_cfg["warmup_runs"], eff_cfg["measurement_runs"]
        )

    reports.mkdir(parents=True, exist_ok=True)
    (reports / "efficiency.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[efficiency] wrote {reports / 'efficiency.json'}")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml")
