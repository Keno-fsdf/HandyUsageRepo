"""
Training-Pipeline für echte Batterie-Daten vom Xiaomi.

Verarbeitet die CSV von der Android Data Collector App:
1. Lädt echte Messdaten (10 Features + session_id + system_estimate)
2. Identifiziert Entlade-Segmente (charging=0)
3. Berechnet Target: verbleibende Stunden bis zum Laden
4. Bildet Sequenzen (Sliding Window) innerhalb jeder Session
5. Trainiert Conv1D-Modell
6. Evaluiert und vergleicht mit Android-Schätzung
7. Konvertiert zu TFLite (INT8)
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import joblib
import json

# --- Konfiguration ---
SEQUENCE_LENGTH = 10
EPOCHS = 150
BATCH_SIZE = 32
LEARNING_RATE = 5e-4
PATIENCE = 20
MIN_SEGMENT_LENGTH = 15  # Mindestens 15 Punkte pro Entlade-Segment

# Features die das Modell bekommt (ohne session_id, timestamp, datetime, system_estimate)
FEATURE_COLS = [
    "battery_level", "screen_on", "brightness", "active_app_category",
    "wifi_on", "mobile_data_on", "charging", "cpu_usage",
    "temperature", "hotspot_on",
]


def load_and_prepare_data(csv_path="data/real_battery_data.csv"):
    """Lädt CSV und bereitet Daten vor."""
    df = pd.read_csv(csv_path)
    print(f"Rohdaten: {len(df)} Zeilen, {df['session_id'].nunique()} Sessions")
    print(f"Battery Range: {df['battery_level'].min():.0f}% - {df['battery_level'].max():.0f}%")
    print(f"Laden: {(df['charging']==1).sum()}, Entladen: {(df['charging']==0).sum()}")

    # Timestamp in Stunden umrechnen (für Target-Berechnung)
    df["time_h"] = (df["timestamp"] - df["timestamp"].iloc[0]) / 3_600_000.0

    return df


def find_discharge_segments(df):
    """
    Findet zusammenhängende Entlade-Segmente innerhalb jeder Session.
    Ein Segment endet wenn: charging=1 wird, Session wechselt, oder große Zeitlücke.
    """
    segments = []

    for session_id, session_df in df.groupby("session_id"):
        session_df = session_df.sort_values("timestamp").reset_index(drop=True)

        # Segmente finden: Gruppen von aufeinanderfolgenden charging=0 Zeilen
        is_discharging = session_df["charging"] == 0
        segment_id = (~is_discharging).cumsum()

        for seg_id, seg_df in session_df[is_discharging].groupby(segment_id[is_discharging]):
            # Zeitlücken > 5 Minuten innerhalb des Segments → splitten
            time_diffs = seg_df["timestamp"].diff()
            big_gaps = time_diffs > 300_000  # 5 min in ms
            sub_segment_id = big_gaps.cumsum()

            for _, sub_seg in seg_df.groupby(sub_segment_id):
                if len(sub_seg) >= MIN_SEGMENT_LENGTH:
                    segments.append(sub_seg.copy())

    print(f"Entlade-Segmente gefunden: {len(segments)}")
    for i, seg in enumerate(segments):
        duration_h = (seg["timestamp"].iloc[-1] - seg["timestamp"].iloc[0]) / 3_600_000
        print(f"  Segment {i+1}: {len(seg)} Punkte, "
              f"{seg['battery_level'].iloc[0]:.0f}% → {seg['battery_level'].iloc[-1]:.0f}%, "
              f"{duration_h:.1f}h")

    return segments


def compute_target(segments):
    """
    Berechnet für jeden Datenpunkt: verbleibende Stunden bis Segment-Ende.

    Da der Nutzer selten auf 0% geht, extrapolieren wir:
    remaining_hours = (time_end - time_current) + battery_at_end / drain_rate

    Wenn das Segment mit z.B. 30% endet und der Drain-Rate 5%/h ist,
    addieren wir noch 30/5 = 6h dazu.
    """
    all_features = []
    all_targets = []
    all_system_estimates = []

    for seg in segments:
        seg = seg.reset_index(drop=True)
        timestamps_ms = seg["timestamp"].values
        battery = seg["battery_level"].values
        features = seg[FEATURE_COLS].values
        sys_est = seg["system_estimate_min"].values

        # Drain-Rate des gesamten Segments (% pro Stunde)
        total_time_h = (timestamps_ms[-1] - timestamps_ms[0]) / 3_600_000
        total_drain = battery[0] - battery[-1]

        if total_time_h <= 0 or total_drain <= 0:
            # Kein Drain → überspringen (z.B. Akku bleibt bei 100%)
            continue

        drain_rate = total_drain / total_time_h  # %/h

        # Extrapolierte Rest-Zeit wenn das Segment nicht bei 0% endet
        extra_hours = battery[-1] / drain_rate if drain_rate > 0 else 0

        for i in range(len(seg)):
            # Zeit bis Segment-Ende
            time_remaining_h = (timestamps_ms[-1] - timestamps_ms[i]) / 3_600_000
            # Plus extrapolierte Zeit
            target = time_remaining_h + extra_hours

            all_features.append(features[i])
            all_targets.append(target)
            all_system_estimates.append(sys_est[i])

    X = np.array(all_features, dtype=np.float32)
    y = np.array(all_targets, dtype=np.float32)
    sys_estimates = np.array(all_system_estimates, dtype=np.float32)

    print(f"\nTarget-Variable berechnet:")
    print(f"  Datenpunkte: {len(y)}")
    print(f"  Remaining Hours — Min: {y.min():.1f}h, Max: {y.max():.1f}h, "
          f"Mean: {y.mean():.1f}h, Median: {np.median(y):.1f}h")

    return X, y, sys_estimates


def create_sequences(X, y, sys_estimates, seq_len=SEQUENCE_LENGTH):
    """Sliding Window über die Feature-Daten."""
    X_seq, y_seq, sys_seq = [], [], []

    # Sequenzen nur innerhalb zusammenhängender Datenpunkte bilden
    # (X, y kommen schon segmentiert → einfacher Sliding Window)
    for i in range(len(X) - seq_len):
        X_seq.append(X[i:i + seq_len])
        y_seq.append(y[i + seq_len - 1])  # Target des letzten Punkts der Sequenz
        sys_seq.append(sys_estimates[i + seq_len - 1])

    return np.array(X_seq), np.array(y_seq), np.array(sys_seq)


def create_sequences_per_segment(segments, seq_len=SEQUENCE_LENGTH):
    """
    Bildet Sequenzen separat pro Segment (damit keine Sequenz
    über Segment-Grenzen hinweg geht).
    """
    all_features = []
    all_targets = []
    all_sys = []

    for seg in segments:
        seg = seg.reset_index(drop=True)
        timestamps_ms = seg["timestamp"].values
        battery = seg["battery_level"].values
        features = seg[FEATURE_COLS].values
        sys_est = seg["system_estimate_min"].values

        total_time_h = (timestamps_ms[-1] - timestamps_ms[0]) / 3_600_000
        total_drain = battery[0] - battery[-1]

        if total_time_h <= 0 or total_drain <= 0:
            continue

        drain_rate = total_drain / total_time_h
        extra_hours = battery[-1] / drain_rate if drain_rate > 0 else 0

        # Targets berechnen
        targets = np.array([
            (timestamps_ms[-1] - timestamps_ms[i]) / 3_600_000 + extra_hours
            for i in range(len(seg))
        ], dtype=np.float32)

        # Sliding Window innerhalb dieses Segments
        for i in range(len(seg) - seq_len):
            all_features.append(features[i:i + seq_len])
            all_targets.append(targets[i + seq_len - 1])
            all_sys.append(sys_est[i + seq_len - 1])

    X = np.array(all_features, dtype=np.float32)
    y = np.array(all_targets, dtype=np.float32)
    sys_est = np.array(all_sys, dtype=np.float32)

    print(f"Sequenzen erstellt: {len(X)}")
    print(f"  Shape: X={X.shape}, y={y.shape}")
    print(f"  Target Range: {y.min():.1f}h - {y.max():.1f}h")

    return X, y, sys_est


def normalize_data(X_train, X_val, X_test):
    """StandardScaler auf Train fitten, auf alle anwenden."""
    n_train, seq_len, n_feat = X_train.shape
    scaler = StandardScaler()

    X_train_flat = X_train.reshape(-1, n_feat)
    scaler.fit(X_train_flat)

    X_train_n = scaler.transform(X_train_flat).reshape(n_train, seq_len, n_feat)
    X_val_n = scaler.transform(X_val.reshape(-1, n_feat)).reshape(X_val.shape)
    X_test_n = scaler.transform(X_test.reshape(-1, n_feat)).reshape(X_test.shape)

    os.makedirs("model", exist_ok=True)
    joblib.dump(scaler, "model/scaler_real.joblib")
    print("Scaler gespeichert: model/scaler_real.joblib")

    return X_train_n, X_val_n, X_test_n, scaler


def build_model(n_features):
    """Conv1D-Modell, angepasst für 10 Features."""
    inputs = keras.Input(shape=(SEQUENCE_LENGTH, n_features), name="input")

    x = layers.Conv1D(32, kernel_size=3, padding="same", activation="relu", name="conv1")(inputs)
    x = layers.Conv1D(32, kernel_size=3, padding="same", activation="relu", name="conv2")(x)
    x = layers.GlobalAveragePooling1D(name="gap")(x)

    x = layers.Dense(32, activation="relu", name="dense_1")(x)
    x = layers.Dropout(0.2)(x)
    x = layers.Dense(16, activation="relu", name="dense_2")(x)

    outputs = layers.Dense(1, activation="linear", name="output")(x)

    model = keras.Model(inputs=inputs, outputs=outputs, name="battery_predictor_real")
    return model


def train(model, X_train, y_train, X_val, y_val):
    """Training mit Early Stopping."""
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss="mse",
        metrics=["mae"],
    )

    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=PATIENCE, restore_best_weights=True
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=5, min_lr=1e-6
        ),
    ]

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=callbacks,
        verbose=1,
    )
    return history


def evaluate(model, X_test, y_test, sys_estimates_test):
    """Evaluation + Vergleich mit Android-Schätzung."""
    y_pred = model.predict(X_test, verbose=0).flatten()

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    acc_1h = np.mean(np.abs(y_test - y_pred) <= 1.0) * 100
    acc_2h = np.mean(np.abs(y_test - y_pred) <= 2.0) * 100

    print("\n" + "=" * 55)
    print("  DEIN MODELL — Evaluation auf Test-Daten")
    print("=" * 55)
    print(f"  MAE:            {mae:.3f} Stunden ({mae*60:.0f} min)")
    print(f"  RMSE:           {rmse:.3f} Stunden")
    print(f"  R²:             {r2:.4f}")
    print(f"  Accuracy ±1h:   {acc_1h:.1f}%")
    print(f"  Accuracy ±2h:   {acc_2h:.1f}%")

    # Vergleich mit Android-Schätzung (nur wo verfügbar: > 0)
    valid_sys = sys_estimates_test > 0
    if valid_sys.sum() > 10:
        sys_hours = sys_estimates_test[valid_sys] / 60.0  # min → Stunden
        y_test_valid = y_test[valid_sys]
        y_pred_valid = y_pred[valid_sys]

        sys_mae = mean_absolute_error(y_test_valid, sys_hours)
        model_mae_valid = mean_absolute_error(y_test_valid, y_pred_valid)
        sys_acc_1h = np.mean(np.abs(y_test_valid - sys_hours) <= 1.0) * 100
        model_acc_1h = np.mean(np.abs(y_test_valid - y_pred_valid) <= 1.0) * 100

        print("\n" + "=" * 55)
        print("  VERGLEICH: Dein Modell vs. Android-Schätzung")
        print(f"  (auf {valid_sys.sum()} Datenpunkten mit System-Schätzung)")
        print("=" * 55)
        print(f"  {'Metrik':<20} {'Dein Modell':>12} {'Android':>12}")
        print(f"  {'-'*20} {'-'*12} {'-'*12}")
        print(f"  {'MAE (Stunden)':<20} {model_mae_valid:>12.3f} {sys_mae:>12.3f}")
        print(f"  {'Accuracy ±1h':<20} {model_acc_1h:>11.1f}% {sys_acc_1h:>11.1f}%")
        winner = "Dein Modell" if model_mae_valid < sys_mae else "Android"
        print(f"\n  → Gewinner: {winner} 🏆")
    else:
        print("\n  (Zu wenig System-Schätzungen für Vergleich)")

    print("=" * 55)

    return {
        "mae": float(mae), "rmse": float(rmse), "r2": float(r2),
        "accuracy_1h": float(acc_1h), "accuracy_2h": float(acc_2h),
        "y_test": y_test, "y_pred": y_pred,
    }


def convert_tflite(model, X_train):
    """Konvertiert zu TFLite INT8."""
    def representative_dataset():
        for i in range(min(200, len(X_train))):
            yield [X_train[i:i+1].astype(np.float32)]

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = representative_dataset
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8

    tflite_model = converter.convert()

    path = "model/battery_model_real.tflite"
    with open(path, "wb") as f:
        f.write(tflite_model)

    size_kb = len(tflite_model) / 1024
    print(f"\nTFLite INT8 gespeichert: {path} ({size_kb:.1f} KB)")
    return tflite_model


def plot_results(history, metrics):
    """Visualisierungen."""
    os.makedirs("plots", exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    axes[0, 0].plot(history.history["loss"], label="Train Loss")
    axes[0, 0].plot(history.history["val_loss"], label="Val Loss")
    axes[0, 0].set_title("Training & Validation Loss")
    axes[0, 0].set_xlabel("Epoch")
    axes[0, 0].set_ylabel("MSE Loss")
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    axes[0, 1].plot(history.history["mae"], label="Train MAE")
    axes[0, 1].plot(history.history["val_mae"], label="Val MAE")
    axes[0, 1].set_title("Training & Validation MAE")
    axes[0, 1].set_xlabel("Epoch")
    axes[0, 1].set_ylabel("MAE (Stunden)")
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    y_test = metrics["y_test"]
    y_pred = metrics["y_pred"]
    axes[1, 0].scatter(y_test, y_pred, alpha=0.3, s=10)
    lims = [0, max(y_test.max(), y_pred.max()) + 1]
    axes[1, 0].plot(lims, lims, "r--", linewidth=1.5, label="Ideal")
    axes[1, 0].set_title("Predicted vs Actual")
    axes[1, 0].set_xlabel("Actual (Stunden)")
    axes[1, 0].set_ylabel("Predicted (Stunden)")
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    errors = y_pred - y_test
    axes[1, 1].hist(errors, bins=50, edgecolor="black", alpha=0.7)
    axes[1, 1].axvline(0, color="r", linestyle="--")
    axes[1, 1].set_title(f"Error Distribution (MAE={metrics['mae']:.2f}h)")
    axes[1, 1].set_xlabel("Prediction Error (Stunden)")
    axes[1, 1].set_ylabel("Häufigkeit")
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("plots/real_training_results.png", dpi=150)
    plt.close()
    print("Plots gespeichert: plots/real_training_results.png")


def main():
    print("=" * 55)
    print("  BATTERY PREDICTOR — Training mit echten Daten")
    print("=" * 55)

    # 1. Daten laden
    df = load_and_prepare_data()

    # 2. Entlade-Segmente finden
    segments = find_discharge_segments(df)
    if not segments:
        print("FEHLER: Keine Entlade-Segmente gefunden!")
        return

    # 3. Sequenzen + Targets erstellen (pro Segment)
    X, y, sys_est = create_sequences_per_segment(segments)
    n_features = X.shape[2]
    print(f"Features: {n_features} ({FEATURE_COLS})")

    # 4. Train/Val/Test Split (70/15/15)
    indices = np.arange(len(X))
    idx_train, idx_temp = train_test_split(indices, test_size=0.3, random_state=42)
    idx_val, idx_test = train_test_split(idx_temp, test_size=0.5, random_state=42)

    X_train, y_train = X[idx_train], y[idx_train]
    X_val, y_val = X[idx_val], y[idx_val]
    X_test, y_test = X[idx_test], y[idx_test]
    sys_test = sys_est[idx_test]

    print(f"Split: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}")

    # 5. Normalisierung
    X_train, X_val, X_test, scaler = normalize_data(X_train, X_val, X_test)

    # 6. Modell bauen
    model = build_model(n_features)
    model.summary()

    param_count = model.count_params()
    print(f"\nParameter: {param_count:,}")
    print(f"Geschätzte INT8-Größe: ~{param_count / 1024:.1f} KB")

    # 7. Training
    print("\nStarte Training...")
    history = train(model, X_train, y_train, X_val, y_val)

    # 8. Evaluation + Vergleich mit Android
    metrics = evaluate(model, X_test, y_test, sys_test)

    # 9. Plots
    plot_results(history, metrics)

    # 10. Modell speichern
    os.makedirs("model", exist_ok=True)
    model.save("model/battery_model_real.keras")
    print(f"Keras-Modell: model/battery_model_real.keras")

    # 11. TFLite-Konvertierung
    convert_tflite(model, X[idx_train])  # Unnormalisierte Daten für Representative Dataset

    # 12. Metriken speichern
    save_metrics = {k: v for k, v in metrics.items() if k not in ("y_test", "y_pred")}
    with open("model/metrics_real.json", "w") as f:
        json.dump(save_metrics, f, indent=2)
    print(f"Metriken: model/metrics_real.json")

    print("\n✅ Fertig! Modell trainiert und konvertiert.")


if __name__ == "__main__":
    main()
