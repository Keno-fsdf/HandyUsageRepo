"""
Phase 3: TensorFlow Lite Conversion mit INT8 Quantisierung.

Konvertiert das trainierte Keras-Modell zu TFLite mit:
- INT8 Full-Quantisierung (kleinste Größe)
- Float16 Quantisierung (Fallback)
- Validierung der konvertierten Modelle
- Inference-Zeit-Messung
"""

import os
import time
import json
import numpy as np
import tensorflow as tf
from sklearn.metrics import mean_absolute_error, mean_squared_error


MODEL_PATH = "model/battery_model.keras"
TFLITE_DIR = "model"
SEQUENCE_LENGTH = 10
NUM_FEATURES = 8


def load_representative_data():
    """Lädt Trainingsdaten für die Quantisierungskalibrierung."""
    X = np.load("data/X_sequences.npy")

    # Normalisieren mit gespeichertem Scaler
    import joblib
    scaler = joblib.load("model/scaler.joblib")
    n, seq_len, n_feat = X.shape
    X_norm = scaler.transform(X.reshape(-1, n_feat)).reshape(n, seq_len, n_feat)

    return X_norm.astype(np.float32)


def representative_dataset_gen(X_cal):
    """Generator für Representative Dataset (INT8 Quantisierung)."""
    # ~200 Samples für Kalibrierung
    indices = np.random.default_rng(42).choice(len(X_cal), size=min(200, len(X_cal)), replace=False)
    for i in indices:
        yield [X_cal[i:i+1]]


def convert_dynamic_range(model_path: str, output_path: str):
    """Dynamic Range Quantisierung (INT8 Gewichte, Float Aktivierungen)."""
    converter = tf.lite.TFLiteConverter.from_keras_model(
        tf.keras.models.load_model(model_path)
    )
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()

    with open(output_path, "wb") as f:
        f.write(tflite_model)

    return len(tflite_model)


def convert_float16(model_path: str, output_path: str):
    """Float16 Quantisierung."""
    converter = tf.lite.TFLiteConverter.from_keras_model(
        tf.keras.models.load_model(model_path)
    )
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]
    tflite_model = converter.convert()

    with open(output_path, "wb") as f:
        f.write(tflite_model)

    return len(tflite_model)


def convert_int8_full(model_path: str, output_path: str, X_cal: np.ndarray):
    """Volle INT8 Quantisierung (Gewichte + Aktivierungen)."""
    converter = tf.lite.TFLiteConverter.from_keras_model(
        tf.keras.models.load_model(model_path)
    )
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = lambda: representative_dataset_gen(X_cal)

    # INT8-only Ops erzwingen
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8

    try:
        tflite_model = converter.convert()
        with open(output_path, "wb") as f:
            f.write(tflite_model)
        return len(tflite_model)
    except Exception as e:
        print(f"  [WARN] Full INT8 fehlgeschlagen: {e}")
        print("  -> Fallback: INT8 mit Float-IO")
        # Fallback: INT8 quantized weights + activations, but float IO
        converter2 = tf.lite.TFLiteConverter.from_keras_model(
            tf.keras.models.load_model(model_path)
        )
        converter2.optimizations = [tf.lite.Optimize.DEFAULT]
        converter2.representative_dataset = lambda: representative_dataset_gen(X_cal)
        tflite_model = converter2.convert()
        with open(output_path, "wb") as f:
            f.write(tflite_model)
        return len(tflite_model)


def validate_tflite(tflite_path: str, X_test: np.ndarray, y_test: np.ndarray):
    """Validiert ein TFLite-Modell gegen Testdaten."""
    interpreter = tf.lite.Interpreter(model_path=tflite_path)
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    input_dtype = input_details[0]["dtype"]
    output_dtype = output_details[0]["dtype"]

    # Quantisierungsparameter lesen
    input_quant = input_details[0].get("quantization_parameters", {})
    output_quant = output_details[0].get("quantization_parameters", {})

    predictions = []
    inference_times = []

    for i in range(min(len(X_test), 500)):
        sample = X_test[i:i+1].copy()

        # Input quantisieren falls nötig
        if input_dtype == np.int8:
            scale = input_quant.get("scales", [1.0])[0]
            zero_point = input_quant.get("zero_points", [0])[0]
            sample = (sample / scale + zero_point).astype(np.int8)
        else:
            sample = sample.astype(np.float32)

        interpreter.set_tensor(input_details[0]["index"], sample)

        start = time.perf_counter()
        interpreter.invoke()
        elapsed = (time.perf_counter() - start) * 1000  # ms
        inference_times.append(elapsed)

        output = interpreter.get_tensor(output_details[0]["index"])

        # Output dequantisieren falls nötig
        if output_dtype == np.int8:
            scale = output_quant.get("scales", [1.0])[0]
            zero_point = output_quant.get("zero_points", [0])[0]
            output = (output.astype(np.float32) - zero_point) * scale

        predictions.append(output.flatten()[0])

    y_pred = np.array(predictions)
    y_actual = y_test[:len(y_pred)]

    mae = mean_absolute_error(y_actual, y_pred)
    rmse = np.sqrt(mean_squared_error(y_actual, y_pred))
    acc_1h = np.mean(np.abs(y_actual - y_pred) <= 1.0) * 100
    avg_time = np.mean(inference_times)
    p95_time = np.percentile(inference_times, 95)

    return {
        "mae": mae,
        "rmse": rmse,
        "accuracy_1h": acc_1h,
        "avg_inference_ms": avg_time,
        "p95_inference_ms": p95_time,
    }


def main():
    print("=" * 55)
    print("  TFLITE CONVERSION & VALIDATION")
    print("=" * 55)

    os.makedirs(TFLITE_DIR, exist_ok=True)

    # Kalibierungsdaten laden
    print("\nLade Kalibierungsdaten...")
    X_cal = load_representative_data()

    # Testdaten für Validierung
    from sklearn.model_selection import train_test_split
    X_all = np.load("data/X_sequences.npy")
    y_all = np.load("data/y_sequences.npy")
    _, X_temp, _, y_temp = train_test_split(X_all, y_all, test_size=0.3, random_state=42)
    _, X_test, _, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)

    import joblib
    scaler = joblib.load("model/scaler.joblib")
    n, sl, nf = X_test.shape
    X_test_norm = scaler.transform(X_test.reshape(-1, nf)).reshape(n, sl, nf).astype(np.float32)

    # --- Conversion Varianten ---
    conversions = {}

    # 1) Dynamic Range Quantisierung
    print("\n[1/3] Dynamic Range Quantisierung...")
    path_dr = os.path.join(TFLITE_DIR, "battery_model_dynamic.tflite")
    size_dr = convert_dynamic_range(MODEL_PATH, path_dr)
    conversions["dynamic_range"] = {"path": path_dr, "size_kb": size_dr / 1024}
    print(f"  -> {size_dr / 1024:.1f} KB")

    # 2) Float16 Quantisierung
    print("\n[2/3] Float16 Quantisierung...")
    path_f16 = os.path.join(TFLITE_DIR, "battery_model_float16.tflite")
    size_f16 = convert_float16(MODEL_PATH, path_f16)
    conversions["float16"] = {"path": path_f16, "size_kb": size_f16 / 1024}
    print(f"  -> {size_f16 / 1024:.1f} KB")

    # 3) Full INT8 Quantisierung
    print("\n[3/3] Full INT8 Quantisierung...")
    path_int8 = os.path.join(TFLITE_DIR, "battery_model_int8.tflite")
    size_int8 = convert_int8_full(MODEL_PATH, path_int8, X_cal)
    conversions["int8_full"] = {"path": path_int8, "size_kb": size_int8 / 1024}
    print(f"  -> {size_int8 / 1024:.1f} KB")

    # --- Validierung ---
    print("\n" + "=" * 55)
    print("  VALIDIERUNG DER KONVERTIERTEN MODELLE")
    print("=" * 55)

    results = {}
    for name, info in conversions.items():
        print(f"\n  [{name}] {info['path']}")
        metrics = validate_tflite(info["path"], X_test_norm, y_test)
        metrics["size_kb"] = info["size_kb"]
        results[name] = metrics

        size_ok = "OK" if info["size_kb"] < 500 else "FAIL"
        time_ok = "OK" if metrics["avg_inference_ms"] < 20 else "FAIL"

        print(f"    Size:          {info['size_kb']:.1f} KB  [{size_ok}]  (Limit: 500 KB)")
        print(f"    MAE:           {metrics['mae']:.3f} h")
        print(f"    RMSE:          {metrics['rmse']:.3f} h")
        print(f"    Accuracy ±1h:  {metrics['accuracy_1h']:.1f}%")
        print(f"    Avg Inference: {metrics['avg_inference_ms']:.2f} ms  [{time_ok}]  (Limit: 20 ms)")
        print(f"    P95 Inference: {metrics['p95_inference_ms']:.2f} ms")

    # --- Bestes Modell als battery_model.tflite kopieren ---
    # Bevorzuge INT8 wenn es die Constraints erfüllt, sonst Dynamic Range
    best_name = "int8_full"
    if results["int8_full"]["size_kb"] > 500:
        best_name = "dynamic_range"

    best_src = conversions[best_name]["path"]
    best_dst = os.path.join(TFLITE_DIR, "battery_model.tflite")

    import shutil
    shutil.copy2(best_src, best_dst)
    print(f"\n{'=' * 55}")
    print(f"  FINALE: battery_model.tflite ({best_name})")
    print(f"  Größe: {results[best_name]['size_kb']:.1f} KB")
    print(f"  MAE:   {results[best_name]['mae']:.3f} h")
    print(f"{'=' * 55}")

    # Ergebnisse speichern
    save_results = {}
    for k, v in results.items():
        save_results[k] = {kk: round(float(vv), 4) for kk, vv in v.items()}
    save_results["best_model"] = best_name

    with open("model/tflite_results.json", "w") as f:
        json.dump(save_results, f, indent=2)
    print("\nErgebnisse gespeichert: model/tflite_results.json")


if __name__ == "__main__":
    main()
