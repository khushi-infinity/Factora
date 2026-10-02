# PROGRESS.md — Factora Build State

**Phase:** M0 — Bootstrap (documentation + repo foundation)
**Last updated:** 2026-10-02
**Repo:** https://github.com/khushi-infinity/Factora
**Hackathon:** Snowflake CoCo CLI Hackathon 2026 — GCC Edition
**Rule:** update this file at the end of every completed milestone (`AGENTS.md` rule 9). Read it together
with `PROJECT_SPEC.md` before changing code (rule 1).

---

## Current Goal

Stand up the project foundation for **M0**: the six root documents (spec, agent rules, progress, readme,
env template, gitignore) must be complete, mutually consistent, and free of secrets — with no application
code written yet. Immediately after M0: **M1 — Snowflake foundation**, where the DDL and seed scripts in
`snowflake/` become re-runnable from a clean account.

---

## Completed

### M0 — Bootstrap (docs) ✅
- [x] `PROJECT_SPEC.md` — pitch (with pitch order), page list, architecture, tech stack, Snowflake vs.
      local-app responsibilities, data model, MVP vs. stretch, core demo flow, guardrails, milestones, risks.
- [x] `AGENTS.md` — the ten governing rules, verification protocol, repo map, working agreement.
- [x] `PROGRESS.md` — this file, with the required sections and a command ledger.
- [x] `README.md` — overview, quick start, structure, exact commands.
- [x] `.env.example` — every env var as a placeholder, no real values.
- [x] `.gitignore` — secrets, key material, build artefacts, caches, OS/editor noise.
- [x] Git repository initialised; initial commit pushed to GitHub.
- [x] Verification run: required sections present + secret scan clean (see *Test Status*).

**Nothing else is done.** No Snowflake objects, no seed data, no app code, no tests.

---

## In Progress

- Nothing yet. Next action is planning **M1** (see *Next 3 Tasks*).
- M1 open question being resolved first: which Cortex model is available in the hackathon account, and
  whether `SNOWFLAKE.ML.FORECAST` is enabled (`PROJECT_SPEC.md` §13).

---

## Next 3 Tasks

1. **M1.1 — Snowflake object scaffolding.** Author `snowflake/01_schemas.sql` (RAW / CURATED / ANALYTICS),
   the deployment role and least-privilege grants, so `snow sql` can create everything from a clean account.
2. **M1.2 — Idempotent seed dataset.** Author `snowflake/02_seed.sql` + Snowpark generator producing
   ≥ 90 days of synthetic telemetry for Line 1/2 machines, with the planted `CNC-03` spindle-bearing
   degradation signature, maintenance history, parts inventory and knowledge docs.
3. **M1.3 — Connection pre-flight.** Wire `.env` (from `.env.example`) into a `snow` connection test and
   record the exact commands in the *Command Ledger*; confirm X-SMALL warehouse only, no cost-setting changes.

---

## Blockers

- **None blocking M0.** M0 was fully completable locally.
- Watch items (not blockers yet, tracked from `PROJECT_SPEC.md` §12):
  - Cortex model availability + quota in the hackathon account (affects M3 wording and demo latency).
  - Confirmation that `SNOWFLAKE.ML.FORECAST` is enabled; fallback is the transparent SQL/Snowpark
    statistical baseline, which is already the MVP design.
  - Snowflake account credentials are supplied out-of-band by the user and go **only** into `.env`
    (gitignored). No credential belongs in this file.

---

## Test Status

| Area | State | Evidence |
|------|-------|----------|
| Docs integrity (M0 gate) | ✅ pass | 6/6 required files, 9/9 required `PROJECT_SPEC.md` sections, 7/7 required `PROGRESS.md` sections, 10/10 `AGENTS.md` rules — commands in *Command Ledger* §1 |
| Secret hygiene | ✅ pass | Scan returned exactly one hit: line 129 of this file, i.e. the scan's own regex text in the ledger. No key material or credential values exist in any file; `.env.example` holds placeholders only |
| App typecheck / lint | ⏳ n/a | No application code exists yet (arrives M5); `npm run typecheck`/`lint` are not yet runnable |
| Unit tests (Vitest) | ⏳ not started | Planned for scoring + impact helpers (M2/M4) |
| Snowflake scripts | ⏳ not started | M1; each script must run twice cleanly (idempotency) before M1 closes |
| E2E demo flow (Playwright) | ⏳ not started | M5/M6; must cover the six demo beats |
| Dry run under 5 min | ⏳ not started | M6 |

**Honest note:** at M0 there is no build or test to run in the application sense — the gate was a
documentation integrity check, and that is what the evidence above records. No milestone may be marked
complete on the strength of "looks right" (`AGENTS.md` rule 3).

---

## Demo Status

- **Status:** Not demo-able yet. No runnable app, no data, no predictions.
- **First demo-able point:** end of **M5** (Factory Twin → CNC-03 → prediction → explanation → part check →
  work order clickable end to end).
- **Judge-ready point:** end of **M6** (fallback/cache, `/demo` reset, timings, full dry run ≤ 5 min).
- **Story locked:** `PROJECT_SPEC.md` §9 — 6 beats, ~5 minutes, CNC-03 spindle bearing degradation,
  with a visible fallback path so the run never stalls.

---

## Command Ledger

Exact, copy-pasteable commands (`AGENTS.md` rule 10). Keep in sync with `README.md` Quick Start.

### §1 — Runnable today (M0)

**Required files exist**
```bash
for f in PROJECT_SPEC.md PROGRESS.md AGENTS.md README.md .env.example .gitignore; do
  [ -f "$f" ] && echo "OK   $f" || echo "MISS $f"; done
```
Expected: six `OK` lines, zero `MISS`.

**Required PROJECT_SPEC.md sections present**
```bash
for s in "Product Pitch" "Page List" "Architecture" "Tech Stack" "Snowflake Responsibilities" \
         "Local App Responsibilities" "Data Model" "MVP vs Stretch" "Core Demo Flow"; do
  grep -q "^## .*$s" PROJECT_SPEC.md && echo "OK   $s" || echo "MISS $s"; done
```
Expected: nine `OK` lines.

**Required PROGRESS.md sections present**
```bash
for s in "Current Goal" "Completed" "In Progress" "Next 3 Tasks" "Blockers" "Test Status" "Demo Status"; do
  grep -q "^## $s" PROGRESS.md && echo "OK   $s" || echo "MISS $s"; done
```
Expected: seven `OK` lines.

**Secret scan (must print nothing)**
```bash
grep -rInE "BEGIN [A-Z ]*PRIVATE KEY|aws_secret|sk-[A-Za-z0-9]{16,}|password[[:space:]]*=[[:space:]]*[\"'][^\"']{6,}" \
  --exclude-dir=.git --exclude-dir=node_modules . || echo "clean"
```
Expected: `clean`. **Known self-match:** the one line in this ledger that *documents* the pattern matches itself
(currently `PROGRESS.md`); that is expected and is not a secret. Anything else — especially a match in
`.env.example` with a real value, or any `*_KEY` in source — fails the gate.

**Confirm nothing sensitive is tracked**
```bash
git ls-files | grep -E "\.env$|\.p8$|\.pem$|rsa_key|credentials" && echo "LEAK — remove" || echo "clean"
```
Expected: `clean`.

### §2 — Planned, not yet runnable (M1+)

| When | Command | Purpose |
|------|---------|---------|
| M1 | `snow connection test -c factora` | Verify `.env` credentials + warehouse reachability |
| M1 | `snow sql -c factora -f snowflake/01_schemas.sql` | Create databases/schemas/roles (idempotent) |
| M1 | `snow sql -c factora -f snowflake/02_seed.sql` | Load synthetic twin dataset |
| M1 | `snow sql -c factora -q "SELECT COUNT(*) FROM FACTORA_DEV.RAW.SENSOR_READING;"` | Seed sanity check |
| M2 | `snow sql -c factora -f snowflake/03_curated.sql` | Dynamic Tables / features |
| M5 | `npm ci && npm run dev` | Run the app locally |
| M5 | `npm run typecheck && npm run lint && npm test` | App gate |
| M6 | `npm run test:e2e` | Playwright walk of all six demo beats |
