"""
Statistische Signifikanztests zwischen Methoden.

Zwei Test-Familien werden berichtet:

1. **Per-Sample Permutationstest (MAE)**:
   MAE ist Sample-additiv: |y_true_i - y_pred_i|. Ein per-Sample-Tausch der
   Methoden-Labels ist hier valide — das ist der Standard paired-permutation-Test.

2. **Paired Bootstrap CI (C-Index)**:
   C-Index ist eine *paarweise* Metric: sie haengt von allen Paaren (i,j) ab,
   nicht von einzelnen Samples. Ein per-Sample-Tausch zerstoert die Paar-
   Struktur und liefert keinen wohldefinierten Null-Distribution-Test.
   Stattdessen: Bootstrap-Resamples auf den (y_true, y_pred_a, y_pred_b)-
   Tripeln, Berechnung von delta_c = C(a) - C(b) pro Resample, dann 95%-CI
   ueber die Resample-Verteilung. Signifikanz: CI schliesst 0 nicht ein.
   Plus zwei-seitiger Bootstrap-p-Wert ueber 2 * min(P(d<=0), P(d>=0)).

Multiple-Comparisons-Korrektur:
   Bei 6 Methoden -> 15 paarweise Tests pro Metric. Ohne Korrektur waere die
   familywise false-positive rate ~54% bei alpha=0.05. Wir berichten daher
   den rohen p-Wert UND zwei adjustierte:
   - p_bonferroni: konservativ (p * n_tests)
   - p_bh:         Benjamini-Hochberg FDR (weniger konservativ)

Targets:
   Permutationstests laufen sowohl gegen y_real (Hauptmetric im Paper) als
   auch gegen y_extrap (Trainings-Target des TinyML-Modells). Frueher: nur
   gegen y_extrap, was die Hauptmetric-Ergebnisse nicht validierte.
"""

from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import numpy as np
import yaml

from evaluation.accuracy import concordance_index, mae


METHOD_FILES = {
    "tinyml": "predictions_tinyml.npz",
    "random_forest": "predictions_random_forest.npz",
    "mean_const": "predictions_mean_const.npz",
    "linear": "predictions_linear.npz",
    "exponential": "predictions_exponential.npz",
    "google": "predictions_google.npz",
}


def _load_predictions(processed: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for name, fname in METHOD_FILES.items():
        path = processed / fname
        if not path.exists():
            continue
        d = dict(np.load(path, allow_pickle=True))
        if "valid" not in d:
            d["valid"] = (~np.isnan(d["y_pred"])).astype(bool)
        else:
            d["valid"] = d["valid"].astype(bool)
        out[name] = d
    return out


def _common_mask(preds: dict[str, dict]) -> np.ndarray:
    masks = list(preds.values())
    m = masks[0]["valid"].copy()
    for p in masks[1:]:
        m &= p["valid"]
    return m


def permutation_test_mae(
    y_true: np.ndarray,
    y_pred_a: np.ndarray,
    y_pred_b: np.ndarray,
    n_perm: int = 1000,
    seed: int = 42,
) -> dict:
    """Paired-Permutation auf MAE-Differenz. Valide weil MAE Sample-additiv ist."""
    rng = np.random.default_rng(seed)
    n = len(y_true)
    if n < 10:
        return {"n": int(n), "delta_obs": float("nan"), "p_value": float("nan"), "n_perm": 0}

    obs_a = float(mae(y_true, y_pred_a))
    obs_b = float(mae(y_true, y_pred_b))
    delta_obs = obs_a - obs_b
    abs_obs = abs(delta_obs)

    count = 0
    for _ in range(n_perm):
        swap = rng.random(n) < 0.5
        a_swap = np.where(swap, y_pred_b, y_pred_a)
        b_swap = np.where(swap, y_pred_a, y_pred_b)
        m_a = float(mae(y_true, a_swap))
        m_b = float(mae(y_true, b_swap))
        if abs(m_a - m_b) >= abs_obs:
            count += 1

    return {
        "n": int(n),
        "metric_a": obs_a,
        "metric_b": obs_b,
        "delta_obs": delta_obs,
        "p_value": (count + 1) / (n_perm + 1),
        "n_perm": int(n_perm),
        "test": "paired_permutation",
    }


def paired_bootstrap_test_cindex(
    y_true: np.ndarray,
    y_pred_a: np.ndarray,
    y_pred_b: np.ndarray,
    n_boot: int = 500,
    seed: int = 42,
    max_pairs: int = 500_000,
) -> dict:
    """
    Paired Bootstrap auf delta_c = C(a) - C(b).
    Resamplet Tripeln (y_true_i, y_pred_a_i, y_pred_b_i) gemeinsam und berechnet
    delta_c pro Resample. Zwei-seitiger p-Wert: 2 * min(P(d<=0), P(d>=0)).

    `max_pairs` steuert das Pair-Subsampling im C-Index (default 500k -> jede
    C-Index-Berechnung ~ms statt ~100ms bei n~3000). Mit n_boot=500 und
    pro-Resample-Seed mittelt sich der Sample-Noise aus.
    """
    rng = np.random.default_rng(seed)
    n = len(y_true)
    if n < 10:
        return {"n": int(n), "delta_obs": float("nan"), "p_value": float("nan"), "n_boot": 0}

    obs_a = float(concordance_index(y_true, y_pred_a, max_pairs=max_pairs, seed=seed))
    obs_b = float(concordance_index(y_true, y_pred_b, max_pairs=max_pairs, seed=seed))
    delta_obs = obs_a - obs_b

    deltas = np.empty(n_boot, dtype=np.float64)
    for b in range(n_boot):
        idx = rng.integers(0, n, size=n)
        c_a = concordance_index(y_true[idx], y_pred_a[idx], max_pairs=max_pairs, seed=seed + 1 + b)
        c_b = concordance_index(y_true[idx], y_pred_b[idx], max_pairs=max_pairs, seed=seed + 1 + b)
        deltas[b] = c_a - c_b

    # Zwei-seitiger Bootstrap-p-Wert
    p_le = float((deltas <= 0).mean())
    p_ge = float((deltas >= 0).mean())
    p_two = float(min(1.0, 2.0 * min(p_le, p_ge)))

    return {
        "n": int(n),
        "metric_a": obs_a,
        "metric_b": obs_b,
        "delta_obs": delta_obs,
        "delta_ci95": [float(np.percentile(deltas, 2.5)), float(np.percentile(deltas, 97.5))],
        "p_value": p_two,
        "n_boot": int(n_boot),
        "test": "paired_bootstrap",
    }


def _adjust_pvalues(pvals: list[float]) -> tuple[list[float], list[float]]:
    """Returns (bonferroni, benjamini_hochberg-FDR) corrected p-values."""
    m = len(pvals)
    if m == 0:
        return [], []
    bonf = [min(1.0, p * m) for p in pvals]

    # Benjamini-Hochberg: rank-based step-up procedure
    order = sorted(range(m), key=lambda i: pvals[i])
    bh_sorted = [0.0] * m
    prev = 1.0
    for rank, idx in enumerate(reversed(order)):
        k = m - rank  # current rank from largest down to 1
        q = pvals[idx] * m / k
        prev = min(prev, q)
        bh_sorted[idx] = min(1.0, prev)
    return bonf, bh_sorted


def _sig_stars(p: float) -> str:
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"


def _run_pairwise(
    preds: dict[str, dict],
    common: np.ndarray,
    y_true: np.ndarray,
    target_label: str,
    n_perm: int,
    n_boot_c: int,
) -> dict:
    method_names = list(preds.keys())
    pairs = list(combinations(method_names, 2))

    mae_raw = []
    c_raw = []
    pair_keys = []
    mae_results: dict[str, dict] = {}
    c_results: dict[str, dict] = {}

    for a, b in pairs:
        ya = preds[a]["y_pred"][common]
        yb = preds[b]["y_pred"][common]
        mae_test = permutation_test_mae(y_true, ya, yb, n_perm=n_perm, seed=42)
        c_test = paired_bootstrap_test_cindex(y_true, ya, yb, n_boot=n_boot_c, seed=42)
        key = f"{a}__vs__{b}"
        pair_keys.append(key)
        mae_results[key] = mae_test
        c_results[key] = c_test
        mae_raw.append(mae_test["p_value"])
        c_raw.append(c_test["p_value"])

    mae_bonf, mae_bh = _adjust_pvalues(mae_raw)
    c_bonf, c_bh = _adjust_pvalues(c_raw)
    for key, b, h in zip(pair_keys, mae_bonf, mae_bh):
        mae_results[key]["p_bonferroni"] = b
        mae_results[key]["p_bh_fdr"] = h
        mae_results[key]["sig_raw"] = _sig_stars(mae_results[key]["p_value"])
        mae_results[key]["sig_bh"] = _sig_stars(h)
    for key, b, h in zip(pair_keys, c_bonf, c_bh):
        c_results[key]["p_bonferroni"] = b
        c_results[key]["p_bh_fdr"] = h
        c_results[key]["sig_raw"] = _sig_stars(c_results[key]["p_value"])
        c_results[key]["sig_bh"] = _sig_stars(h)

    print(f"[sig] target={target_label}  n_tests_per_family={len(pairs)}")
    print(f"[sig] {'pair':>35s}  {'dMAE_h':>8s}  {'p_raw':>7s}  {'p_BH':>7s}  "
          f"{'dC':>7s}  {'p_raw':>7s}  {'p_BH':>7s}")
    for key in pair_keys:
        m = mae_results[key]
        c = c_results[key]
        print(
            f"  {key:>35s}  "
            f"{m['delta_obs']:+8.2f}  {m['p_value']:7.3f}  {m['p_bh_fdr']:7.3f}  "
            f"{c['delta_obs']:+7.3f}  {c['p_value']:7.3f}  {c['p_bh_fdr']:7.3f}"
        )

    return {
        "_target": target_label,
        "_n_tests": len(pairs),
        "_correction_methods": ["bonferroni", "benjamini_hochberg_fdr"],
        "mae_pairs": mae_results,
        "c_index_pairs": c_results,
    }


def main(config_path: str = "configs/default.yaml") -> None:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    processed = Path(cfg["paths"]["processed_dir"])
    reports = Path(cfg["paths"]["reports_dir"])

    preds = _load_predictions(processed)
    common = _common_mask(preds)
    test = dict(np.load(processed / "test.npz"))
    y_real = test["y_real"][common]
    y_extrap = test["y_extrap"][common]

    method_names = list(preds.keys())
    print(f"[sig] common subset n={int(common.sum())}, methods={method_names}")

    n_perm = 1000
    n_boot_c = 500  # paired bootstrap auf delta_c; C-Index nutzt Pair-Subsampling
                   # (max_pairs=500_000) damit ein Resample im ms-Bereich liegt.

    out = {
        "_meta": {
            "n_common": int(common.sum()),
            "n_perm_mae": n_perm,
            "n_boot_cindex": n_boot_c,
            "tests": ["paired_permutation (MAE)", "paired_bootstrap (C-Index)"],
            "note": (
                "Tests laufen gegen BEIDE Targets (y_real und y_extrap). "
                "Im Paper als Hauptmetric: y_real. y_extrap zur Validierung "
                "des Trainings-Pfads. Multiple-Comparisons-Korrektur per "
                "Bonferroni (konservativ) und Benjamini-Hochberg-FDR (default)."
            ),
        },
        "vs_y_real": _run_pairwise(preds, common, y_real, "y_real", n_perm, n_boot_c),
        "vs_y_extrap": _run_pairwise(preds, common, y_extrap, "y_extrap", n_perm, n_boot_c),
    }

    reports.mkdir(parents=True, exist_ok=True)
    (reports / "significance.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[sig] wrote {reports / 'significance.json'}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml")
