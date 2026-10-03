# Factora Baseline Failure Model — MODEL CARD

**Status:** baseline (F3) · **Last trained:** metrics below are reproduced by `ml/train.py` and
enforced to match by `backend/tests/test_ml.py` · **Owner:** Khushi Sarawagi

---

## 1. Intended use

Binary early-warning scoring for the Factora predictive-maintenance demo: given one row of
manufacturing process features, output the **probability that the machine fails in that window**,
plus a human-readable predicted failure type. Decision support only — the model is one input into
the work-order flow, never an autonomous action.

**Out of scope:** autonomous control, RUL estimation, any guarantee about a specific physical
asset, and scoring factory telemetry without the documented demo adapter (§7).

## 2. Dataset source

| | |
|---|---|
| Name | **UCI AI4I 2020 Predictive Maintenance Dataset** |
| Source | https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset |
| Citation | AI4I 2020 Predictive Maintenance Dataset [Dataset]. (2020). UCI Machine Learning Repository. https://doi.org/10.24432/C5HS5C |
| Licence | CC BY 4.0 |
| Local file | `data/raw/ai4i2020.csv`, sha256 `dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e` (hash-verified by `scripts/download_ai4i.py`) |
| Size | 10,000 rows × 14 columns, no missing values |

**The dataset itself is synthetic** — Matzka (2020) generated it to reflect real predictive-
maintenance data. It is a fixed published benchmark, not a record of real failures.

## 3. Target

`Machine failure` — binary label, **339 positives (3.39%)**. Set to 1 when any of five failure
modes occurred: TWF (tool wear), HDF (heat dissipation), PWF (power), OSF (overstrain),
RNF (random). The five mode columns are *components of the target*, not features (§4).

## 4. Features (8)

| Feature | Source | Rationale |
|---|---|---|
| `type_ord` | `Type` (L=0, M=1, H=2) | Published quality variant; affects the OSF limit |
| `air_temperature_k` | published input | Process condition |
| `process_temperature_k` | published input | Process condition |
| `rotational_speed_rpm` | published input | Process condition |
| `torque_nm` | published input | Process condition |
| `tool_wear_min` | published input | Direct wear indicator |
| `power_w` | derived: torque × speed | The variable behind the published PWF rule |
| `temp_diff_k` | derived: process − air | The variable behind the published HDF rule |

**Deliberately excluded:** `UDI` (row id), `Product ID` (serial number; its letter duplicates
`Type`), and `TWF/HDF/PWF/OSF/RNF` (**target leakage** — they define the label).
`ml/train.py` builds features by explicit column selection, so excluded columns cannot enter the
model by construction; the test suite asserts the feature list.

## 5. Model and class-imbalance handling

- **Model:** `RandomForestClassifier(n_estimators=300, max_features="sqrt",
  class_weight="balanced_subsample", random_state=42, n_jobs=-1)` — scikit-learn 1.9.1 only
  (no paid/extra libraries), exposes `predict_proba`, captures the nonlinear rule interactions.
- **Imbalance:** stratified 80/20 split; per-tree minority-class reweighting
  (`balanced_subsample`); **PR-AUC (average precision) is reported** because ROC-AUC flatters
  imbalanced problems; confusion matrix shown so FN cost is visible.
- **Decision threshold:** 0.5 (fixed and stated; no threshold tuning was performed — see §6/§8).
- **Determinism:** fixed seed and no wall-clock values in `metrics.json`; two runs are
  byte-identical (asserted by the test suite).

## 6. Evaluation (honest numbers — AI4I holdout, 20 % stratified, seed 42)

Test set: **2,000 rows, 68 positives** (68 = stratified 20 % of 339 ≈ 67.8 → 68).

| Metric | Value |
|---|---|
| Precision | **0.9375** |
| Recall | **0.6618** |
| F1 | **0.7759** |
| ROC-AUC | 0.9708 |
| Average precision (PR-AUC) | 0.8586 |
| Confusion matrix | TN = 1929, FP = 3, FN = 23, TP = 45 |
| Threshold | 0.5 |

**How to read this honestly:** at threshold 0.5 the model is *conservative* — when it raises an
alarm it is right 19 times out of 20 (FP = 3), but it **misses 23 of 68 failures (recall 0.66)**.
That is a real trade-off of the fixed threshold on a 3.39 % positive class, not a tuned result.
Average precision 0.8586 describes ranking quality across thresholds; a production system would
choose a threshold from the PR curve against the cost of missed failures vs false alarms. No
metrics in this card were produced with the demo adapter, synthetic factory data, or any
post-hoc tuning.

## 7. Demo adapter (CNC-03) — documented, evaluated separately, never mixed in

The demo needs CNC-03 (synthetic factory telemetry: vibration, bearing temperature) to show a
**high bearing-failure risk**. The baseline model has never seen those signals, so pretending the
raw model output alone tells that story would be dishonest. `ml/demo_adapter.py` is the documented
bridge:

1. **Feature projection** — the machine's last-24 h telemetry is mapped into AI4I feature space
   with a fixed table (air = 297.15 K plant ambient; process = air + 10 K + thermal excess above
   the machine's type-nominal bearing temperature; rpm projected proportionally around the AI4I
   nominal 2000 rpm; torque = 1.864 × motor current, a nameplate constant; tool wear fixed at
   120 min mid-life because **no tool-wear sensor exists** — no wear trend is fabricated). The
   **real model scores the projected row**; out-of-training-range projections are returned as
   explicit warnings (CNC-03's process-temperature projection is out of domain — disclosed, not
   hidden).
2. **Rule evidence** — three indicators from the plant knowledge corpus, each scored from its
   published threshold: ISO 10816 vibration zone (A/B/C/D), the 65 °C / 72 °C bearing-temperature
   alarms, and prior bearing-repair count.
3. **Combination** — noisy-OR with no tuned weights:

   `demo_failure_risk = 1 − (1 − model_probability) × (1 − mean(evidence scores))`

   A bearing label is attached only when the combined risk is HIGH **and** bearing evidence is
   high; otherwise `ml/predict.py` falls back to the §7b rule mapping.

**CNC-03, current dataset (actual output of `ml/predict.py --machine CNC-03`):**

| | |
|---|---|
| model probability (real model, projected row) | 0.1833 (3 out-of-domain warnings returned) |
| evidence: vibration 4.995 mm/s → zone C | 0.85 |
| evidence: bearing temp 70.72 °C (65–72 band) | 0.85 |
| evidence: 2 prior bearing repairs | 0.80 |
| mean evidence | 0.8333 |
| **demo_failure_risk** | **0.8639 → HIGH** |
| predicted failure type | Bearing wear – rolling element (BRG-AX-17) |

Healthy control: `PKG-01` → risk 0.1667 (LOW), no bearing label. The adapter does not flag
everything.

**Separation guarantees (mechanically enforced by `backend/tests/test_ml.py`):**

- `ml/train.py` never imports `demo_adapter` and never reads `data/generated/` (source-checked);
- §6 metrics come from the AI4I holdout only;
- every adapter response carries `"is_demo_adapter": true` plus the real `model_holdout` numbers;
- adapter outputs are labelled non-evaluated in the payload itself.

### 7b. Failure-type mapping (both paths)

Human-readable type from model output + flags/context (`ml/predict.py::infer_failure_type`):

- Input carries observed AI4I flags → reported as **observed ground truth**, basis says so.
- Else the published failure rules are evaluated on the row: power outside 3.5–9 kW → **PWF**;
  wear × torque over the variant limit → **OSF**; ΔT < 8.6 K under 1380 rpm → **HDF**;
  wear ≥ 200 min → **TWF** (fixed display precedence PWF > OSF > HDF > TWF; evaluation stays
  binary).
- No rule fires but probability ≥ 0.5 → **"Random / undetermined fault (not inferable from
  process features)"** — RNF by definition cannot be predicted from these inputs, and we do not
  invent a cause.
- Below threshold with no rule → **"No elevated failure risk indicated"**.
- Demo-adapter machines with strong bearing evidence → **"Bearing wear – rolling element
  (BRG-AX-17)"**, basis listing the evidence that fired.

## 8. Limitations

1. **Synthetic source data** (§2) — metrics describe performance on a benchmark generator, not on
   a real plant's failure distribution.
2. **Class imbalance** — recall 0.66 at threshold 0.5 means roughly one in three true failures is
   missed at the reported operating point; FN = 23 is printed in every report on purpose.
3. **No RUL, no failure-mode prediction from the model** — modes come from the transparent rule
   mapping (§7b), not from model output.
4. **Factory telemetry is out of the training domain** — vibration/bearing-temperature signals do
   not exist in AI4I. Projection range warnings are returned; the demo risk is adapter output and
   is explicitly **not evaluated** (no ground truth exists for the synthetic scenario).
5. **Single dataset, single split** — no cross-validation, no temporal split, no external
   validation set.
6. **Threshold not tuned** — 0.5 fixed; selecting an operating point needs an explicit
   cost-of-miss/false-alarm decision.

## 9. Reproduction

```bash
backend/.venv/bin/python ml/train.py                # writes ml/artifacts/{model.joblib,metrics.json}
backend/.venv/bin/python ml/predict.py --row '{"Type":"L","Air temperature [K]":300,"Process temperature [K]":309,"Rotational speed [rpm]":1500,"Torque [Nm]":45,"Tool wear [min]":230}'
backend/.venv/bin/python ml/predict.py --machine CNC-03
cd backend && .venv/bin/pytest tests/test_ml.py     # train determinism, metric↔card match, adapter tests
```

`ml/artifacts/` is build output and gitignored; the metrics above are regenerated and re-checked
against this card by the test suite on every run.
