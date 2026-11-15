# AidOS

**Explainable Emergency Resource Allocation Simulation** — CSCI218 Foundations of Artificial Intelligence, UOWD, Autumn 2026.

AidOS is an academic simulator that helps a *simulated* emergency coordinator decide how to distribute scarce relief supplies (medical kits, water, shelter, nutrition) among competing crisis zones. It combines **fuzzy urgency scoring** and **constraint-based allocation (OR-Tools CP-SAT)**, compares them against FCFS and urgency-greedy baselines, and is designed to add **finite-state crisis updates**.

> **Status: Stage 6 (report, demo and viva preparation).** The editable group report is [`docs/report/AidOS_Final_Group_Report.docx`](docs/report/) (PDF preview alongside), with its figures, an evidence map tracing every number to an artifact, and a reference verification log. The final demo runbook, viva question bank, reflection template, instructor confirmation request and final checklist are in [`docs/submission/`](docs/submission/). Team details in the report are placeholders for the team to complete.
>
> **Stage 5 (submission readiness).** Stage 5 adds an engineering and scientific audit: a proof and exhaustive check that the urgency-first CP-SAT plan equals urgency greedy ([`docs/algorithms/greedy-vs-cpsat-analysis.md`](docs/algorithms/greedy-vs-cpsat-analysis.md)); supplementary floor, fuzzy-sensitivity, controlled-dynamic and runtime experiments ([`docs/evaluation/stage5-supplementary.md`](docs/evaluation/stage5-supplementary.md)); a local git repository with versioned evidence and CI; and submission material in [`docs/submission/`](docs/submission/) (readiness audit, demo runbook, viva preparation, instructor review items).
>
> **Stage 4.** Stage 4 adds the evaluation framework: seven scenario families plus dynamic event scripts, a metric suite that separates objective-aligned from external measures, paired statistics with bootstrap confidence intervals, saved raw and summary results, report figures, and the Evaluation dashboard. Results are in [`docs/evaluation/`](docs/evaluation/); they describe behaviour on synthetic scenarios only.
>
> **Stage 3.** Built: the fuzzy urgency engine (zero-order Sugeno, 27 rules, full rule traces), the CP-SAT allocator (urgency-first and a balanced coverage-floor variant), the FCFS and urgency-greedy baselines, an independent constraint validator, the comparison API, the **crisis simulator** (state machine, eight event types, atomic recomputation, before/after explanations, dispatch ledger, deterministic replay and export/import), the dashboard that shows all of it, and a seeded experiment interface. Also the Stage 1.5 landing story with one 3D scene. **Not built yet:** the evaluation campaign with statistics (Stage 4). No claim is made that any policy is better than another; that needs the Stage 4 experiments. The simulator applies hypothetical events; it does not predict real crises.
>
> This is a student prototype that uses **synthetic data only**. It is not a real dispatch, medical or humanitarian decision system.

The full specification is in [`AidOS project info.md`](AidOS%20project%20info.md), and it overrides this README if the two disagree.

## Repository layout

```text
apps/api/     Python FastAPI backend + AI engine (aidos/domain, ai, simulation, evaluation)
apps/web/     React + TypeScript + Vite frontend (landing page "/" and dashboard "/dashboard")
data/         Synthetic scenario fixtures (see data/README.md)
experiments/  Scenario generator, benchmark runner, fuzzy-method comparison, results
tests/        Backend unit and integration tests (pytest)
docs/         Architecture, algorithm design, protocols, API contract, frontend, decisions, report
scripts/      Development utilities (smoke test, report asset export)
```

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.11 (3.11–3.12 supported) | Pinned in `apps/api/.python-version` |
| uv | 0.11+ | Python environment + lockfile manager ([install](https://docs.astral.sh/uv/getting-started/installation/)) |
| Node.js | 22.22+ or 24.15+ (LTS) | Vite needs 20.19+; the frontend test tools (Vitest 5, jsdom 31) need 22.22+ or 24.15+ |
| npm | 10+ | Ships with Node.js |

## Setup

```bash
# Optional: copy the environment template (no secrets are needed)
cp .env.example .env

# Backend: creates apps/api/.venv from uv.lock
cd apps/api
uv sync

# Frontend: installs exactly what package-lock.json lists
cd ../web
npm ci
```

## Run the app

Use two terminals.

```bash
# 1. Engine (FastAPI) on http://localhost:8000 — from apps/api/
uv run uvicorn aidos.main:app --reload --port 8000

# 2. Frontend (Vite) on http://localhost:5173 — from apps/web/
npm run dev
```

Open <http://localhost:5173/> for the landing page and <http://localhost:5173/dashboard> for the dashboard. The crisis simulator is at <http://localhost:5173/dashboard/simulate>; the live-demo walkthrough is in [`docs/simulation/demo-scenarios.md`](docs/simulation/demo-scenarios.md). Simulation sessions live in the engine's memory: restarting the engine ends them (export a session first to keep it). Run the engine with a single worker. The landing page works without the engine. The dashboard shows a clear "engine is not running" state until the engine starts; it never shows numbers the engine did not compute. Interactive API docs are at <http://localhost:8000/docs>.

The frontend reads the engine URL from `VITE_API_BASE_URL` (default `http://localhost:8000`), and the engine allows the origins in `AIDOS_CORS_ORIGINS` (default: the Vite dev and preview ports). See `.env.example`.

## Development commands

Backend (run from `apps/api/`):

```bash
uv run pytest           # tests in ../../tests (fuzzy, CP-SAT, pipeline, API)
uv run ruff check ../.. # lint
uv run ruff format ../..

# Stage 2 correctness smoke run: 25 scenarios x 4 policies -> experiments/results/stage2-smoke.{json,csv}
uv run python ../../experiments/run_benchmarks.py --smoke
# Stage 4 evaluation: writes experiments/results/<preset>-<UTC time>/ (never overwrites)
uv run python ../../experiments/run_benchmarks.py --preset extended      # about 3 minutes
uv run python ../../experiments/verify_results.py <run_id> --against <other_run_id>
uv run --group analysis python ../../experiments/plot_results.py <run_id>  # figures (needs matplotlib)
uv run python ../../experiments/report_results.py <run_id>                 # docs/evaluation/results-tables.md
# Reproduce the monotonicity measurement behind the fuzzy-method choice
uv run python ../../experiments/fuzzy_method_comparison.py
```

End-to-end smoke test against a running engine (from the repository root, standard library only). It scores every fixture, runs all four policies through the API and re-checks the hard constraints from the outside:

```bash
python scripts/smoke_test.py            # defaults to http://localhost:8000
```

Frontend (run from `apps/web/`):

```bash
npm run dev             # dev server on :5173
npm run typecheck
npm run lint
npm run format:check
npm test                # Vitest + Testing Library (navigation, scenario consistency, error states)
npm run build           # production build into dist/
npm run preview         # serve the production build on :4173
```

## Documentation

- [`docs/architecture.md`](docs/architecture.md): modules and request path as implemented
- [`docs/algorithms/allocation-formulation.md`](docs/algorithms/allocation-formulation.md): the allocation problem, constraints, objectives and a worked example
- [`docs/algorithms/fuzzy-logic.md`](docs/algorithms/fuzzy-logic.md): membership functions, the 27 rules, inference and a worked example
- [`docs/algorithms/cp-sat-allocation.md`](docs/algorithms/cp-sat-allocation.md): the solver, the decision pipeline, statuses, metrics and the experiment interface
- [`docs/simulation/state-machine.md`](docs/simulation/state-machine.md), [`events.md`](docs/simulation/events.md), [`replay.md`](docs/simulation/replay.md), [`demo-scenarios.md`](docs/simulation/demo-scenarios.md): the crisis simulator
- [`docs/evaluation/`](docs/evaluation/): policies, metric definitions, experimental protocol, results, scientific review, Stage 5 supplementary experiments
- [`docs/report/`](docs/report/): the group report (Word and PDF), figures, evidence map, reference verification log
- [`docs/submission/`](docs/submission/): final checklist, final demo runbook, viva question bank, reflection template, instructor confirmation request, readiness audit, git and reproducibility
- [`docs/api-contract.md`](docs/api-contract.md): endpoints, schemas and error shape
- [`docs/frontend.md`](docs/frontend.md): routes, components, data flow, design system
- [`data/README.md`](data/README.md): the synthetic scenario fixtures

## Academic scope

- Synthetic scenarios only, and every fixture declares `"synthetic": true`.
- Decisions stay with a human; AidOS only suggests them and does not control any real operation.
- No benchmark result or performance claim is made until real experiments produce it.
