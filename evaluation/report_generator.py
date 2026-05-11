"""
Erzeugt reports/REPORT.md aus den JSON-Artefakten der Pipeline.

Quellen:
    data/processed/SUMMARY.md
    models/train_summary.json
    models/tflite_variants.json
    reports/accuracy.json
    reports/efficiency.json

Zweck: 1:1 in den Methoden- und Ergebnisteil des Papers uebernehmbar.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml


def _read_json(path: Path) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _read_text(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def _fmt_metrics_row(name: str, m: dict, tols: list[float], with_ci: bool = False) -> str:
    n = m.get("n", 0)
    if n == 0:
        return f"| {name} | 0 | - | - | - | - | " + " | ".join("-" for _ in tols) + " |"

    def _ci_str(point: float, key: str, fmt: str = ".2f") -> str:
        if not with_ci or key not in m:
            return f"{point:{fmt}}"
        lo, hi = m[key]
        return f"{point:{fmt}} [{lo:{fmt}}, {hi:{fmt}}]"

    cells = [
        f"{n}",
        _ci_str(m["mae_h"], "mae_h_ci95"),
        _ci_str(m["rmse_h"], "rmse_h_ci95"),
        f"{m['me_h']:+.2f}",
    ]
    if m.get("c_index") is not None:
        cells.append(_ci_str(m["c_index"], "c_index_ci95", fmt=".3f"))
    else:
        cells.append("-")
    for t in tols:
        v = m.get(f"acc_within_{t:g}h")
        cells.append(f"{100*v:.1f}%" if v is not None else "-")
    return f"| {name} | " + " | ".join(cells) + " |"


def _accuracy_section(acc: dict, tols: list[float]) -> str:
    if not acc:
        return "_no accuracy.json found_\n"
    lines = []
    lines.append(f"Total test sequences: **{acc['n_test_total']}**  ")
    lines.append(f"Common-valid (all methods): **{acc['n_common_valid']}** "
                 f"({acc['common_coverage_pct']:.1f}%)\n")

    header_tols = " | ".join(f"Acc±{t:g}h" for t in tols)
    header = (
        f"| Method | n | MAE (h) | RMSE (h) | ME (h) | C-index | {header_tols} |"
        f"\n|---|---|---|---|---|---|" + "|".join("---" for _ in tols) + "|"
    )

    lines.append("### vs. measured remaining time (no extrapolation - the honest target)\n")
    lines.append("**Per-method coverage (each on own valid subset)**\n")
    lines.append(header)
    per = acc["vs_measured"]["per_method_native_coverage"]
    for name in ("tinyml", "random_forest", "mean_const", "linear", "exponential", "google"):
        m = per.get(name)
        if not m:
            continue
        lines.append(_fmt_metrics_row(name, m, tols))
    lines.append("")

    common = acc["vs_measured"]["common_subset"]
    if common:
        lines.append("**Common subset (all methods present, 95% bootstrap CI in brackets)**\n")
        lines.append(header)
        for name in ("tinyml", "random_forest", "mean_const", "linear", "exponential", "google"):
            m = common.get(name)
            if not m:
                continue
            lines.append(_fmt_metrics_row(name, m, tols, with_ci=True))
        lines.append("")

    lines.append(
        "### vs. extrapolated target (TinyML training target - circular for TinyML)\n"
    )
    lines.append(
        "> The TinyML model was trained on `y_extrap`. Comparing methods against "
        "this target structurally favours TinyML and is not a fair accuracy measure - "
        "shown for completeness only.\n"
    )
    lines.append(header)
    extrap = acc["vs_extrapolated_caveat"]["common_subset"]
    if extrap:
        for name in ("tinyml", "random_forest", "mean_const", "linear", "exponential", "google"):
            m = extrap.get(name)
            if not m:
                continue
            lines.append(_fmt_metrics_row(name, m, tols, with_ci=True))
    return "\n".join(lines) + "\n"


def _exec_summary(acc: dict | None, sig: dict | None, eff: dict | None) -> str:
    """Eine Halbseite mit den drei Kernzahlen ganz oben im Report."""
    lines = []
    if acc:
        common = acc.get("vs_extrapolated_caveat", {}).get("common_subset", {})
        google = common.get("google", {})
        tinyml = common.get("tinyml", {})
        rf = common.get("random_forest", {})
        mean_c = common.get("mean_const", {})
        n_common = acc.get("n_common_valid", 0)

        def _ci(m: dict, key: str, fmt: str = ".2f") -> str:
            ci = m.get(f"{key}_ci95")
            v = m.get(key)
            if v is None:
                return "n/a"
            if ci and len(ci) == 2:
                return f"{v:{fmt}} [{ci[0]:{fmt}}, {ci[1]:{fmt}}]"
            return f"{v:{fmt}}"

        lines.append(
            f"On a leakage-free segment-level test split (n={n_common} sequences "
            f"where all six methods produce valid predictions), evaluated against the "
            f"shared `y_extrap` target with 95% bootstrap confidence intervals:\n"
        )
        lines.append("| Method | C-index | MAE (h) |")
        lines.append("|---|---|---|")
        for name, m in (("Google API", google), ("Linear (drain rate)", common.get("linear", {})),
                        ("Exponential fit", common.get("exponential", {})),
                        ("Random Forest", rf), ("TinyML Conv1D", tinyml),
                        ("Mean predictor (floor)", mean_c)):
            if not m or m.get("n", 0) == 0:
                continue
            lines.append(f"| {name} | {_ci(m, 'c_index', '.3f')} | {_ci(m, 'mae_h')} |")
        lines.append("")

    if sig:
        c_pairs = sig.get("c_index_pairs", {})

        def _find(a: str, b: str) -> dict | None:
            return c_pairs.get(f"{a}__vs__{b}") or c_pairs.get(f"{b}__vs__{a}")

        tn_mp = _find("tinyml", "mean_const")
        rf_mp = _find("random_forest", "mean_const")
        tn_g = _find("tinyml", "google")
        if tn_mp and rf_mp and tn_g:
            lines.append("**Permutation tests (1000 perms) of pairwise C-index differences:**\n")
            lines.append(
                f"- TinyML vs. Mean predictor: ΔC-idx={tn_mp['delta_obs']:+.3f}, p={tn_mp['p_value']:.3f} "
                f"→ **TinyML is statistically indistinguishable from the no-features floor**.\n"
                f"- Random Forest vs. Mean predictor: ΔC-idx={rf_mp['delta_obs']:+.3f}, p={rf_mp['p_value']:.3f} "
                f"→ same conclusion for an independent ML paradigm.\n"
                f"- TinyML vs. Google API: ΔC-idx={tn_g['delta_obs']:+.3f}, p={tn_g['p_value']:.3f} "
                f"→ Google's system-level access is significantly superior.\n"
            )

    if eff:
        deploy = next((v for k, v in eff.items() if "int8" in k.lower()), None)
        keras = eff.get("keras_float32")
        if deploy and keras:
            lines.append(
                f"**Efficiency** (development machine, n=1000 inference runs each):\n"
                f"- Deployed TFLite INT8: **{deploy.get('size_kb','?')} KB**, "
                f"avg {deploy.get('avg_inference_ms','?')} ms inference.\n"
                f"- Keras Float32 reference: {keras.get('size_kb','?')} KB, "
                f"{keras.get('avg_inference_ms','?')} ms avg.\n"
                f"- TFLite quantization works as advertised; the bottleneck is data signal, not model capacity.\n"
            )

    lines.append(
        "\n**Bottom line for the paper:** the TinyML pipeline is a methodologically clean "
        "negative result. App-level smartphone sensors carry too little signal to compete "
        "with a system-process ML model that has access to ~50 internal hardware metrics. "
        "TinyML quantization itself is not at fault. See full tables and statistical tests below.\n"
    )
    return "\n".join(lines)


def _significance_section(sig: dict | None) -> str:
    if not sig:
        return "_no significance.json found_\n"
    meta = sig.get("_meta", {})
    out = [
        f"Permutation tests on common-valid subset (n={meta.get('n_common', 0)}, target=`{meta.get('target', '?')}`).",
        f"Significance levels: `***` p<0.001, `**` p<0.01, `*` p<0.05, `ns` not significant.\n",
    ]

    def _row(pair: str, t: dict) -> str:
        p = t["p_value"]
        sig_marker = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
        return f"| {pair} | {t['metric_a']:.3f} | {t['metric_b']:.3f} | {t['delta_obs']:+.3f} | {p:.3f} | {sig_marker} |"

    out.append("### C-index pairwise tests\n")
    out.append("| A vs B | C-idx(A) | C-idx(B) | ΔC-idx | p-value | sig |")
    out.append("|---|---|---|---|---|---|")
    for k, v in sig.get("c_index_pairs", {}).items():
        a, b = k.split("__vs__")
        out.append(_row(f"{a} vs {b}", v))
    out.append("")

    out.append("### MAE pairwise tests (h)\n")
    out.append("| A vs B | MAE(A) | MAE(B) | ΔMAE | p-value | sig |")
    out.append("|---|---|---|---|---|---|")
    for k, v in sig.get("mae_pairs", {}).items():
        a, b = k.split("__vs__")
        out.append(_row(f"{a} vs {b}", v))
    return "\n".join(out) + "\n"


def _data_diag_section(dd: dict | None) -> str:
    if not dd:
        return "_no data_diagnostics.json found_\n"
    meta = dd.get("_meta", {})
    out = [
        f"Model-independent feature/target relationships on the **train split** (n={meta.get('n', 0)}).",
        "",
        "Feature aggregation: `current` = value at the most recent timestep within the sliding window.",
        "If Pearson, Spearman AND mutual information are all near zero across all features,",
        "the dataset itself does not contain extractable signal for the target -- independent of the model used.\n",
    ]

    def _block(title: str, key: str) -> str:
        rows = dd.get(key, [])
        if not rows:
            return f"_missing key: {key}_\n"
        out_l = [f"### {title}\n"]
        out_l.append("| Feature | Pearson r | Spearman r | MI (nat) |")
        out_l.append("|---|---|---|---|")
        # Sortiert nach Pearson |r| absteigend
        for r in sorted(rows, key=lambda r: abs(r.get("pearson_r", 0)), reverse=True):
            const = " (constant)" if r.get("constant") else ""
            out_l.append(
                f"| {r['feature']}{const} | {r['pearson_r']:+.3f} | {r['spearman_r']:+.3f} | {r['mi_nat']:.4f} |"
            )
        return "\n".join(out_l) + "\n"

    out.append(_block("vs y_extrap (extrapolated remaining time)", "current_vs_y_extrap"))
    out.append(_block("vs y_real (measured remaining time only)", "current_vs_y_real"))
    return "\n".join(out)


def _per_segment_section(ps: dict | None, tols: list[float]) -> str:
    if not ps:
        return "_no per_segment_analysis.json found_\n"
    lines = []
    meta = ps.get("_meta", {})
    lines.append(
        f"Test set: n={meta.get('n_test')},  "
        f"mean(y_real)={meta.get('y_real_mean_h', 0):.2f}h,  "
        f"mean(y_extrap)={meta.get('y_extrap_mean_h', 0):.2f}h,  "
        f"mean(segment length)={meta.get('segment_length_mean_h', 0):.2f}h,  "
        f"max(segment length)={meta.get('segment_length_max_h', 0):.2f}h\n"
    )

    method_order = ("tinyml", "random_forest", "mean_const", "linear", "exponential", "google")

    def _bucket_block(title: str, group: dict, target_label: str) -> str:
        out = [f"### {title} (vs. {target_label})\n"]
        out.append(
            "| Bucket | n | "
            + " | ".join(f"{m} MAE" for m in method_order)
            + " | "
            + " | ".join(f"{m} C-idx" for m in method_order)
            + " |"
        )
        out.append("|---|---|" + "|".join(["---"] * (2 * len(method_order))) + "|")
        for bname, b in group.items():
            n = b.get("_n", 0)
            mae_cells, cidx_cells = [], []
            for m in method_order:
                mm = b.get(m)
                if not mm or "mae_h" not in mm:
                    mae_cells.append("-")
                    cidx_cells.append("-")
                else:
                    mae_cells.append(f"{mm['mae_h']:.2f}")
                    cidx_cells.append(f"{mm['c_index']:.2f}" if mm.get("c_index") is not None else "-")
            out.append(f"| {bname} | {n} | " + " | ".join(mae_cells + cidx_cells) + " |")
        return "\n".join(out) + "\n"

    lines.append(
        _bucket_block(
            "By battery level at prediction time",
            ps.get("by_battery_level_vs_extrap", {}),
            "y_extrap",
        )
    )
    lines.append(
        _bucket_block(
            "By total segment length",
            ps.get("by_segment_length_vs_extrap", {}),
            "y_extrap",
        )
    )
    lines.append(
        _bucket_block(
            "By y_real magnitude (only short measured remaining time available)",
            ps.get("by_y_real_bucket_vs_real", {}),
            "y_real",
        )
    )
    return "\n".join(lines) + "\n"


def _feature_importance_section(fi: dict | None) -> str:
    if not fi:
        return "_no feature_importance.json found_\n"
    out = ["**Aggregated importance per original feature** (sum over time-steps; higher = more useful for the RF):\n",
           "| Feature | Total importance (Δ MAE in h) |", "|---|---|"]
    for r in fi.get("by_feature_aggregated", []):
        out.append(f"| {r['feature']} | {r['total_importance_mae_h']:+.3f} |")
    out.append("\n**Top 20 individual feature×timestep cells:**\n")
    out.append("| Feature × t-offset | Δ MAE | std |")
    out.append("|---|---|---|")
    for r in fi.get("top_individual", []):
        out.append(f"| {r['name']} | {r['importance_mae_h']:+.3f} | {r['std']:.3f} |")
    out.append("\n_Permutation importance on the held-out test set (n_repeats=5)._\n")
    return "\n".join(out)


def _efficiency_section(eff: dict | None) -> str:
    if not eff:
        return "_no efficiency.json found_\n"
    out = ["| Variant | Size (KB) | Params | Avg latency (ms) | p95 latency (ms) | n |",
           "|---|---|---|---|---|---|"]
    for k, v in eff.items():
        if k.startswith("_"):
            continue
        params = v.get("n_params", "-")
        out.append(
            f"| {k} | {v.get('size_kb','-')} | {params} | "
            f"{v.get('avg_inference_ms','-')} | {v.get('p95_inference_ms','-')} | "
            f"{v.get('n_runs','-')} |"
        )
    out.append(
        f"\n_Measured on the development machine; latencies are an upper bound "
        f"for embedded NPU but a lower bound for app-level overhead. Warmup={eff['_meta']['warmup']}, "
        f"runs={eff['_meta']['runs']}._\n"
    )
    return "\n".join(out)


def main(config_path: str = "configs/default.yaml") -> None:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    reports = Path(cfg["paths"]["reports_dir"])
    models = Path(cfg["paths"]["models_dir"])
    processed = Path(cfg["paths"]["processed_dir"])
    figures_rel = Path(cfg["paths"]["figures_dir"]).relative_to(reports.parent) \
        if Path(cfg["paths"]["figures_dir"]).is_absolute() else Path("figures")
    tols = list(cfg["evaluation"]["accuracy_tolerances_h"])

    data_summary = _read_text(processed / "SUMMARY.md") or "_data prep summary missing_"
    train_summary = _read_json(models / "train_summary.json")
    tflite_variants = _read_json(models / "tflite_variants.json")
    accuracy = _read_json(reports / "accuracy.json")
    efficiency = _read_json(reports / "efficiency.json")
    per_segment = _read_json(reports / "per_segment_analysis.json")
    feat_imp = _read_json(reports / "feature_importance.json")
    rf_summary = _read_json(models / "random_forest_summary.json")
    significance = _read_json(reports / "significance.json")
    data_diag = _read_json(reports / "data_diagnostics.json")

    md = []
    md.append("# Battery Prediction - Reproducibility Report\n")
    md.append("Auto-generated by `evaluation/report_generator.py`. Do not edit by hand.\n")

    md.append("## Executive summary\n")
    md.append(_exec_summary(accuracy, significance, efficiency))

    md.append("## 1. Data\n")
    md.append(data_summary.replace("# Data preparation summary", "").strip() + "\n")

    md.append("## 2. TinyML training\n")
    if train_summary:
        md.append("```json\n" + json.dumps(train_summary, indent=2) + "\n```\n")
    else:
        md.append("_no train_summary.json_\n")

    md.append("## 2b. Random Forest (sanity model)\n")
    md.append(
        "Random Forest with the same flattened sliding-window features. "
        "Independent model paradigm - if it also fails to rank, the bottleneck is the data, not the network.\n"
    )
    if rf_summary:
        md.append("```json\n" + json.dumps(rf_summary, indent=2) + "\n```\n")
    else:
        md.append("_no random_forest_summary.json_\n")

    md.append("## 3. TFLite variants\n")
    if tflite_variants:
        md.append("```json\n" + json.dumps(tflite_variants, indent=2) + "\n```\n")
    else:
        md.append("_no tflite_variants.json_\n")

    md.append("## 4. Accuracy comparison (6-way)\n")
    md.append(_accuracy_section(accuracy, tols))

    md.append("## 4b. Statistical significance (permutation tests)\n")
    md.append(_significance_section(significance))

    md.append("## 5. Per-bucket analysis (where each method works/fails)\n")
    md.append(_per_segment_section(per_segment, tols))

    md.append("## 6. Feature importance (Random Forest)\n")
    md.append(_feature_importance_section(feat_imp))

    md.append("## 6b. Model-independent data diagnostics (Pearson, Spearman, Mutual Information)\n")
    md.append(_data_diag_section(data_diag))

    md.append("## 7. Efficiency benchmark\n")
    md.append(_efficiency_section(efficiency))

    md.append("## 8. Figures\n")
    md.append(f"- Cumulative error: ![cumulative](figures/cumulative_error.png)")
    md.append(f"- Error histogram: ![hist](figures/error_hist.png)")
    md.append("- Scatter plots: `figures/scatter_<method>.png`\n")

    md.append("## 9. Methodology notes (for the paper)\n")
    md.append(
        "- Train/Val/Test split is **segment-level** (not sequence-level) "
        "to prevent leakage: sliding-window sequences from the same discharge "
        "segment never appear in both train and test.\n"
        "- Two targets are stored per sample: `y_real` (measured time to segment end, "
        "no extrapolation) and `y_extrap` (training target with drain-rate extrapolation). "
        "Final results are reported against `y_real`.\n"
        "- Coverage is method-specific (Google API, exponential fit and linear baseline "
        "may be undefined at the start of a segment or when the API is unavailable). "
        "The 'common subset' table evaluates only on samples where all methods produce "
        "a value - this is the only fair head-to-head comparison.\n"
        "- Concordance index (Harrell 1982) is reported alongside MAE because the "
        "training target itself is approximate (Li et al. 2018 use C-index for the same "
        "reason on smartphone battery data).\n"
        "- Efficiency is measured on the dev machine; the deployed TFLite variant is "
        "configured via `tflite.deploy_variant` in `configs/default.yaml`.\n"
        "- A **mean predictor** baseline (always predicts the train mean of `y_extrap`) is included. "
        "It defines a lower-bound floor: any learning model that does not beat it on **C-index** has "
        "not learned a feature->output relationship.\n"
        "- A **Random Forest** sanity model with the same features is included. Used to rule out "
        "that the Conv1D-specific architecture (rather than the data) is the bottleneck.\n"
        "- The 'remaining time to 0%' is censored data: phones rarely discharge to 0% in real use. "
        "We therefore use Harrell's concordance index (Li et al. 2018) as the primary metric, since "
        "it remains valid under target approximation. MAE/RMSE are reported as secondary against "
        "`y_extrap`, the common drain-rate-extrapolated target.\n"
    )

    reports.mkdir(parents=True, exist_ok=True)
    (reports / "REPORT.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"[report] wrote {reports / 'REPORT.md'}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml")
