# Portfolio content

## Positioning

Asteria Analyst AI is a governed conversational analytics POC for small commerce teams. It combines ingestion and profiling, transparent typed planning, safe execution, business explanations, reproducible audit trails, and an executive SaaS interface. It demonstrates AI engineering, analytics engineering, backend/frontend delivery, security thinking, evaluation, and DevOps without claiming production usage.

## Design challenges

The principal decision was to reject generated Python in favor of a typed DSL. SQL generation and validation are separate trust domains. The zero-key deterministic planner keeps demonstrations and CI reproducible. Metadata and analytical files are separated; source ownership is enforced at retrieval. Known scope gaps are published rather than hidden behind placeholders.

## Client use cases

Retail sales exploration, campaign reporting, operations KPI review, customer segmentation prototypes, data-quality triage, analyst self-service, and governed internal demonstrations.

## 60-second pitch

“Asteria Analyst AI lets a business user upload a dataset and ask a question in plain English, but it does not blindly run generated code. Every request becomes a typed, visible analysis plan. The system validates columns and operations, executes only an approved dataframe registry—or a read-only SQL query through an AST safety layer—and returns the answer with supporting data, chart, assumptions, warnings, and an audit trace. It runs locally without a paid model key, includes synthetic retail data and adversarial evaluation cases, and ships as a tested React/FastAPI/PostgreSQL Docker stack.”

## Two-minute demo

1. Sign in as analyst and state that all demo data is synthetic.
2. Show overview, real source/row counters, and suggested questions.
3. Upload `orders.csv`; point out profiling, duplicate/null warnings, inferred-type notice, and samples.
4. Ask “Revenue by region.” Show answer, bar chart, table, confidence, runtime, and assumptions.
5. Open the validated plan and explain that it is data, not Python code.
6. Export CSV. Ask “Show performance” to demonstrate clarification.
7. Sign in as admin and show metrics derived from persisted audit records.
8. Close on SQL AST controls, owner isolation, tests, honest limitations, and the next production steps.

## Upwork description

Built a full-stack governed conversational analytics POC with React, TypeScript, FastAPI, SQLAlchemy, PostgreSQL/SQLite, pandas, and SQL parsing. Users can ingest and profile datasets, ask business questions, inspect validated plans, view results/charts, and export evidence. The architecture blocks arbitrary generated Python, restricts SQL, isolates user-owned sources, records audits, runs without a paid API key, and includes Docker, CI, automated security tests, and a 44-case evaluation manifest.

## Repository description

Safe conversational analytics platform with typed dataframe plans, SQL AST validation, profiling, transparent insights, React/FastAPI, deterministic demo mode, tests, evaluation, and Docker.

## LinkedIn post

I built Asteria Analyst AI to explore a question I care about: how can conversational analytics stay useful without turning an LLM into an unrestricted code runner? The answer is a visible typed plan, independent validation, registered operations, read-only SQL controls, grounded result contracts, and reproducible evaluation. The project includes a polished React workspace, FastAPI backend, synthetic retail data, Docker/CI, and explicit limitations. No fabricated client or production claims—just an inspectable engineering POC.

## Resume bullets

- Engineered a React/FastAPI conversational analytics POC that converts natural-language questions into validated typed plans and evidence-backed result contracts.
- Designed independent SQL AST and dataframe DSL safety layers that reject write operations, unknown tables/columns, multi-statements, arbitrary operators, and unbounded results.
- Delivered deterministic synthetic retail data, JWT/RBAC ownership controls, audit metrics, Docker/Alembic/CI, automated tests, and a 44-case adversarial evaluation manifest.

Suggested topics: `conversational-analytics`, `ai-agent`, `fastapi`, `react`, `data-engineering`, `sql-safety`, `pandas`, `llm-evaluation`, `postgresql`, `docker`.

## Screenshot checklist

- 1440×900 login; overview; upload progress; populated sources; profile metrics; schema quality table; analysis empty state; completed bar/table result; validated plan; ambiguity response; dashboards; admin metrics.
- Use generated sample data, keep browser zoom at 100%, hide personal bookmarks/notifications, ensure no secrets or local absolute paths appear, and add short captions identifying the safety control shown.

## Recording plan

1. Reset local runtime and generate sample data.
2. Start Docker Compose and wait for all health checks.
3. Pre-upload `orders.csv`; keep a second small CSV ready for live upload.
4. Record 1080p/30fps with a clean browser profile and visible cursor.
5. Follow the two-minute script, pausing after each important result.
6. Capture narration separately if background noise is present; do not accelerate safety explanations.
7. End on the architecture diagram and repository test output.
8. Verify no token, `.env`, personal path, notification, or real data is visible before publishing.

