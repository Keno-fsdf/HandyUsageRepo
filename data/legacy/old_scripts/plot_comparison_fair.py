"""
Fairer Vergleich: Nur auf Daten wo echte Messwerte vorliegen.
Kein extrapoliertes Target - nur gemessene Restlaufzeit innerhalb des Segments.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import tensorflow as tf
import joblib

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


def create_sequences_no_extrapolation(segments, seq_len=SEQUENCE_LENGTH):
    """
    Target = NUR die echte gemessene Zeit bis Segment-Ende.
    KEINE Extrapolation. Nur echte Daten.
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

        # NUR echte gemessene Restzeit, KEINE Extrapolation
        targets = np.array([
            (timestamps_ms[-1] - timestamps_ms[i]) / 3_600_000
            for i in range(len(seg))
        ], dtype=np.float32)

        for i in range(len(seg) - seq_len):
            all_features.append(features[i:i + seq_len])
            all_targets.append(targets[i + seq_len - 1])
            all_sys.append(sys_est[i + seq_len - 1])

    return np.array(all_features), np.array(all_targets), np.array(all_sys)


def main():
    print("=" * 55)
    print("  FAIRER VERGLEICH (ohne Extrapolation)")
    print("=" * 55)

    # Daten laden
    df = pd.read_csv("data/real_battery_data.csv")
    segments = find_discharge_segments(df)
    
    # Sequenzen OHNE Extrapolation
    X, y_real, sys_est = create_sequences_no_extrapolation(segments)
    print(f"Datenpunkte: {len(X)}")
    print(f"Target Range: {y_real.min():.1f}h - {y_real.max():.1f}h")
    print(f"(Das sind NUR echte gemessene Zeiten, keine Extrapolation)")

    # Gleicher Split
    indices = np.arange(len(X))
    idx_train, idx_temp = train_test_split(indices, test_size=0.3, random_state=42)
    idx_val, idx_test = train_test_split(idx_temp, test_size=0.5, random_state=42)

    X_test = X[idx_test]
    y_test = y_real[idx_test]
    sys_test = sys_est[idx_test]

    # Normalisieren mit gespeichertem Scaler
    scaler = joblib.load("model/scaler_real.joblib")
    n, seq_len, n_feat = X_test.shape
    X_test_norm = scaler.transform(
        X_test.reshape(-1, n_feat)).reshape(n, seq_len, n_feat)

    # TinyML Vorhersage
    model = tf.keras.models.load_model("model/battery_model_real.keras")
    y_pred_tinyml = model.predict(X_test_norm, verbose=0).flatten()

    # Fehler berechnen
    errors_tinyml = np.abs(y_test - y_pred_tinyml)

    # Google API (nur wo verfuegbar)
    valid_sys = sys_test > 0
    sys_hours = sys_test[valid_sys] / 60.0
    y_test_google = y_test[valid_sys]
    errors_google = np.abs(y_test_google - sys_hours)

    # TinyML auf denselben Datenpunkten wie Google (fuer fairen Vergleich)
    y_pred_tinyml_valid = y_pred_tinyml[valid_sys]
    errors_tinyml_valid = np.abs(y_test_google - y_pred_tinyml_valid)

    # --- Metriken ---
    print(f"\n{'='*55}")
    print(f"  ERGEBNISSE (nur echte gemessene Restzeit)")
    print(f"{'='*55}")
    print(f"  {'Metrik':<20} {'TinyML':>12} {'Google API':>12}")
    print(f"  {'-'*20} {'-'*12} {'-'*12}")

    mae_t = mean_absolute_error(y_test_google, y_pred_tinyml_valid)
    mae_g = mean_absolute_error(y_test_google, sys_hours)
    print(f"  {'MAE (Stunden)':<20} {mae_t:>12.2f} {mae_g:>12.2f}")

    rmse_t = np.sqrt(mean_squared_error(y_test_google, y_pred_tinyml_valid))
    rmse_g = np.sqrt(mean_squared_error(y_test_google, sys_hours))
    print(f"  {'RMSE (Stunden)':<20} {rmse_t:>12.2f} {rmse_g:>12.2f}")

    acc1_t = np.mean(errors_tinyml_valid <= 1.0) * 100
    acc1_g = np.mean(errors_google <= 1.0) * 100
    print(f"  {'Accuracy ±1h':<20} {acc1_t:>11.1f}% {acc1_g:>11.1f}%")

    acc2_t = np.mean(errors_tinyml_valid <= 2.0) * 100
    acc2_g = np.mean(errors_google <= 2.0) * 100
    print(f"  {'Accuracy ±2h':<20} {acc2_t:>11.1f}% {acc2_g:>11.1f}%")

    print(f"\n  Datenpunkte: {valid_sys.sum()} (wo Google API verfuegbar)")
    print(f"{'='*55}")

    # --- Plot: Cumulative Error Distribution ---
    tolerances = np.linspace(0, 10, 300)

    acc_curve_tinyml = [np.mean(errors_tinyml_valid <= t) * 100 
                         for t in tolerances]
    acc_curve_google = [np.mean(errors_google <= t) * 100 
                         for t in tolerances]

    plt.figure(figsize=(9, 5.5))
    plt.plot(tolerances, acc_curve_tinyml, 
             label=f"TinyML Conv1D (n={valid_sys.sum()})",
             linewidth=2.5, color="#2196F3")
    plt.plot(tolerances, acc_curve_google, 
             label=f"Google API (n={valid_sys.sum()})",
             linewidth=2.5, color="#FF9800", linestyle="--")

    plt.axhline(y=90, color='gray', linestyle=':', alpha=0.5, 
                label="90% Schwelle")
    plt.axvline(x=1, color='gray', linestyle=':', alpha=0.4)
    plt.axvline(x=2, color='gray', linestyle=':', alpha=0.3)

    plt.annotate(f'TinyML: {acc1_t:.0f}%', xy=(1.1, acc1_t), 
                 fontsize=9, color="#2196F3", fontweight='bold')
    plt.annotate(f'Google: {acc1_g:.0f}%', xy=(1.1, acc1_g - 4), 
                 fontsize=9, color="#FF9800", fontweight='bold')

    plt.xlabel("Fehlertoleranz (Stunden)", fontsize=12)
    plt.ylabel("Trefferquote (%)", fontsize=12)
    plt.title("Fairer Vergleich: TinyML vs. Google API\n"
              "(nur echte gemessene Restlaufzeit, keine Extrapolation)", 
              fontsize=13)
    plt.legend(fontsize=10, loc="lower right")
    plt.grid(True, alpha=0.3)
    plt.xlim(0, 10)
    plt.ylim(0, 105)
    plt.tight_layout()

    os.makedirs("plots", exist_ok=True)
    plt.savefig("plots/fair_comparison.png", dpi=150)
    plt.close()
    print("\nPlot gespeichert: plots/fair_comparison.png")


if __name__ == "__main__":
    main()
