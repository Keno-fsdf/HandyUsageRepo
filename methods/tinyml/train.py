"""
Training des TinyML-Conv1D-Modells.

Architektur (gleich wie urspruenglich, fuer Vergleichbarkeit erhalten):
    Input(seq_len, n_features) -> Conv1D(32,3) -> Conv1D(32,3) -> GAP
    -> Dense(32) -> Dropout(0.2) -> Dense(16) -> Dense(1)

Entscheidungen festgehalten:
- MSE-Loss + Adam, weil Regression mit kontinuierlichem Target.
- Seed gesetzt fuer Reproduzierbarkeit (numpy + tensorflow).
- Trainiert auf y_extrap (extrapoliertes Target). Evaluation gegen
  y_real findet in evaluation/ statt - hier ist der Trainings-Pfad.
"""

from __future__ import annotations

import json
import os
import random
from pathlib import Path

import numpy as np
import yaml


def set_seed(seed: int) -> None:
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    try:
        import tensorflow as tf

        tf.random.set_seed(seed)
    except Exception:
        pass


def load_split(processed_dir: Path, name: str):
    return dict(np.load(processed_dir / f"{name}.npz"))


def build_model(seq_len: int, n_features: int, cfg: dict):
    from tensorflow import keras
    from tensorflow.keras import layers

    inputs = keras.Input(shape=(seq_len, n_features), name="input")
    x = layers.Conv1D(cfg["conv_filters"], cfg["conv_kernel"], padding="same", activation="relu", name="conv1")(inputs)
    x = layers.Conv1D(cfg["conv_filters"], cfg["conv_kernel"], padding="same", activation="relu", name="conv2")(x)
    x = layers.GlobalAveragePooling1D(name="gap")(x)
    x = layers.Dense(cfg["dense_1"], activation="relu", name="dense_1")(x)
    x = layers.Dropout(cfg["dropout"])(x)
    x = layers.Dense(cfg["dense_2"], activation="relu", name="dense_2")(x)
    out = layers.Dense(1, activation="linear", name="output")(x)
    return keras.Model(inputs=inputs, outputs=out, name="battery_predictor")


def plot_history(history, out_path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].plot(history.history["loss"], label="train")
    ax[0].plot(history.history["val_loss"], label="val")
    ax[0].set_title("Loss (MSE)")
    ax[0].set_xlabel("Epoch")
    ax[0].legend()
    ax[0].grid(alpha=0.3)
    ax[1].plot(history.history["mae"], label="train")
    ax[1].plot(history.history["val_mae"], label="val")
    ax[1].set_title("MAE (h)")
    ax[1].set_xlabel("Epoch")
    ax[1].legend()
    ax[1].grid(alpha=0.3)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)


def main(config_path: str = "configs/default.yaml") -> None:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    processed = Path(cfg["paths"]["processed_dir"])
    models = Path(cfg["paths"]["models_dir"])
    figures = Path(cfg["paths"]["figures_dir"])
    train_cfg = cfg["train"]

    set_seed(train_cfg["seed"])

    train = load_split(processed, "train")
    val = load_split(processed, "val")

    seq_len = train["X"].shape[1]
    n_features = train["X"].shape[2]
    print(f"[train] X_train: {train['X'].shape}  y_train(extrap): {train['y_extrap'].shape}")

    from tensorflow import keras

    model = build_model(seq_len, n_features, train_cfg)
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=train_cfg["learning_rate"]),
        loss="mse",
        metrics=["mae"],
    )
    model.summary()

    callbacks = [
        keras.callbacks.EarlyStopping(monitor="val_loss", patience=train_cfg["patience"], restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=train_cfg["reduce_lr_factor"],
            patience=train_cfg["reduce_lr_patience"],
            min_lr=train_cfg["min_lr"],
        ),
    ]

    history = model.fit(
        train["X"],
        train["y_extrap"],
        validation_data=(val["X"], val["y_extrap"]),
        epochs=train_cfg["epochs"],
        batch_size=train_cfg["batch_size"],
        callbacks=callbacks,
        verbose=2,
    )

    models.mkdir(parents=True, exist_ok=True)
    keras_path = models / "battery_model.keras"
    model.save(keras_path)
    plot_history(history, figures / "training_curves.png")

    summary = {
        "params": int(model.count_params()),
        "train_loss_final": float(history.history["loss"][-1]),
        "val_loss_final": float(history.history["val_loss"][-1]),
        "train_mae_final_h": float(history.history["mae"][-1]),
        "val_mae_final_h": float(history.history["val_mae"][-1]),
        "epochs_run": len(history.history["loss"]),
    }
    (models / "train_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[train] saved {keras_path}")
    print(f"[train] train summary: {summary}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml")
