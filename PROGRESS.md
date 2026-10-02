# PROGRESS.md — Factora Build State

**Phase:** M2 — Snowflake foundation (next)
**Last updated:** 2026-10-02
**Repo:** https://github.com/khushi-infinity/Factora
**Hackathon:** Snowflake CoCo CLI Hackathon 2026 — GCC Edition
**Rule:** update this file at the end of every completed milestone (`AGENTS.md` rule 9). Read it together
with `PROJECT_SPEC.md` before changing code (rule 1).

---

## Current Goal

**M2 — Snowflake foundation.** Make the account match the data model: schemas (`RAW` / `CURATED` /
`ANALYTICS`), least-privilege roles, idempotent DDL, and an idempotent seed that plants the **CNC-03
spindle-bearing degradation signature** in ≥ 90 days of synthetic telemetry, plus maintenance history,
spare-parts inventory and knowledge documents. Exit criteria: scripts re-runnable from a clean account, and
the sanity `SELECT`s in *Command Ledger* §3 returning sane data.

**Blocker to resolve first:** the hackathon Snowflake credentials are not yet in `.env`, so the DDL can be
authored but not yet *verified against the account* — and this repo's rule is that unverified work is not
"complete" (AGENTS rule 3). See *Blockers*.

---

## Completed

### M0 — Bootstrap (docs) ✅
- [x] `PROJECT_SPEC.md`, `AGENTS.md`, `PROGRESS.md`, `README.md`, `.env.example`, `.gitignore`.
- [x] Repo initialised and pushed; docs integrity + secret scan verified.

### M1 — Application scaffold ✅
- [x] **Stack decision (spec revision v0.2).** Local app is now **React 19 + Vite + TypeScript SPA
      (`frontend/`) with a FastAPI backend (`backend/`)**, charts via **Recharts**, 3D via
      **@react-three/fiber + @react-three/drei**, ML via **pandas / scikit-learn / joblib**, Snowflake via
      **snowflake-connector-python** in the backend. `PROJECT_SPEC.md` §3, §4, §6, §11 and the `AGENTS.md`
      repo map + verification protocol were reconciled in the same milestone (AGENTS rule 1).
      *Next.js / SSR is now explicitly listed as not used.*
- [x] **Dependency audit (AGENTS rule 5).** Everything added is free/open-source: React, Vite, TypeScript,
      Tailwind CSS, Recharts, three.js, @react-three/fiber, @react-three/drei, FastAPI, Uvicorn, Pydantic,
      pydantic-settings, snowflake-connector-python, pandas, numpy, scikit-learn, joblib, ESLint, Vitest,
      pytest, httpx, ruff. **No paid API or keyed SaaS was introduced (rule 6).**
- [x] **Backend scaffold.** App factory + CORS; typed settings that boot with *no* `.env` and *no*
      credentials; `app/db/snowflake.py` as the only connector import, with key-pair auth preferred,
      credential scrubbing and a TTL-cached `SELECT 1` probe; `/api/health` and `/api/health/live`;
      OpenAPI docs at `/docs`; `app/ml/` reserved for M4.
- [x] **Frontend scaffold.** Vite + React + Tailwind shell that calls the backend health endpoint through the
      dev proxy; typed API client with timeouts; pure, unit-tested health helpers; Recharts panel; lazy-loaded
      react-three-fiber panel behind an error boundary; planned-route inventory marking the 10 spec pages as
      not built. **No product pages implemented, by instruction.**
- [x] **Local run path documented** in `README.md` and *Command Ledger* §1–§2 (frontend + backend, separate
      processes, ports 5173 / 8000). Detached-process note: in this environment a dev server must be started
      with `( nohup … & )` and re-checked in the same shell invocation, or it is reaped with the command.

**Nothing else is done.** No Snowflake objects, no seed data, no predictions, no product pages.

---

## In Progress

- Nothing active. M1 is closed; the next action is resolving the credential blocker and starting M2.

---

## Next 3 Tasks

1. **M2.1 — Snowflake object scaffolding.** Author `snowflake/01_schemas.sql`: databases/schemas
   (`RAW` / `CURATED` / `ANALYTICS` / `AI`), `FACTORA_APP_ROLE` (read-mostly) and a separate deployment role,
   least-privilege grants. Idempotent (`CREATE … IF NOT EXISTS`), no cost-control changes (AGENTS rule 7).
2. **M2.2 — Idempotent seed dataset.** Author `snowflake/02_seed.sql` + a Snowpark/Python generator producing
   ≥ 90 days of synthetic telemetry with the planted CNC-03 spindle-bearing signature, maintenance history,
   parts inventory and knowledge docs — re-runnable, honest about being synthetic (labelled in the data).
3. **M2.3 — Connection pre-flight.** Wire `.env` into `snow connection test -c factora`, add the M2 sanity
   `SELECT`s to *Command Ledger* §3, and confirm the runtime role is X-SMALL/read-mostly with cost settings
   untouched.

---

## Blockers

- **Snowflake credentials not yet supplied.** `.env` does not exist and no account/user/key has been issued to
  this workspace, so M2's exit criterion (scripts run **twice** cleanly against the real account) cannot be
  met yet. Authoring can proceed; **verification cannot**, and unverified work will not be marked complete.
  → *Action for the user: provide the hackathon account details out-of-band into `.env` (never in git).*
- Watch items (from `PROJECT_SPEC.md` §12/§13, still open):
  - Which Cortex model is available in the account (`mistral-large2` assumed) — affects M4 wording/latency.
  - Whether `SNOWFLAKE.ML.FORECAST` is enabled; the transparent SQL/Snowpark baseline is the MVP path either way.
- **Not** a blocker, recorded for accuracy: `.env.example` documents Snowflake variables that remain unused
  until M2; the backend reports `not_configured` rather than failing, by design.

---

## Test Status

| Area | State | Evidence (exact commands in *Command Ledger*) |
|------|-------|----------------------------------------------|
| Frontend typecheck | ✅ pass | `npm run typecheck` — no output, exit 0 (`tsc --noEmit`, TypeScript 6.0) |
| Frontend lint | ✅ pass | `npm run lint` — `eslint .`, no findings (ESLint 10, flat config) |
| Frontend unit tests | ✅ pass | `npm test` — **11/11 passed** in `src/lib/health.test.ts` (Vitest 5) |
| Frontend production build | ✅ pass | `npm run build` — 1143 modules, `dist/` emitted in 284 ms; three.js split into a lazy `three-vendor` chunk |
| Backend lint | ✅ pass | `.venv/bin/ruff check .` — `All checks passed!` |
| Backend tests | ✅ pass | `.venv/bin/pytest` — **28 passed, 1 warning** in 1.49 s (warning is third-party: Starlette advises `httpx2` for `TestClient`; recorded, not suppressed) |
| Dependency smoke (ML stack) | ✅ pass | `tests/test_dependencies.py` — imports + a real `LinearRegression` fit on a pandas frame, so a broken native build cannot hide until M4 |
| Credential-leak guard | ✅ pass | `tests/test_health.py` — API responses asserted free of password, passphrase, account and user |
| Live API | ✅ pass | `uvicorn` + `curl /api/health` → `{"status":"ok", … "snowflake":{"status":"not_configured"}}` |
| Live rendered shell | ✅ pass | Headless Chrome `--dump-dom` against the dev server: `Backend reachable`, `factora-backend`, `recharts-surface` and `<canvas>` all present, **no** error text; backend logged the browser's `GET /api/health` — proving proxy + fetch + render end to end. Screenshot: `/tmp/factora-shell.png` |
| Snowflake scripts | ⏳ blocked | M2 — needs credentials (see *Blockers*) |
| E2E demo flow (Playwright) | ⏳ not started | M6; the `tests/e2e/` directory arrives with it |

**Honest note:** M1's gate was toolchain and plumbing, not product behaviour. There is no prediction, no
Snowflake query and no product page behind any of the green rows above.

---

## Demo Status

- **Status:** Not demo-able. The shell states plainly that 0 / 10 product pages are built.
- **What works on screen:** local shell loads, reports backend reachability and states Snowflake as
  `not configured`, with chart and 3D toolchain panels rendering.
- **First demo-able point:** end of **M6** (Factory Twin → CNC-03 → prediction → explanation → part check →
  work order clickable end to end).
- **Judge-ready point:** end of **M7** (fallback/cache, `/demo` reset, timings, full dry run ≤ 5 min).
- **Story locked:** `PROJECT_SPEC.md` §9 — 6 beats, ~5 minutes, CNC-03 spindle bearing degradation.

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

### §3 — Snowflake (M2, awaiting credentials)

| When | Command | Purpose |
|------|---------|---------|
| M2 | `snow connection test -c factora` | Verify `.env` credentials + warehouse reachability |
| M2 | `snow sql -c factora -f snowflake/01_schemas.sql` | Schemas, roles, grants (idempotent) |
| M2 | `snow sql -c factora -f snowflake/02_seed.sql` | Load the synthetic twin dataset |
| M2 | `snow sql -c factora -q "SELECT COUNT(*) FROM FACTORA_DEV.RAW.SENSOR_READING;"` | Seed sanity check |
| M3 | `snow sql -c factora -f snowflake/03_curated.sql` | Dynamic Tables / curated features |
| M6 | `npm run test:e2e` | Playwright walk of all six demo beats |
