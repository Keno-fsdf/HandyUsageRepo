"""
End-to-End Orchestrator. Standard-Aufruf:

    python run_pipeline.py

Optional einzelne Stages:

    python run_pipeline.py --stage data
    python run_pipeline.py --stage train
    python run_pipeline.py --stage tflite
    python run_pipeline.py --stage predict
    python run_pipeline.py --stage evaluate
    python run_pipeline.py --stage report

Reihenfolge in der vollen Pipeline:
    data -> train -> tflite -> predict (alle Methoden) -> evaluate -> report
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# Live stdout statt buffered, damit der Pipeline-Fortschritt auch beim
# Output-Redirect (z.B. >> log.txt oder im Hintergrund-Job) sofort sichtbar ist.
os.environ.setdefault("PYTHONUNBUFFERED", "1")
try:
    sys.stdout.reconfigure(line_buffering=True)  # Python 3.7+
except Exception:
    pass


def _stage(name: str):
    print(f"\n{'='*72}\n>>> STAGE: {name}\n{'='*72}", flush=True)


def run_merge(cfg: str) -> None:
    _stage("merge_devices")
    from methods.tinyml.merge_devices import main as f

    f(cfg)


def run_data(cfg: str) -> None:
    _stage("data_prep")
    from methods.tinyml.data_prep import main as f

    f(cfg)


def run_train(cfg: str) -> None:
    _stage("train")
    from methods.tinyml.train import main as f

    f(cfg)


def run_tflite(cfg: str) -> None:
    _stage("tflite_convert")
    from methods.tinyml.tflite_convert import main as f

    f(cfg)


def run_train_rf(cfg: str) -> None:
    _stage("train_random_forest")
    from methods.random_forest.train import main as f

    f(cfg)


def run_predict_all(cfg: str) -> None:
    _stage("predict (tinyml)")
    from methods.tinyml.predict import main as ftiny

    ftiny(cfg)
    _stage("predict (random_forest)")
    from methods.random_forest.predict import main as frf

    frf(cfg)
    _stage("predict (mean_const)")
    from methods.mean_predictor.predict import main as fmean

    fmean(cfg)
    _stage("predict (linear)")
    from methods.linear_baseline.predict import main as flin

    flin(cfg)
    _stage("predict (exponential)")
    from methods.exponential_fit.predict import main as fexp

    fexp(cfg)
    _stage("extract (google)")
    from methods.google_api.extract import main as fgoo

    fgoo(cfg)


def run_evaluate(cfg: str) -> None:
    _stage("three_way_compare")
    from evaluation.three_way_compare import main as facc

    facc(cfg)
    _stage("per_segment_analysis")
    from evaluation.per_segment_analysis import main as fps

    fps(cfg)
    _stage("feature_importance")
    from evaluation.feature_importance import main as ffi

    ffi(cfg)
    _stage("data_diagnostics")
    from evaluation.data_diagnostics import main as fdd

    fdd(cfg)
    _stage("significance")
    from evaluation.significance import main as fsig

    fsig(cfg)
    _stage("export_csv")
    from evaluation.export_csv import main as fcsv

    fcsv(cfg)
    _stage("plot_data_distribution")
    from evaluation.plot_data_distribution import main as fdist

    fdist(cfg)
    _stage("per_device_analysis")
    from evaluation.per_device_analysis import main as fpd

    fpd(cfg)
    _stage("efficiency")
    from evaluation.efficiency import main as feff

    feff(cfg)


def run_report(cfg: str) -> None:
    _stage("report_generator")
    from evaluation.report_generator import main as f

    f(cfg)


STAGES = {
    "merge": run_merge,
    "data": run_data,
    "train": run_train,
    "train_rf": run_train_rf,
    "tflite": run_tflite,
    "predict": run_predict_all,
    "evaluate": run_evaluate,
    "report": run_report,
}

DEFAULT_ORDER = ("merge", "data", "train", "tflite", "train_rf", "predict", "evaluate", "report")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/default.yaml")
    p.add_argument("--stage", choices=list(STAGES.keys()) + ["all"], default="all")
    args = p.parse_args()

    if not Path(args.config).exists():
        print(f"config not found: {args.config}", file=sys.stderr)
        sys.exit(2)

    if args.stage == "all":
        for s in DEFAULT_ORDER:
            t0 = time.time()
            STAGES[s](args.config)
            print(f"[pipeline] stage {s} took {time.time() - t0:.1f}s")
    else:
        STAGES[args.stage](args.config)


if __name__ == "__main__":
    main()
