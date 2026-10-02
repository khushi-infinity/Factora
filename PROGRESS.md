# PROGRESS.md — Factora Build State

**Phase:** M1 complete — next milestone pending the route/naming alignment decision (see *Blockers*)
**Last updated:** 2026-10-02
**Repo:** https://github.com/khushi-infinity/Factora
**Hackathon:** Snowflake CoCo CLI Hackathon 2026 — GCC Edition
**Rule:** update this file at the end of every completed milestone (`AGENTS.md` rule 9). Read it together
with `PROJECT_SPEC.md` before changing code (rule 1).

---

## Current Goal

Two things, in order:

1. **Lock the UI/UX target and reconcile the plan.** The design target is now in the repo: ten screen
   mockups extracted at original resolution into [`mockup/`](./mockup/README.md), with the playbook's
   design language and the deltas against this spec recorded there. The playbook (the user's own
   *Beginner Build Playbook*, which also supplied the prompts used so far) specifies routes and Snowflake
   naming that differ from `PROJECT_SPEC.md` §2/§7 — **decide which set wins before writing routes or DDL**,
   because those two choices are expensive to undo.
2. **Then follow the playbook's Master Build Sequence one prompt at a time** (its own rule: *"Do not give
   Prompt 2 until Prompt 1 is working"*). Next in that sequence: **F2** datasets + synthetic factory
   generator (with the scripted CNC-03 degradation and `BRG-AX-17`), then **F3** the AI4I baseline model,
   then **C1/C2** the Snowflake data model and load.

---

## Completed

### M0 — Bootstrap (docs) ✅
- [x] `PROJECT_SPEC.md`, `AGENTS.md`, `PROGRESS.md`, `README.md`, `.env.example`, `.gitignore`.
- [x] Repo initialised and pushed; docs integrity + secret scan verified.

### M1 — Application scaffold ✅
- [x] **Stack decision (spec revision v0.2).** Local app is **React 19 + Vite + TypeScript SPA
      (`frontend/`) with a FastAPI backend (`backend/`)**, charts via **Recharts**, 3D via
      **@react-three/fiber + @react-three/drei**, ML via **pandas / scikit-learn / joblib**, Snowflake via
      **snowflake-connector-python** in the backend. This **matches the playbook's recommended stack**
      (§Recommended tech stack) — no conflict there.
- [x] **Dependency audit (AGENTS rule 5).** All free/open-source; **no paid API or keyed SaaS (rule 6)**.
- [x] **Backend scaffold.** App factory + CORS; typed settings that boot with no `.env` and no credentials;
      `app/db/snowflake.py` as the only connector import (key-pair auth preferred, secret scrubbing,
      TTL-cached `SELECT 1` probe); `/api/health` + `/api/health/live`; OpenAPI at `/docs`; `app/ml/` reserved.
- [x] **Frontend scaffold.** Vite + React + Tailwind shell calling the health endpoint through the dev proxy;
      typed API client with timeouts; unit-tested health helpers; Recharts panel; lazy react-three-fiber
      panel behind an error boundary; planned-route inventory. **No product pages implemented, by instruction.**
- [x] **Local run path documented** in `README.md` and *Command Ledger* §1–§2 (ports 5173 / 8000).

### Design references — extracted ✅
- [x] **Ten UI mockups extracted from the build playbook** into [`mockup/`](./mockup/README.md):
      Command Center, Factory Digital Twin, Machines Explorer, Machine Detail, Predictive Maintenance,
      AI Maintenance Agent, Work Orders, Spare Parts, OEE & Production Analytics, Maintenance Planner & Reports.
- [x] Extracted **losslessly** (original embedded JPEG bytes, no re-encode) and matched to their captions by
      page placement: **10 of 10 unique embedded images consumed, zero unused**. Byte counts reconcile to the
      xref drawn on the page whose caption names that screen.
- [x] `mockup/index.html` — browsable contact sheet (registered in the Preview tab) with each screen's route
      and required elements; `mockup/README.md` — design language, route map, deltas, regeneration steps;
      `mockup/playbook-source-text.md` — the full 31-page playbook text for future agents.
- [x] Independently cross-checked: every image carries the playbook's dark-navy left sidebar
      (sampled RGB ≈ 20–33, 37–47, 57–66) over 58–82 % near-white content, and `02-factory-digital-twin` is
      the most state-coloured image (41 red / 164 green / 51 amber samples) — consistent with the described
      centrepiece.

**Nothing else is done.** No Snowflake objects, no seed data, no ML model, no product pages.

---

## In Progress

- Nothing active. Waiting on the route/naming decision before starting the next milestone.

---

## Next 3 Tasks

Ordered by the playbook's sequence (F-prompt order), pending the alignment decision:

1. **F2 — Datasets + synthetic factory generator.** `scripts/download_ai4i.py` (UCI AI4I 2020, with a
   documented manual fallback) and `scripts/generate_factory_data.py` producing deterministic CSVs for
   machines, sensor readings, maintenance history, spare parts, work orders, production runs, downtime events
   and maintenance knowledge — 24 machines with twin coordinates, a scripted CNC-03 degradation scenario, and
   `BRG-AX-17` as CNC-03's compatible bearing with limited stock. Plus `data/README.md` documenting every
   column and which fields are synthetic.
2. **F3 — Baseline failure model.** scikit-learn only, honest metrics (precision/recall/F1 + confusion
   matrix), joblib artifact, `ml/predict.py`, and `ml/MODEL_CARD.md` with limitations. The CNC-03 demo path
   must be a clearly documented demo adapter, **without corrupting the reported evaluation**.
3. **C1/C2 — Snowflake data model + load.** Schemas, tables, ordered SQL saved under `snowflake/`, then load
   the generated CSVs and verify row counts + sanity checks for CNC-03 and `BRG-AX-17`. *Blocked on
   credentials and on the naming decision.*

---

## Blockers

- **Decision needed — which route/naming set wins?** The playbook's mockups and prompts assume ten specific
  routes (`/`, `/twin`, `/machines`, `/machines/:id`, `/predictive-maintenance`, `/ai-assistant`,
  `/work-orders`, `/spare-parts`, `/oee`, `/planner`) and Snowflake names (`FACTORA` + `RAW`/`CORE`/`AI`/`DOCS`,
  warehouse `FACTORA_WH`). `PROJECT_SPEC.md` currently says otherwise (§2, §7). Recorded as Q7 in
  `PROJECT_SPEC.md` §13 and flagged in `mockup/README.md` → *Deliberate deltas*. **Not resolvable by an agent —
  it changes what every future prompt builds against.**
- **Snowflake credentials not yet supplied.** No account/user/key in this workspace, so no DDL can be
  authored-and-verified and nothing can be loaded. The playbook also expects one-time **human** setup in
  Snowsight (warehouse `FACTORA_WH` XSMALL, auto-suspend 60 s, resource monitor, CoCo credit caps) — those are
  cost-control settings, which `AGENTS.md` rule 7 keeps read-only for agents. → *Action for the user: run the
  playbook's §5 cost-safety SQL yourself, then put account details in `.env` (never in git).*
- Watch items (from `PROJECT_SPEC.md` §12/§13): Cortex model availability; whether
  `SNOWFLAKE.ML.FORECAST` is enabled (the transparent baseline is the MVP path either way).

---

## Test Status

| Area | State | Evidence (exact commands in *Command Ledger*) |
|------|-------|----------------------------------------------|
| Frontend typecheck | ✅ pass | `npm run typecheck` — no findings (`tsc --noEmit`, TypeScript 6.0) |
| Frontend lint | ✅ pass | `npm run lint` — `eslint .`, no findings (ESLint 10, flat config) |
| Frontend unit tests | ✅ pass | `npm test` — **11/11 passed** (Vitest 5) |
| Frontend production build | ✅ pass | `npm run build` — 1143 modules; initial chunk 14.9 kB (5.19 kB gz), three.js in a lazy chunk |
| Backend lint | ✅ pass | `.venv/bin/ruff check .` — `All checks passed!` |
| Backend tests | ✅ pass | `.venv/bin/pytest` — **28 passed, 1 warning** (third-party Starlette `httpx2` advisory; recorded, not suppressed) |
| Dependency smoke (ML stack) | ✅ pass | `tests/test_dependencies.py` — imports + a real `LinearRegression` fit |
| Credential-leak guard | ✅ pass | `tests/test_health.py` — responses asserted free of password, passphrase, account and user |
| Live API | ✅ pass | `uvicorn` + `curl /api/health` → `{"status":"ok", … "snowflake":{"status":"not_configured"}}` |
| Live rendered shell | ✅ pass | Headless Chrome against the dev server: `Backend reachable`, `recharts-surface`, one `<canvas>`, no error text; backend logged the browser's `GET /api/health` |
| Mockup extraction | ✅ pass | 10/10 unique images consumed, zero unused; byte counts match page placements; navy-sidebar + light-content + state-colour sampling consistent with each caption; regeneration steps in `mockup/README.md` |
| Snowflake scripts | ⏳ blocked | Needs credentials + naming decision (see *Blockers*) |
| ML model | ⏳ not started | F3 |
| E2E demo flow | ⏳ not started | Later playbook (F10/F11); Playwright walk of the demo beats |

**Honest note:** no prediction, no Snowflake query, no ML model and no product page exists yet. The mockups
are design references, not implemented UI.

---

## Demo Status

- **Status:** Not demo-able. The shell states plainly that 0 / 10 product pages are built.
- **What works on screen:** local shell loads, reports backend reachability + Snowflake `not configured`,
  and renders the chart and 3D toolchain panels.
- **Design target:** locked in `mockup/` — ten screens, playbook's 90-second run-of-show
  (Command Center → Twin + scenario → Machine Detail → AI investigation → part check + work order).
  `PROJECT_SPEC.md` §9 still describes a 5-minute six-beat version; the timing gets settled with the same
  alignment decision.
- **First demo-able point:** after the playbook sequence reaches F6/F7 (Command Center, Machine Detail, Twin)
  with real API data; **judge-ready** at F10 (Demo Mode + script) and F11 (QA, README, submission assets).

---

## Command Ledger

Exact, copy-pasteable commands (`AGENTS.md` rule 10). Keep in sync with `README.md` Quick Start.

### §1 — Run locally (verified at M1)

```bash
# Backend — FastAPI on :8000 (Python 3.11+; macOS `python3` is often 3.9, so be explicit)
cd backend
python3.11 -m venv .venv                                  # first time only
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/uvicorn app.main:app --reload --port 8000

# Frontend — Vite on :5173 (proxies /api → 127.0.0.1:8000)
cd frontend
npm install                                               # first time only
npm run dev                                               # http://localhost:5173
```

**Detached-start note (this environment):** a server started with `cmd &` is reaped when the shell command
returns. Start it as `( nohup cmd > /tmp/log 2>&1 < /dev/null & )` and verify the port in the **same**
command:
```bash
( cd backend && nohup .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/factora-api.log 2>&1 < /dev/null & )
for i in $(seq 1 15); do [ "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/api/health)" = "200" ] && break; sleep 1; done
```

### §2 — Verify (the M1 gate)

```bash
# Frontend
cd frontend
npm run typecheck && npm run lint && npm test && npm run build

# Backend
cd backend
.venv/bin/ruff check . && .venv/bin/pytest
```

**Live rendered-page check** (servers must be up first — see §1):
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader \
  --virtual-time-budget=9000 --window-size=1440,1500 \
  --screenshot=/tmp/factora-shell.png --dump-dom http://localhost:5173/ > /tmp/factora-dom.html
grep -o "Backend reachable\|recharts-surface\|<canvas" /tmp/factora-dom.html | sort | uniq -c
```
Expected: `Backend reachable`, `recharts-surface` and one `<canvas>`, with no error text.

### §3 — Design references (verified, no server needed)

```bash
# Contact sheet of all ten mockups — already registered in the Preview tab as mockup/index.html.
ls -la mockup/                      # expect 10 .jpg files + index.html + README.md + playbook-source-text.md
du -sh mockup/                      # expect ≈ 780 KB
```
Regeneration from the playbook PDF: see `mockup/README.md` → *Regenerating these files* (PyMuPDF, original
JPEG bytes, verified 10/10 with zero unused).

### §4 — Snowflake (next, awaiting credentials + naming decision)

| When | Command | Purpose |
|------|---------|---------|
| Setup (human, Snowsight) | playbook §5 SQL | `FACTORA_WH` XSMALL + auto-suspend 60 + resource monitor + CoCo credit caps — **user-run only**; agents stay read-only on cost controls (AGENTS rule 7) |
| C1 | `snow sql -c factora -f snowflake/sql/01_schemas.sql` | Schemas + tables |
| C2 | `snow sql -c factora -f snowflake/sql/02_load.sql` | Load generated CSVs, verify row counts |
| C3–C6 | `snow sql -c factora -f snowflake/…` | Semantic view, Cortex Search, Cortex Agent, work-order tool |
