# Factora — Operational Digital Twin for Predictive Maintenance

**Snowflake CoCo CLI Hackathon 2026 — GCC Edition**

Factora is an AI-powered operational digital twin that unifies factory sensor, maintenance, production and
inventory data to predict equipment failures, explain the evidence, quantify production impact, and create
preventive maintenance work orders before downtime happens.

> **Status: F1 (scaffold) complete, plan realigned to the build playbook.** A React SPA and a FastAPI backend
> run locally and talk to each other; the ten UI mockups are extracted and locked as the design target; the
> API exposes health endpoints only and **no product pages exist yet**.
> Live state → [`PROGRESS.md`](./PROGRESS.md) · Plan of record → [`PROJECT_SPEC.md`](./PROJECT_SPEC.md) ·
> Design target → [`mockup/`](./mockup/README.md)

---

## Document map

| Path | What it is |
|------|-----------|
| [`PROJECT_SPEC.md`](./PROJECT_SPEC.md) | Plan of record: pitch, ten pages, architecture, stack, data model, scope, 90-second demo, build sequence |
| [`AGENTS.md`](./AGENTS.md) | Ten governing rules for any agent/human contributing |
| [`PROGRESS.md`](./PROGRESS.md) | Current goal, completed, in progress, next 3, blockers, test status, demo status, command ledger |
| [`mockup/`](./mockup/README.md) | The ten screen mockups + `index.html` contact sheet — the visual target |
| [`mockup/playbook-source-text.md`](./mockup/playbook-source-text.md) | Archived build playbook (31 pages): prompt sequence, data plan, cost-safety SQL, checkpoints |
| `.env.example` | Backend environment variables (placeholders only) · `frontend/.env.example` for overrides |

## The 90-second story

CNC-03's vibration and temperature drift outside baseline → the twin moves healthy → warning → **critical** →
the model predicts bearing failure and remaining useful life → the Cortex Agent explains *why*, with evidence
from telemetry, maintenance history and machine knowledge → `BRG-AX-17` stock is checked → the least
disruptive window is proposed → **Create Work Order** → Snowflake records it and the twin moves to scheduled
maintenance.

## Quick start (verified)

**Prerequisites:** Node.js 22+, Python **3.11+** (macOS `python3` is often 3.9 — call `python3.11`), npm.
Snowflake CLI (`snow`) and CoCo CLI (`cortex`) are needed from the C1/C2 prompts, not for local UI work.

```bash
git clone https://github.com/khushi-infinity/Factora.git
cd Factora
cp .env.example .env          # fill Snowflake values when issued; .env is gitignored
```

**Backend — FastAPI on :8000**

```bash
cd backend
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/uvicorn app.main:app --reload --port 8000
```
health → <http://127.0.0.1:8000/api/health> · docs → <http://127.0.0.1:8000/docs>

**Frontend — Vite on :5173**

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173, proxies /api → 127.0.0.1:8000
```

**Checks**

```bash
cd frontend && npm run typecheck && npm run lint && npm test && npm run build
cd backend  && .venv/bin/ruff check . && .venv/bin/pytest
```

The app boots with **no `.env` and no credentials**: it reports Snowflake as `not configured` rather than
failing. Never commit `.env`, key files or credentials (`AGENTS.md` rule 4).

## What exists today

```
frontend/   React 19 + Vite + TS + Tailwind — shell only: backend status, chart toolchain (Recharts),
            3D toolchain (@react-three/fiber, lazy + error-boundaried), route inventory 0/10
backend/    FastAPI: app factory, CORS, typed settings, /api/health + /api/health/live,
            app/db/snowflake.py (the only connector import, TTL-cached probe), 28 pytest tests
mockup/     the ten screen mockups + contact sheet + playbook text  ← design target
           ⏳ still to come (playbook sequence): ml/ · data/ · snowflake/sql|semantic|agent · docs/ · scripts/
```

**The ten pages, with their mockups:**

| Route | Page | Priority |
|-------|------|----------|
| `/` | Command Center | MUST |
| `/twin` | Factory Digital Twin | MUST |
| `/machines` | Machines Explorer | SHOULD |
| `/machines/:id` | Machine Detail | MUST |
| `/predictive-maintenance` | Predictive Maintenance | MUST |
| `/ai-assistant` | AI Maintenance Agent | MUST |
| `/work-orders` | Work Orders | MUST |
| `/spare-parts` | Spare Parts | SHOULD |
| `/oee` | OEE & Production Analytics | SHOULD |
| `/planner` | Maintenance Planner & Reports | SHOULD |

## Architecture at a glance

```
React SPA (:5173)  ──/api/*──►  FastAPI BFF (:8000)  ──snowflake-connector-python──►  FACTORA_WH (XSMALL)
  Command Center · Factory Twin ·   typed payloads, one data-access     RAW → CORE   (app reads CORE)
  Machine Detail · Agent ·          module, snapshot caching,           AI  → Semantic view, Cortex Search,
  Work Orders · Parts · OEE ·       graceful degradation                DOCS → knowledge corpus
  Planner · 3D twin (R3F)                                                 └─► FACTORA_MAINTENANCE_AGENT
                                                                              + create_work_order tool
        ▲
        └── CoCo CLI + Snowflake CLI: schemas, tables, semantic view, Search, Agent, tool — all from repo
```

Boundary rules (`PROJECT_SPEC.md` §3.5): the SPA never talks to Snowflake; only `backend/app/db/` imports the
connector; only `snowflake/` scripts create or alter Snowflake objects; scores, predictions and costs are
computed in Snowflake or in the documented local ML path — never inside a React component.

## Data, honesty and cost

- **Sources:** the baseline model uses the **UCI AI4I 2020** predictive-maintenance dataset; everything else
  (machines, telemetry, parts, work orders, knowledge chunks, the CNC-03 scenario) is **synthetic and
  labelled as such** — `data/README.md` will document every column and which fields are synthetic.
- **Cost discipline:** one XSMALL warehouse with 60-second auto-suspend, snapshot reads (no per-second
  polling), locally animated demo scenario, no continuous services.
- **Cost controls are human-run:** the playbook's warehouse/resource-monitor/CoCo-credit SQL is executed by
  you in Snowsight; agents are read-only on those settings (`AGENTS.md` rule 7).
- **Honest AI:** the agent separates observed data, prediction, evidence and recommendation, cites its
  sources, and never claims certainty; `MODEL_CARD.md` will record the model's real limitations.

## Build sequence

The playbook's prompt order is the build order (`PROJECT_SPEC.md` §11): **F0** control files ✅ · **F1** scaffold ✅ ·
**F2** datasets + generator ⏳ next · **F3** ML baseline · **C1/C2** Snowflake tables + load ·
**F4** API · **F5** design system · **F6** Command Center/Machines/Machine Detail · **F7** digital twin ·
**C3–C6** semantic view, Search, Agent, work-order tool · **F8** agent in the UI · **F9** remaining pages ·
**F10** demo mode · **C7** cost review · **F11** QA + submission. One prompt at a time; each has a checkpoint.

## License

Project code is intended to be released under the MIT License. All dependencies are free/open-source
(`PROJECT_SPEC.md` §4); Snowflake platform features are used within the hackathon-provided account.
A `LICENSE` file will be added when the application code is feature-complete.
