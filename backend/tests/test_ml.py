"""F3 ML baseline tests: training determinism, metric<->card honesty, inference, and the
demo adapter's separation from real evaluation (AGENTS verification protocol: "ml/train.py
reproduces the metrics quoted in ml/MODEL_CARD.md; inference smoke test passes; the CNC-03
demo adapter is documented and kept separate from the real evaluation")."""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ML_DIR = REPO_ROOT / "ml"
MODEL_CARD = ML_DIR / "MODEL_CARD.md"


def _run(args: list[str], timeout: int = 240) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout)


def _ml_modules():
    """Import ml/ modules (scripts, not a package) without polluting collection time."""
    if str(ML_DIR) not in sys.path:
        sys.path.insert(0, str(ML_DIR))
    import demo_adapter  # noqa: PLC0415
    import predict  # noqa: PLC0415
    import train  # noqa: PLC0415
    return demo_adapter, predict, train


@pytest.fixture(scope="module")
def trained(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("artifacts")
    proc = _run([sys.executable, str(ML_DIR / "train.py"), "--out", str(out), "--quiet"])
    assert proc.returncode == 0, f"train failed:\n{proc.stderr}"
    return out


@pytest.fixture(scope="module")
def metrics(trained: Path) -> dict:
    return json.loads((trained / "metrics.json").read_text(encoding="utf-8"))


def test_training_is_deterministic(trained: Path, tmp_path: Path) -> None:
    """Same seed twice -> byte-identical metrics.json (no wall-clock or float drift)."""
    proc = _run([sys.executable, str(ML_DIR / "train.py"), "--out", str(tmp_path), "--quiet"])
    assert proc.returncode == 0, proc.stderr
    first = (trained / "metrics.json").read_bytes()
    second = (tmp_path / "metrics.json").read_bytes()
    assert first == second, "metrics.json differs between identical runs"


def test_metrics_shape_and_leakage_guards(metrics: dict) -> None:
    evaluation = metrics["evaluation"]
    assert metrics["dataset"]["path"] == "data/raw/ai4i2020.csv"
    assert metrics["dataset"]["rows"] == 10_000
    assert 0.03 < metrics["dataset"]["positive_rate"] < 0.04  # ~3.39% positive
    assert len(metrics["features"]) == 8
    assert set(metrics["excluded_columns"]) == {"UDI", "Product ID", "TWF", "HDF", "PWF", "OSF", "RNF"}
    assert set(evaluation["confusion_matrix"]) == {"tn", "fp", "fn", "tp"}
    cm = evaluation["confusion_matrix"]
    assert cm["tn"] + cm["fp"] + cm["fn"] + cm["tp"] == evaluation["test_rows"] == 2000
    assert cm["tp"] + cm["fn"] == evaluation["test_positives"]
    for name in ("precision", "recall", "f1", "roc_auc", "average_precision"):
        assert 0.0 <= evaluation[name] <= 1.0, name
    assert metrics["split"]["stratify"] is True
    assert metrics["model_params"]["class_weight"] == "balanced_subsample"


def test_model_card_quotes_the_real_metrics(metrics: dict) -> None:
    """MODEL_CARD.md must quote exactly what train.py produced - no hand-tuned numbers."""
    card = MODEL_CARD.read_text(encoding="utf-8")
    evaluation = metrics["evaluation"]
    for label in ("Precision", "Recall", "F1", "ROC-AUC", "Average precision (PR-AUC)"):
        match = re.search(rf"\|\s*{re.escape(label)}\s*\|\s*(?:\*\*)?([0-9.]+)", card)
        assert match, f"metric row missing from MODEL_CARD: {label}"
        assert float(match.group(1)) == evaluation[_card_key(label)], (
            f"MODEL_CARD {label}={match.group(1)} != metrics.json {evaluation[_card_key(label)]}")
    cm = evaluation["confusion_matrix"]
    match = re.search(r"TN = (\d+), FP = (\d+), FN = (\d+), TP = (\d+)", card)
    assert match, "confusion matrix missing from MODEL_CARD"
    assert tuple(int(v) for v in match.groups()) == (cm["tn"], cm["fp"], cm["fn"], cm["tp"])


def _card_key(label: str) -> str:
    return {"Precision": "precision", "Recall": "recall", "F1": "f1", "ROC-AUC": "roc_auc",
            "Average precision (PR-AUC)": "average_precision"}[label]


def test_training_evaluation_is_pure() -> None:
    """ml/train.py must never touch the demo adapter or the synthetic factory data -
    the two layers cannot contaminate each other."""
    source = (ML_DIR / "train.py").read_text(encoding="utf-8")
    assert "demo_adapter" not in source, "train.py must not reference the demo adapter"
    assert "data/generated" not in source, "train.py must not read synthetic factory data"
    assert "generate_factory_data" not in source


def test_infer_failure_type_maps_rules_and_flags() -> None:
    _, predict, train = _ml_modules()

    def features(row: dict) -> dict:
        import pandas as pd  # noqa: PLC0415
        return train.featurize(pd.DataFrame([row])).iloc[0].to_dict()

    base = {"Type": "L", "Air temperature [K]": 300.0, "Process temperature [K]": 309.0,
            "Rotational speed [rpm]": 1500.0, "Torque [Nm]": 45.0, "Tool wear [min]": 230.0}

    # Wear at the published end-of-life boundary -> TWF via the published rule.
    decision = predict.infer_failure_type(0.10, features(base))
    assert decision["type_code"] == "TWF"
    assert "wear" in decision["predicted_failure_type"].lower()

    # Overstrain rule (wear x torque > 11000 for L) co-fires; documented precedence picks OSF.
    decision = predict.infer_failure_type(0.60, features({**base, "Torque [Nm]": 50.0}))
    assert decision["type_code"] == "OSF"
    assert set(decision["contributing_types"]) == {"OSF", "TWF"}

    # Observed flags are reported as ground truth, not as a prediction.
    decision = predict.infer_failure_type(0.02, features({**base, "Tool wear [min]": 50.0}),
                                          observed_flags={"TWF": 1, "HDF": 0, "PWF": 0,
                                                          "OSF": 0, "RNF": 0})
    assert decision["type_code"] == "TWF"
    assert "ground-truth" in decision["basis"]

    # No rule + low probability -> honest "no risk".
    decision = predict.infer_failure_type(0.05, features({**base, "Tool wear [min]": 50.0}))
    assert decision["type_code"] == "NONE"

    # No rule + elevated probability -> honest RNF-like label, never an invented cause.
    decision = predict.infer_failure_type(0.80, features({**base, "Tool wear [min]": 50.0}))
    assert decision["type_code"] == "RNF"
    assert "not inferable" in decision["predicted_failure_type"]


def test_predict_machine_cnc03_shows_high_bearing_risk(trained: Path, metrics: dict) -> None:
    proc = _run([sys.executable, str(ML_DIR / "predict.py"), "--machine", "CNC-03",
                 "--artifacts", str(trained)])
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)

    assert result["is_demo_adapter"] is True
    assert result["demo_failure_risk"] >= 0.70, "CNC-03 must show a HIGH demo risk"
    assert result["risk_band"] == "HIGH"
    assert result["type_decision"]["type_code"] == "BEARING_WEAR"
    assert "BRG-AX-17" in result["type_decision"]["predicted_failure_type"]
    assert 0.0 <= result["model_probability"] <= 1.0
    assert len(result["evidence"]) == 3
    # Out-of-domain projections must be disclosed, not hidden.
    assert result["projected_feature_warnings"], "projected feature warnings expected"
    # The payload carries the real holdout numbers so the demo never shows unevaluated
    # confidence without its provenance.
    assert result["model_holdout"]["f1"] == metrics["evaluation"]["f1"]
    assert "is_demo_adapter" not in str(metrics)  # metrics themselves stay adapter-free


def test_predict_machine_healthy_stays_low(trained: Path) -> None:
    proc = _run([sys.executable, str(ML_DIR / "predict.py"), "--machine", "PKG-01",
                 "--artifacts", str(trained)])
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)

    assert result["demo_failure_risk"] < 0.45, "a healthy machine must not look risky"
    assert result["risk_band"] == "LOW"
    assert result["type_decision"]["type_code"] != "BEARING_WEAR"


def test_demo_adapter_is_pure_and_matches_generator_baselines() -> None:
    """demo_adapter must run without a model (stub scorer) and its mirrored type baselines
    must equal the generator's, so projection and generation cannot drift apart."""
    demo_adapter, _, _ = _ml_modules()
    data_dir = REPO_ROOT / "data" / "generated"

    result = demo_adapter.machine_prediction("CNC-03", data_dir, score_fn=lambda features: 0.0)
    assert result["is_demo_adapter"] is True
    # With a zeroed model, only the rule evidence can raise the risk:
    assert result["demo_failure_risk"] >= 0.70
    assert result["model_probability"] == 0.0

    spec = importlib.util.spec_from_file_location(
        "factora_generator", REPO_ROOT / "scripts" / "generate_factory_data.py")
    generator = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(generator)
    assert demo_adapter.TYPE_BASELINES == generator.BASELINES, (
        "demo_adapter.TYPE_BASELINES drifted from scripts/generate_factory_data.py")
