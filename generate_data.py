"""
Phase 1: Synthetische Datengenerierung für Battery-Lifetime-Prediction.

Simuliert realistische Smartphone-Nutzungssessions, bei denen sich der Akku
über die Zeit entlädt. Jede Session hat konsistente Nutzungsmuster und
erzeugt echte zeitliche Korrelationen für das LSTM.
"""

import numpy as np
import pandas as pd
import os

SEED = 42
NUM_SESSIONS = 300        # Anzahl simulierter Nutzungssessions
STEPS_PER_SESSION = 60    # Messungen pro Session (alle ~5 min -> ~5h Session)
SEQUENCE_LENGTH = 10      # Letzte 10 Messungen als LSTM-Input
MEASUREMENT_INTERVAL_H = 5 / 60  # 5 Minuten zwischen Messungen


def compute_drain_rate(screen_on, brightness, app_cat, cpu_usage,
                       wifi_on, mobile_data_on):
    """Berechnet den Akkuverbrauch in %/Stunde basierend auf aktuellen Features."""
    # Basis: ~4%/h im Idle
    base_drain = 4.0

    if screen_on:
        base_drain += 3.0 + 4.0 * (brightness / 100.0)  # +3-7% je nach Helligkeit
    # App-Kategorie
    app_drain_map = {0: 0, 1: 2.5, 2: 4.0, 3: 7.0, 4: 2.0, 5: 1.5}
    base_drain += app_drain_map.get(app_cat, 0)

    # CPU
    base_drain += 5.0 * (cpu_usage / 100.0)

    # Connectivity
    if wifi_on:
        base_drain += 0.8
    if mobile_data_on:
        base_drain += 1.5

    return base_drain  # %/Stunde


def generate_session(rng: np.random.Generator, session_id: int):
    """
    Simuliert eine vollständige Nutzungssession.
    Der Akku entlädt sich realistisch über die Zeit.
    """
    # Session-Start: zufälliger Akkulevel
    battery = rng.uniform(30, 100)

    # Session-Profil (bleibt teilweise über die Session bestehen)
    base_scenario = rng.choice(
        ["idle", "light", "medium", "heavy", "gaming", "video"],
        p=[0.12, 0.22, 0.28, 0.15, 0.12, 0.11],
    )

    wifi_on = int(rng.random() < 0.7)
    mobile_data_on = int(rng.random() < 0.5)

    rows = []
    for step in range(STEPS_PER_SESSION):
        # Gelegentlich wechselt das Nutzungsverhalten innerhalb der Session
        if rng.random() < 0.15:
            base_scenario = rng.choice(
                ["idle", "light", "medium", "heavy", "gaming", "video"],
                p=[0.15, 0.22, 0.25, 0.15, 0.12, 0.11],
            )
        if rng.random() < 0.05:
            wifi_on = 1 - wifi_on
        if rng.random() < 0.05:
            mobile_data_on = 1 - mobile_data_on

        # Features je nach Szenario
        if base_scenario == "idle":
            screen_on, brightness, app_cat = 0, 0.0, 0
            cpu_usage = rng.uniform(2, 12)
        elif base_scenario == "light":
            screen_on = 1
            brightness = rng.uniform(15, 45)
            app_cat = rng.choice([1, 4, 5])
            cpu_usage = rng.uniform(10, 35)
        elif base_scenario == "medium":
            screen_on = 1
            brightness = rng.uniform(30, 70)
            app_cat = rng.choice([1, 2, 4, 5])
            cpu_usage = rng.uniform(25, 60)
        elif base_scenario == "heavy":
            screen_on = 1
            brightness = rng.uniform(60, 100)
            app_cat = rng.choice([1, 2, 3, 4])
            cpu_usage = rng.uniform(55, 95)
        elif base_scenario == "gaming":
            screen_on = 1
            brightness = rng.uniform(65, 100)
            app_cat = 3
            cpu_usage = rng.uniform(70, 99)
        else:  # video
            screen_on = 1
            brightness = rng.uniform(50, 95)
            app_cat = 2
            cpu_usage = rng.uniform(40, 75)

        charging = 0  # Sessions ohne Laden (vereinfacht)

        # Drain berechnen
        drain_rate = compute_drain_rate(
            screen_on, brightness, app_cat, cpu_usage, wifi_on, mobile_data_on
        )
        # Etwas Rauschen auf den Drain
        drain_rate *= rng.uniform(0.85, 1.15)

        # hours_remaining = aktueller Akku / aktuelle Drain-Rate
        hours_remaining = max(battery / drain_rate, 0.0)
        # Rauschen auf die Vorhersage
        hours_remaining += rng.normal(0, 0.15)
        hours_remaining = np.clip(hours_remaining, 0.0, 24.0)

        rows.append({
            "session_id": session_id,
            "battery_level": round(battery, 1),
            "screen_on": int(screen_on),
            "brightness": round(brightness, 1),
            "active_app_category": int(app_cat),
            "wifi_on": int(wifi_on),
            "mobile_data_on": int(mobile_data_on),
            "charging": int(charging),
            "cpu_usage": round(cpu_usage, 1),
            "hours_remaining": round(hours_remaining, 2),
        })

        # Akku entladen
        battery -= drain_rate * MEASUREMENT_INTERVAL_H
        battery += rng.normal(0, 0.1)  # kleines Mess-Rauschen
        battery = np.clip(battery, 0.0, 100.0)

        if battery <= 0:
            break

    return rows


def generate_dataset(num_sessions: int = NUM_SESSIONS, seed: int = SEED) -> pd.DataFrame:
    """Generiert den vollständigen Datensatz aus mehreren Sessions."""
    rng = np.random.default_rng(seed)
    all_rows = []
    for sid in range(num_sessions):
        all_rows.extend(generate_session(rng, sid))
    df = pd.DataFrame(all_rows)
    return df


def create_sequences(df: pd.DataFrame, seq_len: int = SEQUENCE_LENGTH):
    """
    Erzeugt Zeitreihen-Sequenzen, NUR innerhalb derselben Session.
    Returns: X (num_sequences, seq_len, num_features), y (num_sequences,)
    """
    feature_cols = [c for c in df.columns if c not in ("hours_remaining", "session_id")]
    X, y = [], []

    for _, session_df in df.groupby("session_id"):
        data = session_df[feature_cols].values
        targets = session_df["hours_remaining"].values

        for i in range(len(data) - seq_len):
            X.append(data[i : i + seq_len])
            y.append(targets[i + seq_len])

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


def main():
    os.makedirs("data", exist_ok=True)

    print("Generiere synthetischen Datensatz (Sessions)...")
    df = generate_dataset()
    df.to_csv("data/battery_data.csv", index=False)
    print(f"  -> {len(df)} Datenpunkte aus {df['session_id'].nunique()} Sessions")

    # Statistiken
    print("\n--- Datensatz-Statistiken ---")
    print(df.drop(columns=["session_id"]).describe().round(2))

    print("\n--- Korrelation mit hours_remaining ---")
    corr = df.drop(columns=["session_id"]).corr()["hours_remaining"]
    corr = corr.drop("hours_remaining").sort_values()
    print(corr.round(3))

    # Sequenzen erstellen
    X, y = create_sequences(df)
    np.save("data/X_sequences.npy", X)
    np.save("data/y_sequences.npy", y)
    print(f"\n  -> Sequenzen: X={X.shape}, y={y.shape}")
    print(f"  -> Gespeichert in data/X_sequences.npy, data/y_sequences.npy")


if __name__ == "__main__":
    main()
