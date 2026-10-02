# PROGRESS.md — Factora Build State

**Phase:** F2 — datasets + synthetic factory generator (next); plan now follows the build playbook
**Last updated:** 2026-10-02
**Repo:** https://github.com/khushi-infinity/Factora
**Hackathon:** Snowflake CoCo CLI Hackathon 2026 — GCC Edition
**Rule:** update this file at the end of every completed milestone (`AGENTS.md` rule 9). Read it together
with `PROJECT_SPEC.md` before changing code (rule 1).

**Build order:** the playbook's prompt sequence (F0–F11 / C1–C7) as recorded in `PROJECT_SPEC.md` §11.
Control files in play: `PROJECT_SPEC.md`, `AGENTS.md`, `PROGRESS.md`, `README.md`, `.env.example`,
`.gitignore`, plus [`mockup/`](./mockup/README.md) as the visual target and
[`mockup/playbook-source-text.md`](./mockup/playbook-source-text.md) as the archived playbook.

---

## Current Goal

**F2 — Datasets + synthetic factory generator.** Produce the data the whole demo stands on, locally and
deterministically: `scripts/download_ai4i.py` for the UCI AI4I 2020 baseline, `scripts/generate_factory_data.py`
for the synthetic factory context, and `data/README.md` documenting every column and which fields are
synthetic. Exit criteria (AGENTS verification protocol): generator re-runs give identical output for the same
seed, every CSV is non-empty and internally consistent, 24 machines carry twin coordinates, CNC-03 has a
scripted degradation scenario, and `BRG-AX-17` is CNC-03's compatible bearing with limited stock.

---

## Completed

### F0 — Bootstrap (docs) ✅
- [x] `PROJECT_SPEC.md`, `AGENTS.md`, `PROGRESS.md`, `README.md`, `.env.example`, `.gitignore`.
- [x] Repo initialised and pushed; docs integrity + secret scan verified.

### F1 — Application scaffold ✅
- [x] **Stack** (matches the playbook's recommended stack exactly): React 19 + Vite + TypeScript SPA
      (`frontend/`), FastAPI (`backend/`), Tailwind, Recharts, `@react-three/fiber` + `drei`,
      pandas/scikit-learn/joblib, `snowflake-connector-python` in the backend.
- [x] **Dependency audit (AGENTS rule 5):** all free/open-source; **no paid API or keyed SaaS (rule 6)**.
- [x] **Backend:** app factory + CORS; typed settings that boot with no `.env` and no credentials;
      `app/db/snowflake.py` as the only connector import (key-pair auth preferred, secret scrubbing,
      TTL-cached `SELECT 1` probe); `/api/health` + `/api/health/live`; OpenAPI at `/docs`.
- [x] **Frontend:** shell calling the health endpoint through the dev proxy; typed API client with timeouts;
      unit-tested health helpers; Recharts panel; lazy R3F panel behind an error boundary; honest
      "0 / 10 pages built" route inventory.
- [x] **Run path documented** in `README.md` and *Command Ledger* §1–§2 (ports 5173 / 8000).

### Design references ✅
- [x] **Ten UI mockups extracted** from the playbook into [`mockup/`](./mockup/README.md) — lossless
      (original JPEG bytes), matched to their captions by page placement: **10/10 unique images consumed,
      zero unused**; byte counts reconcile to the xref on the page whose caption names that screen.
- [x] `mockup/index.html` contact sheet (registered in the Preview tab), `mockup/README.md` (design language,
      route map, deltas, regeneration), `mockup/playbook-source-text.md` (all 31 pages of playbook text).
- [x] Cross-checked independently: navy left sidebar in all ten (RGB ≈ 20–33, 37–47, 57–66) over 58–82 %
      near-white content; `02-factory-digital-twin` is the most state-coloured (41 red / 164 green / 51 amber).

### Plan realignment ✅ (user decision: the playbook wins)
- [x] **`PROJECT_SPEC.md` v0.3** rewritten to the playbook: routes `/`, `/twin`, `/machines`,
      `/machines/:id`, `/predictive-maintenance`, `/ai-assistant`, `/work-orders`, `/spare-parts`, `/oee`,
      `/planner`; database **`FACTORA`** with schemas **`RAW` / `CORE` / `AI` / `DOCS`** and warehouse
      **`FACTORA_WH`**; the nine-table data model; MUST/SHOULD/STRETCH scope; the **90-second** demo script
      (the 5-minute six-beat version is retired); and the build sequence table with checkpoints.
- [x] **`AGENTS.md`** repo map extended (`ml/`, `data/`, `snowflake/{sql,semantic,agent}`, `docs/`, `scripts/`),
      rule 2 now points at the prompt sequence, and the verification protocol gained dataset and ML rows.
- [x] **Code renamed to match, tests re-run:** `backend/app/config.py` defaults now `FACTORA` / `CORE`
      (asserted in `tests/test_config.py`); `frontend/src/components/PlannedPages.tsx` lists the ten
      playbook routes with MUST/SHOULD scope.
- [x] `.env.example` updated to `FACTORA_WH` / `FACTORA` / `CORE`.

**Nothing else is done.** No datasets, no ML model, no Snowflake objects, no product pages.

---

## In Progress

- Nothing active. F2 is ready to start and needs **no** Snowflake credentials.

---

## Next 3 Tasks

1. **F2.1 — AI4I download script.** `scripts/download_ai4i.py`: fetch the UCI AI4I 2020 CSV into `data/raw/`,
   verify checksum/row count, and print a clear manual-download fallback if automated download is blocked.
2. **F2.2 — Synthetic factory generator.** `scripts/generate_factory_data.py`: deterministic (fixed seeds) CSVs
   for `machines`, `sensor_readings`, `maintenance_history`, `spare_parts`, `work_orders`, `production_runs`,
   `downtime_events`, `maintenance_knowledge`; 24 machines across CNC/press/assembly/packaging/quality with
   `x, y, z` + status; scripted CNC-03 degradation (rising vibration + temperature → bearing-failure risk);
   `BRG-AX-17` compatible with CNC-03 and in limited stock; sizes kept hackathon-small.
3. **F2.3 — Data documentation + validation.** `data/README.md` (every column, which fields are synthetic) and
   a validation pass proving every CSV is non-empty, referentially consistent, and byte-identical on a second
   run with the same seed. Then F3 (ML baseline) starts.

---

## Blockers

- **Snowflake credentials not supplied yet.** No account/user/key exists in this workspace, so C1/C2 (and the
  agent prompts C3–C6) cannot run. The playbook also expects one-time **human** setup in Snowsight —
  `FACTORA_WH` XSMALL with auto-suspend 60 s, the resource monitor, and the CoCo daily credit caps — all of
  which are cost-control settings and therefore **read-only for agents** (`AGENTS.md` rule 7).
  → *Action for the user: run the playbook §5 cost-safety SQL yourself, then place the account details in
  `.env` (never in git).*
- **Not blocking F2/F3:** both are local and credential-free, which is why they come first in the sequence.
- Watch items: which Cortex model the account exposes, and whether `SNOWFLAKE.ML.FORECAST` is enabled (the
  transparent scikit-learn baseline is the MVP path regardless).

---

## Test Status

| Area | State | Evidence (exact commands in *Command Ledger*) |
|------|-------|----------------------------------------------|
| Frontend typecheck | ✅ pass | `npm run typecheck` — no findings (`tsc --noEmit`) |
| Frontend lint | ✅ pass | `npm run lint` — `eslint .`, no findings |
| Frontend unit tests | ✅ pass | `npm test` — **11/11 passed** (Vitest 5) |
| Frontend production build | ✅ pass | `npm run build` — initial chunk 14.9 kB (5.22 kB gz), three.js in a lazy chunk |
| Backend lint | ✅ pass | `.venv/bin/ruff check .` — `All checks passed!` |
| Backend tests | ✅ pass | `.venv/bin/pytest` — **28 passed, 1 warning** (third-party Starlette `httpx2` advisory) |
| Rename re-verification | ✅ pass | After the `FACTORA`/`CORE` + route-list change both gates were re-run: 11/11 frontend tests, build OK, 28/28 backend tests, ruff clean |
| Live API | ✅ pass | `uvicorn` + `curl /api/health` → `{"status":"ok", … "snowflake":{"status":"not_configured"}}` |
| Live rendered shell | ✅ pass | Headless Chrome: `Backend reachable`, `recharts-surface`, one `<canvas>`, no error text |
| Mockup extraction | ✅ pass | 10/10 images consumed, zero unused; byte counts + navy/light/state-colour sampling consistent with captions |
| Dataset generator | ⏳ not started | F2 — must be deterministic and non-empty with the CNC-03 scenario present |
| ML model | ⏳ not started | F3 — honest metrics + `MODEL_CARD.md` required |
| Snowflake objects | ⏳ blocked | C1/C2 — needs credentials (see *Blockers*) |
| End-to-end demo | ⏳ not started | F10/F11 — reset → scenario → investigation → part → work order, twice |

**Honest note:** there is still no data, no model, no Snowflake object and no product page. Everything green
above is scaffold + documentation + design assets.

---

## Demo Status

- **Status:** Not demo-able. Shell renders, 0 / 10 pages built.
- **Design target:** locked. Ten mockups in `mockup/`, ninety-second run-of-show in `PROJECT_SPEC.md` §9.
- **First demo-able point:** after F6/F7 (Command Center, Machine Detail, Factory Twin on real API data).
- **Judge-ready point:** F10 (Demo Mode + `docs/demo-script.md`) and F11 (QA, README, submission assets).
- **Story locked:** CNC-03 rises from healthy → warning → critical; the agent explains why with evidence;
  `BRG-AX-17` checked; work order created; twin moves to scheduled maintenance.

---

## Command Ledger

Exact, copy-pasteable commands (`AGENTS.md` rule 10). Keep in sync with `README.md` Quick Start.

### §1 — Run locally (verified at F1)

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
returns. Start it as `( nohup cmd > /tmp/log 2>&1 < /dev/null & )` and verify the port in the **same** command:
```bash
( cd backend && nohup .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/factora-api.log 2>&1 < /dev/null & )
for i in $(seq 1 15); do [ "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/api/health)" = "200" ] && break; sleep 1; done
```

### §2 — Verify (the current gate)

```bash
cd frontend && npm run typecheck && npm run lint && npm test && npm run build
cd backend  && .venv/bin/ruff check . && .venv/bin/pytest
```

**Live rendered-page check** (servers up first — see §1):
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader \
  --virtual-time-budget=9000 --window-size=1440,1500 \
  --screenshot=/tmp/factora-shell.png --dump-dom http://localhost:5173/ > /tmp/factora-dom.html
grep -o "Backend reachable\|recharts-surface\|<canvas" /tmp/factora-dom.html | sort | uniq -c
```

### §3 — Design references (verified)

```bash
ls -la mockup/     # 10 .jpg + index.html + README.md + playbook-source-text.md  (≈ 816 KB total)
```
Regeneration from the playbook PDF: `mockup/README.md` → *Regenerating these files*.

### §4 — F2 / F3 (next, no credentials needed)

| When | Command | Purpose |
|------|---------|---------|
| F2 | `python3 scripts/download_ai4i.py` | Fetch AI4I 2020 into `data/raw/` |
| F2 | `python3 scripts/generate_factory_data.py` | Generate the synthetic factory CSVs into `data/generated/` |
| F2 | `python3 scripts/generate_factory_data.py --verify` | Re-run determinism + consistency check |
| F3 | `python3 ml/train.py` | Train the baseline, print precision/recall/F1 + confusion matrix |
| F3 | `python3 ml/predict.py --machine CNC-03` | Inference smoke test on the demo machine |

### §5 — Snowflake (C1/C2, awaiting credentials)

| When | Command | Purpose |
|------|---------|---------|
| Setup (**human**, Snowsight) | playbook §5 SQL | `FACTORA_WH` XSMALL + auto-suspend 60 + resource monitor + CoCo credit caps — agents stay read-only on cost controls (AGENTS rule 7) |
| C1 | `snow sql -c factora -f snowflake/sql/01_schemas.sql` | Schemas + tables in `FACTORA` |
| C2 | `snow sql -c factora -f snowflake/sql/02_load.sql` | Load generated CSVs; verify row counts |
| C3–C6 | `snow sql -c factora -f snowflake/…` | Semantic view, Cortex Search, Cortex Agent, work-order tool |
