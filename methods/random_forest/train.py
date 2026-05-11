"""
Random Forest Regressor als Sanity-Modell.

Begruendung im Paper-Kontext:
    Wenn der Conv1D auf C-Index 0.5 (Zufallsniveau) landet, ist die Frage:
    Liegt das am Modell oder an den Daten? Random Forest ist ein
    voellig anderes Modell-Paradigma (Ensembles ueber flachen Features),
    bekannt fuer robuste Performance auf strukturierten Tabellen.

    Wenn der RF auf denselben Features ebenfalls bei C-Index ~0.5 landet,
    ist es ein **Daten-Limit**, kein Modell-Fehler.
    Wenn der RF deutlich besser performt, ist Conv1D mit 5697 Parametern
    schlicht ueberfittet/unterausgestattet.

Input-Aufbereitung:
    Die Sliding-Window-Tensoren (n, 10, 10) werden zu flachen (n, 100)
    Vektoren reshaped. RF kann zeitliche Struktur nicht direkt verarbeiten,
    aber durch das Flatten hat es Zugriff auf die letzten 10 Zeitpunkte
    aller 10 Features - das ist die gleiche Information, die der Conv1D
    bekommt.

Hyperparameter konservativ gewaehlt:
    n_estimators=200, max_depth=None (default), random_state fuer
    Reproduzierbarkeit.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import yaml
from sklearn.ensemble import RandomForestRegressor


def main(config_path: str = "configs/default.yaml") -> None:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    processed = Path(cfg["paths"]["processed_dir"])
    models = Path(cfg["paths"]["models_dir"])

    train = dict(np.load(processed / "train.npz"))
    val = dict(np.load(processed / "val.npz"))

    n_train, seq_len, n_feat = train["X"].shape
    X_train = train["X"].reshape(n_train, seq_len * n_feat)
    X_val = val["X"].reshape(len(val["X"]), seq_len * n_feat)

    rf = RandomForestRegressor(
        n_estimators=200,
        max_depth=None,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    print(f"[rf-train] fitting on X={X_train.shape}, y={train['y_extrap'].shape}")
    rf.fit(X_train, train["y_extrap"])

    val_pred = rf.predict(X_val)
    val_mae = float(np.mean(np.abs(val["y_extrap"] - val_pred)))
    train_pred = rf.predict(X_train)
    train_mae = float(np.mean(np.abs(train["y_extrap"] - train_pred)))
    print(f"[rf-train] train_mae={train_mae:.3f}h  val_mae={val_mae:.3f}h")

    models.mkdir(parents=True, exist_ok=True)
    joblib.dump(rf, models / "random_forest.joblib")
    summary = {
        "n_estimators": rf.n_estimators,
        "n_input_features": int(seq_len * n_feat),
        "train_mae_h_extrap": round(train_mae, 4),
        "val_mae_h_extrap": round(val_mae, 4),
        "train_n": int(n_train),
        "val_n": int(len(val["X"])),
    }
    (models / "random_forest_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[rf-train] wrote {models / 'random_forest.joblib'}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml")
