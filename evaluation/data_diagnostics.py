"""
Modell-unabhaengige Daten-Diagnose: enthalten die Features ueberhaupt
nutzbares Signal fuer das Target?

Drei Statistiken pro Feature, jeweils gegen y_extrap und y_real:

1. **Pearson-Korrelation** - linearer Zusammenhang.
   Werte nah 0 = kein linearer Zusammenhang.

2. **Spearman-Rangkorrelation** - monotoner Zusammenhang (auch nicht-linear).
   Robuster gegen Skalierung und Ausreisser.

3. **Mutual Information** - misst beliebige Abhaengigkeit (auch nicht-monoton).
   Werte in nat (natuerliche log). 0 = unabhaengig.
   Bei MI > 0.05 nat ist Abhaengigkeit praktisch relevant
   (Faustregel: ~0.05 nat = ~7% Reduktion der Target-Entropie).

Argument fuer's Paper: das Random-Forest-Permutation-Importance-Ergebnis
ist modellabhaengig. Wenn ALLE drei klassischen Statistiken hier auch
nahe 0 liegen, ist das Daten-Argument modell-unabhaengig untermauert.

Wir aggregieren die Sliding-Window-Sequenzen pro Feature so:
    - "current": Wert am letzten Zeitschritt (Vorhersage-Zeitpunkt)
    - "mean": Mittelwert ueber das Window
    - "std":  Std ueber das Window
    - "trend": Differenz letzter - erster Schritt

Das ist die einfachste Aggregation, die mehr Information als nur ein
Snapshot liefert. Reichere Aggregationen sind moeglich, aendern aber
das Ergebnis kaum, wenn das Roh-Signal so schwach ist.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml
from scipy.stats import pearsonr, spearmanr
from sklearn.feature_selection import mutual_info_regression


def _aggregate(X: np.ndarray, agg: str) -> np.ndarray:
    """X: (n, t, f). Returns (n, f)."""
    if agg == "current":
        return X[:, -1, :]
    if agg == "mean":
        return X.mean(axis=1)
    if agg == "std":
        return X.std(axis=1)
    if agg == "trend":
        return X[:, -1, :] - X[:, 0, :]
    raise ValueError(agg)


def _stats_for_target(X_agg: np.ndarray, y: np.ndarray, feature_names: list[str]) -> list[dict]:
    """
    Returns list of dicts: {feature, pearson_r, pearson_p, spearman_r, mi}.
    """
    rows = []
    # Mutual Info: berechnet alle gleichzeitig
    mi = mutual_info_regression(X_agg, y, random_state=42)
    for fi, fname in enumerate(feature_names):
        x = X_agg[:, fi]
        # Konstante Features -> Korrelation undefiniert
        if x.std() == 0:
            rows.append({
                "feature": fname,
                "pearson_r": 0.0,
                "pearson_p": float("nan"),
                "spearman_r": 0.0,
                "mi_nat": float(mi[fi]),
                "constant": True,
            })
            continue
        try:
            pr = pearsonr(x, y)
            sr = spearmanr(x, y)
            rows.append({
                "feature": fname,
                "pearson_r": float(pr.statistic),
                "pearson_p": float(pr.pvalue),
                "spearman_r": float(sr.correlation if hasattr(sr, "correlation") else sr.statistic),
                "mi_nat": float(mi[fi]),
                "constant": False,
            })
        except Exception as e:
            rows.append({
                "feature": fname,
                "pearson_r": float("nan"),
                "pearson_p": float("nan"),
                "spearman_r": float("nan"),
                "mi_nat": float(mi[fi]),
                "constant": False,
                "error": str(e),
            })
    return rows


def main(config_path: str = "configs/default.yaml") -> None:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    processed = Path(cfg["paths"]["processed_dir"])
    reports = Path(cfg["paths"]["reports_dir"])
    feature_names = list(cfg["features"])

    # Wir nutzen den Train-Split fuer die Daten-Diagnose
    # (saubere Trennung: Test-Daten bleiben unangetastet).
    train = dict(np.load(processed / "train.npz"))
    X = train["X"]
    y_extrap = train["y_extrap"]
    y_real = train["y_real"]

    out: dict = {
        "_meta": {
            "n": int(len(y_extrap)),
            "feature_names": feature_names,
            "split": "train",
        },
    }

    for agg in ("current", "mean", "std", "trend"):
        X_agg = _aggregate(X, agg)
        out[f"{agg}_vs_y_extrap"] = _stats_for_target(X_agg, y_extrap, feature_names)
        out[f"{agg}_vs_y_real"] = _stats_for_target(X_agg, y_real, feature_names)

    reports.mkdir(parents=True, exist_ok=True)
    (reports / "data_diagnostics.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[data-diag] wrote {reports / 'data_diagnostics.json'}")

    # Konsole-Zusammenfassung: 'current' Aggregation gegen y_extrap
    print("\n[data-diag] Feature signals (aggregation=current, target=y_extrap):")
    print(f"  {'feature':<22} {'pearson_r':>10} {'spearman_r':>11} {'mi_nat':>9}")
    for r in sorted(out["current_vs_y_extrap"], key=lambda r: abs(r["pearson_r"]), reverse=True):
        print(f"  {r['feature']:<22} {r['pearson_r']:>+10.3f} {r['spearman_r']:>+11.3f} {r['mi_nat']:>9.4f}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml")
