"""
Statistische Signifikanztests zwischen Methoden.

Permutationstest fuer C-Index- und MAE-Differenzen:
    Beobachtete Differenz delta_obs = metric(A) - metric(B).
    Null-Hypothese: A und B kommen aus derselben Verteilung.
    Wenn das stimmt, kann man die Vorhersagen von A und B pro Sample
    zufaellig vertauschen und sollte aehnliche Differenzen erhalten.

    Algorithmus:
        Fuer b = 1..n_perm:
            Mische pro Sample, ob es als A oder B gezaehlt wird.
            Berechne delta_perm = metric(A_swapped) - metric(B_swapped).
        p = Anteil der |delta_perm| >= |delta_obs|.

Vorteile gegenueber t-Test:
    - Annahmefrei (kein Normalverteilungs-Assumption).
    - Funktioniert fuer jede Metrik (auch C-Index).
    - Klein genug fuer typische Test-Set-Groessen (n < 10k).

Im Paper: erlaubt Aussagen wie "Google's C-Index 0.79 ist signifikant
hoeher als TinyML's 0.50 (Permutation p < 0.001, n_perm = 1000)".
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


def permutation_test(
    metric_fn,
    y_true: np.ndarray,
    y_pred_a: np.ndarray,
    y_pred_b: np.ndarray,
    n_perm: int = 1000,
    seed: int = 42,
) -> dict:
    """Two-sided permutation test on metric difference between A and B."""
    rng = np.random.default_rng(seed)
    n = len(y_true)
    if n < 10:
        return {"n": int(n), "delta_obs": float("nan"), "p_value": float("nan"), "n_perm": 0}

    obs_a = float(metric_fn(y_true, y_pred_a))
    obs_b = float(metric_fn(y_true, y_pred_b))
    delta_obs = obs_a - obs_b

    # Per-Sample Swap: fuer jedes Sample muenze werfen, ob A und B getauscht werden
    count = 0
    abs_obs = abs(delta_obs)
    for _ in range(n_perm):
        swap = rng.random(n) < 0.5
        a_swap = np.where(swap, y_pred_b, y_pred_a)
        b_swap = np.where(swap, y_pred_a, y_pred_b)
        m_a = float(metric_fn(y_true, a_swap))
        m_b = float(metric_fn(y_true, b_swap))
        if abs(m_a - m_b) >= abs_obs:
            count += 1

    p_val = (count + 1) / (n_perm + 1)  # +1 fuer korrigierte Schaetzung
    return {
        "n": int(n),
        "metric_a": obs_a,
        "metric_b": obs_b,
        "delta_obs": delta_obs,
        "p_value": p_val,
        "n_perm": int(n_perm),
    }


def main(config_path: str = "configs/default.yaml") -> None:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    processed = Path(cfg["paths"]["processed_dir"])
    reports = Path(cfg["paths"]["reports_dir"])

    preds = _load_predictions(processed)
    common = _common_mask(preds)
    test = dict(np.load(processed / "test.npz"))
    y_extrap = test["y_extrap"][common]

    method_names = list(preds.keys())
    print(f"[sig] common subset n={int(common.sum())}, methods={method_names}")

    # Alle paarweisen Tests fuer C-Index und MAE auf y_extrap
    out = {
        "_meta": {
            "n_common": int(common.sum()),
            "target": "y_extrap",
            "n_perm": 1000,
        },
        "c_index_pairs": {},
        "mae_pairs": {},
    }

    for a, b in combinations(method_names, 2):
        ya = preds[a]["y_pred"][common]
        yb = preds[b]["y_pred"][common]
        # MAE: kleiner ist besser
        mae_test = permutation_test(mae, y_extrap, ya, yb, n_perm=1000, seed=42)
        # C-Index: groesser ist besser
        c_test = permutation_test(concordance_index, y_extrap, ya, yb, n_perm=200, seed=42)
        # (C-Index Permutation kostet O(n^2) pro Permutation, daher 200 statt 1000)
        key = f"{a}__vs__{b}"
        out["c_index_pairs"][key] = c_test
        out["mae_pairs"][key] = mae_test
        sig_c = "***" if c_test["p_value"] < 0.001 else "**" if c_test["p_value"] < 0.01 else "*" if c_test["p_value"] < 0.05 else "ns"
        sig_m = "***" if mae_test["p_value"] < 0.001 else "**" if mae_test["p_value"] < 0.01 else "*" if mae_test["p_value"] < 0.05 else "ns"
        print(
            f"  {a:>15s} vs {b:<15s}  "
            f"d_C-idx={c_test['delta_obs']:+.3f} p={c_test['p_value']:.3f} {sig_c}   "
            f"d_MAE={mae_test['delta_obs']:+.2f}h p={mae_test['p_value']:.3f} {sig_m}"
        )

    reports.mkdir(parents=True, exist_ok=True)
    (reports / "significance.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[sig] wrote {reports / 'significance.json'}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml")
