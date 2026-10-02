# Factora — Operational Digital Twin for Predictive Maintenance

**Event:** Snowflake CoCo CLI Hackathon 2026 — GCC Edition
**Repository:** https://github.com/khushi-infinity/Factora
**Doc status:** v0.3 — **realigned to the build playbook** (routes, Snowflake naming, data model, demo timing and build sequence). The playbook wins wherever it disagrees with earlier drafts.
**Last updated:** 2026-10-02
**Owner:** Khushi Sarawagi

> **Sources of truth, in order:**
> 1. the **build playbook** — *Factora Beginner Build Playbook*, archived in full at
>    [`mockup/playbook-source-text.md`](./mockup/playbook-source-text.md) (its prompt sequence F0–F11 / C1–C7
>    is the build order);
> 2. **`mockup/`** — the ten screen mockups and design language ([`mockup/README.md`](./mockup/README.md));
> 3. **this file** — plan of record: pages, architecture, data model, scope, demo flow;
> 4. [`PROGRESS.md`](./PROGRESS.md) — live state. Read it together with this spec before changing code
>    (`AGENTS.md` rule 1).

---

## 1. Product Pitch

### 1.1 Pitch order

Shortest unit first, so an interruption still lands the point.

1. **One-liner (10 s)** — the hook.
2. **Elevator (30 s)** — problem → what Factora does → what nobody else does.
3. **90-second demo** — CNC-03 degrades and becomes a scheduled work order, on screen (§9).
4. **Why Snowflake (20 s)** — governed data + semantic view + Cortex Search + Cortex Agent, all inside the account.
5. **Close (10 s)** — the rubric words: predictive maintenance + OEE command center, IT+OT converged.

### 1.2 One-liner

> **Factora is an AI-powered operational digital twin that unifies factory sensor, maintenance, production
> and inventory data to predict equipment failures, explain the evidence, quantify production impact, and
> create preventive maintenance work orders before downtime happens.**

### 1.3 Elevator pitch

A plant needs one answer at 06:00: *which machine breaks next, and what do I do about it?* Today that
knowledge is scattered across a historian nobody queries, a spreadsheet of past breakdowns, a PDF manual, a
bin of spare parts and one senior engineer's memory.

Factora converges IT and OT data into a single operational twin: it scores every asset, flags the one that is
degrading, predicts the failure mode and remaining useful life, explains the evidence — citing the sensor
trend, the maintenance history and the machine knowledge it used — prices the production impact, checks
whether the replacement part is actually in stock, picks the least disruptive maintenance window and creates
the preventive work order without leaving the interface.

### 1.4 The 90-second demo story

1. Factory is running normally.
2. CNC-03 starts showing rising vibration + temperature.
3. Factora moves CNC-03 healthy → warning → critical.
4. The model predicts bearing failure with high probability.
5. The user asks: *"Why is CNC-03 at risk?"*
6. The Cortex Agent queries telemetry + maintenance history + machine knowledge.
7. Factora checks spare part `BRG-AX-17` and the production schedule.
8. It recommends the least disruptive maintenance window.
9. The user clicks **Create Work Order**.
10. Snowflake records the work order and the twin moves to scheduled maintenance.

### 1.5 What makes it more than a dashboard

| Verb | What Factora does |
|------|-------------------|
| **Predict** | Estimate failure risk before breakdown |
| **Explain** | Show the sensor evidence and historical context behind the prediction |
| **Simulate** | Estimate downtime, output loss and business impact |
| **Decide** | Check maintenance history, spare parts and the production schedule |
| **Act** | Create a work order from the same interface |
| **Visualize** | Reflect machine state in the operational digital twin |

### 1.6 Why Snowflake

- Telemetry, history, inventory and manuals live in **one governed account** — no warehouse-to-warehouse copy.
- A **semantic view** turns the operational tables into business entities, dimensions and metrics that
  natural-language questions can be grounded in.
- **Cortex Search** retrieves procedures, symptoms and repair notes from the plant's own knowledge base.
- A **Cortex Agent** combines structured + unstructured evidence, separates fact from prediction from
  recommendation, and can call a **custom tool** to create the work order.
- The GCC problem statement is an IT+OT convergence and data-residency story: nothing leaves the account to
  get an answer.

### 1.7 Who pays, and how this is judged

Maintenance and reliability managers at GCC manufacturers — steel, aluminium, cement, plastics, food
processing, energy services — running 30–500 machines where one bottleneck asset stopping unexpectedly costs
more than a year of software.

Hackathon rubric shape: **40 % technical execution, 30 % real-world relevance, 30 % solution completeness.**
Every scope decision in §8 is weighted against those three.

---

## 2. Page List

Ten pages. Routes and must-contain lists come from the playbook (§2 UI/UX Blueprint); each has a mockup that
is the **visual target**.

| # | Route | Page | Must contain | Priority | Mockup |
|---|-------|------|--------------|----------|--------|
| 1 | `/` | **Command Center** | Top KPIs, OEE trend, machine health distribution, AI summary, critical alerts, production output, upcoming maintenance | MUST | `01-command-center.jpg` |
| 2 | `/twin` | **Factory Digital Twin** | The visual centrepiece; machines and lines change state (healthy / warning / critical / maintenance-offline) | MUST | `02-factory-digital-twin.jpg` |
| 3 | `/machines` | **Machines Explorer** | Sortable list: health score, failure probability, RUL, vibration, temperature, actions | SHOULD | `03-machines-explorer.jpg` |
| 4 | `/machines/:id` | **Machine Detail** | Live telemetry, prediction, root-cause evidence, maintenance history, parts, Create Work Order | MUST | `04-machine-detail.jpg` |
| 5 | `/predictive-maintenance` | **Predictive Maintenance** | Machines ranked by failure risk / RUL with recommended preventive actions | MUST | `05-predictive-maintenance.jpg` |
| 6 | `/ai-assistant` | **AI Maintenance Agent** | Natural-language investigation with citations/evidence from telemetry, history and knowledge base | MUST | `06-ai-maintenance-agent.jpg` |
| 7 | `/work-orders` | **Work Orders** | Create, assign, schedule, track the work orders Factora generates | MUST | `07-work-orders.jpg` |
| 8 | `/spare-parts` | **Spare Parts** | Stock, reorder level, supplier, lead time, compatible machines | SHOULD | `08-spare-parts.jpg` |
| 9 | `/oee` | **OEE & Production Analytics** | Availability, performance, quality, OEE, output vs target, downtime causes | SHOULD | `09-oee-production-analytics.jpg` |
| 10 | `/planner` | **Maintenance Planner & Reports** | Calendar view, recent alerts, maintenance history, AI-generated report | SHOULD | `10-maintenance-planner-reports.jpg` |

**Shell (every page):** dark navy sidebar, Factora logo/wordmark, plant selector, live-data indicator, search
field, notifications, profile area, responsive dashboard content.

**Design language (binding):** clean enterprise dashboard — **light/white content panels**, blue accent,
machine states green/amber/red/blue-gray/gray, no random gradients, no excessive animation. Full detail and
the colour evidence: [`mockup/README.md`](./mockup/README.md).

**Out of scope as pages:** auth/admin, mobile-specific layouts, multi-tenant onboarding.

---

## 3. Architecture

### 3.1 Shape

```
                          FACTORA UI
                 React + TypeScript + Tailwind (+ shadcn/ui)
                      + React Three Fiber
                               │
                               ▼
                        FastAPI backend
                               │
              ┌────────────────┼─────────────────┐
              ▼                ▼                 ▼
        Snowflake SQL      Cortex Agent     ML inference
              │                │                 │
      ┌───────┼───────┐   ┌────┼─────────┐       │
   Tables  Semantic  Views Search   Custom Tool   │
            View           Service  create_work_order()
      └───────┴───────┴───┴──────────────┴───────┘
                               │
                    Sensors + maintenance + production
                        + inventory + manuals
```

### 3.2 Layers and why they exist

| Layer | Responsibility | Deliberate constraint |
|-------|----------------|-----------------------|
| Presentation (`frontend/`) | Renders the twin, charts, evidence, forms; animates the demo scenario locally | No scoring, no thresholds, no prompt text in components; numbers come from the API |
| BFF (`backend/`) | Auth to Snowflake, shape payloads, cache, call ML inference, degrade gracefully | Never invent data; a failure surfaces as an explicit error or a labelled demo fallback |
| Data access (`backend/app/db/`) | The only place the Snowflake connector is imported | No SQL built in route modules or components |
| ML (`backend/app/ml/`, `ml/`) | Feature work, training, inference, model artefacts | Every model result carries honest metrics and a documented demo adapter |
| Snowflake data (`FACTORA`) | Landing, conformance, analytics-serving tables | Idempotent, re-runnable, versioned in `snowflake/sql/` |
| Snowflake AI (`FACTORA.AI`, `snowflake/agent/`) | Semantic view, Cortex Search, Cortex Agent, work-order tool | Prompts/config versioned in repo; agent separates fact / prediction / recommendation |

### 3.3 Data path

1. `scripts/` produces deterministic CSVs: AI4I 2020 baseline data plus synthetic factory context
   (`data/raw/`, `data/generated/`).
2. `snowflake/sql/` loads them into `FACTORA.RAW` → `FACTORA.CORE` (the operational tables the app reads).
3. Local scikit-learn inference (`ml/`) produces failure probability / RUL; results are written to
   `FAILURE_PREDICTIONS`.
4. `FACTORA.AI` holds the semantic view, the Cortex Search service over `MAINTENANCE_KNOWLEDGE`, and the
   Cortex Agent plus its `create_work_order` tool.
5. The app reads Snowflake (snapshot per page load, not per second) and persists only meaningful events.

### 3.4 Cost discipline (non-negotiable)

- **Do not poll Snowflake per second.** Fetch a snapshot on page load, animate the demo locally in the
  frontend, and persist important events/actions.
- For the judge demo, a 15–30-second refresh or a manual **Refresh** button is enough.
- Warehouse stays **XSMALL with 60-second auto-suspend**; no new warehouses; no always-on services
  (no continuous Snowpipe); static knowledge corpus with minimal refresh.
- Cost-control settings are **human-run** (playbook §5, in Snowsight) and read-only for agents
  (`AGENTS.md` rule 7).

### 3.5 Repository layout

```
Factora/
├── frontend/                  React + Vite + TS SPA (:5173) — pages, components, typed API client
├── backend/                   FastAPI BFF (:8000)
│   ├── app/api/               route modules
│   ├── app/db/                the ONLY Snowflake connector import
│   ├── app/ml/                local inference helpers
│   └── tests/                 pytest API + unit tests
├── ml/                        train.py · predict.py · artifacts/ · MODEL_CARD.md
├── data/                      raw/ (AI4I) · generated/ (synthetic CSVs) · README.md
├── snowflake/                 sql/ (ordered, re-runnable) · semantic/ · agent/
├── docs/                      demo-script.md · SUBMISSION_CHECKLIST.md · demo assets
├── scripts/                   download_ai4i.py · generate_factory_data.py
├── mockup/                    the ten screen mockups + design target (visual source of truth)
└── PROJECT_SPEC.md · AGENTS.md · PROGRESS.md · README.md · .env.example · .gitignore
```

**Status at v0.3:** `frontend/`, `backend/` and `mockup/` exist. `ml/`, `data/`, `snowflake/`, `docs/` and
`scripts/` are created by the next prompts in §11.

### 3.6 Deployment path

`CoCo CLI` creates and validates every Snowflake object (tables, semantic view, Search, Agent, tool) from
scripts kept in `snowflake/`; FastAPI reads with a read-mostly role. Everything reproducible from the repo —
no manual object creation in the Snowsight UI except the one-time cost-safety SQL the human runs.

---

## 4. Tech Stack

| Layer | Choice | License | Why |
|-------|--------|---------|-----|
| Frontend | **React + Vite + TypeScript** | MIT | Fast to scaffold; easy local demo |
| Design | **Tailwind CSS + shadcn/ui** | MIT | Matches the clean dashboard mockups |
| Charts | **Recharts** | MIT | OEE, telemetry and output charts |
| Digital twin | **@react-three/fiber + @react-three/drei** | MIT | 3D/2.5D scene without a game engine |
| Backend | **FastAPI + Python 3.11** | MIT | Easy ML + Snowflake integration |
| Snowflake client | **snowflake-connector-python** | Apache-2.0 | Direct SQL and stored-procedure calls |
| ML | **pandas + scikit-learn + joblib** | BSD-3-Clause | Free, beginner-friendly, sufficient for the prototype |
| Snowflake AI | **Semantic Views + Cortex Search + Cortex Agent** | supplied | Structured + unstructured reasoning and actions |
| Snowflake SQL | Warehouse `FACTORA_WH` (XSMALL, auto-suspend 60 s) | supplied | Hackathon account; cost settings untouched |
| Coding agent | **Freebuff** | — | Most local coding work |
| Snowflake agent | **CoCo CLI** (`cortex`) | supplied | Snowflake-specific creation, validation, agent workflows |
| Frontend tests | **Vitest** | MIT | Fast TS unit tests |
| Backend tests | **pytest** (+ httpx) | MIT / BSD-3 | API smoke + unit tests |
| Lint/format | ESLint + Prettier; `ruff` | MIT | Standard, fast |

**Not used (intentionally):** Next.js/SSR, any external paid LLM API (OpenAI, Anthropic, Gemini), paid data
sources, proprietary BI, a second cloud, microservices, an external vector DB. Anything not in this table
needs a written justification in `PROGRESS.md` (`AGENTS.md` rule 5).

---

## 5. Snowflake Responsibilities

Snowflake is the system of record, the retrieval layer and the action layer:

1. **Storage** — machines, sensor readings, maintenance history, spare parts, work orders, production runs,
   downtime events, failure predictions, maintenance knowledge.
2. **Structured reasoning** — the **semantic view** defining business entities, joins, dimensions and metrics
   (e.g. which machines have the highest failure risk, which line has the lowest OEE, what production is at
   risk if CNC-03 stops).
3. **Unstructured reasoning** — **Cortex Search** over machine manuals, procedures and repair notes, with
   machine type / id / document-type filters.
4. **Agent reasoning** — a **Cortex Agent** (`FACTORA_MAINTENANCE_AGENT`, persona: senior reliability
   engineer) that uses the semantic view for facts, Search for evidence, separates observed data from
   prediction and recommendation, never claims certainty, and cites its evidence.
5. **Action** — a **custom tool / stored procedure** that creates a single `PROPOSED`/`SCHEDULED` work order,
   validating `machine_id`, never deleting rows, logging `created_at` and `source='CORTEX_AGENT'`.
6. **Compute discipline** — `FACTORA_WH` XSMALL, auto-suspend 60 s, small datasets, no continuous services,
   no polling from the app.
7. **Governance** — least-privilege roles, credentials never in git, cost controls untouchable.
8. **Reproducibility** — every object created by a script in `snowflake/`, re-runnable from a clean account.

---

## 6. Local App Responsibilities

The local app is a thin, honest client in two processes (SPA + BFF):

1. **Render the twin** — Command Center, Factory Twin, machine pages, agent panel, work orders, parts, OEE,
   planner — matching `mockup/` exactly.
2. **Visualise evidence** — telemetry trends, prediction, RUL, root-cause evidence; never a bare number.
3. **Explain** — present the agent's answer with its citations, and visually separate observed data,
   prediction and recommendation.
4. **Act** — Create Work Order from the UI, persisted through the agent's tool or the API.
5. **Demo Mode** — Reset Demo + Start CNC-03 Failure Scenario, deterministic 90-second story.
6. **Degrade gracefully** — a clearly isolated `DEMO_MODE` fallback using generated CSVs only when Snowflake
   is unavailable; normal mode always uses Snowflake.
7. **Cache** — never let the UI hammer Snowflake; snapshot per load.
8. **Label simulation** — simulated/demo telemetry is marked as simulated in the UI or About section.
9. **Stay credential-safe** — secrets from the environment only, never logged, never sent to the browser.

**The app must not:** fake model metrics, invent numbers in components, poll Snowflake continuously, call any
external paid API, or hide a failure behind a plausible-looking chart.

---

## 7. Data Model

**Database `FACTORA`**, schemas **`RAW`** (as loaded), **`CORE`** (operational tables the app reads),
**`AI`** (semantic view, Search, Agent), **`DOCS`** (knowledge corpus). Warehouse `FACTORA_WH` (XSMALL).

| Table | Schema | Purpose | Approx. size |
|-------|--------|---------|--------------|
| `MACHINES` | CORE | Asset registry + twin coordinates (`x`, `y`, `z`), line, type, `status`, `health_score` | 20–30 machines (24 in the generator: CNC, press, assembly, packaging, quality) |
| `SENSOR_READINGS` | CORE | Telemetry snapshots / demo series per machine and timestamp | 10k–50k rows |
| `FAILURE_PREDICTIONS` | CORE | Model output: risk, RUL, contributing features | 1 row per machine/run |
| `MAINTENANCE_HISTORY` | CORE | Past faults and repairs | 100–200 rows |
| `SPARE_PARTS` | CORE | Inventory and machine compatibility (incl. `BRG-AX-17` for CNC-03, limited stock) | 30–50 parts |
| `WORK_ORDERS` | CORE | Preventive/corrective work; written by the custom tool | 50–100 rows |
| `PRODUCTION_RUNS` | CORE | Target vs actual output (drives OEE) | 1–2 weeks |
| `DOWNTIME_EVENTS` | CORE | Downtime causes and duration | 50–100 rows |
| `MAINTENANCE_KNOWLEDGE` | DOCS | Manual/SOP text chunks for Cortex Search | 30–80 chunks |

**Machine state model:** `HEALTHY` / `WARNING` / `CRITICAL` / `MAINTENANCE` / `OFFLINE` — the same vocabulary
as the UI state colours and the twin.

**OEE definitions (keep explicit, no invented numbers):**
`Availability = Run Time / Planned Production Time`, `Performance = (Ideal Cycle Time × Total Count) / Run Time`,
`Quality = Good Count / Total Count`, `OEE = Availability × Performance × Quality`.

**Data sources and disclosure:** the baseline model uses the **UCI AI4I 2020 Predictive Maintenance** dataset
(10,000 observations, air/process temperature, rotational speed, torque, tool wear, failure flag and failure
modes). Everything else (machines, enterprise context, parts, work orders, knowledge chunks, the CNC-03
scenario) is **synthetic and must be labelled as such**; `data/README.md` documents every column and which
fields are synthetic. **NASA IMS Bearings** is stretch-only.

---

## 8. MVP vs Stretch

| Priority | Build | Rule |
|----------|-------|------|
| **MUST** | Command Center, Factory Twin, Machine Detail, Predictive Maintenance, AI Agent, Work Order creation | One flawless end-to-end flow before anything else |
| **SHOULD** | Machines Explorer, Spare Parts, OEE analytics, Maintenance planner | Only after MUST pages render real data |
| **STRETCH** | NASA bearing model, advanced 3D assets, continuous streaming, deployment, PDF parsing | Only after the full demo runs twice cleanly |

**Non-goals:** production auth/SSO, real SCADA/OPC-UA connectivity, ERP write-back, live Arabic localisation,
any paid service.

---

## 9. Core Demo Flow

**90 seconds, deterministic, resettable.** One machine (CNC-03), one story: risk → evidence → part → work order.

| Time | Action | What is said |
|------|--------|--------------|
| 0–15 s | Command Center | *"Factora unifies machine telemetry with maintenance, production and inventory context instead of treating sensors in isolation."* |
| 15–35 s | Factory Twin → **Start scenario** | *"CNC-03 begins degrading. The operational twin changes state as its vibration and temperature move outside baseline."* |
| 35–55 s | Machine Detail / Predictive Maintenance | *"The model predicts bearing failure before breakdown and estimates remaining useful life."* |
| 55–75 s | Ask the AI Agent why | *"The Cortex Agent combines governed factory data with maintenance knowledge to explain the evidence and the recommended action."* |
| 75–90 s | Part check + **Create Work Order** | *"Factora verifies `BRG-AX-17` inventory and turns the prediction into a preventive work order in the lowest-impact window."* |

**Scenario timeline (Demo Mode):** healthy baseline → vibration and temperature rise → warning → critical
(with the demo prediction displayed only if backed by the documented demo adapter) → AI investigation →
`BRG-AX-17` shown → proposed repair window → Create Work Order → twin switches to scheduled maintenance.

**Rules:** Reset Demo and Start CNC-03 Failure Scenario buttons; the scenario animates locally and persists
only meaningful events; simulated live telemetry is labelled; Demo Mode must never generate thousands of
Snowflake queries. `docs/demo-script.md` holds the click-by-click narration.

*(The earlier 5-minute six-beat flow is retired in favour of this timing.)*

---

## 10. Guardrails & Constraints

1. **No secrets in git** — only `.env.example`; `.env*`, `*.p8`, `*.pem`, `rsa_key*` ignored; key-pair auth
   preferred; the API has tests asserting credentials cannot appear in a response (`AGENTS.md` rule 4).
2. **Free/open-source only; no paid API** — no external LLM endpoints (rules 5, 6).
3. **Cost-control settings are read-only for agents** — the playbook's warehouse/resource-monitor/CoCo-cap
   SQL is a one-time human action in Snowsight (rule 7).
4. **Cost discipline** — XSMALL, auto-suspend 60 s, snapshot reads, local demo animation, small datasets.
5. **Honest numbers** — no faked metrics, no invented component data, no unbounded accuracy claims;
   `MODEL_CARD.md` records limitations.
6. **Label simulation** — synthetic data and demo telemetry are visibly disclosed.
7. **Explainable first** — if a result cannot be traced to stored evidence, it does not ship to the UI.
8. **Preserve working functionality** — a green demo beat stays green; revert to the last working commit
   rather than debugging on stage (rule 8).

---

## 11. Build Sequence

The playbook's Master Build Sequence is the build order — **one prompt at a time**, never all at once.

| Order | Prompt | Owner | Deliverable | Status |
|-------|--------|-------|-------------|--------|
| 0 | **F0** | Freebuff | Project control files + progress system | ✅ done |
| 1 | **F1** | Freebuff | React/Vite/TS/Tailwind + FastAPI scaffold, health endpoint, shell, run commands | ✅ done |
| — | — | — | Ten UI mockups extracted into `mockup/` + spec realignment | ✅ done |
| 2 | **F2** | Freebuff | `scripts/download_ai4i.py`, `scripts/generate_factory_data.py`, generated CSVs, `data/README.md` | ⏳ next |
| 3 | **F3** | Freebuff | Baseline model, honest metrics, `ml/predict.py`, `ml/MODEL_CARD.md`, CNC-03 demo adapter | ⏳ |
| 4 | **C1** | CoCo CLI | Inspect account, create schemas + tables in `FACTORA`, save SQL to `snowflake/sql/` | ⏳ needs credentials |
| 5 | **C2** | CoCo CLI | Load generated CSVs, verify row counts, sanity-check CNC-03 and `BRG-AX-17` | ⏳ needs credentials |
| 6 | **F4** | Freebuff | API endpoints (`/api/overview`, machines, telemetry, predictions, parts, work orders, OEE) + tests | ⏳ |
| 7 | **F5** | Freebuff | Design system + shell matching `mockup/`, ten empty routes | ⏳ |
| 8 | **F6** | Freebuff | Command Center, Machines Explorer, Machine Detail with real API data | ⏳ |
| 9 | **F7** | Freebuff | `/twin` with R3F: floor, zones, 24 machines, state colours, click → side panel, 2D fallback | ⏳ |
| 10 | **C3** | CoCo CLI | Governed semantic view + validation questions | ⏳ |
| 11 | **C4** | CoCo CLI | Cortex Search over `MAINTENANCE_KNOWLEDGE` | ⏳ |
| 12 | **C5** | CoCo CLI | `FACTORA_MAINTENANCE_AGENT` + test questions | ⏳ |
| 13 | **C6** | CoCo CLI | `create_work_order` custom tool + test on CNC-03 | ⏳ |
| 14 | **F8** | Freebuff | Agent integrated into `/ai-assistant` (no external LLM APIs) | ⏳ |
| 15 | **F9** | Freebuff | Work Orders, Spare Parts, OEE, Planner pages | ⏳ |
| 16 | **F10** | Freebuff | Demo Mode: reset + scenario + `docs/demo-script.md` | ⏳ |
| 17 | **C7** | CoCo CLI | Final Snowflake validation + cost review → `FINAL_SNOWFLAKE_CHECK.md` | ⏳ |
| 18 | **F11** | Freebuff | Final QA, README, submission assets; no new features | ⏳ |

**Checkpoints (pass condition before moving on):** local scaffold → frontend opens and `/api/health` returns
success · data → all CSVs non-empty + CNC-03 degradation present · ML → model trains, metrics reported,
artifact loads · Snowflake tables → exist with matching row counts · API → overview + CNC-03 endpoints return
Snowflake-backed data · UI → pages render API data · Twin → CNC-03 changes state and is clickable · semantic
view → questions return correct results · Search → relevant chunks · Agent → uses structured + unstructured
evidence · Action → one proposed work order created · final demo → reset → scenario → investigation → part →
work order, twice in a row.

---

## 12. Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| `cortex` not found / CoCo unavailable on the account | Verify the hackathon/dedicated CoCo-enabled account; check PATH (`~/.local/bin`); ask Hack2Skill support |
| Credits burning while debugging | XSMALL + auto-suspend 60 s; suspend manually while working on the frontend; one warehouse only |
| Agent cannot access tables | Check role grants + warehouse usage; let CoCo diagnose missing grants |
| Cortex Search returns poor results | Tighten `MAINTENANCE_KNOWLEDGE` chunks and metadata; keep documents short and specific |
| 3D is slow on a laptop | Boxes instead of models, fewer lights/shadows, no large GLB assets |
| Frontend hammering Snowflake | Backend cache, no 1-second polling, local demo animation |
| Model metrics look odd | Do not tune for fake accuracy — inspect imbalance, report recall/F1 and limitations |
| Agent edits too much, late in the build | `git diff`, revert unwanted changes, one smaller prompt at a time |
| Something breaks near the deadline | Revert to the last working commit; the end-to-end demo flow is protected above all |

---

## 13. Open Questions

1. Which Cortex model is available in the hackathon account, and is `SNOWFLAKE.ML.FORECAST` enabled? (The
   transparent scikit-learn baseline is the MVP path either way.)
2. How much 3D earns its keep: pass 1 = boxes + state colours, pass 2 = labels/side panel/legend, pass 3 =
   simple GLB models only if the MVP is already complete.
3. Whether the judge wants the live scenario animation or a deterministic replay — default is deterministic.
4. Which AI4I file location is reachable from the build machine if the automated download is blocked (F2
   documents the manual fallback path).
5. Public repo hygiene: the playbook text and mockups are now in the repo; confirm they are safe to publish
   (no credentials or account identifiers are present).
