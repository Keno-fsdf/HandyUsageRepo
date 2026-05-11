"""
Exponentielle Fit-Baseline.

Konzept:
    Pro Test-Datenpunkt nehmen wir die letzten fit_window Roh-Punkte aus
    DEMSELBEN Discharge-Block desselben Sessions. Wir fitten:

        b(dt) = a + c * exp(-k * dt)        (dt in Stunden)

    auf (dt, battery_level), wobei dt=0 dem juengsten Punkt entspricht.
    Restzeit = dt0 fuer das b(dt0) = 0  ->  dt0 = -ln(-a/c) / k.

    Faelle:
    - Wenn der Fit divergiert (zu wenige Punkte, schlecht konditioniert)
      und fallback_to_linear=true, fallen wir auf die lineare Baseline
      ueber dasselbe Fenster zurueck.
    - Wenn auch das nicht geht: NaN.

Begruendung:
    Smartphone-Akkus zeigen oft nicht-lineare Entladung (Voltage-Plateau).
    Ein einzelner exponentieller Term ist die einfachste nicht-lineare
    Form, die das abbilden kann; mehr Komplexitaet (doppel-exp, polynom 3.
    Grades) wuerde bei N=10 Punkten ueberfitten.

Output: data/processed/predictions_exponential.npz
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.optimize import curve_fit


def _exp_model(dt: np.ndarray, a: float, c: float, k: float) -> np.ndarray:
    return a + c * np.exp(-k * dt)


def _fit_one(window: pd.DataFrame) -> tuple[float, str]:
    """Returns (predicted_remaining_h, method_used)."""
    if len(window) < 3:
        return float("nan"), "skip"

    t = window["timestamp"].values.astype(np.float64)
    b = window["battery_level"].values.astype(np.float64)
    # Zeit-Achse: 0 = juengster Punkt, negative Werte = Vergangenheit
    dt = (t - t[-1]) / 3_600_000.0  # in Stunden, <= 0
    # Wir loesen nach kuenftigen Zeiten, also positive dt ab 0
    # -> einfacher: x = (t - t[0]) / 3.6e6, dann dt0 fuer b=0 ueber Newton
    x = (t - t[0]) / 3_600_000.0  # >= 0
    x_now = x[-1]

    # Initialwerte: lineare Heuristik
    drain = b[0] - b[-1]
    span_h = max(x_now - x[0], 1e-6)
    drain_rate = drain / span_h if drain > 0 else 1e-3
    a0 = b[-1] - 5.0
    c0 = b[0] - a0
    k0 = drain_rate / max(c0, 1e-3)

    try:
        popt, _ = curve_fit(
            _exp_model,
            x,
            b,
            p0=[a0, c0, max(k0, 1e-4)],
            maxfev=2000,
            bounds=([-100.0, 1e-3, 1e-5], [100.0, 200.0, 10.0]),
        )
    except Exception:
        return float("nan"), "fit_fail"

    a, c, k = popt
    # Wir wollen das kleinste x_future > x_now mit b(x_future) = 0:
    #   0 = a + c * exp(-k * x_future)  ->  x_future = -ln(-a/c) / k
    if c == 0 or k <= 0:
        return float("nan"), "degenerate"
    ratio = -a / c
    if ratio <= 0:
        return float("nan"), "no_zero_crossing"
    x_zero = -np.log(ratio) / k
    if not np.isfinite(x_zero) or x_zero <= x_now:
        return float("nan"), "past_crossing"
    pred = float(x_zero - x_now)
    # Sanity-Cap: bei sehr flacher Kurve (k -> 0) divergiert die Extrapolation
    # zu mehreren tausend Stunden. Smartphone-Akku haelt physikalisch nie laenger
    # als wenige Tage, daher cap auf 72h. Solche Faelle gelten als degeneriert,
    # weil sie aus einem lokal flachen Fenster (= User hat gerade kaum entladen)
    # extrapoliert wurden, nicht aus einem stabilen Regime.
    if pred > 72.0:
        return float("nan"), "diverged_cap"
    return pred, "exp_fit"


def _linear_fallback(window: pd.DataFrame) -> float:
    if len(window) < 2:
        return float("nan")
    b0 = float(window["battery_level"].iloc[0])
    b1 = float(window["battery_level"].iloc[-1])
    t0 = int(window["timestamp"].iloc[0])
    t1 = int(window["timestamp"].iloc[-1])
    dh = (t1 - t0) / 3_600_000.0
    drain = b0 - b1
    if dh <= 0 or drain <= 0:
        return float("nan")
    rate = drain / dh
    return b1 / rate


def predict_test(config_path: str = "configs/default.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    processed = Path(cfg["paths"]["processed_dir"])
    raw_csv = Path(cfg["paths"]["raw_csv"])
    fit_window = int(cfg["baselines"]["exponential_fit"]["fit_window"])
    use_linear_fallback = bool(cfg["baselines"]["exponential_fit"]["fallback_to_linear"])

    test = dict(np.load(processed / "test.npz"))
    df = pd.read_csv(raw_csv).sort_values(["session_id", "timestamp"]).reset_index(drop=True)
    by_session = {sid: g.reset_index(drop=True) for sid, g in df.groupby("session_id")}
    df_idx = df.set_index("timestamp")

    n = len(test["timestamp_ms"])
    y_pred = np.full(n, np.nan, dtype=np.float32)
    method = np.full(n, "skip", dtype=object)

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
        start = max(0, pos - fit_window + 1)
        window = sess_df.iloc[start : pos + 1]
        window = window[window["charging"] == 0]
        if len(window) < 3:
            if use_linear_fallback:
                lin = _linear_fallback(window)
                y_pred[i] = lin
                method[i] = "lin_fallback_short" if not np.isnan(lin) else "skip"
            continue

        pred, m = _fit_one(window)
        if np.isnan(pred) and use_linear_fallback:
            lin = _linear_fallback(window)
            y_pred[i] = lin
            method[i] = "lin_fallback_failfit" if not np.isnan(lin) else "skip"
        else:
            y_pred[i] = pred
            method[i] = m

    methods, counts = np.unique(method, return_counts=True)
    print("[predict-exp] method distribution:")
    for m, c in zip(methods, counts):
        print(f"  {m}: {c}")
    valid = ~np.isnan(y_pred)
    print(f"[predict-exp] valid {int(valid.sum())}/{n} ({100.0 * valid.mean():.1f}%)")

    return {
        "y_pred": y_pred,
        "valid": valid,
        "method": method.astype(str),
        "y_extrap": test["y_extrap"],
        "y_real": test["y_real"],
        "system_estimate_min": test["system_estimate_min"],
        "battery_level": test["battery_level"],
        "timestamp_ms": test["timestamp_ms"],
        "segment_idx": test["segment_idx"],
    }


def main(config_path: str = "configs/default.yaml") -> None:
    out = predict_test(config_path)
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    out_dir = Path(cfg["paths"]["processed_dir"])
    np.savez_compressed(out_dir / "predictions_exponential.npz", **out)
    print(f"[predict-exp] wrote {out_dir / 'predictions_exponential.npz'}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml")
