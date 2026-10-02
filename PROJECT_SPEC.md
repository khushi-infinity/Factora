# Factora — Operational Digital Twin for Predictive Maintenance

**Event:** Snowflake CoCo CLI Hackathon 2026 — GCC Edition
**Repository:** https://github.com/khushi-infinity/Factora
**Doc status:** v0.2 — M1 revised the local stack to a **React + Vite SPA with a FastAPI backend** (was Next.js), so the Python ML toolchain sits behind one typed API boundary; product scope and demo flow unchanged
**Last updated:** 2026-10-02
**Owner:** Khushi Sarawagi

> This document is the source of truth. Read it together with `PROGRESS.md` **before** changing any code
> (see `AGENTS.md` rule 1). If this spec and the code disagree, fix one of them in the same milestone.

---

## 1. Product Pitch

### 1.1 Pitch order

Deliver the pitch in this order — shortest unit first, so any judge interruption still lands the point.

1. **One-liner (10 s)** — The hook.
2. **Elevator (30 s)** — Problem → what Factora does → the one thing nobody else does.
3. **Story (2 min)** — Walk one machine (CNC-03) from "fine" to "saved", on screen.
4. **Why Snowflake (20 s)** — Data, features, models, retrieval and generation never leave the account.
5. **Close (10 s)** — Impact numbers + who pays for it.

### 1.2 One-liner

> **Factora is an AI operational digital twin that predicts machine failure before it happens, explains
> why in plain language, prices the production impact, and opens the preventive work order — all inside
> Snowflake.**

### 1.3 Elevator pitch

A plant needs one useful answer at 06:00: *which machine breaks next, and what do I do about it?*
Today that knowledge is scattered across a SCADA historian nobody queries, a spreadsheet of past
breakdowns, a PDF manual, a bin of spare parts, and one senior engineer's memory.

Factora unifies machine sensor telemetry, maintenance history, production context, spare-parts stock and
machine knowledge into a single operational digital twin. It scores every asset continuously, flags the
one that is degrading, predicts the failure mode and horizon, writes a grounded explanation that cites
the exact sensor trend and past work orders it used, checks whether the replacement part is actually in
stock, estimates the tonnage and money lost if the machine dies mid-shift versus being fixed in the next
planned window, and creates the preventive work order with a checklist — turning a reactive firefight
into a scheduled 40-minute job.

### 1.4 Story pitch (the 2-minute version)

> CNC-03 is the bottleneck on Line 2. It has been running 14 months without a planned service.
> Nobody has looked at its spindle vibration in weeks.
> Factora sees the vibration RMS climbing and the spindle bearing temperature drifting against its own
> baseline. It raises CNC-03 to **CRITICAL** on the Factory Twin.
> It tells the shift supervisor: *"Spindle bearing degradation, 8–11 days to failure, 78 % confidence."*
> It shows **why** — which sensor, which window, which rate of change, which three historical work orders
> looked like this — with citations, not vibes.
> It checks the parts bin: 2 × SKF-6208-2RS on hand, in the right store.
> It prices both futures: unplanned stop ≈ 6.5 h downtime and 42 t lost output; planned intervention in
> the next window ≈ 45 min.
> Then it writes the work order, assigns the skill level, attaches the checklist and the manual page.
> The supervisor approves. Failure becomes maintenance.

### 1.5 Why Snowflake

- Telemetry, history, inventory and manuals land in **one governed account** — no warehouse-to-warehouse copy.
- Feature engineering and scoring run **next to the data** (Snowpark / Dynamic Tables), so the twin is always current.
- **Cortex Search** grounds every explanation in the plant's own manuals and work-order history — citations, not hallucination.
- **Cortex LLM** turns a probability into a sentence a supervisor can act on.
- The GCC industrial case is a **data-residency and governance** case: nothing has to leave the region or the account to get an answer.

### 1.6 Who pays

Maintenance and reliability managers at GCC manufacturers — steel, aluminium, cement, plastics, food
processing, energy services — running 30–500 machines where one bottleneck asset stopping unexpectedly
costs more than a year of software.

---

## 2. Page List

| # | Route | Page | Job to be done | Scope |
|---|-------|------|----------------|-------|
| 1 | `/` | **Factory Twin** | See the whole plant; spot the one red asset | MVP |
| 2 | `/machines/[machineId]` | **Machine 360** | Everything about one asset: live sensors, trends, health, history | MVP |
| 3 | `/predictions` | **Risk Board** | Ranked list of predicted failures with horizon + confidence | MVP |
| 4 | `/predictions/[predictionId]` | **Diagnosis & Explanation** | Why is it failing? Evidence, citations, feature attribution | MVP |
| 5 | `/parts` | **Spare Parts & Readiness** | Is the fix actually possible today? Stock, lead time, substitutes | MVP |
| 6 | `/work-orders` (list) + `/work-orders/[id]` (detail) | **Preventive Work Orders** | Create, assign, close; full audit trail | MVP |
| 7 | `/impact` | **Production Impact** | Cost of failure now vs. planned intervention in the next window | MVP |
| 8 | `/copilot` | **Ask Factora** | Natural-language questions over the twin (Cortex Analyst / semantic view) | Stretch |
| 9 | `/system` | **Data & Trust** | Pipeline freshness, model version, AI action log, cost guardrail snapshot | Stretch |
| 10 | `/demo` | **Run of Show** | Judge-facing walkthrough, seeded-state reset, timings | MVP (cheap) |

**Navigation spine:** Factory Twin → Machine 360 → (Risk Board) → Diagnosis → Parts check → Impact →
Work Order. Every page keeps a breadcrumb back to that spine so the demo never dead-ends.

**Out of scope as pages:** auth/admin screens (demo runs as a read-mostly single-role app), mobile layouts,
multi-tenant onboarding.

**Visual target:** the ten screen mockups and the binding design language live in
[`mockup/`](./mockup/README.md) (extracted from the build playbook, §2 UI/UX Blueprint). The route shapes
in the table above are this spec's naming; the playbook's mockups assume `/twin`, `/predictive-maintenance`,
`/ai-assistant`, `/spare-parts`, `/oee` and `/planner` instead — **reconcile the two before routing is
written** (§13 Q7).

---

## 3. Architecture

### 3.1 Shape

```
                    ┌─────────────────────────── CoCo CLI (build & deploy agent) ─────────────────────────┐
                    │  scaffolding · Snowflake DDL · deploy scripts · SQL/Snowpark authoring · repo hygiene │
                    └──────────────────────────────────────────────────────────────────────────────────────┘
                                                              │ generates / runs
                                                              ▼
┌──────────────────────────── LOCAL APP (two localhost processes) ────────────────────────────────┐
│  UI  (frontend/, :5173)  React + Vite SPA → Factory Twin · Machine 360 · Risk Board · Diagnosis  │
│                          Parts · Work Orders · Impact · 3D asset view (react-three-fiber)        │
│  BFF (backend/,  :8000)  FastAPI → typed payloads, OpenAPI docs, one thin data-access layer      │
│  No business truth lives here: every score/prediction/explanation is computed in or fetched      │
│  from Snowflake.                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                              │ snowflake-connector-python (key-pair auth, TLS)
                                                              ▼
┌────────────────────────────────────── SNOWFLAKE (system of record + intelligence) ──────────────┐
│  RAW      → landed telemetry, work orders, parts, manuals                                        │
│  CURATED  → Dynamic Tables: clean readings, machine health features, part readiness              │
│  ANALYTICS→ predictions, impact model, KPI marts                                                 │
│  AI       → Cortex Search service (knowledge) · Cortex COMPLETE (explanation, WO draft)          │
│  GOVERN   → roles, masking, row access, query/AI action log, cost guardrails                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Layers and why they exist

| Layer | Responsibility | Deliberate constraint |
|-------|----------------|-----------------------|
| Presentation (React + Vite) | Renders twin state, trends, evidence, forms, 3D asset view | No scoring, no thresholds, no prompt text hardcoded in components |
| BFF (FastAPI) | Auth to Snowflake, shape payloads, cache, degrade gracefully | Never invent data; if Snowflake is down, return an explicit `stale` flag |
| Data access | Single module (`backend/app/db/`) that owns every SQL call | UI code cannot import the connector directly |
| Snowflake curated | All cleansing, feature and score computation | Idempotent, re-runnable, versioned in `/snowflake` |
| Snowflake AI | Retrieval + generation with citations | Prompts stored as files, outputs persisted with model name + inputs hash |

### 3.3 Data path (batch-first, streaming-shaped)

1. Seeded/synthetic historised telemetry lands in `RAW.SENSOR_READING` (documented seed script).
2. Dynamic Tables materialise `CURATED` features incrementally (rolling windows, drift vs. own baseline).
3. Anomaly/health scoring writes `ANALYTICS.MACHINE_HEALTH` and, when thresholds trip, `ANALYTICS.PREDICTION`.
4. Cortex Search indexes manuals + closed work orders; Cortex COMPLETE produces the explanation.
5. The app reads gold tables only — it never scans raw telemetry at request time.

### 3.4 Deployment path

`CoCo CLI` → generates `snowflake/*.sql` and `snowflake/*.py` → run via Snowflake CLI (`snow`) with a
dedicated role → app reads with a read-only role. **No manual object creation in the Snowsight UI** —
everything reproducible from the repo.

### 3.5 Repository layout

```
Factora/
├── frontend/           React 19 + Vite + TS SPA (:5173) — pages, components, typed API client
│   └── src/lib/        API client + pure helpers (unit-tested with Vitest)
├── backend/            FastAPI BFF (:8000)
│   ├── app/api/        route modules (health now; twin, predictions, parts, work orders later)
│   ├── app/db/         Snowflake access — the only place the connector is imported
│   ├── app/ml/         pandas / scikit-learn / joblib scoring + model artefacts (M3+)
│   └── tests/          pytest API + unit tests
├── snowflake/          SQL + Snowpark: schemas, DDL, seeds, dynamic tables, prompts (M2+)
├── tests/e2e/          Playwright demo-flow tests (M6+)
└── PROJECT_SPEC.md · AGENTS.md · PROGRESS.md · README.md · .env.example · .gitignore
```

**Boundary rules:** the SPA never talks to Snowflake directly; FastAPI never renders UI; only
`backend/app/db/` imports the Snowflake connector; only scripts in `snowflake/` create or alter Snowflake
objects; anything that computes a health score, prediction or cost lives in Snowflake (or, for local ML
experiments, in `backend/app/ml/`) — never in a React component.

---

## 4. Tech Stack

| Layer | Choice | License | Why this |
|-------|--------|---------|----------|
| Build/deploy agent | **Snowflake CoCo CLI** (hackathon-supplied) | supplied | Track requirement; used for scaffolding, DDL and deployment |
| Snowflake CLI | `snowflake-cli` (`snow`) | Apache-2.0 | Versioned, scriptable deployments |
| Warehouse compute | Snowflake trial warehouse (X-SMALL workload) | supplied | Hackathon account; cost settings untouched (AGENTS rule 7) |
| Transformation | **Dynamic Tables** + scheduled Tasks | supplied | Incremental, declarative, no external orchestrator |
| Feature/ML code | **Snowpark Python** (`snowpark-python`) | Apache-2.0 | Features next to data; scikit-learn optional for stretch model |
| Statistical scoring | SQL window functions + `REGR_SLOPE`/z-scores, optionally `SNOWFLAKE.ML.FORECAST` | supplied | Fully explainable by construction |
| Retrieval | **Cortex Search** | supplied | Grounded, citable retrieval over manuals and history |
| Generation | **Cortex COMPLETE** (`mistral-large2` default, configurable) | supplied | Runs inside the account; no external LLM key |
| Frontend | **React 19 + Vite + TypeScript** | MIT | SPA with fast HMR; one explicit HTTP boundary to the Python API |
| Frontend styling | **Tailwind CSS** | MIT | Fast, consistent industrial-console look, dark-mode friendly |
| Charts | **Recharts** | MIT | Sensor trend + degradation lines, zero license friction |
| 3D asset view | **@react-three/fiber + @react-three/drei** (three.js) | MIT | Spatial plant/asset view without a paid viewer |
| Backend (BFF) | **FastAPI + Uvicorn** | MIT / BSD-3-Clause | Typed request layer + auto OpenAPI docs; Python ML sits beside it |
| Validation / config | **Pydantic v2 + pydantic-settings** | MIT | Env + payload validation at the boundary |
| Snowflake driver (Python) | `snowflake-connector-python` | Apache-2.0 | Official OSS connector; key-pair auth |
| Data / ML | **pandas, scikit-learn, joblib** | BSD-3-Clause | Local feature work, model training, artefact loading |
| Frontend tests | **Vitest** | MIT | Fast, TS-native unit tests |
| Backend tests | **pytest** (+ `httpx` for the test client) | MIT / BSD-3-Clause | API smoke + unit tests |
| E2E tests | **Playwright** | Apache-2.0 | Drives the real demo flow — the thing judges watch |
| Lint/format | ESLint + Prettier (TS); `ruff` (Python) | MIT | Boring, standard |

**Not used (intentionally):** Next.js / SSR (the SPA + API split keeps the Python ML toolchain
first-class and the boundary honest), any paid API or keyed SaaS (AGENTS rule 6), proprietary BI or
dashboards, a second cloud, GraphQL federation, microservices, a separate feature-store product, an
external vector DB. Anything not in the table above needs a written justification in `PROGRESS.md`
before it is added.

---

## 5. Snowflake Responsibilities

Snowflake owns the **system of record and every piece of intelligence**:

1. **Landing & storage** — telemetry, maintenance history, parts, production calendar, manuals.
2. **Cleansing & conformance** — units, dedupe, late/missing reading handling, machine identity mapping.
3. **Feature engineering** — rolling windows, drift vs. per-machine baseline, RMS/peak, operating-hour accumulation.
4. **Health scoring & anomaly detection** — transparent, parameterised, SQL/Snowpark, versioned in repo.
5. **Prediction** — failure mode + horizon + probability + confidence + evidence payload (JSON).
6. **Impact model** — downtime hours × line throughput × contribution margin; parts + labour cost.
7. **Retrieval** — Cortex Search services over manuals, SOPs and closed work orders; return citations.
8. **Generation** — Cortex COMPLETE for diagnosis narrative, recommended action and work-order draft.
9. **Write-back** — the created work order, its tasks, and its audit record.
10. **Governance & accounting** — least-privilege roles, masking where needed, AI/query action log with
    actor, prompt, model and row counts; credit visibility for the demo, **settings unchanged**.
11. **Reproducibility** — every object created by a repo script that can be re-run from scratch.

---

## 6. Local App Responsibilities

The app is a **thin, honest client**, split across two local processes: a React SPA (`frontend/`) that
renders, and a FastAPI BFF (`backend/`) that authenticates, queries and shapes payloads.

1. **Render the twin** — plant → line → machine → component, with health state and freshness timestamp;
   optional 3D asset view for spatial context.
2. **Visualise evidence** — sensor trends (Recharts), baseline band, anomaly window, degradation slope; never a bare number.
3. **Explain** — present the AI narrative *with* its citations, model name and generated-at time.
4. **Show readiness** — parts on hand vs. required, location, lead time, substitutes, blockers.
5. **Quantify impact** — failure-now vs. planned-window comparison with visible assumptions.
6. **Act** — create a preventive work order (with confirmation), then show it as persisted in Snowflake.
7. **Degrade gracefully** — if a Snowflake call fails or is slow, show cached/synthetic state clearly
   marked `DEMO CACHE`, never silently fabricate.
8. **Enforce demo safety** — read-mostly; the only writes are work orders + audit rows.
9. **Stay credential-safe** — secrets from environment only; never logged, never in the repo, never sent to the browser.

The app **must not**: duplicate scoring logic, hold a copy of the truth in a local database, call any
external AI/paid API, or hardcode demo numbers into components.

---

## 7. Data Model

Three logical schemas plus AI objects. Names are logical; physical naming follows
`FACTORA_{ENV}` databases with `RAW` / `CURATED` / `ANALYTICS` schemas.

### 7.1 Master & context

| Table | Grain | Key fields | Notes |
|-------|-------|-----------|-------|
| `FACTORY` | 1 row / plant | `factory_id, name, country, timezone, currency` | Demo: one GCC plant |
| `PRODUCTION_LINE` | 1 row / line | `line_id, factory_id, name, nominal_rate_uph, bottleneck_flag` | Drives impact maths |
| `MACHINE` | 1 row / machine | `machine_id, line_id, name, type, criticality, install_date, rated_hours_per_day, is_bottleneck` | `CNC-03` lives here |
| `MACHINE_COMPONENT` | 1 row / component | `component_id, machine_id, name, position, expected_life_hours` | Spindle bearing, hydraulic pump… |
| `SENSOR` | 1 row / sensor | `sensor_id, machine_id, component_id, sensor_type, unit, baseline_low, baseline_high, sample_interval_s` | Defines "normal" per asset |

### 7.2 Time series & maintenance

| Table | Grain | Key fields | Notes |
|-------|-------|-----------|-------|
| `SENSOR_READING` | 1 row / sensor / ts | `sensor_id, ts, value, quality_flag` | Append-only, clustered by time; synthetic + replayable |
| `MAINTENANCE_EVENT` | 1 row / historical event | `event_id, machine_id, component_id, event_type, started_at, ended_at, downtime_min, root_cause, free_text` | Training labels + retrieval corpus |
| `FAILURE_MODE` | 1 row / mode | `failure_mode_id, machine_type, name, typical_horizon_days, severity` | e.g. `SPINDLE_BEARING_DEGRADATION` |
| `PRODUCTION_RUN` | 1 row / run / machine | `run_id, machine_id, shift, start_ts, end_ts, units_produced, scrap_units, planned` | Context for impact |

### 7.3 Spare parts

| Table | Grain | Key fields | Notes |
|-------|-------|-----------|-------|
| `PART` | 1 row / part | `part_id, part_number, description, oem, unit_cost, lead_time_days, is_critical` | e.g. `SKF-6208-2RS` |
| `COMPONENT_PART` | many-many | `component_id, part_id, qty_required, fit_confidence` | Component → BOM |
| `PART_INVENTORY` | 1 row / part / store | `part_id, store_id, qty_on_hand, qty_reserved, bin_location, last_counted_at` | "Is the fix possible today?" |
| `SUPPLIER` | 1 row / supplier | `supplier_id, name, region, lead_time_days, contact_channel` | GCC-local sourcing story |

### 7.4 Knowledge & AI

| Table / object | Grain | Key fields | Notes |
|----------------|-------|-----------|-------|
| `KNOWLEDGE_DOC` | 1 row / doc chunk | `doc_id, machine_type, component_id, doc_type, title, section, text, source_uri` | Manuals, SOPs, safety notes |
| `CORTEX_SEARCH_SERVICE_FACTORA_KNOWLEDGE` | service | indexes `KNOWLEDGE_DOC` + closed `MAINTENANCE_EVENT` notes | Returns citations with score |
| `PROMPT_TEMPLATE` | 1 row / prompt version | `prompt_id, version, purpose, body, created_by` | Prompts versioned in the account |
| `AI_ACTION_LOG` | 1 row / model call | `action_id, actor, purpose, model, prompt_version, input_ref, output_ref, latency_ms, created_at` | Audit + demo trust |

### 7.5 Curated & analytics

| Table | Grain | Key fields | Notes |
|-------|-------|-----------|-------|
| `MACHINE_HEALTH` (CURATED) | 1 row / machine / interval | `machine_id, computed_at, health_score, state, drift_pct, readings_used, freshness_s` | Single source of "is it OK?" |
| `SENSOR_FEATURE` (CURATED) | 1 row / sensor / window | `sensor_id, window_end, mean, p95, rms, slope_per_day, zscore_vs_baseline, samples` | Evidence the explanation cites |
| `PREDICTION` (ANALYTICS) | 1 row / prediction | `prediction_id, machine_id, component_id, failure_mode_id, horizon_days_min/max, probability, confidence, state, evidence_json, model_version, created_at` | Drives Risk Board + diagnosis |
| `AI_EXPLANATION` (ANALYTICS) | 1 row / prediction | `explanation_id, prediction_id, narrative, recommended_action, citations_json, model, created_at` | Persisted so the demo can replay it offline |
| `IMPACT_ASSESSMENT` (ANALYTICS) | 1 row / prediction | `impact_id, prediction_id, unplanned_downtime_h, unplanned_cost, planned_downtime_h, planned_cost, units_at_risk, assumptions_json` | Every number traceable to a formula |
| `PART_READINESS` (ANALYTICS) | 1 row / prediction / part | `prediction_id, part_id, qty_required, qty_on_hand, status, eta_days` | `READY` / `PARTIAL` / `BLOCKED` |
| `WORK_ORDER` | 1 row / order | `work_order_id, prediction_id, machine_id, priority, status, planned_start, planned_end, assigned_skill, created_by, created_at, source` | Written back by the app |
| `WORK_ORDER_TASK` | 1 row / task | `work_order_id, seq, task, est_minutes, part_id, safety_note` | Generated checklist, human-editable |

**Design rules:** every derived table carries `model_version` (or `logic_version`) and `computed_at`;
every AI narrative is persisted with its citations and model id; no number reaches the UI without a
drill-down row behind it. Demo seed data plants a known-degradation signature on `CNC-03` so the story
is repeatable.

---

## 8. MVP vs Stretch

### MVP (must work for the demo, end to end)

1. Snowflake objects created from repo scripts; seeded synthetic dataset (≥ 90 days of readings, CNC-03 signature).
2. Curated features + transparent health scoring; CNC-03 reaches `CRITICAL` from the data, not hardcoded.
3. `PREDICTION` row for CNC-03: spindle bearing degradation, horizon + probability + confidence + evidence.
4. Cortex-grounded explanation with citations; persisted, replayable offline.
5. Parts readiness check for the required bearing, from inventory data.
6. Impact comparison (unplanned vs planned) with visible assumptions.
7. Work order creation that writes back to Snowflake and is visible in `/work-orders`.
8. Factory Twin + Machine 360 pages with real trends; freshness shown.
9. Demo-mode cache so a slow/failed Snowflake call cannot break the run.
10. Playwright test that walks the full demo flow; Vitest for the scoring/impact helpers.

### Stretch (only after MVP is green)

1. Cortex Analyst / semantic view behind `/copilot` ("which machines will fail this month?").
2. `SNOWFLAKE.ML.FORECAST` or a trained classifier for RUL, compared against the transparent baseline.
3. Multi-machine Risk Board ranking with lead-time and parts-availability weighting.
4. Cost/benefit roll-up across the plant ("saved this quarter").
5. `/system` page: model version, action log, credit guardrail snapshot.
6. Simulated IoT stream (Task-driven inserts) so the twin visibly moves during the demo.
7. Mobile/tablet floor view; Arabic UI strings for GCC usability.
8. Work-order closure loop → new `MAINTENANCE_EVENT` → model feedback.

### Explicit non-goals

Production auth/SSO, real SCADA/OPC-UA connectivity, ERP write-back, live Arabic localisation of AI text,
any paid service.

---

## 9. Core Demo Flow

**Target: 5 minutes, 6 beats, one machine.** Reset-able at `/demo`.
`Factory Twin → CNC-03 critical → prediction → AI explanation → part check → work order`

### Beat 0 — Setup (before judges arrive)
- Seed run completed; `DEMO_MODE=cache` warm; browser on `/`; Snowflake query running warm.

### Beat 1 — Factory Twin (`/`) — "See the plant"
- Tiles for every machine on Line 1/2 with health state and freshness.
- **One tile is red: CNC-03 — CRITICAL.** Everything else green/amber.
- Line: *"One screen. Nobody had to run a report."*
- On screen: state, health score, last reading age, and the sparkline that has obviously turned.

### Beat 2 — CNC-03 critical → Machine 360 (`/machines/CNC-03`) — "Trust the signal"
- Vibration RMS and bearing-temperature trends over 90 days with the baseline band.
- Drift vs. the machine's *own* baseline; operating hours since last service.
- Maintenance history: three past interventions on the same component.
- Line: *"This isn't a threshold I typed in. It's this machine drifting away from itself."*

### Beat 3 — Prediction (`/predictions/[id]`) — "What and when"
- Failure mode: **spindle bearing degradation**; horizon **8–11 days**; probability + confidence.
- Evidence panel: which sensor, which window, slope per day, z-score, readings used.
- Line: *"The model shows its work. That's the difference between a dashboard and a maintenance decision."*

### Beat 4 — AI explanation — "Why, in words I can act on"
- Cortex narrative: what is degrading, likely cause, why now, what happens if ignored.
- **Citations** to the manual section and the three resembling historical work orders.
- Model name + generated-at visible; note that this ran inside the account.
- Line: *"Grounded in the plant's own documents — not a generic chatbot."*

### Beat 5 — Part check (`/parts`) — "Can we actually fix it today?"
- Required part(s) for the component: `SKF-6208-2RS` ×2 — `READY` (in stock, bin location shown).
- Show the counter-case honestly: a second candidate part is `BLOCKED` with lead time, so the check isn't theatre.
- Line: *"A prediction you can't action is just anxiety."*

### Beat 6 — Impact + work order (`/impact` → `/work-orders/[id]`) — "Make it maintenance"
- Unplanned stop: ~6.5 h downtime, ~42 t units at risk, cost `X` (assumptions visible).
- Planned window: ~45 min, cost `Y`; delta highlighted.
- Click **Create preventive work order** → confirmation → row persisted in Snowflake.
- Work order page: priority, planned window, assigned skill, generated checklist, linked manual, part,
  audit entry (`created_by`, source = prediction).
- Close: *"Sensor to signed work order in under five minutes — every step inside Snowflake."*

### Failure/fallback policy
- Slow call (> 3 s): show skeleton + `DEMO CACHE` badge, keep narrating, never block the run.
- AI unavailable: replay the persisted `AI_EXPLANATION` row (same text the model produced), labelled as replay.
- Snowflake fully down: cached snapshot everywhere, single global banner. **The demo always completes.**

---

## 10. Guardrails & Constraints

1. **No secrets in git** — only `.env.example` is committed; `.env*` and key files are ignored. Key-pair
   auth preferred over passwords. (AGENTS rules 4, 6.)
2. **Free/open-source only**; no new paid APIs. Cortex/Snowflake features are used strictly within the
   hackathon-supplied account.
3. **Do not change Snowflake cost-control settings** (resource monitors, budgets, auto-suspend, warehouse
   size caps) — read and display them only, if at all. (AGENTS rule 7.)
4. **Least privilege at runtime** — the app connects with a read-mostly role; DDL runs as a separate
   deployment role, never `ACCOUNTADMIN` in app config.
5. **Reversible everything** — seed and DDL scripts are idempotent and re-runnable; the demo can be reset.
6. **Honest AI** — every generated sentence carries model, prompt version and citations; no uncited claim
   is rendered as fact; clearly label simulated/mock telemetry as such.
7. **Explainable first** — if a result cannot be explained from stored features, it does not ship to the UI.
8. **Preserve working functionality** — a refactor may not break a green demo beat (AGENTS rule 8).

---

## 11. Milestones

| ID | Milestone | Exit criteria |
|----|-----------|---------------|
| **M0** | Bootstrap (docs) | Six root docs exist, consistent; repo initialised; verification command passes |
| **M1** | Application scaffold | `frontend/` builds (React+Vite+TS+Tailwind, Recharts + react-three-fiber wired) and `backend/` serves `/api/health` with pytest green; run commands documented; **no product pages** |
| **M2** | Snowflake foundation | DDL + seed scripts re-runnable from repo; RAW tables populated; `SELECT`s return sane data |
| **M3** | Curated twin | Dynamic Tables + Snowpark features live; `MACHINE_HEALTH` shows CNC-03 degrading |
| **M4** | Prediction + explanation | `PREDICTION` + `AI_EXPLANATION` rows for CNC-03 with citations; offline replay works |
| **M5** | Parts + impact | `PART_READINESS` and `IMPACT_ASSESSMENT` correct for the demo case, exposed through the API |
| **M6** | Product pages + action | Factory Twin → Work Order flow clickable end to end; work order persists; Playwright flow green |
| **M7** | Demo hardening | Fallback/cache, run-of-show, timings, `/demo` reset; full dry run under 5 min |
| **M8+** | Stretch | Only after M7 is green (see §8) |

Rule: **one milestone at a time**, and `PROGRESS.md` is updated at the end of every completed milestone.

---

## 12. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Cortex/LLM quota or latency in the hackathon account | Demo stalls | Persist explanations; cache mode; verify model availability before demo day |
| Synthetic data too clean → prediction looks rigged | Judges discount it | Realistic noise, extra sensors that are *not* anomalous, honest uncertainty bands |
| Credentials/time-zone/region mismatch on demo machine | Cannot connect live | Key-pair auth script, connection pre-flight page, recorded fallback |
| Scope creep into stretch features | Crisis mode on demo day | Milestone gate in §11; stretch only after M6 |
| Cost surprises | Hackathon rules / bill | X-SMALL warehouse, cached reads, no settings changes, credit check before demo |

---

## 13. Open Questions

1. Final plant story (steel vs. plastics line) and machine naming for the visuals.
2. Whether `SNOWFLAKE.ML.FORECAST` is available on the hackathon account (affects M3 wording).
3. Which Cortex model to pin for the demo (`mistral-large2` assumed) — verify in the account.
4. Whether judges expect a live stream (beat-6 realism) or a deterministic replay — default is deterministic.
5. Public repo hygiene: confirm the demo dataset may remain in the repo if small (< 5 MB), else seed on demand.
6. How much 3D earns its keep: default is one asset view on Machine 360, with a plant-floor diorama on the
   Factory Twin as stretch — decide after M7 based on remaining time and demo impact.
7. **Route and naming alignment with the build playbook.** The playbook and its mockups use `/`, `/twin`,
   `/machines`, `/machines/:id`, `/predictive-maintenance`, `/ai-assistant`, `/work-orders`, `/spare-parts`,
   `/oee`, `/planner`; database `FACTORA` with schemas `RAW` / `CORE` / `AI` / `DOCS`; warehouse
   `FACTORA_WH` (XSMALL, auto-suspend 60 s). This spec currently uses different page names (§2) and
   `FACTORA_{ENV}` with `RAW` / `CURATED` / `ANALYTICS` (§7). Pick one set before routing or DDL is written —
   see `mockup/README.md` → *Deliberate deltas*.
