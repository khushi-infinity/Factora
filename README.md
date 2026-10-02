# Factora — Operational Digital Twin for Predictive Maintenance

**Snowflake CoCo CLI Hackathon 2026 — GCC Edition**

Factora unifies machine sensor telemetry, maintenance history, production context, spare parts and
machine knowledge into one operational digital twin. It predicts failures, explains **why** with citations
from the plant's own documents, estimates the production impact, checks whether the fix is physically
possible today, and opens the preventive work order — with every computation and every generated sentence
executed inside Snowflake.

> **Status:** M0 (project bootstrap). Documentation and repo foundation only — no application code yet.
> See [`PROGRESS.md`](./PROGRESS.md) for live state and [`PROJECT_SPEC.md`](./PROJECT_SPEC.md) for the spec.

---

## The 60-second version

A plant needs one answer at 06:00: *which machine breaks next, and what do I do about it?*

- **Detect** — CNC-03's spindle vibration is drifting away from its own baseline. It goes **CRITICAL** on the Factory Twin.
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
| `.env.example` | Every environment variable, placeholders only | Whoever runs it |

---

## Planned quick start

> Commands marked **⏳** land in later milestones (see `PROJECT_SPEC.md` §11) and are listed here so the
> run path is unambiguous from day one. Nothing below is runnable yet except the M0 checks.

**Prerequisites**

- Node.js **22+** and npm
- Python **3.11+** (Snowpark helpers, M2+)
- Snowflake CLI (`snow`) — Apache-2.0
- Snowflake CoCo CLI (hackathon-supplied)
- A Snowflake account supplied by the hackathon (no paid services are used)

**1. Clone and configure**

```bash
git clone https://github.com/khushi-infinity/Factora.git
cd Factora
cp .env.example .env        # then fill in your own Snowflake values; .env is gitignored
```
Never commit `.env`, key files or credentials (`AGENTS.md` rule 4).

**2. Snowflake foundation** ⏳ (M1)

```bash
snow connection test -c factora
snow sql -c factora -f snowflake/01_schemas.sql
snow sql -c factora -f snowflake/02_seed.sql
snow sql -c factora -q "SELECT COUNT(*) FROM FACTORA_DEV.RAW.SENSOR_READING;"
```

**3. Curated twin + predictions** ⏳ (M2–M4)

```bash
snow sql -c factora -f snowflake/03_curated.sql
python snowflake/run_features.py
snow sql -c factora -f snowflake/04_predict.sql
```

**4. Run the app** ⏳ (M5)

```bash
npm ci
npm run dev                 # http://localhost:3000
```

**5. Verify before claiming anything works** ⏳ (M5+)

```bash
npm run typecheck && npm run lint && npm test   # unit gate
npm run test:e2e                                # Playwright: all six demo beats
```

**6. M0 documentation checks (runnable now)**

```bash
for f in PROJECT_SPEC.md PROGRESS.md AGENTS.md README.md .env.example .gitignore; do
  [ -f "$f" ] && echo "OK   $f" || echo "MISS $f"; done
```

The full ledger — including section checks and the secret scan — lives in [`PROGRESS.md`](./PROGRESS.md) → *Command Ledger*.

---

## Planned repository structure

```
PROJECT_SPEC.md   spec: product, architecture, data model, scope, demo flow
AGENTS.md         rules of engagement for contributors and AI agents
PROGRESS.md       live milestone state + exact commands
README.md         this file
.env.example      env var template (placeholders only)
.gitignore        secrets / artefacts hygiene

snowflake/        ⏳ M1+  schemas, DDL, seeds, dynamic tables, Snowpark jobs, prompt templates
src/              ⏳ M5+  Next.js app: pages (Factory Twin, Machine 360, Risk Board, Diagnosis,
                          Parts, Work Orders, Impact), server routes, single data-access module
tests/e2e/        ⏳ M5+  Playwright walk of the demo flow
```

---

## Architecture at a glance

```
Next.js app (localhost)  ──thin client, no business truth──►  Snowflake
  Factory Twin · Machine 360 · Risk Board ·                   RAW → CURATED → ANALYTICS
  Diagnosis · Parts · Impact · Work Orders                    Cortex Search + Cortex COMPLETE
        ▲                                                     roles, masking, AI action log
        └── CoCo CLI + Snowflake CLI: build, deploy, seed, everything reproducible from repo
```

Full detail, including the data model and per-layer responsibilities, is in
[`PROJECT_SPEC.md`](./PROJECT_SPEC.md) §3–§7.

---

## Guardrails

- **Open source only.** No paid APIs, no external LLM endpoints — the approved list is `PROJECT_SPEC.md` §4.
- **Secrets never in git.** `.env*`, `*.p8`, `*.pem`, `rsa_key*` are ignored; key-pair auth preferred.
- **Snowflake cost controls are read-only for this project.** Resource monitors, budgets and auto-suspend
  are never modified (`AGENTS.md` rule 7). X-SMALL warehouse, cached reads.
- **Honest AI.** Every generated claim carries its model, prompt version and citations; simulated data and
  cached output are visibly labelled in the UI.
- **The demo always completes.** If Snowflake is slow or unavailable, the app shows clearly-marked cached
  state instead of stalling.

## License

Project code is intended to be released under the MIT License. All dependencies are free/open-source
(see `PROJECT_SPEC.md` §4); Snowflake platform features are used within the hackathon-provided account.
A `LICENSE` file will be added when the application code lands.
