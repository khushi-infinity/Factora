# PROGRESS.md — Factora Build State

**Phase:** F2 — datasets + synthetic factory generator ✅ (F3 next); plan follows the build playbook
**Last updated:** 2026-10-03
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

**F3 — Baseline failure model.** Train the scikit-learn baseline on the AI4I 2020 dataset (`ml/train.py`),
expose deterministic local inference (`ml/predict.py`), document honest metrics and limitations in
`ml/MODEL_CARD.md`, and keep the CNC-03 demo adapter separate from the real evaluation. Exit criteria
(AGENTS verification protocol): `ml/train.py` reproduces the metrics quoted in `MODEL_CARD.md`, the inference
smoke test passes, and the demo adapter is documented and kept separate from the real evaluation.

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

### F2 — Datasets + synthetic factory generator ✅
- [x] **`scripts/download_ai4i.py`:** fetches the UCI AI4I 2020 CSV from the official endpoint,
      sha256-verified (`dc6630cd…c8a8e`, BOM-tolerant read), prints manual-download instructions if blocked,
      `--check` re-validates offline. `data/raw/ai4i2020.csv` committed (10,000 × 14, CC BY 4.0, cited in
      `data/README.md`).
- [x] **`scripts/generate_factory_data.py` (stdlib-only):** deterministic generator — master seed `20261003`,
      one SHA-256-derived RNG per domain, fixed `AS_OF = 2026-10-03T00:00:00` (never reads the wall clock) →
      byte-identical re-runs forever.
- [x] **Eight CSVs in `data/generated/` (+ `manifest.json`), all inside the playbook's size targets:**
      machines 24 · sensor_readings 11,136 (16 days; CNC-03 at 10-minute cadence) · maintenance_history 140 ·
      spare_parts 32 · work_orders 97 · production_runs 336 · downtime_events 54 · maintenance_knowledge 49.
- [x] **24 machines** across CNC/press/assembly/packaging/quality lines, each with twin `x, y, z` + status
      (20 HEALTHY, WARNING = CNC-06, CRITICAL = CNC-03, MAINTENANCE = PRS-03, OFFLINE = PKG-04).
- [x] **CNC-03 scripted degradation:** vibration 2.39 → 5.0 mm/s and bearing temp 62.0 → 70.7 °C
      (first-24h → last-24h means) over a 5-day ramp; CRITICAL at snapshot; two prior `BRG-AX-17` bearing
      repairs in history (Dec 2025, May 2026) as the agent's evidence base.
- [x] **`BRG-AX-17`:** CNC-compatible axial spindle bearing, **stock 2 ≤ reorder point 3 (limited)**, cited by
      knowledge chunks and by the PROPOSED demo work order `WO-0096` (`FACTORA_AGENT`, window Sun
      2026-10-04 07:00 — lowest-impact slot).
- [x] **Built-in validation on every run:** row-count windows, machine/part referential integrity +
      part↔machine compatibility, work-order ↔ history 1:1 pairing, downtime ↔ production-runs reconciliation,
      and the CNC-03 scenario asserts.
- [x] **`data/README.md`:** every column of every file, which fields are synthetic, AI4I licence citation,
      and the scripted-scenario table.

**Nothing else is done beyond F2.** No ML model, no Snowflake objects, no product pages.

---

## In Progress

- Nothing active. F3 is ready to start and needs **no** Snowflake credentials.

---

## Next 3 Tasks

1. **F3.1 — Training script.** `ml/train.py`: load `data/raw/ai4i2020.csv`, train the scikit-learn baseline
   (machine failure vs not), report precision/recall/F1 + confusion matrix honestly (class imbalance!), save
   artefacts to `ml/artifacts/` (gitignored).
2. **F3.2 — Inference + demo adapter.** `ml/predict.py` (Command Ledger smoke test: `--machine CNC-03`) scoring
   generated telemetry; the CNC-03 demo adapter documented and kept separate from the real evaluation.
3. **F3.3 — `ml/MODEL_CARD.md`.** Metrics, limitations, imbalance treatment — must match what `train.py`
   prints. Then C1/C2 (Snowflake tables + load) as soon as credentials arrive.

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
| Dataset generator (F2) | ✅ pass | `python3.11 scripts/generate_factory_data.py --verify` → `DETERMINISM OK` (byte-identical re-run) + `CONSISTENCY OK` (all tables non-empty, cross-references + CNC-03 scenario verified); rows 24 / 11,136 / 140 / 32 / 97 / 336 / 54 / 49 |
| AI4I download (F2) | ✅ pass | `python3.11 scripts/download_ai4i.py` + `--check` → `OK … 10,000 rows x 14 columns`, sha256 `dc6630cd…c8a8e` verified against the official UCI endpoint |
| Scripts lint | ✅ pass | `backend/.venv/bin/ruff check scripts/` → `All checks passed!` (root `pyproject.toml`: 120-col budget for scripts/, DTZ + ISC004 ignored with documented reasons) |
| ML model | ⏳ not started | F3 — honest metrics + `MODEL_CARD.md` required |
| Snowflake objects | ⏳ blocked | C1/C2 — needs credentials (see *Blockers*) |
| End-to-end demo | ⏳ not started | F10/F11 — reset → scenario → investigation → part → work order, twice |

**Honest note:** there is still no ML model, no Snowflake object and no product page. Data now exists (F2);
everything else green above is scaffold + documentation + design assets.

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
| F2 ✅ | `python3.11 scripts/download_ai4i.py` | Fetch AI4I 2020 into `data/raw/` (verified; `--check` re-validates offline) |
| F2 ✅ | `python3.11 scripts/generate_factory_data.py` | Generate the synthetic factory CSVs into `data/generated/` |
| F2 ✅ | `python3.11 scripts/generate_factory_data.py --verify` | Re-run determinism + consistency check (verified byte-identical) |
| F3 | `python3.11 ml/train.py` | Train the baseline, print precision/recall/F1 + confusion matrix |
| F3 | `python3.11 ml/predict.py --machine CNC-03` | Inference smoke test on the demo machine |

### §5 — Snowflake (C1/C2, awaiting credentials)

| When | Command | Purpose |
|------|---------|---------|
| Setup (**human**, Snowsight) | playbook §5 SQL | `FACTORA_WH` XSMALL + auto-suspend 60 + resource monitor + CoCo credit caps — agents stay read-only on cost controls (AGENTS rule 7) |
| C1 | `snow sql -c factora -f snowflake/sql/01_schemas.sql` | Schemas + tables in `FACTORA` |
| C2 | `snow sql -c factora -f snowflake/sql/02_load.sql` | Load generated CSVs; verify row counts |
| C3–C6 | `snow sql -c factora -f snowflake/…` | Semantic view, Cortex Search, Cortex Agent, work-order tool |
