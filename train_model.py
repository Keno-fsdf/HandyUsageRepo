"""
Phase 2: Model Training & Evaluation für Battery-Lifetime-Prediction.

Trainiert ein kompaktes FFNN + LSTM Hybrid-Modell, optimiert für TinyML.
Ziel: <500 KB nach Quantisierung, >75% Accuracy.
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

# --- Konfiguration ---
SEQUENCE_LENGTH = 10
NUM_FEATURES = 8
EPOCHS = 150
BATCH_SIZE = 32
LEARNING_RATE = 5e-4
PATIENCE = 20  # Early stopping


def load_data():
    """Lädt Sequenz-Daten aus .npy Dateien."""
    X = np.load("data/X_sequences.npy")
    y = np.load("data/y_sequences.npy")
    print(f"Daten geladen: X={X.shape}, y={y.shape}")
    return X, y


def normalize_data(X_train, X_val, X_test):
    """Normalisiert Features mit StandardScaler (fit nur auf Train)."""
    n_train, seq_len, n_feat = X_train.shape
    scaler = StandardScaler()

    # Flatten -> fit -> transform -> reshape
    X_train_flat = X_train.reshape(-1, n_feat)
    scaler.fit(X_train_flat)

    X_train_norm = scaler.transform(X_train_flat).reshape(n_train, seq_len, n_feat)
    X_val_norm = scaler.transform(X_val.reshape(-1, n_feat)).reshape(X_val.shape)
    X_test_norm = scaler.transform(X_test.reshape(-1, n_feat)).reshape(X_test.shape)

    # Scaler speichern für Inference
    os.makedirs("model", exist_ok=True)
    joblib.dump(scaler, "model/scaler.joblib")
    print("Scaler gespeichert: model/scaler.joblib")

    return X_train_norm, X_val_norm, X_test_norm, scaler


def build_model(seq_len: int = SEQUENCE_LENGTH, n_features: int = NUM_FEATURES):
    """
    Kompaktes Conv1D-Modell für TinyML.
    Conv1D fängt temporale Muster ab, ist TFLite-nativ und schneller als LSTM.
    """
    inputs = keras.Input(shape=(seq_len, n_features), name="input")

    # Temporal Feature Extraction via Conv1D
    x = layers.Conv1D(32, kernel_size=3, padding="same", activation="relu", name="conv1")(inputs)
    x = layers.Conv1D(32, kernel_size=3, padding="same", activation="relu", name="conv2")(x)
    x = layers.GlobalAveragePooling1D(name="gap")(x)

    # Dense-Head
    x = layers.Dense(32, activation="relu", name="dense_1")(x)
    x = layers.Dropout(0.2)(x)
    x = layers.Dense(16, activation="relu", name="dense_2")(x)

    # Output: verbleibende Stunden (Regression)
    outputs = layers.Dense(1, activation="linear", name="output")(x)

    model = keras.Model(inputs=inputs, outputs=outputs, name="battery_predictor")
    return model


def train_model(model, X_train, y_train, X_val, y_val):
    """Trainiert das Modell mit Early Stopping und LR-Reduction."""
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


def evaluate_model(model, X_test, y_test):
    """Berechnet Evaluation Metrics und gibt sie aus."""
    y_pred = model.predict(X_test, verbose=0).flatten()

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    # "Accuracy" als %-Anteil der Vorhersagen innerhalb ±1h Toleranz
    tolerance_1h = np.mean(np.abs(y_test - y_pred) <= 1.0) * 100
    tolerance_2h = np.mean(np.abs(y_test - y_pred) <= 2.0) * 100

    print("\n" + "=" * 50)
    print("  EVALUATION METRICS")
    print("=" * 50)
    print(f"  MAE:                  {mae:.3f} Stunden")
    print(f"  RMSE:                 {rmse:.3f} Stunden")
    print(f"  R² Score:             {r2:.4f}")
    print(f"  Accuracy (±1h):       {tolerance_1h:.1f}%")
    print(f"  Accuracy (±2h):       {tolerance_2h:.1f}%")
    print("=" * 50)

    return {
        "mae": mae, "rmse": rmse, "r2": r2,
        "accuracy_1h": tolerance_1h, "accuracy_2h": tolerance_2h,
        "y_test": y_test, "y_pred": y_pred,
    }


def plot_results(history, metrics):
    """Erstellt Visualisierungen für Training und Evaluation."""
    os.makedirs("plots", exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 1) Training Loss
    axes[0, 0].plot(history.history["loss"], label="Train Loss")
    axes[0, 0].plot(history.history["val_loss"], label="Val Loss")
    axes[0, 0].set_title("Training & Validation Loss")
    axes[0, 0].set_xlabel("Epoch")
    axes[0, 0].set_ylabel("MSE Loss")
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # 2) Training MAE
    axes[0, 1].plot(history.history["mae"], label="Train MAE")
    axes[0, 1].plot(history.history["val_mae"], label="Val MAE")
    axes[0, 1].set_title("Training & Validation MAE")
    axes[0, 1].set_xlabel("Epoch")
    axes[0, 1].set_ylabel("MAE (Stunden)")
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    # 3) Predicted vs Actual
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

    # 4) Error Distribution
    errors = y_pred - y_test
    axes[1, 1].hist(errors, bins=50, edgecolor="black", alpha=0.7)
    axes[1, 1].axvline(0, color="r", linestyle="--")
    axes[1, 1].set_title(f"Error Distribution (MAE={metrics['mae']:.2f}h)")
    axes[1, 1].set_xlabel("Prediction Error (Stunden)")
    axes[1, 1].set_ylabel("Häufigkeit")
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("plots/training_results.png", dpi=150)
    plt.close()
    print("\nPlots gespeichert: plots/training_results.png")


def main():
    print("=" * 50)
    print("  BATTERY LIFETIME PREDICTOR - TRAINING")
    print("=" * 50)

    # Daten laden
    X, y = load_data()

    # Train/Val/Test Split (70/15/15)
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)
    print(f"Split: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}")

    # Normalisierung
    X_train, X_val, X_test, scaler = normalize_data(X_train, X_val, X_test)

    # Modell bauen
    model = build_model()
    model.summary()

    param_count = model.count_params()
    print(f"\nParameter: {param_count:,}")
    print(f"Geschätzte Größe (FP32): ~{param_count * 4 / 1024:.1f} KB")
    print(f"Geschätzte Größe (INT8): ~{param_count / 1024:.1f} KB")

    # Training
    print("\nStarte Training...")
    history = train_model(model, X_train, y_train, X_val, y_val)

    # Evaluation
    metrics = evaluate_model(model, X_test, y_test)

    # Plots
    plot_results(history, metrics)

    # Modell speichern (Keras-Format)
    os.makedirs("model", exist_ok=True)
    model.save("model/battery_model.keras")
    print(f"\nModell gespeichert: model/battery_model.keras")

    # Metrics als JSON speichern
    import json
    metrics_save = {k: float(v) if isinstance(v, (float, np.floating)) else v
                    for k, v in metrics.items() if k not in ("y_test", "y_pred")}
    with open("model/metrics.json", "w") as f:
        json.dump(metrics_save, f, indent=2)
    print("Metrics gespeichert: model/metrics.json")


if __name__ == "__main__":
    main()
