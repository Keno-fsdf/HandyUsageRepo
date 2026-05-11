"""
Vergleichsplot: TinyML vs. Google API
Erstellt Cumulative Error Distribution Plot.
Muss NACH train_real_data.py ausgeführt werden.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
import joblib

# --- Konfiguration (identisch mit train_real_data.py) ---
SEQUENCE_LENGTH = 10
MIN_SEGMENT_LENGTH = 15

FEATURE_COLS = [
    "battery_level", "screen_on", "brightness", "active_app_category",
    "wifi_on", "mobile_data_on", "charging", "cpu_usage",
    "temperature", "hotspot_on",
]


def find_discharge_segments(df):
    segments = []
    for session_id, session_df in df.groupby("session_id"):
        session_df = session_df.sort_values("timestamp").reset_index(drop=True)
        is_discharging = session_df["charging"] == 0
        segment_id = (~is_discharging).cumsum()
        for seg_id, seg_df in session_df[is_discharging].groupby(segment_id[is_discharging]):
            time_diffs = seg_df["timestamp"].diff()
            big_gaps = time_diffs > 300_000
            sub_segment_id = big_gaps.cumsum()
            for _, sub_seg in seg_df.groupby(sub_segment_id):
                if len(sub_seg) >= MIN_SEGMENT_LENGTH:
                    segments.append(sub_seg.copy())
    return segments


def create_sequences_per_segment(segments, seq_len=SEQUENCE_LENGTH):
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

        targets = np.array([
            (timestamps_ms[-1] - timestamps_ms[i]) / 3_600_000 + extra_hours
            for i in range(len(seg))
        ], dtype=np.float32)

        for i in range(len(seg) - seq_len):
            all_features.append(features[i:i + seq_len])
            all_targets.append(targets[i + seq_len - 1])
            all_sys.append(sys_est[i + seq_len - 1])

    return np.array(all_features), np.array(all_targets), np.array(all_sys)


def main():
    print("Lade Daten...")
    df = pd.read_csv("data/real_battery_data.csv")
    segments = find_discharge_segments(df)
    X, y, sys_est = create_sequences_per_segment(segments)

    # Gleicher Split wie beim Training
    indices = np.arange(len(X))
    idx_train, idx_temp = train_test_split(indices, test_size=0.3, random_state=42)
    idx_val, idx_test = train_test_split(idx_temp, test_size=0.5, random_state=42)

    X_test = X[idx_test]
    y_test = y[idx_test]
    sys_test = sys_est[idx_test]

    # Normalisieren mit gespeichertem Scaler
    scaler = joblib.load("model/scaler_real.joblib")
    n, seq_len, n_feat = X_test.shape
    X_test_norm = scaler.transform(X_test.reshape(-1, n_feat)).reshape(n, seq_len, n_feat)

    # Modell laden und vorhersagen
    print("Lade Modell...")
    model = tf.keras.models.load_model("model/battery_model_real.keras")
    y_pred_tinyml = model.predict(X_test_norm, verbose=0).flatten()

    # --- Cumulative Error Distribution ---
    errors_tinyml = np.abs(y_test - y_pred_tinyml)

    # Google API: nur wo verfuegbar (> 0)
    valid_sys = sys_test > 0
    sys_hours = sys_test[valid_sys] / 60.0
    errors_google = np.abs(y_test[valid_sys] - sys_hours)

    tolerances = np.linspace(0, 10, 300)

    acc_tinyml = [np.mean(errors_tinyml <= t) * 100 for t in tolerances]
    acc_google = [np.mean(errors_google <= t) * 100 for t in tolerances]

    # Plot
    plt.figure(figsize=(9, 5.5))
    plt.plot(tolerances, acc_tinyml, label=f"TinyML Conv1D (n={len(y_test)})",
             linewidth=2.5, color="#2196F3")
    plt.plot(tolerances, acc_google, label=f"Google API (n={valid_sys.sum()})",
             linewidth=2.5, color="#FF9800", linestyle="--")

    plt.axhline(y=90, color='gray', linestyle=':', alpha=0.5, label="90% Schwelle")
    plt.axvline(x=1, color='gray', linestyle=':', alpha=0.4)
    plt.axvline(x=2, color='gray', linestyle=':', alpha=0.3)

    # Annotations
    tinyml_1h = np.mean(errors_tinyml <= 1.0) * 100
    google_1h = np.mean(errors_google <= 1.0) * 100
    plt.annotate(f'{tinyml_1h:.0f}%', xy=(1, tinyml_1h), fontsize=9,
                 color="#2196F3", fontweight='bold',
                 xytext=(1.3, tinyml_1h - 5))
    plt.annotate(f'{google_1h:.0f}%', xy=(1, google_1h), fontsize=9,
                 color="#FF9800", fontweight='bold',
                 xytext=(1.3, google_1h + 3))

    plt.xlabel("Fehlertoleranz (Stunden)", fontsize=12)
    plt.ylabel("Trefferquote (%)", fontsize=12)
    plt.title("Cumulative Error Distribution:\nTinyML vs. Google API", fontsize=13)
    plt.legend(fontsize=10, loc="lower right")
    plt.grid(True, alpha=0.3)
    plt.xlim(0, 10)
    plt.ylim(0, 105)
    plt.tight_layout()

    os.makedirs("plots", exist_ok=True)
    plt.savefig("plots/error_distribution_comparison.png", dpi=150)
    plt.close()
    print("Plot gespeichert: plots/error_distribution_comparison.png")

    # Metriken ausgeben
    print(f"\n{'='*50}")
    print(f"  Bei ±1h Toleranz:")
    print(f"    TinyML: {tinyml_1h:.1f}%")
    print(f"    Google: {google_1h:.1f}%")
    print(f"  Bei ±2h Toleranz:")
    tinyml_2h = np.mean(errors_tinyml <= 2.0) * 100
    google_2h = np.mean(errors_google <= 2.0) * 100
    print(f"    TinyML: {tinyml_2h:.1f}%")
    print(f"    Google: {google_2h:.1f}%")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
