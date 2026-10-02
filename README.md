# Factora — Operational Digital Twin for Predictive Maintenance

**Snowflake CoCo CLI Hackathon 2026 — GCC Edition**

Factora unifies machine sensor telemetry, maintenance history, production context, spare parts and
machine knowledge into one operational digital twin. It predicts failures, explains **why** with citations
from the plant's own documents, estimates the production impact, checks whether the fix is physically
possible today, and opens the preventive work order — with every computation and every generated sentence
executed inside Snowflake.

> **Status: M1 (application scaffold) complete.** A React SPA and a FastAPI backend run locally and talk to
> each other; the API exposes health endpoints only and **no product pages exist yet**.
> Live state → [`PROGRESS.md`](./PROGRESS.md) · Spec → [`PROJECT_SPEC.md`](./PROJECT_SPEC.md)

---

## The 60-second version

A plant needs one answer at 06:00: *which machine breaks next, and what do I do about it?*

- **Detect** — CNC-03's spindle vibration drifts away from its own baseline. It goes **CRITICAL** on the Factory Twin.
- **Predict** — spindle bearing degradation, 8–11 days to failure, with probability *and* confidence.
- **Explain** — a Cortex-generated diagnosis grounded in the machine manual and similar closed work orders, **with citations**.
- **Cost it** — unplanned stop ≈ 6.5 h downtime and 42 t of output at risk; planned fix in the next window ≈ 45 min.
- **Act** — the required bearing is in stock, so it creates the preventive work order and writes it back to Snowflake.

## Documentation map

| File | What it is | Audience |
|------|-----------|----------|
| [`PROJECT_SPEC.md`](./PROJECT_SPEC.md) | Source of truth: pitch, pages, architecture, stack, data model, MVP vs. stretch, demo flow | Everyone |
| [`AGENTS.md`](./AGENTS.md) | Ten governing rules for any agent/human contributing | Contributors, AI agents |
| [`PROGRESS.md`](./PROGRESS.md) | Current goal, completed, in progress, next 3, blockers, test + demo status, command ledger | Everyone |
| `.env.example` | Backend environment variables, placeholders only | Whoever runs it |
| `frontend/.env.example` | Optional frontend overrides | Front-end work |

---

## Quick start (verified at M1)

**Prerequisites**

- Node.js **22+** and npm
- Python **3.11+** — on macOS the bundled `python3` is often 3.9, so call `python3.11` explicitly
- Snowflake CLI (`snow`) and the Snowflake CoCo CLI — needed from M2, not for the scaffold

**1. Configure (optional at M1)**

```bash
git clone https://github.com/khushi-infinity/Factora.git
cd Factora
cp .env.example .env      # fill in Snowflake values when they are issued; .env is gitignored
```

The backend boots with **no `.env` and no credentials**: it reports Snowflake as `not configured` rather
than failing. Never commit `.env`, key files or credentials (`AGENTS.md` rule 4).

**2. Backend — FastAPI on :8000**

```bash
cd backend
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/uvicorn app.main:app --reload --port 8000
```

- health: <http://127.0.0.1:8000/api/health> · liveness: `/api/health/live` · OpenAPI docs: <http://127.0.0.1:8000/docs>

**3. Frontend — Vite dev server on :5173**

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173 — proxies /api to 127.0.0.1:8000
```

**4. Checks (what "done" means for this repo)**

```bash
# frontend
cd frontend && npm run typecheck && npm run lint && npm test && npm run build

# backend
cd backend && .venv/bin/ruff check . && .venv/bin/pytest
```

**5. Snowflake foundation** ⏳ arrives at M2

```bash
snow connection test -c factora
snow sql -c factora -f snowflake/01_schemas.sql
snow sql -c factora -f snowflake/02_seed.sql
```

The full ledger — including the M1 rendered-page verification — lives in [`PROGRESS.md`](./PROGRESS.md) → *Command Ledger*.

---

## What exists today (M1)

```
backend/                    FastAPI BFF (:8000)
├── app/main.py             app factory, CORS, OpenAPI
├── app/config.py           typed settings from the repo-root .env; boots with nothing set
├── app/api/health.py       /api/health (deps) + /api/health/live (pure liveness)
├── app/db/snowflake.py     the ONLY module importing the Snowflake connector; TTL-cached probe
├── app/ml/                 reserved for pandas/scikit-learn/joblib work (M4+)
└── tests/                  28 pytest tests: shapes, CORS, credential-leak guards, stack import

frontend/                   React 19 + Vite + TypeScript SPA (:5173)
├── src/App.tsx             shell: backend status, chart toolchain, 3D toolchain, planned routes
├── src/lib/api.ts          typed, time-boxed API client (the only HTTP boundary)
├── src/lib/health.ts       pure helpers for health state (unit-tested)
├── src/components/         BackendStatus · StackCheck (Recharts) · TwinPreview3D (r3f, lazy) ·
│                           PanelBoundary (keeps a failed panel from blanking the shell) · PlannedPages
└── src/lib/health.test.ts  11 Vitest tests

snowflake/                  ⏳ M2: schemas, DDL, seeds, dynamic tables, prompts
tests/e2e/                  ⏳ M6: Playwright walk of the demo flow
```

**M1 deliberately does not implement product pages.** The shell exists to prove the toolchain — including
that Recharts and react-three-fiber render and that the SPA can reach the API — so a WebGL or bundling
regression surfaces now rather than on stage.

---

## Architecture at a glance

```
React SPA (:5173)  ──HTTP /api/*──►  FastAPI BFF (:8000)  ──snowflake-connector-python──►  Snowflake
  Factory Twin · Machine 360 ·         typed payloads, one data-access        RAW → CURATED → ANALYTICS
  Risk Board · Diagnosis · Parts ·     module, TTL caching, graceful          Cortex Search + Cortex COMPLETE
  Work Orders · Impact · 3D view       degradation, never invents data         roles, action log, guardrails
        ▲
        └── CoCo CLI + Snowflake CLI: scaffolding, DDL, seeds, deploys — everything reproducible from repo
```

Boundary rules (`PROJECT_SPEC.md` §3.5): the SPA never talks to Snowflake; only `backend/app/db/` imports the
connector; only `snowflake/` scripts create or alter Snowflake objects; health scores, predictions and costs
are computed in Snowflake, never in a React component.

---

## Guardrails

- **Open source only.** No paid APIs, no external LLM endpoints — the approved list is `PROJECT_SPEC.md` §4.
- **Secrets never in git.** `.env*`, `*.p8`, `*.pem`, `rsa_key*` are ignored; key-pair auth preferred; the API
  has tests asserting credentials cannot appear in a response.
- **Snowflake cost controls are read-only for this project.** Resource monitors, budgets and auto-suspend are
  never modified (`AGENTS.md` rule 7). X-SMALL warehouse, cached reads, no session-per-request.
- **Honest AI.** Every generated claim carries its model, prompt version and citations; simulated data and
  cached output are visibly labelled in the UI.
- **The demo always completes.** A failed panel degrades to a labelled message instead of a blank page.

## License

Project code is intended to be released under the MIT License. All dependencies are free/open-source
(`PROJECT_SPEC.md` §4); Snowflake platform features are used within the hackathon-provided account.
A `LICENSE` file will be added when the application code is feature-complete.
