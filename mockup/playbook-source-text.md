# Extracted text — factora_build_playbook.pdf
Source: /Users/khushisarawagi/Downloads/factora_build_playbook.pdf (31 pages, PDF 1.7)
Extracted with PyMuPDF on 2026-10-02 for design/UI reference.


## Page 1

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 1
FACTORA
Beginner Build Playbook
Snowflake CoCo CLI Hackathon 2026 — GCC Edition
Use this document as your build sequence
Start at Step 0 and move in order. Do not jump ahead unless the current checkpoint works. Every agent prompt in 
this guide is written so a beginner can copy-paste it.
Project: AI-powered predictive maintenance + operational digital twin
Last updated: 2 October 2026

## Page 2

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 2
START HERE
The shortest version of what you are building and what to do first.
Your single goal
Build one flawless end-to-end flow first: Factory Twin 
 CNC-03 turns critical 
 failure prediction 
 AI explanation 
→
→
→
 spare-part check 
 create work order. Everything else is secondary until this works.
→
→
Priority
Build
MUST
Command Center, Factory Twin, Machine Detail, Predictive 
Maintenance, AI Agent, Work Order creation
SHOULD
Machines list, Spare Parts, OEE analytics, Maintenance planner
STRETCH
NASA bearing model, advanced 3D assets, continuous 
streaming, deployment, PDF parsing
Do these first today
1.
Create a new local folder named factora and initialize Git.
2.
Install Freebuff and run Prompt F0 from this guide.
3.
Open your hackathon Snowflake account and apply the cost-safety settings before creating anything else.
4.
Install CoCo CLI and connect it to the hackathon Snowflake account.
5.
Run the prompts in the Master Build Sequence one by one. Never paste all prompts at once.
Very important about the Snowflake trial
If Hack2Skill gave you a special hackathon Snowflake account with credits and CoCo access, use that account. 
Snowflake documentation says standard self-service trial accounts do not include CoCo CLI; the dedicated CoCo 
trial or an eligible account is required. Do not create a second random trial unless the hackathon account does not 
work.
Official hackathon fit
The GCC problem statement asks you to converge IT + OT data to predict failures, automate work orders, and 
improve OEE. The rubric is 40% technical execution, 30% real-world relevance, and 30% solution completeness. 
Factora is designed directly around that flow.
Official Hack2Skill GCC hackathon page

## Page 3

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 3
1. What Factora Is
Use this wording in your README, submission form, and when briefing coding agents.
One-line pitch: Factora is an AI-powered operational digital twin that unifies factory sensor, maintenance, 
production, and inventory data to predict equipment failures, explain the evidence, quantify production impact, 
and create preventive maintenance work orders before downtime happens.
Core demo story
The 90-second judge demo
1. Factory is running normally.
2. CNC-03 starts showing rising vibration + temperature.
3. Factora changes CNC-03 from healthy → warning → critical.
4. ML predicts bearing failure with high probability.
5. User asks: “Why is CNC-03 at risk?”
6. Cortex Agent queries telemetry + maintenance history + machine knowledge.
7. Factora checks spare part BRG-AX-17 and production schedule.
8. It recommends the least disruptive maintenance window.
9. User clicks Create Work Order.
10. Snowflake records the work order and the twin moves to scheduled maintenance.
What makes it more than a dashboard

Predict: estimate failure risk before breakdown.

Explain: show the sensor evidence and historical context behind the prediction.

Simulate: estimate downtime, output loss, and business impact.

Decide: check maintenance history, spare parts, and production schedule.

Act: create a work order from the same interface.

Visualize: reflect machine state in the operational digital twin.
2. UI / UX Blueprint
These images are the design target. Put the image files in docs/mockups/ inside the repository so Freebuff 
can inspect them while building.

## Page 4

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 4
Page 1 — Command Center
Top KPIs, OEE trend, machine health distribution, AI summary, critical alerts, production output, upcoming maintenance.
Page 2 — Factory Digital Twin
The visual centerpiece. Machines and production lines change state: healthy, warning, critical, maintenance/offline.

## Page 5

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 5
Page 3 — Machines Explorer
Sortable list of machines with health score, failure probability, RUL, vibration, temperature and actions.

## Page 6

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 6
Page 4 — Machine Detail
Live telemetry, prediction, root-cause evidence, maintenance history, parts and Create Work Order action.

## Page 7

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 7
Page 5 — Predictive Maintenance
Rank machines by failure risk/RUL and show recommended preventive actions.

## Page 8

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 8
Page 6 — AI Maintenance Agent
Natural-language investigation with citations/evidence from telemetry, maintenance history and knowledge base.
Page 7 — Work Orders
Create, assign, schedule and track maintenance actions generated by Factora.

## Page 9

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 9
Page 8 — Spare Parts
Stock, reorder level, supplier, lead time and compatible machines.
Page 9 — OEE & Production Analytics
Availability, performance, quality, OEE, output vs target and downtime causes.

## Page 10

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 10
Page 10 — Maintenance Planner & Reports
Calendar view, recent alerts, maintenance history and AI-generated report.
3. Technical Architecture
Keep the architecture simple enough to finish, but make Snowflake essential to the product.
Target architecture
                          FACTORA UI
                 React + TypeScript + Tailwind
                      + React Three Fiber
                               │
                               ▼
                         FastAPI backend
                               │
              ┌────────────────┼─────────────────┐
              │                │                 │
              ▼                ▼                 ▼
        Snowflake SQL      Cortex Agent     ML inference
              │                │                 │
      ┌───────┼───────┐   ┌────┼─────────┐       │
      │       │       │   │    │         │       │
   Tables  Semantic  Views Search     Custom Tool │
            View         Service    create_work_order()
      │       │       │   │              │       │
      └───────┴───────┴───┴──────────────┴───────┘
                               │
                          Snowflake data
                               │
      Sensors + maintenance + production + inventory + manuals

## Page 11

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 11
Recommended tech stack
Layer
Use
Why
Frontend
React + Vite + TypeScript
Fast to scaffold; easy local demo.
Design
Tailwind CSS + shadcn/ui
Matches the clean dashboard mockups.
Charts
Recharts
Simple OEE, telemetry and output charts.
Digital twin
React Three Fiber + drei
3D/2.5D scene without building a game 
engine.
Backend
FastAPI + Python 3.11
Easy ML + Snowflake integration.
Snowflake client
snowflake-connector-python
Direct SQL and stored-procedure calls.
ML
pandas + scikit-learn + joblib
Free, beginner-friendly, sufficient for 
prototype.
Snowflake AI
Semantic Views + Cortex Search + Cortex 
Agent
Structured + unstructured reasoning and 
actions.
Coding agent
Freebuff
Most local coding work.
Snowflake agent
CoCo CLI
Snowflake-specific creation, validation 
and agent workflows.
Repository structure
Folder layout
factora/
├── frontend/
│   ├── src/
│   └── public/
├── backend/
│   ├── app/
│   └── requirements.txt
├── ml/
│   ├── train.py
│   ├── predict.py
│   └── artifacts/
├── data/
│   ├── raw/
│   └── generated/
├── snowflake/
│   ├── sql/
│   ├── semantic/
│   └── agent/
├── docs/
│   ├── mockups/
│   └── demo-script.md
├── scripts/
├── PROJECT_SPEC.md
├── PROGRESS.md
├── AGENTS.md
├── .env.example

## Page 12

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 12
├── .gitignore
└── README.md
4. Data Plan
Use one real predictive-maintenance dataset plus synthetic enterprise context. This is faster and more 
convincing than hunting for one perfect factory dataset.
MUST: AI4I 2020 Predictive Maintenance
Use the UCI AI4I 2020 dataset for the baseline model. It contains 10,000 observations and variables such as 
air/process temperature, rotational speed, torque, tool wear, machine failure and failure modes.
UCI AI4I 2020 dataset
OPTIONAL/STRETCH: NASA IMS Bearings
Use the NASA IMS bearing dataset only after the MVP works. It is useful for richer vibration degradation signals 
and bearing-failure visuals, but it adds preprocessing complexity.
NASA IMS Bearings
Generate the rest synthetically
Table
Purpose
Approx. size
MACHINES
Asset registry + twin coordinates
20–30 machines
SENSOR_READINGS
Telemetry snapshots / demo series
10k–50k rows
FAILURE_PREDICTIONS
Model results
1 row per machine/run
MAINTENANCE_HISTORY
Past faults and repairs
100–200 rows
SPARE_PARTS
Inventory and machine compatibility
30–50 parts
WORK_ORDERS
Preventive / corrective work
50–100 rows
PRODUCTION_RUNS
Target vs actual output
1–2 weeks
DOWNTIME_EVENTS
Downtime causes and duration
50–100 rows
MAINTENANCE_KNOWLEDGE
Manual/SOP text for Cortex Search
30–80 chunks
Cost-saving live data strategy
Do NOT poll Snowflake every second. Fetch a snapshot when the page loads, animate the demo locally in the 
frontend, and persist important events/actions to Snowflake. For the judge demo, a 15–30 second refresh or manual 
Refresh button is enough.

## Page 13

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 13
5. Snowflake Cost Safety — Do This Before 
Building
Your goal is to use the hackathon credits, not your own money.
Rule #1
Do not add a personal credit card just to “make it work” unless the hackathon instructions explicitly require it. If 
the special hackathon account already has credits and CoCo enabled, stay inside that account.
5.1 Check your balance
6.
Sign in to Snowsight using the hackathon account.
7.
Look for the remaining trial/free-usage balance in the account UI or open Admin 
 Cost management.
→
8.
Confirm you are in the account that contains the hackathon credits before running any setup.
5.2 Create one tiny warehouse
In Snowsight use Projects 
 Workspaces (or Worksheets if your hackathon account still exposes it), create a SQL file/worksheet, 
→
switch the role to ACCOUNTADMIN for setup, and paste the following SQL.
RUN ONCE — basic Snowflake setup
USE ROLE ACCOUNTADMIN;
CREATE OR REPLACE WAREHOUSE FACTORA_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;
CREATE DATABASE IF NOT EXISTS FACTORA;
CREATE SCHEMA IF NOT EXISTS FACTORA.RAW;
CREATE SCHEMA IF NOT EXISTS FACTORA.CORE;
CREATE SCHEMA IF NOT EXISTS FACTORA.AI;
CREATE SCHEMA IF NOT EXISTS FACTORA.DOCS;
5.3 Add a hard warehouse guardrail
RUN ONCE — protects user-managed warehouse credits
USE ROLE ACCOUNTADMIN;
CREATE OR REPLACE RESOURCE MONITOR FACTORA_RM
  WITH CREDIT_QUOTA = 20
  FREQUENCY = MONTHLY
  START_TIMESTAMP = IMMEDIATELY
  TRIGGERS
    ON 50 PERCENT DO NOTIFY
    ON 80 PERCENT DO SUSPEND
    ON 100 PERCENT DO SUSPEND_IMMEDIATE;

## Page 14

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 14
ALTER WAREHOUSE FACTORA_WH
  SET RESOURCE_MONITOR = FACTORA_RM;
Resource monitors protect warehouses, not serverless AI features. Snowflake documents Budgets/daily limits for CoCo and 
AI/serverless usage.
5.4 Limit CoCo usage per day
OPTIONAL BUT RECOMMENDED — simple CoCo caps
USE ROLE ACCOUNTADMIN;
ALTER ACCOUNT SET CORTEX_CODE_CLI_DAILY_EST_CREDIT_LIMIT_PER_USER = 10;
ALTER ACCOUNT SET CORTEX_CODE_SNOWSIGHT_DAILY_EST_CREDIT_LIMIT_PER_USER = 5;
If CoCo blocks you because the daily limit is reached, increase the value slightly. Do not set it to -1 while you are learning; -1 
means no limit.
5.5 Use the cheapest CoCo model selector

Open CoCo and choose /model (CLI) or the model selector in Snowsight.

Select Auto Efficient for normal work. Snowflake describes it as the lowest-cost Auto option.

Use Auto/Auto Intelligent only for a hard problem that Auto Efficient cannot solve.

Avoid CoCo automations, scheduled jobs, or repeated agent calls during the prototype unless necessary.
Your safe default
XSMALL warehouse + 60-second auto-suspend + 20-credit warehouse monitor + Auto Efficient CoCo + small datasets 
+ no constant polling.
6. Install the Tools
These commands assume macOS/Linux. Windows users can use the equivalent PowerShell instructions 
from the linked Snowflake docs.
6.1 Create the project folder
Terminal
mkdir factora
cd factora
git init
6.2 Install Freebuff
Terminal
npm install -g freebuff
freebuff
Freebuff’s official launch documentation says to install globally with npm and then run freebuff from inside the repository.
6.3 Install CoCo CLI
Terminal — official Snowflake install

## Page 15

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 15
curl -LsS https://ai.snowflake.com/static/cc-scripts/install.sh | sh
cortex --version
cortex
9.
The first time you run cortex, the setup wizard asks for a Snowflake connection.
10. If it lists your hackathon connection, select it with the arrow keys and press Enter.
11. Otherwise choose More options and enter the Snowflake account details from your hackathon account.
12. After connection, run /model and choose Auto Efficient.
13. Exit and later start CoCo inside the project with: cortex -w .
If CoCo says unavailable
Do not switch to a normal Snowflake self-service trial. Official Snowflake docs say standard trials do not include 
CoCo CLI. Verify that you are using the hackathon/dedicated CoCo-enabled account and ask Hack2Skill support if 
the entitlement is missing.
7. Where You Paste Each Prompt
This is the part beginners usually get confused by.
Prompt label
Where to paste it
What it is allowed to do
FREEBUFF
Terminal 
 cd factora 
 run freebuff 
 
→
→
→
paste prompt
Create/edit local app files, run 
npm/python, tests, UI, ML, backend.
COCO CLI
Terminal 
 cd factora 
 run cortex -w . 
→
→
 paste prompt
→
Create/query Snowflake objects, 
semantic views, Search, Agents; also 
inspect local repo.
SNOWFLAKE SQL
Snowsight 
 Projects 
 Workspaces 
 
→
→
→
SQL file (or Worksheets on older 
account)
Run one-time SQL for cost controls, 
database, roles or troubleshooting.
COCO IN SNOWSIGHT
Snowsight 
 CoCo icon in lower-right 
 
→
→
chat box
Optional alternative to CLI; useful for 
Snowflake-only questions.
Do not paste Freebuff prompts into Snowflake
Freebuff owns local application code. CoCo owns Snowflake-specific work. Both see the same repository, but avoid 
having both edit the same files at the same time.
8. Agent Working Rules
These files stop the agents from losing track of the project.
First thing Freebuff creates
Project control files
PROJECT_SPEC.md  — product requirements and architecture
PROGRESS.md      — completed / in progress / next / blockers
AGENTS.md         — rules every coding agent must follow

## Page 16

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 16
README.md         — project setup and demo
.env.example      — variable names only, never secrets
PROMPT F0 — Freebuff: Initialize the project and progress system
We are starting a completely fresh project called Factora for the Snowflake CoCo CLI Hackathon 2026 GCC 
Edition.
Factora is an AI-powered operational digital twin for predictive maintenance. It unifies machine sensor 
data, maintenance history, production context, spare parts and machine knowledge. It predicts failures, 
explains why, estimates production impact, and can create preventive maintenance work orders.
Before writing application code, create these files at the repository root:
- PROJECT_SPEC.md
- PROGRESS.md
- AGENTS.md
- README.md
- .env.example
- .gitignore
PROJECT_SPEC.md must contain:
- product pitch
- core demo flow: Factory Twin → CNC-03 critical → prediction → AI explanation → part check → work 
order
- page list
- architecture
- tech stack
- Snowflake responsibilities
- local app responsibilities
- data model
- MVP vs stretch features
AGENTS.md rules:
1. Always read PROJECT_SPEC.md and PROGRESS.md before changing code.
2. Work on one milestone at a time.
3. Never mark a task complete without running a relevant test/build.
4. Never put passwords, Snowflake keys, tokens or credentials in git.
5. Use only free/open-source dependencies unless already supplied by the hackathon.
6. Do not introduce a paid API.
7. Do not change Snowflake cost-control settings.
8. Preserve working functionality while adding features.
9. Update PROGRESS.md at the end of every completed milestone.
10. Record exact commands needed to run the project.
PROGRESS.md should contain sections: Current Goal, Completed, In Progress, Next 3 Tasks, Blockers, Test 
Status, Demo Status.
Do not build features yet. Show me the files created and summarize them.
After it finishes: Open PROJECT_SPEC.md and PROGRESS.md and make sure they reflect the project before moving on.
9. Master Build Sequence — Run These Prompts 
One by One
Do not give Prompt 2 until Prompt 1 is working. The order is deliberate.

## Page 17

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 17
PROMPT F1 — Freebuff: Scaffold the local application
Read PROJECT_SPEC.md, AGENTS.md and PROGRESS.md first.
Scaffold Factora with:
- frontend: React + Vite + TypeScript + Tailwind CSS
- backend: FastAPI + Python
- charts: Recharts
- 3D: @react-three/fiber and @react-three/drei
- ML: pandas, scikit-learn, joblib
- Snowflake Python connector in backend
Create the repository structure described in PROJECT_SPEC.md.
Add a health endpoint to FastAPI and a minimal React shell that calls it.
Add commands to run frontend and backend locally.
Do not implement product pages yet.
Run the frontend build and a backend smoke test. Fix errors before updating PROGRESS.md.
After it finishes: You should be able to start backend and frontend locally and see a basic Factora shell.
PROMPT F2 — Freebuff: Create the datasets and synthetic factory generator
Read PROJECT_SPEC.md, AGENTS.md and PROGRESS.md.
Create a reproducible data pipeline for Factora.
1. Add scripts/download_ai4i.py that downloads the UCI AI4I 2020 Predictive Maintenance CSV from the 
official source or explains the manual download location if automated download is blocked.
2. Add scripts/generate_factory_data.py.
3. Generate realistic CSVs for:
   machines
   sensor_readings
   maintenance_history
   spare_parts
   work_orders
   production_runs
   downtime_events
   maintenance_knowledge
4. Use deterministic random seeds.
5. Create 24 machines across CNC, press, assembly, packaging and quality lines.
6. Give every machine twin coordinates x, y, z and status.
7. Build a scripted CNC-03 degradation scenario with rising vibration and temperature ending in a 
bearing-failure risk.
8. Include BRG-AX-17 as CNC-03's compatible bearing with limited stock.
9. Keep generated data small enough for a hackathon.
10. Add data/README.md describing every column and which fields are synthetic.
Run the generator and validate that every CSV is non-empty and internally consistent. Update 
PROGRESS.md.
After it finishes: Confirm data/generated contains the CSVs and CNC-03 has a clear degradation scenario.
PROMPT F3 — Freebuff: Train the baseline failure model
Read project files first.
Build a simple, defensible predictive-maintenance baseline using the AI4I dataset.
Use scikit-learn only unless a stronger library is already installed.

## Page 18

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 18
Requirements:
- train/test split
- handle class imbalance sensibly
- use a model that provides failure probability
- report precision, recall, F1 and confusion matrix
- save the model with joblib
- create ml/predict.py with a clean inference function
- create a lightweight mapping from model output + failure flags/context to a human-readable predicted 
failure type
- do not fake model metrics
- write ml/MODEL_CARD.md with dataset source, limitations, features, target and evaluation
Then make CNC-03 demo data produce a high bearing-failure risk through a clearly documented demo 
adapter/feature mapping without corrupting the real model evaluation.
Run training and inference tests. Update PROGRESS.md.
After it finishes: You should have an artifact in ml/artifacts and an honest MODEL_CARD.md.
PROMPT C1 — CoCo CLI: Inspect Snowflake and create the Factora data model
Read PROJECT_SPEC.md, AGENTS.md and PROGRESS.md in this repository.
We are using the Snowflake hackathon account and must minimize credits.
Before changing anything:
1. show the current role, warehouse and database context;
2. confirm FACTORA_WH is XSMALL with AUTO_SUSPEND 60 seconds;
3. do not resize the warehouse;
4. do not create additional warehouses.
Create or validate these schemas in database FACTORA: RAW, CORE, AI, DOCS.
Design and create tables for:
MACHINES
SENSOR_READINGS
MAINTENANCE_HISTORY
SPARE_PARTS
WORK_ORDERS
PRODUCTION_RUNS
DOWNTIME_EVENTS
FAILURE_PREDICTIONS
MAINTENANCE_KNOWLEDGE
Use sensible data types, primary-key-like identifiers, timestamps and comments.
Save all SQL you execute into snowflake/sql/ with ordered filenames so the environment is reproducible.
Do not create Cortex Search or Agents yet.
Validate the objects with SHOW/DESCRIBE commands and update PROGRESS.md.
After it finishes: Check Snowflake object explorer for FACTORA and verify tables exist.
PROMPT C2 — CoCo CLI: Load the generated data into Snowflake
Read project files first.
Load the CSV files from data/generated into the corresponding FACTORA tables using the lowest-
complexity Snowflake method available in this account.
Keep FACTORA_WH at XSMALL.
Do not use continuous Snowpipe or any always-on service.

## Page 19

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 19
Requirements:
- preserve source CSVs
- create staging/file-format SQL only if needed
- load all core tables
- verify row counts
- run sanity checks for CNC-03, BRG-AX-17, work orders and production data
- save the SQL/scripts used under snowflake/sql/
- report exact row counts and any rejected rows
- update PROGRESS.md
Stop if loading would require a new paid external service.
After it finishes: In Snowsight, SELECT from MACHINES and SENSOR_READINGS and verify data is present.
PROMPT F4 — Freebuff: Build the FastAPI data and prediction API
Read project files first.
Build the Factora backend API.
Use environment variables from .env; never hardcode credentials.
Use snowflake-connector-python.
Create endpoints for:
GET /api/health
GET /api/overview
GET /api/machines
GET /api/machines/{machine_id}
GET /api/machines/{machine_id}/telemetry
GET /api/predictions
GET /api/spare-parts
GET /api/work-orders
POST /api/work-orders
GET /api/oee
The API should query Snowflake for operational data and use the local ML artifact only for 
prediction/inference where appropriate.
Add a clearly isolated DEMO_MODE fallback using generated CSVs only when Snowflake is unavailable; 
normal mode must use Snowflake.
Add caching so the frontend does not repeatedly query Snowflake every few seconds.
Add unit/smoke tests for the key endpoints.
Update .env.example with required Snowflake variables but no secrets.
Run tests and update PROGRESS.md.
After it finishes: Call /api/overview and /api/machines/CNC-03 successfully.
PROMPT F5 — Freebuff: Build the design system and application shell
Read project files first. Use the Factora UI mockup images from docs/mockups as the visual target.
Build the shared UI shell:
- dark navy sidebar
- Factora logo/wordmark
- plant selector
- live-data indicator
- search field
- notifications
- profile area

## Page 20

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 20
- responsive dashboard content
Create routes for:
/
/twin
/machines
/machines/:id
/predictive-maintenance
/ai-assistant
/work-orders
/spare-parts
/oee
/planner
Use Tailwind and reusable components. Do not use random gradients or excessive animation. Match the 
reference mockups: clean enterprise dashboard, blue accent, green/yellow/red machine states, 
white/light panels.
Implement empty page shells only, then run npm build and fix all errors. Update PROGRESS.md.
After it finishes: Navigate every route with no crash before continuing.
PROMPT F6 — Freebuff: Implement Command Center + Machines + Machine Detail
Read project files and mockup images first.
Implement three pages using the real backend API:
1. Command Center
2. Machines Explorer
3. Machine Detail
Command Center must include: OEE, machines online, predicted failures, maintenance cost, production 
output, OEE trend, machine health distribution, alerts and upcoming maintenance.
Machines Explorer must show health score, failure probability, RUL, vibration and temperature.
Machine Detail must show CNC-03 live/latest telemetry, recent trend charts, failure prediction, root-
cause explanation panel, maintenance history, required part and Create Work Order button placeholder.
Use loading/error states. Do not invent random numbers in components; data must come from API or 
clearly tagged demo seed data.
Run npm build and backend smoke tests. Update PROGRESS.md.
After it finishes: Compare the pages side-by-side with the UI references and fix the biggest visual gaps.
PROMPT F7 — Freebuff: Build the operational digital twin
Read project files and the Factory Twin mockup first.
Implement /twin with React Three Fiber.
This is an operational twin, not CAD.
Requirements:
- simple factory floor
- production-line zones
- 24 machines positioned from MACHINES x/y/z coordinates
- machine status colors: healthy green, warning amber, critical red, maintenance blue/gray, offline 
gray
- labels for important machines
- orbit/pan/zoom controls with sane limits

## Page 21

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 21
- clicking a machine opens a side panel with machine health, failure probability, telemetry and link to 
full Machine Detail
- a 2D fallback if WebGL is unavailable
- optimize for laptop performance; use simple geometry rather than heavy models
- scripted Demo Scenario button that locally animates CNC-03 from healthy → warning → critical without 
sending a Snowflake query every frame
Persist only important scenario events, not each animation frame.
Run build and test the page. Update PROGRESS.md.
After it finishes: The twin should be visually convincing and CNC-03 should be clickable and change state.
PROMPT C3 — CoCo CLI: Create the governed semantic view
Read PROJECT_SPEC.md and inspect the FACTORA tables.
Create a semantic view for Factora's structured operational data.
It must support questions such as:
- Which machines have the highest failure risk?
- Which production line has the lowest OEE?
- What caused the most downtime this week?
- Which machines need maintenance soon?
- What production is at risk if CNC-03 stops?
- Which spare part is needed for CNC-03?
- Which work orders are open or overdue?
Define clear business entities, joins, dimensions and metrics. Do not invent relationships that are not 
supported by the schema.
Validate the semantic view with test questions.
Save any generated SQL/YAML/definitions into snowflake/semantic/ and update PROGRESS.md.
Keep queries on FACTORA_WH and do not create a larger warehouse.
After it finishes: Ask 3–5 questions and confirm results are grounded in the tables.
PROMPT C4 — CoCo CLI: Create Cortex Search over maintenance knowledge
Read project files first.
Use FACTORA.DOCS.MAINTENANCE_KNOWLEDGE as the source for a small Cortex Search service for machine 
manuals, maintenance procedures and historical repair notes.
Keep the corpus intentionally small to control cost.
Use the smallest practical refresh settings for a static hackathon dataset; avoid frequent refreshes.
Search should support filters such as MACHINE_TYPE, MACHINE_ID or DOCUMENT_TYPE if those columns exist.
Test queries:
- bearing vibration symptoms CNC milling
- CNC-03 bearing replacement procedure
- hydraulic temperature warning Press-02
Save creation SQL/notes under snowflake/agent/ or snowflake/sql/.
Report the service name and test results. Update PROGRESS.md.
After it finishes: Confirm the service returns relevant maintenance knowledge before building the Agent.
PROMPT C5 — CoCo CLI: Build the Factora Cortex Agent

## Page 22

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 22
Help me build and deploy a Cortex Agent named FACTORA_MAINTENANCE_AGENT using the existing Factora 
semantic view and maintenance Cortex Search service.
Persona: senior factory reliability engineer.
The agent must:
- use the semantic view for metrics, machine state, production, parts and work orders;
- use Cortex Search for procedures, symptoms and maintenance knowledge;
- clearly separate observed facts, model predictions, retrieved evidence and recommendations;
- never claim a prediction is certain;
- answer concisely for operators;
- cite/refer to the evidence source when Search is used.
Test these questions:
1. Why is CNC-03 at risk?
2. What happens to production if CNC-03 fails?
3. Do we have the required bearing in stock?
4. What should maintenance do next?
Do not enable web search, automations or unnecessary tools.
Save configuration/notes in snowflake/agent/ and update PROGRESS.md.
After it finishes: Use Snowflake AI & ML 
 Agents to inspect the created agent and test it manually too.
→
PROMPT C6 — CoCo CLI: Create the work-order action tool
Read project files first.
Create the lowest-risk Snowflake action that lets FACTORA_MAINTENANCE_AGENT create a proposed 
preventive maintenance work order.
Prefer a stored procedure/custom tool that inserts into FACTORA.CORE.WORK_ORDERS.
Required inputs:
machine_id, issue, priority, required_part, scheduled_time, estimated_downtime, reason
Safety rules:
- only create PROPOSED or SCHEDULED demo work orders;
- never delete existing rows;
- validate machine_id exists;
- return the created work_order_id and summary;
- log created_at and source='CORTEX_AGENT'.
Attach the tool to the Cortex Agent if supported by the current account and test it using CNC-03.
Save SQL/config under snowflake/agent/ and update PROGRESS.md.
After it finishes: Verify the inserted work order appears in FACTORA.CORE.WORK_ORDERS.
PROMPT F8 — Freebuff: Integrate Cortex Agent into the Factora UI
Read project files first.
Integrate the existing FACTORA_MAINTENANCE_AGENT into the backend and /ai-assistant page using the 
supported Snowflake API/connector approach already available to this project.
Do not introduce OpenAI, Anthropic, Gemini or any external paid LLM API.
UI requirements:

## Page 23

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 23
- chat-style question box
- sample prompts
- answer panel
- evidence/data-source cards
- show observed data vs prediction vs recommendation clearly
- button to open CNC-03 Machine Detail
- Create Work Order action only when the agent recommends maintenance
Add backend timeouts and useful error messages.
Avoid repeated background agent calls; only call the Agent when the user submits a question/action.
Run tests/build and update PROGRESS.md.
After it finishes: Ask “Why is CNC-03 at risk?” from the UI and verify the answer reaches the real Cortex Agent.
PROMPT F9 — Freebuff: Finish work orders, spare parts, OEE and planner
Read project files and UI references first.
Implement remaining MVP/should-have pages using backend data:
- Work Orders
- Spare Parts Inventory
- OEE & Production Analytics
- Maintenance Planner & Reports
Requirements:
- Work Orders must show the Cortex-created CNC-03 work order.
- Spare Parts must highlight BRG-AX-17 stock/reorder status.
- OEE page must compute/visualize Availability, Performance, Quality and OEE from documented data 
fields/formulas; do not invent formula outputs silently.
- Planner shows scheduled work orders on a calendar/list.
- Reports can be a simple generated summary; no need for PDF export unless time remains.
Match the mockups closely. Run build/tests and update PROGRESS.md.
After it finishes: All 10 routes should now be useful and visually consistent.
PROMPT F10 — Freebuff: Create a polished judge demo mode
Read project files first.
Create an explicit Demo Mode that gives us a deterministic 90-second story without fake hidden data.
Add a Reset Demo button and Start CNC-03 Failure Scenario button.
Scenario timeline:
- healthy baseline
- vibration and temperature rise
- warning state
- critical state with 92% demo prediction display only if backed by the documented demo adapter
- AI investigation button
- spare part BRG-AX-17 shown
- proposed repair window shown
- Create Work Order
- twin switches to scheduled-maintenance state after work order creation
Clearly label simulated live telemetry as simulated/demo telemetry in the UI or About section.
Demo Mode must never generate thousands of Snowflake queries.
Add docs/demo-script.md with exact click-by-click narration.

## Page 24

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 24
Run full build and update PROGRESS.md.
After it finishes: Practice the demo once with the backend/Snowflake connected.
PROMPT C7 — CoCo CLI: Final Snowflake validation and cost review
Read PROGRESS.md and inspect only the Snowflake portion of Factora.
Perform a final validation:
- list Factora tables/views/semantic view/Search service/Agent/custom tool
- confirm FACTORA_WH is XSMALL and AUTO_SUSPEND is still 60 seconds
- show recent query/warehouse usage if accessible
- identify any object that could consume credits continuously
- confirm no scheduled CoCo automations were created
- run one final Agent question and one work-order test only
- do not enlarge compute or create new services
Write snowflake/FINAL_SNOWFLAKE_CHECK.md with what exists, how each Snowflake component is used, and 
any cost-risk warnings.
Update PROGRESS.md.
After it finishes: Read FINAL_SNOWFLAKE_CHECK.md before the final submission.
PROMPT F11 — Freebuff: Final QA, README and submission assets
Read every project control file first.
Prepare Factora for submission.
1. Run frontend build, backend tests and ML smoke test.
2. Run a lightweight end-to-end smoke test against Snowflake if credentials are available.
3. Fix broken routes, console errors, obvious mobile/desktop layout issues and dead buttons.
4. Update README.md with:
   - problem statement
   - solution
   - architecture
   - Snowflake technologies used
   - CoCo CLI usage
   - data sources
   - ML approach and limitations
   - local setup
   - demo flow
   - screenshots section
5. Add a Mermaid architecture diagram to README if GitHub supports it.
6. Ensure .env and secrets are ignored.
7. Create docs/SUBMISSION_CHECKLIST.md and docs/DEMO_SCRIPT.md.
8. Do not add new major features.
9. Update PROGRESS.md to final status.
Show me all remaining failures or blockers instead of hiding them.
After it finishes: Only polish after this. Do not start a new feature the night before submission.
10. Snowflake UI Walkthrough
What to click when you are completely new to Snowsight.

## Page 25

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 25
Run SQL
14. Sign in to your Snowflake hackathon account (Snowsight).
15. Open Projects 
 Workspaces. Create a SQL file. If the account still shows Worksheets, use Projects 
 
→
→
Worksheets 
 + SQL Worksheet.
→
16. Use the context selector to choose the role and FACTORA_WH.
17. For one-time account setup/cost SQL, choose ACCOUNTADMIN if your hackathon user has it.
18. Paste one SQL block from this guide and run it. Do not paste every SQL block at once.
19. When finished, allow FACTORA_WH to auto-suspend; do not keep clicking Resume just to leave it running.
Use CoCo inside Snowsight
20. Look for the CoCo icon in the lower-right area of Snowsight and open it.
21. Use the model selector next to the message box and choose Auto Efficient.
22. You can ask Snowflake questions here, but for the hackathon build use CoCo CLI for the main prompts so the 
repository and Snowflake work stay together.
Create/test Cortex Agent manually
23. Open AI & ML 
 Agents.
→
24. Open FACTORA_MAINTENANCE_AGENT after CoCo creates it.
25. Check its tools: semantic view, Cortex Search and the work-order custom tool.
26. Ask “Why is CNC-03 at risk?” and verify the answer uses the correct data.
27. Do not repeatedly spam the Agent during development; each run can consume AI credits.
Inspect Cortex Search manually
28. Open AI & ML 
 Cortex Search.
→
29. Open the maintenance search service created by CoCo.
30. Run one or two bearing/CNC searches to verify relevance.
31. Because the source data is static for the hackathon, avoid aggressive refresh settings.
11. How the Digital Twin Actually Works
You do not need CAD. The twin is a visual projection of Factora machine state.
Twin data flow
Snowflake MACHINES row
  machine_id: CNC-03
  line: CNC
  x: 30
  y: 0
  z: 8
  status: CRITICAL
  health_score: 45
       │
       ▼
FastAPI /api/machines
       │
       ▼
React state
       │

## Page 26

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 26
       ▼
<Machine position={[30,0,8]} color="red" />
       │
       ▼
User clicks machine → side panel → Machine Detail
Build it in three passes
Pass
What to build
Stop when
1 — Functional
Floor, zones, boxes for machines, status 
colors, click selection
CNC-03 can be clicked and turns red.
2 — Usable
Labels, side panel, orbit controls, filters, 
mini legend
Judge can understand the plant without 
explanation.
3 — Polished
Simple GLB models, better lighting, 
subtle animation
Only if MVP is already complete.
Do not do this
Do not spend hours searching for perfect CAD files or building Blender models. A clean operational twin with real 
state changes scores better than a beautiful static factory.
12. Credentials and .env
Never give Freebuff or GitHub your actual password inside a prompt or committed file.
Example only — actual .env stays local
# .env.example
SNOWFLAKE_ACCOUNT=
SNOWFLAKE_USER=
SNOWFLAKE_PASSWORD=
SNOWFLAKE_WAREHOUSE=FACTORA_WH
SNOWFLAKE_DATABASE=FACTORA
SNOWFLAKE_SCHEMA=CORE
SNOWFLAKE_ROLE=
FACTORA_DEMO_MODE=false

Put .env in .gitignore.

Prefer browser/SSO/key-pair authentication if the hackathon account provides it.

Never paste credentials into PROGRESS.md, README, screenshots or agent prompts.

Before pushing to GitHub, run git status and inspect every changed file.
13. Checkpoints and Tests
Do not trust an agent that says “done” without a visible checkpoint.
Checkpoint
Pass condition
Local scaffold
Frontend opens; FastAPI /api/health returns success.

## Page 27

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 27
Checkpoint
Pass condition
Data
Generator produces all CSVs; CNC-03 degradation exists.
ML
Model trains; metrics are reported; artifact loads and predicts.
Snowflake tables
FACTORA tables exist and row counts match expected files.
API
Overview + CNC-03 endpoints return Snowflake-backed data.
UI
Command Center/Machine Detail render with API data.
Twin
CNC-03 status changes and click opens details.
Semantic view
Structured natural-language questions return correct results.
Search
Bearing/CNC knowledge retrieval returns relevant chunks.
Agent
“Why is CNC-03 at risk?” uses structured + unstructured 
evidence.
Action
Agent/UI creates one proposed work order in Snowflake.
Final demo
Reset 
 scenario 
 investigation 
 part 
 work order works 
→
→
→
→
twice in a row.
14. Final Demo Script
Keep the spoken demo short. Show, do not explain architecture for five minutes.
Time
Action
What you say
0–15s
Command Center
“Factora unifies machine telemetry with 
maintenance, production and inventory 
context instead of treating sensors in 
isolation.”
15–35s
Open Factory Twin; start scenario
“CNC-03 begins degrading. The 
operational twin changes state as its 
vibration and temperature trend moves 
outside baseline.”
35–55s
Machine Detail / Predictive Maintenance
“The model predicts bearing failure 
before breakdown and estimates 
remaining useful life.”
55–75s
Ask AI Agent why
“The Cortex Agent combines governed 
factory data with maintenance 
knowledge to explain the evidence and 
recommended action.”
75–90s
Part check + Create Work Order
“Factora verifies BRG-AX-17 inventory 
and turns the prediction into a 
preventive work order during the lowest-
impact maintenance window.”

## Page 28

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 28
15. Submission Checklist
Do this before you submit. No last-minute feature building.

Factora name used consistently everywhere; no FactoryPulse leftovers.

Problem statement explicitly says Predictive Maintenance + OEE Command Center.

README explains why Snowflake is essential.

README names CoCo CLI, Semantic Views, Cortex Search, Cortex Agent and Snowflake data storage/compute 
actually used.

Screenshots/GIF/video show the 3D operational twin.

Demo shows an end-to-end action, not only prediction.

Data sources and synthetic-data disclosure are documented.

MODEL_CARD.md contains honest limitations.

No secrets in GitHub.

Snowflake warehouse remains XSMALL with auto-suspend.

Demo has been reset and run twice successfully.

Submission video/audio is understandable without reading tiny text.
16. Common Problems
Fast fixes before you panic.
Problem
What to do
cortex command not found
Close/reopen Terminal; check ~/.local/bin is in PATH; rerun 
official installer.
CoCo says unavailable on trial
Verify you are on the hackathon/dedicated CoCo-enabled 
account; standard Snowflake trial does not include CoCo CLI.
Warehouse spending too much
Check FACTORA_WH size; set XSMALL and AUTO_SUSPEND=60; 
suspend it manually while debugging frontend.
Agent cannot access tables
Check default role permissions and warehouse usage; ask CoCo 
to diagnose missing grants.
Cortex Search returns poor results
Improve MAINTENANCE_KNOWLEDGE chunks and metadata; 
keep documents short and specific.
3D is slow
Replace models with boxes, reduce shadows/lights, avoid large 
GLB assets.
Frontend repeatedly hits Snowflake
Use backend cache; stop 1-second polling; use local demo 
animation.
ML accuracy looks weird
Do not tune for fake accuracy. Inspect imbalance, report 
recall/F1 and limitations.
Freebuff changed too much
Use git diff; revert unwanted changes; give one smaller prompt 
at a time.
Something is broken near deadline
Revert to last working commit and preserve the end-to-end 
demo flow.

## Page 29

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 29
17. Beginner Git Safety
Make a working checkpoint after each major milestone.
Basic workflow
git status
git add .
git commit -m "milestone: scaffold factora"
# later milestones
git add .
git commit -m "milestone: snowflake data loaded"
git commit -am "milestone: digital twin working"   # only if all changes are tracked
Before any risky agent prompt
Run git status and commit a working checkpoint first. That gives you a safe point to return to if Freebuff/CoCo edits 
the wrong files.
Appendix A — Starter PROGRESS.md Template
Freebuff Prompt F0 will create this automatically, but this is what good progress tracking should look like.
Template
# Factora Progress
## Current Goal
Get the core end-to-end demo working.
## Completed
- [ ] Repository initialized
- [ ] Cost controls configured
- [ ] Data generated
- [ ] ML baseline trained
- [ ] Snowflake tables loaded
- [ ] Backend API working
- [ ] Command Center working
- [ ] Digital Twin working
- [ ] Semantic View created
- [ ] Cortex Search created
- [ ] Cortex Agent created
- [ ] Work Order action works
- [ ] Demo Mode works
## In Progress
- None yet
## Next 3 Tasks
1. ...
2. ...
3. ...

## Page 30

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 30
## Blockers
- None
## Test Status
- Frontend build: NOT RUN
- Backend tests: NOT RUN
- ML smoke test: NOT RUN
- Snowflake validation: NOT RUN
- End-to-end demo: NOT RUN
## Demo Status
- Reset works: NO
- CNC-03 scenario works: NO
- Agent answer works: NO
- Work order works: NO
## Last Updated
YYYY-MM-DD HH:MM
Appendix B — OEE and Demo Metrics
Keep definitions explicit so the dashboard is defensible.
Standard OEE structure
Availability = Run Time / Planned Production Time
Performance  = (Ideal Cycle Time × Total Count) / Run Time
Quality      = Good Count / Total Count
OEE          = Availability × Performance × Quality
Use percentages consistently and document how your synthetic production fields map to these formulas. Do not display arbitrary 
OEE numbers without an underlying calculation.
Appendix C — Verified References
Use these when an agent needs the official current behavior rather than guessing.

Hack2Skill — Snowflake CoCo CLI Hackathon 2026 GCC Edition
 
 

Snowflake — CoCo CLI getting started
 
 

Snowflake — CoCo cost controls
 
 

Snowflake — CoCo daily credit usage limits
 
 

Snowflake — Resource monitors
 
 

Snowflake — Cortex Agents getting started
 
 

Snowflake — Create/manage Cortex Agents
 
 

Snowflake — Cortex Search overview
 
 

Snowflake — Semantic views overview
 
 

Freebuff — official launch/install
 
 

UCI — AI4I 2020 Predictive Maintenance Dataset
 
 

NASA — IMS Bearings
 
 
Final instruction

## Page 31

Factora — Beginner Build Playbook  |  Snowflake CoCo CLI Hackathon 2026
Page 31
Build the core flow before beautifying anything: CNC-03 risk 
 evidence 
 part 
 work order. If that flow is real 
→
→
→
and Snowflake-backed, Factora already has a strong hackathon story. Every additional page should reinforce that 
story, not distract from it.
