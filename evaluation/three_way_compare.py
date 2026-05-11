"""
Drei-Wege-Vergleich (eigentlich vier-Wege mit Linear-Baseline) auf identischem Testset.

Fairness-Regel:
    Vergleicht man Methode A vs. B nur dort, wo beide gueltige Werte haben.
    Berechnet zusaetzlich eine "common-mask"-Schnittmenge ueber ALLE Methoden,
    auf der die Tabelle "Gesamtvergleich" basiert. Per-Methode-Spalten ohne
    Maskierung werden zusaetzlich angegeben (zeigt, wie hoch die Coverage ist).

Targets:
    Wir evaluieren gegen y_real (gemessene Restzeit ohne Extrapolation).
    Optional zusaetzlich gegen y_extrap (das Trainings-Target) -
    fairness-bewusst: Vergleich gegen y_extrap bevorteilt TinyML strukturell
    (zirkulaer), das wird im Report explizit benannt.

Plots:
    1. Cumulative Error Distribution
    2. Predicted vs. Actual Scatter pro Methode
    3. Error-Histogramm pro Methode

Output:
    reports/accuracy.json
    reports/figures/cumulative_error.png
    reports/figures/scatter_<method>.png
    reports/figures/error_hist.png
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import yaml

from evaluation.accuracy import all_metrics, all_metrics_with_ci


METHODS = ("tinyml", "random_forest", "mean_const", "linear", "exponential", "google")
METHOD_LABELS = {
    "tinyml": "TinyML Conv1D",
    "random_forest": "Random Forest",
    "mean_const": "Mean predictor (floor)",
    "linear": "Linear (drain rate)",
    "exponential": "Exponential fit",
    "google": "Google API",
}
METHOD_COLORS = {
    "tinyml": "#2196F3",
    "random_forest": "#9C27B0",
    "mean_const": "#BDBDBD",
    "linear": "#9E9E9E",
    "exponential": "#4CAF50",
    "google": "#FF9800",
}


@dataclass
class MethodPreds:
    name: str
    y_pred: np.ndarray
    valid: np.ndarray  # bool mask; True = Vorhersage existiert


def _load_predictions(processed: Path) -> dict[str, MethodPreds]:
    files = {
        "tinyml": "predictions_tinyml.npz",
        "random_forest": "predictions_random_forest.npz",
        "mean_const": "predictions_mean_const.npz",
        "linear": "predictions_linear.npz",
        "exponential": "predictions_exponential.npz",
        "google": "predictions_google.npz",
    }
    out: dict[str, MethodPreds] = {}
    for name, fname in files.items():
        path = processed / fname
        if not path.exists():
            print(f"[3way] WARN: {fname} missing, skipping {name}")
            continue
        d = dict(np.load(path, allow_pickle=True))
        y_pred = d["y_pred"]
        if "valid" in d:
            valid = d["valid"].astype(bool)
        else:
            valid = ~np.isnan(y_pred)
        out[name] = MethodPreds(name=name, y_pred=y_pred, valid=valid)
    return out


def _common_mask(preds: dict[str, MethodPreds]) -> np.ndarray:
    if not preds:
        return np.array([], dtype=bool)
    masks = list(preds.values())
    m = masks[0].valid.copy()
    for p in masks[1:]:
        m &= p.valid
    return m


def _per_method_table(preds: dict[str, MethodPreds], y_true: np.ndarray, tols, with_ci: bool = False) -> dict:
    """Metriken pro Methode auf der eigenen Validity-Mask (Coverage-Spalte)."""
    out = {}
    metric_fn = all_metrics_with_ci if with_ci else all_metrics
    for name, p in preds.items():
        m = p.valid & ~np.isnan(p.y_pred)
        if m.sum() == 0:
            out[name] = {"n": 0}
            continue
        out[name] = {
            "coverage_pct": round(100.0 * m.mean(), 1),
            **metric_fn(y_true[m], p.y_pred[m], tols_h=tols),
        }
    return out


def _common_table(preds: dict[str, MethodPreds], y_true: np.ndarray, common: np.ndarray, tols, with_ci: bool = False) -> dict:
    out = {}
    if not common.any():
        return out
    metric_fn = all_metrics_with_ci if with_ci else all_metrics
    for name, p in preds.items():
        out[name] = metric_fn(y_true[common], p.y_pred[common], tols_h=tols)
    return out


def _plot_cumulative_error(preds, y_true, common, max_h, steps, out_path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 5.5))
    tolerances = np.linspace(0, max_h, steps)
    for name, p in preds.items():
        m = p.valid & ~np.isnan(p.y_pred)
        if m.sum() == 0:
            continue
        err = np.abs(y_true[m] - p.y_pred[m])
        curve = [float((err <= t).mean()) * 100.0 for t in tolerances]
        ax.plot(tolerances, curve, label=f"{METHOD_LABELS[name]} (n={int(m.sum())})",
                linewidth=2.0, color=METHOD_COLORS.get(name))
    ax.axhline(y=90, color="gray", linestyle=":", alpha=0.4)
    ax.axvline(x=1, color="gray", linestyle=":", alpha=0.3)
    ax.axvline(x=2, color="gray", linestyle=":", alpha=0.3)
    ax.set_xlabel("Error tolerance (h)")
    ax.set_ylabel("Hit rate (%)")
    ax.set_title("Cumulative error distribution\n(per-method validity, vs. measured remaining time)")
    ax.set_xlim(0, max_h)
    ax.set_ylim(0, 105)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _plot_scatter(preds, y_true, out_dir):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir.mkdir(parents=True, exist_ok=True)
    for name, p in preds.items():
        m = p.valid & ~np.isnan(p.y_pred)
        if m.sum() == 0:
            continue
        fig, ax = plt.subplots(figsize=(5.5, 5.5))
        ax.scatter(y_true[m], p.y_pred[m], alpha=0.3, s=8, color=METHOD_COLORS.get(name))
        lim = max(float(np.max(y_true[m])), float(np.max(p.y_pred[m]))) + 1
        ax.plot([0, lim], [0, lim], "r--", linewidth=1, label="ideal")
        ax.set_xlim(0, lim)
        ax.set_ylim(0, lim)
        ax.set_xlabel("Measured remaining time (h)")
        ax.set_ylabel("Predicted (h)")
        ax.set_title(f"{METHOD_LABELS[name]} (n={int(m.sum())})")
        ax.grid(alpha=0.3)
        ax.legend()
        fig.tight_layout()
        fig.savefig(out_dir / f"scatter_{name}.png", dpi=150)
        plt.close(fig)


def _plot_error_hist(preds, y_true, out_path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 5))
    bins = np.linspace(-15, 15, 61)
    for name, p in preds.items():
        m = p.valid & ~np.isnan(p.y_pred)
        if m.sum() == 0:
            continue
        err = p.y_pred[m] - y_true[m]
        ax.hist(err, bins=bins, alpha=0.45, label=METHOD_LABELS[name], color=METHOD_COLORS.get(name))
    ax.axvline(0, color="black", linestyle="--", linewidth=1)
    ax.set_xlabel("Prediction error (h)  [pred - measured]")
    ax.set_ylabel("Count")
    ax.set_title("Error distribution (per-method validity)")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main(config_path: str = "configs/default.yaml") -> None:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    processed = Path(cfg["paths"]["processed_dir"])
    reports = Path(cfg["paths"]["reports_dir"])
    figures = Path(cfg["paths"]["figures_dir"])
    eval_cfg = cfg["evaluation"]
    tols = list(eval_cfg["accuracy_tolerances_h"])

    preds = _load_predictions(processed)
    if not preds:
        raise RuntimeError("Keine Predictions gefunden.")

    test = dict(np.load(processed / "test.npz"))
    y_real = test["y_real"]
    y_extrap = test["y_extrap"]

    common = _common_mask(preds)
    print(f"[3way] n_total={len(y_real)}  common_valid={int(common.sum())} ({100.0 * common.mean():.1f}%)")

    out = {
        "n_test_total": int(len(y_real)),
        "n_common_valid": int(common.sum()),
        "common_coverage_pct": round(100.0 * common.mean(), 2),
        "vs_measured": {
            "per_method_native_coverage": _per_method_table(preds, y_real, tols),
            "common_subset": _common_table(preds, y_real, common, tols, with_ci=True),
        },
        "vs_extrapolated_caveat": {
            "_note": "y_extrap = Trainings-Target des TinyML-Modells. "
                     "Vergleich hier zeigt zirkulaeren Bias des TinyML-Modells.",
            "per_method_native_coverage": _per_method_table(preds, y_extrap, tols),
            "common_subset": _common_table(preds, y_extrap, common, tols, with_ci=True),
        },
    }
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "accuracy.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    _plot_cumulative_error(preds, y_real, common, eval_cfg["cumulative_max_h"],
                           eval_cfg["cumulative_steps"], figures / "cumulative_error.png")
    _plot_scatter(preds, y_real, figures)
    _plot_error_hist(preds, y_real, figures / "error_hist.png")

    print(f"[3way] wrote {reports / 'accuracy.json'} and figures in {figures}/")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml")
