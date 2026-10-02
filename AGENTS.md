# AGENTS.md — Operating Rules for Factora

This file governs any AI agent (or human) contributing to Factora. It is intentionally short and
non-negotiable. If a rule conflicts with a convenience, the rule wins (AGENTS rule 8's spirit: never
trade working software for speed).

---

## The Rules

1. **Always read `PROJECT_SPEC.md` and `PROGRESS.md` before changing code.**
   Read the spec for *what* and *why*; read progress for *where we are*. If either file contradicts the
   code, reconcile them in the same change.
2. **Work on one milestone at a time.**
   Milestones are defined in `PROJECT_SPEC.md` §11 and tracked in `PROGRESS.md`. Do not start milestone
   N+1 while N is unfinished, and do not silently expand scope — stretch work waits until MVP is green.
3. **Never mark a task complete without running a relevant test/build.**
   "Relevant" is defined by the *Verification Protocol* below. If no automated test exists for the
   change, add one or run the documented manual check and record the exact command + observed result.
4. **Never put passwords, Snowflake keys, tokens or credentials in git.**
   Only `.env.example` (placeholders) is committed. `.env*`, `*.p8`, `*.pem`, `rsa_key*` are ignored.
   Use key-pair auth over passwords. Never paste secrets into code, docs, SQL files, comments, issues,
   commit messages, screenshots or logs. If a secret is ever committed, treat it as compromised: rotate
   it, then remove it from history.
5. **Use only free/open-source dependencies unless already supplied by the hackathon.**
   The approved list is `PROJECT_SPEC.md` §4. A new dependency requires: license check, a one-line
   justification, and a `PROGRESS.md` entry.
6. **Do not introduce a paid API.**
   No keyed third-party services, no external LLM endpoints, no paid data sources. Intelligence runs
   inside the hackathon-provided Snowflake account, or locally on open weights.
7. **Do not change Snowflake cost-control settings.**
   Resource monitors, budgets, auto-suspend/auto-resume, warehouse size caps and account limits are
   read-only for us. You may *display* them; you may not modify them. Prefer the smallest warehouse and
   cached reads.
8. **Preserve working functionality while adding features.**
   A green demo beat must stay green. Refactors are small and reversible; add behind a flag or a
   fallback path where the risk is real. Never leave the default branch in a half-built state.
9. **Update `PROGRESS.md` at the end of every completed milestone.**
   Move finished items into *Completed* with the verification evidence, refresh *Current Goal*,
   *Next 3 Tasks*, *Blockers*, *Test Status* and *Demo Status*. An unrecorded milestone is not done.
10. **Record exact commands needed to run the project.**
    Copy-pasteable, in order, with expected output: setup, seed, transform, run, test. Keep the
    *Command Ledger* in `PROGRESS.md` and the Quick Start in `README.md` in sync — a teammate must be
    able to go from a clean clone to a running demo using only those commands.

---

## Verification Protocol (how rule 3 is satisfied)

| Change type | Required evidence before "done" |
|-------------|--------------------------------|
| Docs only (`*.md`, `.env.example`, `.gitignore`) | Presence/completeness check for required sections + secret scan (`grep`) |
| SQL / Dynamic Table / Snowpark | Script runs twice without error (idempotency) + row-count/sanity `SELECT` output recorded |
| Frontend code (TS/React) | `cd frontend && npm run typecheck && npm run lint && npm test` |
| Frontend build-affecting change | `cd frontend && npm run build` — the production bundle must succeed |
| Backend code (Python) | `cd backend && .venv/bin/pytest -q` **and** `.venv/bin/ruff check .`; any new route needs a TestClient test |
| Demo flow / UI wiring | `npm run test:e2e` on the affected beats; attach the run result |
| Prompt / AI output change | Regenerate once, confirm citations resolve, persist the row, replay offline |
| Dependency added | License verified (rule 5), `npm ci && npm run build` still succeeds |

**Never** write "tested manually" without the command and its observable result. Never report a
milestone as complete because code "looks right".

---

## Repo Map

```
PROJECT_SPEC.md   what we are building and why (source of truth)
AGENTS.md         this file — rules of engagement
PROGRESS.md       live state: goal, completed, in progress, next 3, blockers, tests, demo
README.md         human-facing overview + quick start + exact commands
.env.example      every env var, placeholders only (never real values)
.gitignore        secret and artefact hygiene

frontend/         (M1+) React + Vite + TS SPA: pages, components (`src/lib` = typed API client)
backend/          (M1+) FastAPI BFF: `app/api/` routes, `app/db/` (the ONLY place the Snowflake
                  connector is imported), `app/ml/` (pandas/scikit-learn/joblib, M3+), `tests/` pytest
snowflake/        (M2+) SQL + Snowpark: schemas, DDL, seeds, dynamic tables, prompts
tests/e2e/        (M6+) Playwright demo-flow tests
```

Files not listed here (logs, caches, `.env`, key material, `node_modules/`, local scratch) must never be
committed.

---

## Working Agreement

- **Ask before destructive or irreversible actions** (history rewrite, dropping objects with data,
  deleting branches, force push). Never run `git push --force` on shared branches.
- **Keep the demo cold-startable**: any command chain that only works on your machine is a bug.
- **Label simulation honestly**: synthetic telemetry, cached AI output and replayed data must be visibly
  marked in the UI and in the docs.
- **Small, reviewable changes**: one milestone-scoped commit with a message that names the milestone
  (e.g. `M3: curated health features for CNC-03`).
- **Stop and record a blocker** rather than guessing around a missing credential, quota or dataset —
  write it in `PROGRESS.md` → *Blockers* and continue with something unblocked.
