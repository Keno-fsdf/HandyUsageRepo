"""
Per-Device Performance-Analyse.

Wertet alle 6 Methoden separat pro Gerät aus. Beantwortet die zentrale
Multi-Device-Frage des Papers:
    Generalisiert das Hauptergebnis ueber Geraete hinweg, oder ist es
    Xiaomi-spezifisch? Insbesondere: schneidet Google API auf Pixel-
    Geraeten anders ab als auf dem Xiaomi (Pixel-Geraete nutzen die
    ML-Schaetzung in den System-Settings, andere Hersteller oft nicht)?

Ausgabe: reports/per_device_analysis.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

from evaluation.accuracy import all_metrics


METHOD_FILES = {
    "tinyml": "predictions_tinyml.npz",
    "random_forest": "predictions_random_forest.npz",
    "mean_const": "predictions_mean_const.npz",
    "linear": "predictions_linear.npz",
    "exponential": "predictions_exponential.npz",
    "google": "predictions_google.npz",
}


def main(config_path: str = "configs/default.yaml") -> None:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    processed = Path(cfg["paths"]["processed_dir"])
    reports = Path(cfg["paths"]["reports_dir"])
    tols = list(cfg["evaluation"]["accuracy_tolerances_h"])

    test = dict(np.load(processed / "test.npz", allow_pickle=True))
    if "device" not in test:
        print("[per-device] no device column in test set, skipping")
        return
    devices = test["device"]
    unique_devices = sorted(set(devices.tolist()))
    print(f"[per-device] devices in test: {unique_devices}")

    # Predictions laden
    preds = {}
    for name, fname in METHOD_FILES.items():
        path = processed / fname
        if not path.exists():
            continue
        d = dict(np.load(path, allow_pickle=True))
        if "valid" not in d:
            d["valid"] = (~np.isnan(d["y_pred"])).astype(bool)
        else:
            d["valid"] = d["valid"].astype(bool)
        preds[name] = d

    out: dict = {
        "_meta": {
            "test_n": int(len(devices)),
            "devices": unique_devices,
            "_note": ("vs_real = Hauptmetric im Paper (gemessene Restzeit). "
                      "vs_extrap = gegen Trainings-Target, zirkulaerer Bias zugunsten "
                      "TinyML/RF; nur zum Vergleich gegen Modell-Pfad."),
        },
        "per_device": {},
    }

    for dev in unique_devices:
        dev_mask = devices == dev
        n = int(dev_mask.sum())
        out["per_device"][dev] = {"n_test": n, "methods_vs_real": {}, "methods_vs_extrap": {}}
        if n < 10:
            continue
        for name, p in preds.items():
            mask = dev_mask & p["valid"] & ~np.isnan(p["y_pred"])
            n_valid = int(mask.sum())
            cov = round(100.0 * n_valid / n, 1)
            if n_valid < 5:
                out["per_device"][dev]["methods_vs_real"][name] = {"n": n_valid}
                out["per_device"][dev]["methods_vs_extrap"][name] = {"n": n_valid}
                continue
            y_p = p["y_pred"][mask]
            out["per_device"][dev]["methods_vs_real"][name] = {
                "coverage_pct": cov,
                **all_metrics(test["y_real"][mask], y_p, tols_h=tols),
            }
            out["per_device"][dev]["methods_vs_extrap"][name] = {
                "coverage_pct": cov,
                **all_metrics(test["y_extrap"][mask], y_p, tols_h=tols),
            }

    reports.mkdir(parents=True, exist_ok=True)
    (reports / "per_device_analysis.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[per-device] wrote {reports / 'per_device_analysis.json'}")

    # Konsole-Zusammenfassung
    print("\n[per-device] C-index by method and device (vs y_real):")
    method_order = ("tinyml", "random_forest", "mean_const", "linear", "exponential", "google")
    header = f"  {'method':<15}" + "".join(f"  {d[:14]:<14}" for d in unique_devices)
    print(header)
    for m in method_order:
        cells = []
        for dev in unique_devices:
            md = out["per_device"][dev]["methods_vs_real"].get(m, {})
            c = md.get("c_index")
            cells.append(f"{c:.3f}" if c is not None else "  -  ")
        print(f"  {m:<15}" + "".join(f"  {c:<14}" for c in cells))


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml")
