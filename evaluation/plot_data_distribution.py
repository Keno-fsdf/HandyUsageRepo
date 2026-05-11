"""
Visualisiert die Datenverteilung des Test-Sets - speziell die Verteilung
der Segment-Laengen und der y_real-Werte.

Argumentations-Hilfe fuer's Paper: zeigt visuell, dass das Test-Set durch
die Censored-Eigenschaft des Use-Cases auf kurze Restzeiten beschraenkt
ist. Das ist die methodische Standard-Limitation der Domaene, nicht ein
Defekt der Studie.

Output: reports/figures/data_distribution.png
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml


def _segment_lengths_hours(test: dict, raw_csv: Path) -> np.ndarray:
    """Pro Test-Punkt die Laenge des zugehoerigen Discharge-Segments (in h)."""
    df = pd.read_csv(raw_csv).sort_values(["session_id", "timestamp"]).reset_index(drop=True)
    df_idx = df.set_index("timestamp")
    by_session = {sid: g.reset_index(drop=True) for sid, g in df.groupby("session_id")}

    out = np.full(len(test["timestamp_ms"]), np.nan, dtype=np.float32)
    max_gap = 300_000

    for i, ts in enumerate(test["timestamp_ms"]):
        try:
            row = df_idx.loc[int(ts)]
        except KeyError:
            continue
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]
        sid = row["session_id"]
        sess_df = by_session[sid]
        pos_arr = np.where(sess_df["timestamp"].values == int(ts))[0]
        if len(pos_arr) == 0:
            continue
        pos = int(pos_arr[0])
        start = pos
        while start > 0:
            prev = start - 1
            if (
                sess_df.iloc[prev]["charging"] == 0
                and (sess_df.iloc[start]["timestamp"] - sess_df.iloc[prev]["timestamp"]) <= max_gap
            ):
                start = prev
            else:
                break
        end = pos
        while end < len(sess_df) - 1:
            nxt = end + 1
            if (
                sess_df.iloc[nxt]["charging"] == 0
                and (sess_df.iloc[nxt]["timestamp"] - sess_df.iloc[end]["timestamp"]) <= max_gap
            ):
                end = nxt
            else:
                break
        out[i] = (int(sess_df.iloc[end]["timestamp"]) - int(sess_df.iloc[start]["timestamp"])) / 3_600_000.0
    return out


def main(config_path: str = "configs/default.yaml") -> None:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    processed = Path(cfg["paths"]["processed_dir"])
    raw_csv = Path(cfg["paths"]["raw_csv"])
    figures = Path(cfg["paths"]["figures_dir"])

    test = dict(np.load(processed / "test.npz"))
    train = dict(np.load(processed / "train.npz"))

    seg_h = _segment_lengths_hours(test, raw_csv)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(13, 4))

    # 1. Verteilung der y_real-Werte (Test-Set)
    ax = axes[0]
    ax.hist(test["y_real"], bins=40, color="#2196F3", alpha=0.8, edgecolor="black")
    ax.axvline(float(test["y_real"].mean()), color="red", linestyle="--", linewidth=1.5,
               label=f"mean = {float(test['y_real'].mean()):.2f}h")
    ax.axvline(float(test["y_real"].max()), color="orange", linestyle=":", linewidth=1.5,
               label=f"max = {float(test['y_real'].max()):.2f}h")
    ax.set_xlabel("Measured remaining time $y^{real}$ (h)")
    ax.set_ylabel("Frequency")
    ax.set_title(f"(a) Test set $y^{{real}}$\n(censored: phone never reaches 0%)")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)

    # 2. Verteilung der y_extrap-Werte (Test-Set)
    ax = axes[1]
    ax.hist(test["y_extrap"], bins=40, color="#FF9800", alpha=0.8, edgecolor="black")
    ax.axvline(float(test["y_extrap"].mean()), color="red", linestyle="--", linewidth=1.5,
               label=f"mean = {float(test['y_extrap'].mean()):.2f}h")
    ax.set_xlabel("Extrapolated remaining time $y^{extrap}$ (h)")
    ax.set_ylabel("Frequency")
    ax.set_title("(b) Test set $y^{extrap}$\n(common evaluation target)")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)

    # 3. Verteilung der Segment-Laengen
    ax = axes[2]
    valid = ~np.isnan(seg_h)
    ax.hist(seg_h[valid], bins=30, color="#4CAF50", alpha=0.8, edgecolor="black")
    ax.axvline(float(np.nanmean(seg_h)), color="red", linestyle="--", linewidth=1.5,
               label=f"mean = {float(np.nanmean(seg_h)):.2f}h")
    ax.axvline(float(np.nanmax(seg_h)), color="orange", linestyle=":", linewidth=1.5,
               label=f"max = {float(np.nanmax(seg_h)):.2f}h")
    ax.set_xlabel("Total discharge segment length (h)")
    ax.set_ylabel("Frequency (per test sample)")
    ax.set_title("(c) Length of full discharge segment\ncontaining each test sample")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)

    fig.suptitle(
        "Data distribution of the leakage-free test set "
        f"(n = {len(test['y_real'])} sequences from {len(np.unique(test['segment_idx']))} segments)",
        fontsize=12,
    )
    fig.tight_layout()
    figures.mkdir(parents=True, exist_ok=True)
    out_path = figures / "data_distribution.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"[plot-dist] wrote {out_path}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml")
