#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Train the Factora baseline failure model on the UCI AI4I 2020 dataset.

Design decisions (each justified in ml/MODEL_CARD.md):

  * Target: `Machine failure` (binary, 3.39% positive - class imbalance is real).
  * Features: the six published inputs plus `power_w` and `temp_diff_k`, which are the
    variables behind the published AI4I failure rules (PWF and HDF). The ID columns
    (`UDI`, `Product ID`) and the five failure-mode flags (`TWF/HDF/PWF/OSF/RNF`) are
    deliberately EXCLUDED: the flags are components of the target - using them would be
    target leakage.
  * Split: stratified 80/20, fixed random_state.
  * Imbalance: `class_weight="balanced_subsample"` (per-tree reweighting of the minority
    class) + stratified split; PR-AUC (average precision) is reported because ROC-AUC
    flatters imbalanced problems.
  * Model: RandomForestClassifier - scikit-learn only, provides `predict_proba`, captures
    the nonlinear failure-rule interactions a linear model cannot.
  * Determinism: fixed random_state, no wall-clock values in metrics.json - re-running
    reproduces byte-identical metrics (asserted by the test suite).

Evaluation purity (asserted by backend/tests/test_ml.py): this script references neither the
demo adapter layer nor the synthetic factory CSVs - they are a separate, documented layer that
cannot contaminate real evaluation.

Usage:
    backend/.venv/bin/python ml/train.py                 # writes ml/artifacts/{model.joblib,metrics.json}
    backend/.venv/bin/python ml/train.py --out DIR       # write elsewhere (tests use this)
    backend/.venv/bin/python ml/train.py --quiet         # no stdout report
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = REPO_ROOT / "data" / "raw" / "ai4i2020.csv"
DEFAULT_OUT = REPO_ROOT / "ml" / "artifacts"

# Published AI4I column names (the official file spells the ID column UDI).
COL_TYPE = "Type"
COL_AIR_K = "Air temperature [K]"
COL_PROC_K = "Process temperature [K]"
COL_RPM = "Rotational speed [rpm]"
COL_TORQUE = "Torque [Nm]"
COL_WEAR = "Tool wear [min]"
COL_TARGET = "Machine failure"
MODE_FLAGS = ["TWF", "HDF", "PWF", "OSF", "RNF"]
ID_COLS = ["UDI", "Product ID"]

REQUIRED_COLUMNS = [COL_TYPE, COL_AIR_K, COL_PROC_K, COL_RPM, COL_TORQUE, COL_WEAR, COL_TARGET]

FEATURES = [
    "type_ord",             # L=0, M=1, H=2 (published quality variant)
    "air_temperature_k",
    "process_temperature_k",
    "rotational_speed_rpm",
    "torque_nm",
    "tool_wear_min",
    "power_w",              # derived: torque x angular speed  (the PWF rule variable)
    "temp_diff_k",          # derived: process - air           (the HDF rule variable)
]

MODEL_PARAMS = {
    "n_estimators": 300,
    "max_features": "sqrt",
    "class_weight": "balanced_subsample",
    "random_state": 42,
    "n_jobs": -1,
}
SPLIT = {"test_size": 0.20, "random_state": 42, "stratify": True}
THRESHOLD = 0.5


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        sys.exit(f"dataset not found: {path}\n"
                 f"run: python3.11 scripts/download_ai4i.py")
    # utf-8-sig: the official UCI file carries a UTF-8 BOM.
    df = pd.read_csv(path, encoding="utf-8-sig")
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        sys.exit(f"{path} is missing expected columns: {missing} "
                 f"(is this really ai4i2020.csv?)")
    if len(df) != 10_000:
        sys.exit(f"expected 10,000 rows in ai4i2020.csv, found {len(df)}")
    return df


def featurize(df: pd.DataFrame) -> pd.DataFrame:
    """Build the model matrix by explicit column selection - ID and failure-mode flag
    columns can never enter the feature set by construction (anti-leakage)."""
    features = pd.DataFrame(index=df.index)
    features["type_ord"] = df[COL_TYPE].map({"L": 0, "M": 1, "H": 2}).astype(int)
    features["air_temperature_k"] = df[COL_AIR_K].astype(float)
    features["process_temperature_k"] = df[COL_PROC_K].astype(float)
    features["rotational_speed_rpm"] = df[COL_RPM].astype(float)
    features["torque_nm"] = df[COL_TORQUE].astype(float)
    features["tool_wear_min"] = df[COL_WEAR].astype(float)
    features["power_w"] = features["torque_nm"] * features["rotational_speed_rpm"] * 6.283185 / 60.0
    features["temp_diff_k"] = features["process_temperature_k"] - features["air_temperature_k"]
    assert list(features.columns) == FEATURES, "feature list drift"
    return features


def evaluate(model, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= THRESHOLD).astype(int)
    tn, fp, fn, tp = (int(v) for v in confusion_matrix(y_test, pred, labels=[0, 1]).ravel())
    return {
        "precision": round(float(precision_score(y_test, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, proba)), 4),
        "average_precision": round(float(average_precision_score(y_test, proba)), 4),
        "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
        "test_rows": int(len(y_test)),
        "test_positives": int(y_test.sum()),
    }


def train(data_path: Path, out_dir: Path) -> dict:
    df = load_dataset(data_path)
    X = featurize(df)
    y = df[COL_TARGET].astype(int)
    assert not (set(ID_COLS + MODE_FLAGS) & set(FEATURES)), "leakage guard tripped"

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=SPLIT["test_size"], random_state=SPLIT["random_state"],
        stratify=y if SPLIT["stratify"] else None,
    )
    model = RandomForestClassifier(**MODEL_PARAMS)
    model.fit(X_train, y_train)

    metrics = {
        "dataset": {
            "path": str(data_path.relative_to(REPO_ROOT)),
            "sha256": sha256_of(data_path),
            "rows": int(len(df)),
            "positive_rate": round(float(y.mean()), 4),
        },
        "model": "sklearn.ensemble.RandomForestClassifier",
        "model_params": {k: v for k, v in MODEL_PARAMS.items()},
        "features": FEATURES,
        "excluded_columns": ID_COLS + MODE_FLAGS,
        "split": {**SPLIT, "train_rows": int(len(X_train)), "test_rows": int(len(X_test)),
                  "train_positives": int(y_train.sum()), "test_positives": int(y_test.sum())},
        "imbalance_handling": ["stratified_split", "class_weight=balanced_subsample",
                               "report_average_precision"],
        "threshold": THRESHOLD,
        "evaluation": evaluate(model, X_test, y_test),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, out_dir / "model.joblib")
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    return metrics


def report(metrics: dict) -> None:
    e = metrics["evaluation"]
    cm = e["confusion_matrix"]
    print(f"dataset   : {metrics['dataset']['path']}  ({metrics['dataset']['rows']:,} rows, "
          f"{metrics['dataset']['positive_rate']:.2%} positive)")
    print(f"split     : stratified {metrics['split']['test_size']:.0%} test, "
          f"seed {metrics['split']['random_state']} "
          f"({metrics['split']['test_rows']:,} test rows, {e['test_positives']} positives)")
    print(f"model     : {metrics['model']}  (class_weight={metrics['model_params']['class_weight']})")
    print(f"precision : {e['precision']:.4f}")
    print(f"recall    : {e['recall']:.4f}")
    print(f"f1        : {e['f1']:.4f}")
    print(f"roc_auc   : {e['roc_auc']:.4f}   average_precision: {e['average_precision']:.4f}")
    print(f"confusion : TN={cm['tn']} FP={cm['fp']}  FN={cm['fn']} TP={cm['tp']}  "
          f"(threshold {metrics['threshold']})")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="path to ai4i2020.csv")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="artifact output directory")
    parser.add_argument("--quiet", action="store_true", help="suppress the metrics report")
    args = parser.parse_args()

    metrics = train(args.data, args.out)
    if not args.quiet:
        report(metrics)
    print(f"saved     : {args.out / 'model.joblib'} + {args.out / 'metrics.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
