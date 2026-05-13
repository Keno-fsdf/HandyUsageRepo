"""
Permutation Feature Importance (Sklearn) auf dem Random Forest.

Idee:
    Permutiere eine Feature-Spalte (zerstoere die Information dieses Features),
    miss wie viel sich die Performance verschlechtert. Je mehr Verschlechterung,
    desto wichtiger das Feature.

Da die Sliding-Window-Tensoren zu (n, 100) flachgemacht wurden, gibt es 100
Features (10 Original-Features x 10 Zeitschritte). Wir berichten:
    1. Pro Original-Feature aggregiert (Mittelwert ueber Zeitschritte) -
       das ist die "echte" Aussage zur Wichtigkeit des Sensors.
    2. Top-K der individuellen 100 Features (welcher Sensor an welcher
       relativen Zeitposition).

Aussage fuer's Paper: zeigt, ob ueberhaupt ein Sensor ein nutzbares Signal
liefert, oder ob alle Features gleich (un)wichtig sind. Wenn alle bei ~0
liegen -> die Daten enthalten kein nutzbares Signal fuer das Target.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import yaml
from sklearn.inspection import permutation_importance


def main(config_path: str = "configs/default.yaml") -> None:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    processed = Path(cfg["paths"]["processed_dir"])
    models = Path(cfg["paths"]["models_dir"])
    reports = Path(cfg["paths"]["reports_dir"])
    feature_names = list(cfg["features"])

    rf_path = models / "random_forest.joblib"
    if not rf_path.exists():
        raise RuntimeError("Random Forest noch nicht trainiert.")

    test = dict(np.load(processed / "test.npz"))
    n_test, seq_len, n_feat = test["X"].shape
    X_test = test["X"].reshape(n_test, seq_len * n_feat)
    y_test = test["y_extrap"]

    rf = joblib.load(rf_path)
    # Bei sehr grossen Test-Sets (Multi-Device) Subsample, sonst dauert
    # die Permutation O(n_features x n_repeats x n_test x rf_predict) zu lange.
    # Device-stratifiziert sampeln, damit das Importance-Bild nicht vom
    # dominanten Geraet (Xiaomi) dominiert wird.
    n_repeats = 5
    if n_test > 1500:
        rng = np.random.default_rng(42)
        devices = test.get("device", None)
        if devices is not None and len(devices) == n_test:
            devices = np.asarray(devices).astype(str)
            unique = np.unique(devices)
            per_dev = max(1, 1500 // len(unique))
            sub_parts = []
            for d in unique:
                idx_d = np.where(devices == d)[0]
                k = min(per_dev, len(idx_d))
                sub_parts.append(rng.choice(idx_d, size=k, replace=False))
            sub = np.concatenate(sub_parts)
            rng.shuffle(sub)
            print(f"[feat-imp] stratified subsample {len(sub)}/{n_test} "
                  f"({per_dev} per device, {len(unique)} devices)")
        else:
            sub = rng.choice(n_test, size=1500, replace=False)
            print(f"[feat-imp] subsampled (no device info): {len(sub)}/{n_test}")
        X_eval = X_test[sub]
        y_eval = y_test[sub]
    else:
        X_eval = X_test
        y_eval = y_test
    print(f"[feat-imp] permutation importance (n_repeats={n_repeats}, n_jobs=2)")
    # n_jobs=2 statt -1: 89MB-Modell x viele Cores macht RAM eng und ist
    # paradoxerweise langsamer als wenige Workers.
    result = permutation_importance(
        rf, X_eval, y_eval, n_repeats=n_repeats, random_state=42, n_jobs=2,
        scoring="neg_mean_absolute_error",
    )
    importances = -result.importances_mean  # MAE-Erhoehung beim Permutieren
    importances_std = result.importances_std

    # 100 individuelle Features mit Bezeichnung
    individual = []
    for t in range(seq_len):  # t von 0 (aeltester Punkt im Window) bis seq_len-1 (juengster)
        for fi in range(n_feat):
            idx = t * n_feat + fi
            individual.append(
                {
                    "name": f"{feature_names[fi]}@t-{seq_len - 1 - t}",
                    "feature": feature_names[fi],
                    "time_offset_steps": int(seq_len - 1 - t),
                    "importance_mae_h": round(float(importances[idx]), 4),
                    "std": round(float(importances_std[idx]), 4),
                }
            )

    # Aggregiert pro Original-Feature ueber alle Zeitschritte
    aggregated = []
    for fi, fname in enumerate(feature_names):
        idxs = [t * n_feat + fi for t in range(seq_len)]
        agg = float(importances[idxs].sum())
        aggregated.append({"feature": fname, "total_importance_mae_h": round(agg, 4)})
    aggregated.sort(key=lambda x: x["total_importance_mae_h"], reverse=True)

    individual.sort(key=lambda x: x["importance_mae_h"], reverse=True)

    out = {
        "_method": f"permutation_importance, scoring=neg_MAE, n_repeats={n_repeats}",
        "_subsample": f"{len(X_eval)}/{n_test} (device-stratified if available)",
        "by_feature_aggregated": aggregated,
        "top_individual": individual[:20],
    }
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "feature_importance.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[feat-imp] wrote {reports / 'feature_importance.json'}")
    print("[feat-imp] aggregated by feature (top):")
    for r in aggregated[:10]:
        print(f"  {r['feature']:<25} {r['total_importance_mae_h']:+.3f}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml")
