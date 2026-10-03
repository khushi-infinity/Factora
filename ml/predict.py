#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Score failure risk with the Factora baseline model - clean inference entry points.

Two modes:

  1. AI4I-domain row (the real model, same feature pipeline as training):
         backend/.venv/bin/python ml/predict.py --row '{"Type":"L","Air temperature [K]":300,
             "Process temperature [K]":309,"Rotational speed [rpm]":1500,
             "Torque [Nm]":45,"Tool wear [min]":230}'
     Fails-to: failure probability + a human-readable predicted failure type derived from
     the published AI4I failure rules applied to the row (TWF/HDF/PWF/OSF), or from the
     observed flags if the row carries them (ground truth, labelled as such).

  2. Factory machine via the demo adapter (documented, separate layer):
         backend/.venv/bin/python ml/predict.py --machine CNC-03
     Projects recent telemetry into AI4I space (ml/demo_adapter.py), scores it with the
     real model, combines with bearing evidence by noisy-OR, and sets
     "is_demo_adapter": true. Never used by ml/train.py evaluation.

Clean function API (imported by backend/tests/test_ml.py):
    load_artifacts(dir) -> (model, metrics)
    score_features(model, features: dict) -> float
    infer_failure_type(probability, features, observed_flags=None) -> dict

All output is JSON on stdout so it can be piped into tools or the FastAPI layer (F4).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))  # allow `import demo_adapter` / `import train`

import demo_adapter  # noqa: E402
from train import FEATURES, MODE_FLAGS, featurize  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ARTIFACTS = REPO_ROOT / "ml" / "artifacts"
DEFAULT_DATA_DIR = REPO_ROOT / "data" / "generated"
DEFAULT_AI4I = REPO_ROOT / "data" / "raw" / "ai4i2020.csv"

# Human-readable predicted failure types. The four process rules are the published AI4I
# failure-mode definitions (Matzka 2020); RNF is by definition NOT inferable from
# process features, so an unexplained elevated probability is labelled honestly as such.
FAILURE_TYPE_LABELS = {
    "PWF": "Power failure (torque x speed outside the 3.5-9 kW process envelope)",
    "OSF": "Overstrain failure (tool wear x torque above the variant limit)",
    "HDF": "Heat dissipation failure (air-process delta < 8.6 K below 1380 rpm)",
    "TWF": "Tool wear failure (tool at end of life, >= 200 min wear)",
    "RNF": "Random / undetermined fault (not inferable from process features)",
    "BEARING_WEAR": "Bearing wear - rolling element",
    "NONE": "No elevated failure risk indicated",
}
# Display precedence when several published rules fire on the same row (documented,
# display-only: the evaluated target is binary - see MODEL_CARD).
RULE_PRECEDENCE = ["PWF", "OSF", "HDF", "TWF"]
RULE_VARIABLES = "AI4I published failure-mode definitions (Matzka 2020)"


def load_artifacts(artifacts_dir: Path) -> tuple[object, dict]:
    model_path = artifacts_dir / "model.joblib"
    metrics_path = artifacts_dir / "metrics.json"
    for path in (model_path, metrics_path):
        if not path.exists():
            sys.exit(f"missing {path}\nrun: backend/.venv/bin/python ml/train.py")
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    return joblib.load(model_path), metrics


def score_features(model, features: dict) -> float:
    """Probability of failure for one featurised row - the single scoring entry point."""
    frame = pd.DataFrame([{k: features[k] for k in FEATURES}])
    return float(model.predict_proba(frame)[0, 1])


def _rule_codes(features: dict) -> list[str]:
    """Published AI4I failure rules applied to a featurised row."""
    codes: list[str] = []
    if features["temp_diff_k"] < 8.6 and features["rotational_speed_rpm"] < 1380:
        codes.append("HDF")
    if features["power_w"] < 3500 or features["power_w"] > 9000:
        codes.append("PWF")
    osf_limit = {0: 11000, 1: 12000, 2: 13000}[features["type_ord"]]
    if features["tool_wear_min"] * features["torque_nm"] > osf_limit:
        codes.append("OSF")
    if features["tool_wear_min"] >= 200:
        codes.append("TWF")
    return codes


def infer_failure_type(probability: float, features: dict,
                       observed_flags: dict | None = None) -> dict:
    """Map model output + failure flags/context to a human-readable predicted failure type.

    - If the input row carries observed AI4I failure-mode flags (ground-truth columns in
      the dataset), they are reported as OBSERVED facts, clearly separated from inference.
    - Otherwise the published failure rules are evaluated on the row's features.
    - If no rule fires but the probability is elevated, the label is honestly
      "random / undetermined" (RNF-like) rather than an invented cause.
    """
    observed = {}
    if observed_flags:
        observed = {c: int(observed_flags.get(c, 0) or 0) for c in MODE_FLAGS
                    if str(observed_flags.get(c, "")) != ""}

    if observed:
        codes = [c for c in MODE_FLAGS if observed.get(c) == 1]
        basis = ("observed failure-mode flag(s) in the input row "
                 "(ground-truth labels, not a prediction)")
    else:
        codes = _rule_codes(features)
        basis = f"published failure rules evaluated on the row features ({RULE_VARIABLES})"

    if codes:
        primary = next(c for c in RULE_PRECEDENCE if c in codes) if not observed else codes[0]
        return {
            "type_code": primary,
            "predicted_failure_type": FAILURE_TYPE_LABELS[primary],
            "contributing_types": codes,
            "basis": basis,
            "model_probability": round(probability, 4),
        }
    if probability >= 0.5:
        return {
            "type_code": "RNF",
            "predicted_failure_type": FAILURE_TYPE_LABELS["RNF"],
            "contributing_types": [],
            "basis": ("elevated model probability with no process rule explaining it - "
                      "random faults are not inferable from process features"),
            "model_probability": round(probability, 4),
        }
    return {
        "type_code": "NONE",
        "predicted_failure_type": FAILURE_TYPE_LABELS["NONE"],
        "contributing_types": [],
        "basis": "no failure rule fired and model probability is below the decision threshold",
        "model_probability": round(probability, 4),
    }


def ai4i_range_warnings(features: dict, ai4i_path: Path) -> list[str]:
    """Out-of-domain guard: flag projected features outside the AI4I training range."""
    if not ai4i_path.exists():
        return ["ai4i2020.csv not found - training-range cross-check skipped"]
    df = featurize(pd.read_csv(ai4i_path, encoding="utf-8-sig"))
    warnings = []
    for name in FEATURES:
        lo, hi = float(df[name].min()), float(df[name].max())
        value = features[name]
        if value < lo or value > hi:
            warnings.append(f"projected {name}={value} outside AI4I training range "
                            f"[{lo:.1f}, {hi:.1f}] - out-of-domain input")
    return warnings


def run_machine(machine_id: str, artifacts_dir: Path, data_dir: Path, ai4i_path: Path) -> dict:
    model, metrics = load_artifacts(artifacts_dir)
    result = demo_adapter.machine_prediction(machine_id, data_dir,
                                              score_fn=lambda f: score_features(model, f))
    result["projected_feature_warnings"].extend(
        ai4i_range_warnings(result["projected_features"], ai4i_path))
    if result["type_decision"]["type_code"] is None:
        # No bearing evidence: fall back to the AI4I rule mapping on the projected row.
        fallback = infer_failure_type(result["model_probability"], result["projected_features"])
        result["type_decision"] = {
            "type_code": fallback["type_code"],
            "predicted_failure_type": fallback["predicted_failure_type"],
            "basis": "no strong bearing evidence; " + fallback["basis"],
            "source": "AI4I rule mapping (ml/predict.py)",
        }
    evaluation = metrics["evaluation"]
    result["model_holdout"] = {
        "precision": evaluation["precision"], "recall": evaluation["recall"],
        "f1": evaluation["f1"], "note": ("real evaluation on the AI4I holdout - the demo "
                                         "adapter is NOT part of these metrics"),
    }
    return result


def run_row(row: dict, artifacts_dir: Path) -> dict:
    model, metrics = load_artifacts(artifacts_dir)
    features = featurize(pd.DataFrame([row])).iloc[0].to_dict()
    probability = score_features(model, features)
    observed = {c: row[c] for c in MODE_FLAGS if c in row}
    decision = infer_failure_type(probability, features, observed_flags=observed or None)
    return {
        "model": metrics["model"],
        "threshold": metrics["threshold"],
        "model_probability": round(probability, 4),
        "features": {k: round(float(v), 3) for k, v in features.items()},
        "predicted_failure_type": decision["predicted_failure_type"],
        "type_code": decision["type_code"],
        "contributing_types": decision["contributing_types"],
        "basis": decision["basis"],
        "is_demo_adapter": False,
        "model_holdout": {"precision": metrics["evaluation"]["precision"],
                          "recall": metrics["evaluation"]["recall"],
                          "f1": metrics["evaluation"]["f1"]},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--row", help="AI4I-domain row as a JSON object")
    mode.add_argument("--machine", help="factory machine id, via the demo adapter (e.g. CNC-03)")
    parser.add_argument("--artifacts", type=Path, default=DEFAULT_ARTIFACTS)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR,
                        help="directory holding the generated factory CSVs")
    parser.add_argument("--ai4i", type=Path, default=DEFAULT_AI4I,
                        help="ai4i2020.csv, used only for training-range cross-checks")
    args = parser.parse_args()

    if args.machine:
        result = run_machine(args.machine, args.artifacts, args.data_dir, args.ai4i)
    else:
        try:
            row = json.loads(args.row)
        except json.JSONDecodeError as exc:
            sys.exit(f"--row must be a JSON object: {exc}")
        result = run_row(row, args.artifacts)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
