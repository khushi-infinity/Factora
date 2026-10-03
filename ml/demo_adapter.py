#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""CNC-03 demo adapter: project factory telemetry into AI4I feature space and score
bearing-failure evidence, WITHOUT touching the real model evaluation.

Why this exists
---------------
The baseline model (ml/train.py) is trained only on UCI AI4I process features; it has
never seen vibration or bearing-temperature telemetry and cannot be honestly retrained
on factory data we just synthesised. The 90-second demo still needs CNC-03 to show a
high bearing-failure risk. This module provides that through a *separately documented*
adapter with two explicit, inspectable stages:

1. FEATURE PROJECTION - map the machine's recent telemetry into the AI4I feature space
   with a fixed, documented table (see `project_features`). The real model scores the
   projected row, so the model output in the demo is genuinely the baseline model's.

2. EVIDENCE SCORE - three rule-based bearing indicators from the plant knowledge corpus
   (ISO 10816 vibration zones, the 65/72 C bearing-temperature alarms, prior bearing
   repair count). Each maps to a score in [0, 1]; their mean is the rule evidence score.

   demo_failure_risk = 1 - (1 - model_probability) x (1 - mean(evidence scores))

   i.e. a noisy-OR: the demo risk is high when EITHER the model OR the rules are
   convinced. For CNC-03 the vibration/temperature/repair-history evidence sits at
   0.83 mean, so the risk lands high; for a healthy machine all three scores are low
   and the risk stays low. No weights are tuned to hit a target number.

Separation guarantee (asserted by backend/tests/test_ml.py):
  * ml/train.py never imports this module and never reads data/generated/;
  * the MODEL_CARD evaluation section reports only AI4I holdout metrics;
  * every response produced through this adapter sets "is_demo_adapter": true.

This module is pure stdlib (csv, datetime, pathlib) - no sklearn, no joblib - so it can
be unit-tested without a model.

Usage is via ml/predict.py:  backend/.venv/bin/python ml/predict.py --machine CNC-03
"""

from __future__ import annotations

import csv
from datetime import datetime, timedelta
from pathlib import Path

# Mirrors BASELINES in scripts/generate_factory_data.py - the test suite asserts equality
# with the generator so the two tables cannot silently drift apart.
TYPE_BASELINES = {
    "CNC":       {"vib": 2.4, "temp": 62.0, "rpm": 8500, "amp": 22.0, "cool": 6.2, "cycle": 118.0},
    "PRESS":     {"vib": 3.1, "temp": 55.0, "rpm": 520,  "amp": 48.0, "cool": 4.0, "cycle": 6.5},
    "ASSEMBLY":  {"vib": 1.8, "temp": 48.0, "rpm": 2100, "amp": 12.0, "cool": 0.0, "cycle": 34.0},
    "PACKAGING": {"vib": 2.8, "temp": 50.0, "rpm": 1400, "amp": 15.0, "cool": 0.0, "cycle": 3.2},
    "QUALITY":   {"vib": 0.9, "temp": 41.0, "rpm": 900,  "amp": 9.0,  "cool": 0.0, "cycle": 42.0},
}

# Plant ambient (K). AI4I air temperature sits ~295-308 K; 297.15 K (24 C) is both the
# plant assumption and inside the training range.
AMBIENT_K = 297.15
# Motor constant: 41 Nm at 22 A nameplate (CNC nominal), applied plant-wide as a first-
# order torque estimate because the factory feed has current, not torque.
NM_PER_AMP = 1.864
# AI4I nominal operating speed: spindle rpm is projected proportionally around it so only
# the relative deviation (which the degradation ramp changes slightly) carries meaning.
AI4I_NOMINAL_RPM = 2000.0
# No tool-wear sensor exists in the factory feed; a documented mid-life constant is used.
# The adapter does NOT fabricate a wear trend - see MODEL_CARD limitations.
TOOL_WEAR_MID_LIFE_MIN = 120.0

WINDOW = timedelta(hours=24)

# Evidence tables, straight from the plant knowledge corpus (maintenance_knowledge.csv):
#   - vibration zones MA-CNC-VB-010 (ISO 10816: A<2.8, B<4.5, C<7.1, D>=7.1 mm/s)
#   - temperature alarms BU-CNC-TM-004 (warning 65 C, critical 72 C)
#   - repair history: repeat failures are the strongest single signal
VIBRATION_ZONES = [(2.8, "A", 0.05), (4.5, "B", 0.35), (7.1, "C", 0.85), (float("inf"), "D", 0.98)]
TEMP_ALARMS = [(65.0, 0.05, "below warning"), (72.0, 0.85, "warning band"),
               (float("inf"), 0.98, "critical band")]
PRIOR_REPAIR_SCORES = {0: 0.10, 1: 0.45}          # 2+ repairs -> 0.80
HIGH_EVIDENCE_SCORE = 0.85
HIGH_RISK_THRESHOLD = 0.70


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_machine(machine_id: str, data_dir: Path) -> dict:
    """Row from machines.csv (type, status) or a clear error."""
    for row in _read_csv(data_dir / "machines.csv"):
        if row["machine_id"] == machine_id:
            return row
    raise ValueError(f"unknown machine_id: {machine_id}")


def recent_stats(machine_id: str, data_dir: Path) -> dict:
    """Last-24h means anchored on the machine's newest reading (works for any cadence)."""
    rows = [r for r in _read_csv(data_dir / "sensor_readings.csv") if r["machine_id"] == machine_id]
    if not rows:
        raise ValueError(f"no telemetry for {machine_id} in {data_dir}")
    anchor = max(datetime.fromisoformat(r["ts"]) for r in rows)
    cutoff = anchor - WINDOW
    window = [r for r in rows if datetime.fromisoformat(r["ts"]) >= cutoff]
    mean = lambda col: sum(float(r[col]) for r in window) / len(window)  # noqa: E731
    return {
        "window_start": min(r["ts"] for r in window),
        "window_end": max(r["ts"] for r in window),
        "readings_in_window": len(window),
        "vibration_mean": round(mean("vibration_rms_mm_s"), 3),
        "temp_mean": round(mean("bearing_temp_c"), 2),
        "rpm_mean": round(mean("spindle_speed_rpm"), 1),
        "current_mean": round(mean("motor_current_a"), 2),
    }


def prior_bearing_repairs(machine_id: str, data_dir: Path) -> int:
    return sum(1 for r in _read_csv(data_dir / "maintenance_history.csv")
               if r["machine_id"] == machine_id and r["failure_mode"] == "bearing_wear")


def project_features(machine_type: str, stats: dict) -> tuple[dict, list[str]]:
    """Factory telemetry -> AI4I feature vector. Documented mapping table (MODEL_CARD):

        air_temperature_k  <- plant ambient 297.15 K (constant, in training range)
        process_temperature_k <- air + 10 K (the AI4I definition) + thermal excess
                              = max(0, bearing temp mean - type nominal temp)
        rotational_speed_rpm <- 2000 * (rpm mean / type nominal rpm): proportional map
                              into the AI4I nominal operating point
        torque_nm         <- 1.864 * motor current (nameplate constant)
        tool_wear_min     <- 120 (documented mid-life constant; no sensor exists)
        type_ord          <- L/0: factory feed carries no product variant (neutral)
        power_w, temp_diff_k derived by the shared featurizer rules.

    Returns (features, out_of_range_warnings).
    """
    base = TYPE_BASELINES[machine_type]
    air_k = AMBIENT_K
    thermal_excess = max(0.0, stats["temp_mean"] - base["temp"])
    features = {
        "type_ord": 0,
        "air_temperature_k": air_k,
        "process_temperature_k": round(air_k + 10.0 + thermal_excess, 3),
        "rotational_speed_rpm": round(AI4I_NOMINAL_RPM * stats["rpm_mean"] / base["rpm"], 1),
        "torque_nm": round(NM_PER_AMP * stats["current_mean"], 3),
        "tool_wear_min": TOOL_WEAR_MID_LIFE_MIN,
    }
    features["power_w"] = round(features["torque_nm"] * features["rotational_speed_rpm"]
                                * 6.283185 / 60.0, 1)
    features["temp_diff_k"] = round(features["process_temperature_k"] - air_k, 3)
    warnings: list[str] = []
    if features["process_temperature_k"] > 311.0:
        warnings.append(f"projected process temperature {features['process_temperature_k']} K "
                        "exceeds the AI4I training maximum (~311 K): out-of-domain input, "
                        "treat model_probability as indicative only")
    if features["rotational_speed_rpm"] <= 0:
        warnings.append("projected rotational speed is 0 (machine idle/offline): "
                        "out-of-domain input for the AI4I model")
    return features, warnings


def bearing_evidence(stats: dict, repairs: int) -> list[dict]:
    """Three independent bearing indicators, each scored from a published threshold."""
    vib_score, zone = next((score, name) for limit, name, score in VIBRATION_ZONES
                           if stats["vibration_mean"] < limit)
    evidence = [{
        "signal": "vibration_rms_mm_s (24h mean)",
        "value": stats["vibration_mean"],
        "threshold_context": f"ISO 10816 zone {zone} (<2.8 A / <4.5 B / <7.1 C / >=7.1 D mm/s)",
        "score": vib_score,
        "source": "maintenance_knowledge.csv MA-CNC-VB-010",
    }, {
        "signal": "bearing_temp_c (24h mean)",
        "value": stats["temp_mean"],
        "threshold_context": "alarms at 65 C warning / 72 C critical",
        "score": next(s for limit, s, _label in TEMP_ALARMS if stats["temp_mean"] < limit),
        "source": "maintenance_knowledge.csv BU-CNC-TM-004",
    }, {
        "signal": "prior bearing repairs (all time)",
        "value": repairs,
        "threshold_context": "0 -> 0.10, 1 -> 0.45, >=2 -> 0.80 (repeat failures dominate)",
        "score": PRIOR_REPAIR_SCORES.get(repairs, 0.80),
        "source": "maintenance_history.csv failure_mode=bearing_wear",
    }]
    return evidence


def demo_failure_risk(model_probability: float, evidence: list[dict]) -> float:
    """Noisy-OR of the real model probability and the mean rule-evidence score."""
    rules = sum(e["score"] for e in evidence) / len(evidence)
    return round(1.0 - (1.0 - model_probability) * (1.0 - rules), 4)


def decide_failure_type(machine_id: str, evidence: list[dict], risk: float) -> dict:
    """Bearing label only when the combined risk is HIGH AND the bearing evidence is
    genuinely high; otherwise None and the caller falls back to the AI4I rule-based
    mapping in ml/predict.py. A machine with prior repairs but healthy signals therefore
    never gets a bearing label at low risk."""
    if risk < HIGH_RISK_THRESHOLD:
        return {"type_code": None, "predicted_failure_type": None, "basis": None, "source": None}
    bearing_signals = [e for e in evidence if e["signal"].startswith(("vibration", "bearing_temp"))]
    strong = any(e["score"] >= HIGH_EVIDENCE_SCORE for e in bearing_signals)
    repeat_history = evidence[2]["score"] >= PRIOR_REPAIR_SCORES[1]
    if strong or repeat_history:
        part = " (BRG-AX-17)" if machine_id.startswith("CNC") else ""
        high = [e for e in evidence if e["score"] >= HIGH_EVIDENCE_SCORE]
        detail = ", ".join(f"{e['signal']}={e['value']} -> {e['score']}" for e in high)
        if not detail:
            detail = f"{evidence[2]['signal']}={evidence[2]['value']} -> {evidence[2]['score']}"
        return {
            "type_code": "BEARING_WEAR",
            "predicted_failure_type": f"Bearing wear - rolling element{part}",
            "basis": f"bearing evidence high: {detail}",
            "source": "demo adapter rule evidence (ml/demo_adapter.py)",
        }
    return {"type_code": None, "predicted_failure_type": None, "basis": None, "source": None}


def machine_prediction(machine_id: str, data_dir: Path, score_fn) -> dict:
    """Assemble the full adapter response. `score_fn(features) -> float` is injected (the
    real model scorer from ml/predict.py, or a stub in tests) so this module stays free
    of sklearn/joblib imports."""
    machine = load_machine(machine_id, data_dir)
    machine_type = machine["type"]
    stats = recent_stats(machine_id, data_dir)
    repairs = prior_bearing_repairs(machine_id, data_dir)
    projected, warnings = project_features(machine_type, stats)
    model_probability = float(score_fn(projected))
    evidence = bearing_evidence(stats, repairs)
    risk = demo_failure_risk(model_probability, evidence)
    decision = decide_failure_type(machine_id, evidence, risk)
    rules_mean = round(sum(e["score"] for e in evidence) / len(evidence), 4)
    return {
        "machine_id": machine_id,
        "machine_status": machine["status"],
        "is_demo_adapter": True,
        "model_probability": round(model_probability, 4),
        "projected_features": projected,
        "projected_feature_warnings": warnings,
        "evidence": evidence,
        "rule_evidence_score": rules_mean,
        "demo_failure_risk": risk,
        "risk_band": "HIGH" if risk >= HIGH_RISK_THRESHOLD else "MODERATE" if risk >= 0.45 else "LOW",
        "type_decision": decision,
        "adapter_note": ("demo adapter output - projection + rule evidence combined by noisy-OR; "
                         "not an evaluated prediction (see ml/MODEL_CARD.md)"),
    }
