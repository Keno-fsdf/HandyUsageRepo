"""
Reproduziert den Leakage-Effekt aus Table~I des Papers:
identische Datenbasis, identisches Conv1D, identische Hyperparameter --
nur die Split-Strategie unterscheidet sich.

Variante A: random shuffle ueber alle Sliding-Window-Sequenzen
            (Leakage, weil Sequenzen aus demselben Segment in Train UND Test)
Variante B: segment-level Split (kein Leakage)

Output: reports/leakage_comparison.json

Aufruf:
    python -m evaluation.leakage_comparison
"""

from __future__ import annotations

import json
import os
import random
import time
from pathlib import Path

import numpy as np
import yaml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from methods.tinyml.data_prep import (
    PrepConfig,
    build_sequences,
    find_discharge_segments,
    load_raw,
)
from methods.tinyml.train import build_model, set_seed


def _train_and_eval(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    train_cfg: dict,
) -> dict:
    """Train Conv1D wie in methods/tinyml/train.py und gib MAE auf Test zurueck."""
    from tensorflow import keras

    set_seed(train_cfg["seed"])
    model = build_model(X_train.shape[1], X_train.shape[2], train_cfg)
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=train_cfg["learning_rate"]),
        loss="mse",
        metrics=["mae"],
    )
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=train_cfg["patience"], restore_best_weights=True
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=train_cfg["reduce_lr_factor"],
            patience=train_cfg["reduce_lr_patience"],
            min_lr=train_cfg["min_lr"],
        ),
    ]
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=train_cfg["epochs"],
        batch_size=train_cfg["batch_size"],
        callbacks=callbacks,
        verbose=0,
    )
    y_pred = model.predict(X_test, verbose=0).flatten().astype(np.float32)
    return {
        "test_mae_h": float(np.mean(np.abs(y_test - y_pred))),
        "test_rmse_h": float(np.sqrt(np.mean((y_test - y_pred) ** 2))),
        "epochs_run": int(len(history.history["loss"])),
    }


def main(config_path: str = "configs/default.yaml", device_filter: str | None = None) -> None:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg_prep = PrepConfig.from_yaml(config_path)
    train_cfg = cfg["train"]

    print(f"[leakage] reading {cfg_prep.raw_csv}")
    df = load_raw(cfg_prep.raw_csv)
    if device_filter:
        if "device" not in df.columns:
            raise RuntimeError(
                f"--device {device_filter} requested but combined CSV has no 'device' column. "
                "Re-run merge_devices first."
            )
        before = len(df)
        df = df[df["device"] == device_filter].reset_index(drop=True)
        print(f"[leakage] device-filter={device_filter}: {len(df)}/{before} rows kept")
        if df.empty:
            raise RuntimeError(f"No rows for device='{device_filter}'.")
    segments = find_discharge_segments(df, cfg_prep.min_segment_length, cfg_prep.max_gap_ms)
    print(f"[leakage] {len(segments)} discharge segments")

    arrs = build_sequences(segments, cfg_prep.features, cfg_prep.sequence_length)
    n_total = len(arrs["X"])
    print(f"[leakage] {n_total} sliding-window sequences total")

    n_features = arrs["X"].shape[2]
    seq_len = arrs["X"].shape[1]

    # ----- Variante A: random shuffle ueber alle SEQUENZEN (Leakage) -----
    rng = np.arange(n_total)
    idx_train_A, idx_temp = train_test_split(
        rng, test_size=0.30, random_state=cfg_prep.seed, shuffle=True
    )
    idx_val_A, idx_test_A = train_test_split(
        idx_temp, test_size=0.50, random_state=cfg_prep.seed, shuffle=True
    )

    def _take(idx):
        return {k: v[idx] for k, v in arrs.items()}

    train_A = _take(idx_train_A)
    val_A = _take(idx_val_A)
    test_A = _take(idx_test_A)

    scaler_A = StandardScaler()
    flat = train_A["X"].reshape(-1, n_features)
    scaler_A.fit(flat)

    def _norm(d, scaler):
        n, t, f = d["X"].shape
        d["X"] = scaler.transform(d["X"].reshape(-1, f)).reshape(n, t, f).astype(np.float32)
        return d

    train_A = _norm(train_A, scaler_A)
    val_A = _norm(val_A, scaler_A)
    test_A = _norm(test_A, scaler_A)

    print(f"[leakage] A (random shuffle): train={len(train_A['X'])} val={len(val_A['X'])} test={len(test_A['X'])}")
    t0 = time.time()
    res_A = _train_and_eval(
        train_A["X"], train_A["y_extrap"],
        val_A["X"], val_A["y_extrap"],
        test_A["X"], test_A["y_extrap"],
        train_cfg,
    )
    print(f"[leakage] A took {time.time() - t0:.1f}s   test_MAE={res_A['test_mae_h']:.3f}h")

    # ----- Variante B: segment-level Split (kein Leakage) -----
    n_seg = len(segments)
    seg_train, seg_temp = train_test_split(
        np.arange(n_seg), test_size=0.30, random_state=cfg_prep.seed, shuffle=True
    )
    seg_val, seg_test = train_test_split(
        seg_temp, test_size=0.50, random_state=cfg_prep.seed, shuffle=True
    )
    seg_train, seg_val, seg_test = set(seg_train), set(seg_val), set(seg_test)

    mask_train = np.isin(arrs["segment_idx"], list(seg_train))
    mask_val = np.isin(arrs["segment_idx"], list(seg_val))
    mask_test = np.isin(arrs["segment_idx"], list(seg_test))

    train_B = {k: v[mask_train] for k, v in arrs.items()}
    val_B = {k: v[mask_val] for k, v in arrs.items()}
    test_B = {k: v[mask_test] for k, v in arrs.items()}

    scaler_B = StandardScaler()
    flat = train_B["X"].reshape(-1, n_features)
    scaler_B.fit(flat)
    train_B = _norm(train_B, scaler_B)
    val_B = _norm(val_B, scaler_B)
    test_B = _norm(test_B, scaler_B)

    print(f"[leakage] B (segment-level): train={len(train_B['X'])} val={len(val_B['X'])} test={len(test_B['X'])}")
    t0 = time.time()
    res_B = _train_and_eval(
        train_B["X"], train_B["y_extrap"],
        val_B["X"], val_B["y_extrap"],
        test_B["X"], test_B["y_extrap"],
        train_cfg,
    )
    print(f"[leakage] B took {time.time() - t0:.1f}s   test_MAE={res_B['test_mae_h']:.3f}h")

    out = {
        "_meta": {
            "source_csv": str(cfg_prep.raw_csv),
            "device_filter": device_filter,
            "n_total_sequences": int(n_total),
            "n_segments": int(n_seg),
        },
        "random_shuffle_leaky": {
            "n_train": int(len(train_A["X"])),
            "n_val": int(len(val_A["X"])),
            "n_test": int(len(test_A["X"])),
            **res_A,
        },
        "segment_level_clean": {
            "n_train": int(len(train_B["X"])),
            "n_val": int(len(val_B["X"])),
            "n_test": int(len(test_B["X"])),
            **res_B,
        },
        "inflation_factor": res_B["test_mae_h"] / max(res_A["test_mae_h"], 1e-9),
    }

    reports = Path(cfg["paths"]["reports_dir"])
    reports.mkdir(parents=True, exist_ok=True)
    suffix = f"_{device_filter}" if device_filter else ""
    out_path = reports / f"leakage_comparison{suffix}.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\n[leakage] wrote {out_path}")
    print(f"[leakage] inflation factor (segment_MAE / random_MAE) = {out['inflation_factor']:.2f}x")


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("config", nargs="?", default="configs/default.yaml")
    p.add_argument("--device", default=None,
                   help="restrict to one device (e.g. xiaomi_2107113sg) for single-device leakage")
    args = p.parse_args()
    main(args.config, device_filter=args.device)
