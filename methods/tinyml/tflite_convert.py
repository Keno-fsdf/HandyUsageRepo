"""
Konvertiert das Keras-Modell in mehrere TFLite-Varianten und misst Groesse +
On-Device-Praedikabilitaet (auf dem Trainingsrechner als Proxy fuer das Phone).

Drei Standard-Quantisierungen + Default-Float32:
- dynamic_range : Gewichte INT8, Aktivierungen Float32 (kein Repr. Dataset noetig)
- float16       : Gewichte Float16, Aktivierungen Float32
- int8_full     : Voll INT8 mit representative dataset (deploy-Variante)

Output:
- models/<variant>.tflite
- models/tflite_variants.json (Groesse, Inferenz-Latenz auf PC, MAE auf Test)

Latenz auf dem Smartphone wird in evaluation/efficiency.py separat gemessen
(zumindest als TFLite-Interpreter-Run-Time, was eine untere Schranke fuer
das echte Geraet ist).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import yaml


def representative_dataset(X_train: np.ndarray, n: int):
    n = min(n, len(X_train))
    for i in range(n):
        yield [X_train[i : i + 1].astype(np.float32)]


def convert(model, variant: str, X_train: np.ndarray, n_repr: int):
    import tensorflow as tf

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    if variant == "dynamic_range":
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
    elif variant == "float16":
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.target_spec.supported_types = [tf.float16]
    elif variant == "int8_full":
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.representative_dataset = lambda: representative_dataset(X_train, n_repr)
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        # Float-I/O behalten - vereinfacht die Android-Integration drastisch
        converter.inference_input_type = tf.float32
        converter.inference_output_type = tf.float32
    else:
        raise ValueError(f"unknown variant: {variant}")
    return converter.convert()


def benchmark_tflite(tflite_bytes: bytes, X: np.ndarray, n_runs: int = 200) -> dict:
    import tensorflow as tf

    interp = tf.lite.Interpreter(model_content=tflite_bytes)
    interp.allocate_tensors()
    in_details = interp.get_input_details()[0]
    out_details = interp.get_output_details()[0]

    # Warmup
    for i in range(min(20, len(X))):
        interp.set_tensor(in_details["index"], X[i : i + 1].astype(np.float32))
        interp.invoke()

    # Latenz
    times: list[float] = []
    for i in range(min(n_runs, len(X))):
        x = X[i : i + 1].astype(np.float32)
        t0 = time.perf_counter()
        interp.set_tensor(in_details["index"], x)
        interp.invoke()
        _ = interp.get_tensor(out_details["index"])
        times.append(time.perf_counter() - t0)
    arr = np.asarray(times) * 1000.0  # ms
    return {
        "avg_inference_ms": float(arr.mean()),
        "p50_inference_ms": float(np.median(arr)),
        "p95_inference_ms": float(np.percentile(arr, 95)),
        "n_runs": int(len(arr)),
    }


def predict_full(tflite_bytes: bytes, X: np.ndarray) -> np.ndarray:
    import tensorflow as tf

    interp = tf.lite.Interpreter(model_content=tflite_bytes)
    interp.allocate_tensors()
    in_details = interp.get_input_details()[0]
    out_details = interp.get_output_details()[0]
    out = np.zeros(len(X), dtype=np.float32)
    for i in range(len(X)):
        interp.set_tensor(in_details["index"], X[i : i + 1].astype(np.float32))
        interp.invoke()
        out[i] = float(interp.get_tensor(out_details["index"]).flatten()[0])
    return out


def main(config_path: str = "configs/default.yaml") -> None:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    models = Path(cfg["paths"]["models_dir"])
    processed = Path(cfg["paths"]["processed_dir"])
    variants = list(cfg["tflite"]["variants"])
    n_repr = int(cfg["tflite"]["representative_samples"])
    deploy = cfg["tflite"]["deploy_variant"]

    from tensorflow import keras

    model = keras.models.load_model(models / "battery_model.keras")
    train = dict(np.load(processed / "train.npz"))
    test = dict(np.load(processed / "test.npz"))

    results: dict[str, dict] = {}
    for v in variants:
        print(f"[tflite] converting {v}")
        b = convert(model, v, train["X"], n_repr)
        path = models / f"battery_model_{v}.tflite"
        path.write_bytes(b)
        size_kb = len(b) / 1024.0

        bench = benchmark_tflite(b, test["X"], n_runs=200)
        y_pred = predict_full(b, test["X"])
        mae = float(np.mean(np.abs(test["y_extrap"] - y_pred)))

        results[v] = {
            "size_kb": round(size_kb, 4),
            "mae_h_extrap": round(mae, 4),
            **{k: round(v_, 6) for k, v_ in bench.items() if isinstance(v_, float)},
            "n_runs": bench["n_runs"],
        }
        print(f"[tflite] {v}: {results[v]}")

    # Deploy-Kopie
    src = models / f"battery_model_{deploy}.tflite"
    if src.exists():
        deploy_copy = models / "battery_model.tflite"
        deploy_copy.write_bytes(src.read_bytes())
        results["_deploy_variant"] = deploy
        print(f"[tflite] deploy copy: {deploy_copy} (= {src.name})")

    (models / "tflite_variants.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"[tflite] wrote models/tflite_variants.json")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml")
