"""
Accuracy-Metriken fuer Battery-Restzeit-Vorhersagen.

Standard-Regressionsmetriken: MAE, RMSE.
Schwellenmetriken: Anteil der Vorhersagen mit |error| <= tol_h.

Concordance-Index (C-Index, Harrell 1982):
    Anteil aller geordneten Paare (i,j) mit y_i < y_j, fuer die auch
    y_pred_i < y_pred_j gilt. Wertebereich [0, 1], 0.5 = Zufall.
    Robust gegenueber Bias und Skalierungs-Artefakten - daher in
    Li et al. 2018 als primaere Metrik bei Battery-Prediction
    eingesetzt.
"""

from __future__ import annotations

from typing import Callable, Iterable

import numpy as np


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def me(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Error - Bias-Indikator (positiv = Modell ueberschaetzt)."""
    return float(np.mean(y_pred - y_true))


def accuracy_within(y_true: np.ndarray, y_pred: np.ndarray, tol_h: float) -> float:
    return float(np.mean(np.abs(y_true - y_pred) <= tol_h))


def concordance_index(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    max_pairs: int = 5_000_000,
    seed: int = 0,
) -> float:
    """
    Harrell C-Index. O(n log n) ueber Sortierung + n^2 worst case ueber Paarvergleich;
    fuer typische n (~Tausende) komfortabel. Bei sehr grossen n samplen wir.

    Der `seed` steuert nur das Pair-Sampling im Large-n-Fall (n*(n-1)/2 > max_pairs).
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    n = len(y_true)
    if n < 2:
        return float("nan")

    # Bei zu vielen Paaren: zufaellige Stichprobe
    total_pairs = n * (n - 1) // 2
    if total_pairs > max_pairs:
        rng = np.random.default_rng(seed)
        idx_a = rng.integers(0, n, size=max_pairs)
        idx_b = rng.integers(0, n, size=max_pairs)
        mask = idx_a != idx_b
        idx_a = idx_a[mask]
        idx_b = idx_b[mask]
    else:
        idx_a, idx_b = np.triu_indices(n, k=1)

    diff_true = y_true[idx_a] - y_true[idx_b]
    diff_pred = y_pred[idx_a] - y_pred[idx_b]
    valid = diff_true != 0
    if not valid.any():
        return float("nan")
    diff_true = diff_true[valid]
    diff_pred = diff_pred[valid]
    concordant = (np.sign(diff_true) == np.sign(diff_pred)) & (diff_pred != 0)
    tied = diff_pred == 0
    score = (concordant.sum() + 0.5 * tied.sum()) / len(diff_true)
    return float(score)


def all_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    tols_h: Iterable[float] = (1.0, 2.0),
) -> dict:
    out: dict = {
        "n": int(len(y_true)),
        "mae_h": mae(y_true, y_pred),
        "rmse_h": rmse(y_true, y_pred),
        "me_h": me(y_true, y_pred),
        "c_index": concordance_index(y_true, y_pred),
    }
    for t in tols_h:
        out[f"acc_within_{t:g}h"] = accuracy_within(y_true, y_pred, float(t))
    return out


def bootstrap_ci(
    metric_fn: Callable[..., float],
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_boot: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
) -> tuple[float, float, float]:
    """
    Bootstrap-Konfidenzintervall fuer eine beliebige Punkt-Metrik
    (MAE, RMSE, C-Index, ...).

    Bei `concordance_index` wird zusaetzlich pro Resample ein eigener Pair-Sample-Seed
    durchgereicht, damit das interne Subsampling (n*(n-1)/2 > max_pairs) nicht ueber
    alle Bootstrap-Iterationen identisch ist und die CI dadurch zu eng wird.

    Returns:
        (point_estimate, ci_low, ci_high) bei (1-alpha)*100% Niveau
        (Default: 95% CI).
    """
    rng = np.random.default_rng(seed)
    n = len(y_true)
    accepts_seed = metric_fn is concordance_index
    point = float(metric_fn(y_true, y_pred, seed=seed) if accepts_seed else metric_fn(y_true, y_pred))
    if n < 5:
        return point, float("nan"), float("nan")
    samples = np.empty(n_boot, dtype=np.float64)
    for b in range(n_boot):
        idx = rng.integers(0, n, size=n)
        if accepts_seed:
            samples[b] = metric_fn(y_true[idx], y_pred[idx], seed=seed + 1 + b)
        else:
            samples[b] = metric_fn(y_true[idx], y_pred[idx])
    low = float(np.percentile(samples, 100 * alpha / 2))
    high = float(np.percentile(samples, 100 * (1 - alpha / 2)))
    return point, low, high


def all_metrics_with_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    tols_h: Iterable[float] = (1.0, 2.0),
    n_boot: int = 1000,
    seed: int = 42,
) -> dict:
    """
    Wie all_metrics, aber mit 95%-Bootstrap-CI fuer MAE, RMSE und C-Index.
    Acc-Schwellen werden ohne CI geliefert (binaer, weniger interessant).
    """
    n = int(len(y_true))
    mae_p, mae_lo, mae_hi = bootstrap_ci(mae, y_true, y_pred, n_boot, seed=seed)
    rmse_p, rmse_lo, rmse_hi = bootstrap_ci(rmse, y_true, y_pred, n_boot, seed=seed)
    me_p, me_lo, me_hi = bootstrap_ci(me, y_true, y_pred, n_boot, seed=seed)

    # C-Index ist teurer (O(n^2)) - eigene niedrigere Resample-Zahl, sonst zu langsam
    n_boot_c = max(200, n_boot // 4)
    cidx_p, cidx_lo, cidx_hi = bootstrap_ci(concordance_index, y_true, y_pred, n_boot_c, seed=seed)

    out: dict = {
        "n": n,
        "mae_h": mae_p,
        "mae_h_ci95": [mae_lo, mae_hi],
        "rmse_h": rmse_p,
        "rmse_h_ci95": [rmse_lo, rmse_hi],
        "me_h": me_p,
        "me_h_ci95": [me_lo, me_hi],
        "c_index": cidx_p,
        "c_index_ci95": [cidx_lo, cidx_hi],
    }
    for t in tols_h:
        out[f"acc_within_{t:g}h"] = accuracy_within(y_true, y_pred, float(t))
    return out
