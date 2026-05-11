"""
Exportiert die Hauptergebnis-Tabellen als CSV fuer den direkten Import
in LaTeX (csvtable / pgfplotstable) oder Word (Tabelle einfuegen).

Erzeugt:
    reports/main_table.csv          - 6 Methoden x Hauptmetriken (mit CI)
    reports/significance_table.csv  - paarweise C-Idx + MAE p-Werte
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml


METHOD_ORDER = ("tinyml", "random_forest", "mean_const", "linear", "exponential", "google")


def _ci_str(point: float, ci: list | None, fmt: str) -> str:
    if ci is None or len(ci) != 2:
        return f"{point:{fmt}}"
    return f"{point:{fmt}} [{ci[0]:{fmt}}, {ci[1]:{fmt}}]"


def write_main_table(reports: Path) -> None:
    accuracy = json.loads((reports / "accuracy.json").read_text(encoding="utf-8"))
    common = accuracy["vs_measured"]["common_subset"]
    common_extrap = accuracy["vs_extrapolated_caveat"]["common_subset"]

    csv_path = reports / "main_table.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "method",
                "n",
                "target",
                "MAE_h",
                "MAE_h_ci95_low",
                "MAE_h_ci95_high",
                "RMSE_h",
                "RMSE_h_ci95_low",
                "RMSE_h_ci95_high",
                "ME_h",
                "C_index",
                "C_index_ci95_low",
                "C_index_ci95_high",
                "Acc_within_1h",
                "Acc_within_2h",
            ]
        )
        for target_name, table in (("y_extrap", common_extrap), ("y_real", common)):
            for name in METHOD_ORDER:
                m = table.get(name)
                if not m or m.get("n", 0) == 0:
                    continue
                mae_ci = m.get("mae_h_ci95", [None, None])
                rmse_ci = m.get("rmse_h_ci95", [None, None])
                cidx_ci = m.get("c_index_ci95", [None, None])
                w.writerow(
                    [
                        name,
                        m["n"],
                        target_name,
                        f"{m['mae_h']:.3f}",
                        f"{mae_ci[0]:.3f}" if mae_ci[0] is not None else "",
                        f"{mae_ci[1]:.3f}" if mae_ci[1] is not None else "",
                        f"{m['rmse_h']:.3f}",
                        f"{rmse_ci[0]:.3f}" if rmse_ci[0] is not None else "",
                        f"{rmse_ci[1]:.3f}" if rmse_ci[1] is not None else "",
                        f"{m['me_h']:+.3f}",
                        f"{m['c_index']:.4f}" if m.get("c_index") is not None else "",
                        f"{cidx_ci[0]:.4f}" if cidx_ci[0] is not None else "",
                        f"{cidx_ci[1]:.4f}" if cidx_ci[1] is not None else "",
                        f"{m.get('acc_within_1h', 0):.4f}",
                        f"{m.get('acc_within_2h', 0):.4f}",
                    ]
                )
    print(f"[csv] wrote {csv_path}")


def write_significance_table(reports: Path) -> None:
    sig_path = reports / "significance.json"
    if not sig_path.exists():
        print("[csv] significance.json missing, skipping")
        return
    sig = json.loads(sig_path.read_text(encoding="utf-8"))
    csv_path = reports / "significance_table.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "method_a", "method_b", "value_a", "value_b", "delta", "p_value", "n", "n_perm"])
        for metric_name, group in (("c_index", sig.get("c_index_pairs", {})), ("mae", sig.get("mae_pairs", {}))):
            for key, t in group.items():
                a, b = key.split("__vs__")
                w.writerow(
                    [
                        metric_name,
                        a,
                        b,
                        f"{t['metric_a']:.4f}",
                        f"{t['metric_b']:.4f}",
                        f"{t['delta_obs']:+.4f}",
                        f"{t['p_value']:.4f}",
                        t["n"],
                        t["n_perm"],
                    ]
                )
    print(f"[csv] wrote {csv_path}")


def main(config_path: str = "configs/default.yaml") -> None:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    reports = Path(cfg["paths"]["reports_dir"])
    reports.mkdir(parents=True, exist_ok=True)
    write_main_table(reports)
    write_significance_table(reports)


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml")
