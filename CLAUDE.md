# CLAUDE.md — instructions for Claude Code

**Canonical specification: [`AidOS project info.md`](AidOS%20project%20info.md).** Read it in full at the start of every session, and especially Sections 0, 4, 5, 7, 8, 10 and 11. If anything here conflicts with it, the spec wins. Flag the conflict explicitly instead of quietly reinterpreting it.

## Role

Claude Code is the **primary implementer**. It owns the architecture, the core domain, the fuzzy urgency engine, the CP-SAT allocator, the baselines, the simulation FSM, the API and the main frontend. Codex handles scoped fixes, tests and polish (see `AGENTS.md`).

## Current stage

**Stage 6 done, 13 Nov 2026.** Documentation only; no engine change. It added `docs/report/` (an editable Word report generated from `docs/report/source/` and then edited in Word, a PDF preview, figures with generators in `figures/src/`, `report-evidence-map.md` and `references-verification.md`), and in `docs/submission/`: `final-demo-runbook.md`, `viva-question-bank.md`, `final-checklist.md`, `reflection-template.md` and `instructor-confirmation-request.md`. Once the team edits the Word report, it is the master. Remaining work is human: completing the placeholders, real Git history, reflections, instructor confirmations and submission.

**Stage 5 done, 12 Nov 2026.** An audit and hardening stage, not a feature stage. It added the greedy/CP-SAT proof and checks, supplementary experiments (`experiments/{greedy_equivalence,floor_sweep,fuzzy_sensitivity,dynamic_controlled,runtime_benchmark}.py`, `evaluation/dynamic_controlled.py`, `evaluation/supplementary.py`), a local git repository (no commits; the team commits under their own identities), versioned evidence in `experiments/results/`, CI, and `docs/submission/`. The frozen Stage 4 runs must never be modified. 

**Stage 4 built, 12 Nov 2026.** Evaluation: `evaluation/families.py`, `stats.py`, `dynamic.py`, `analysis.py`, `campaign.py`, `artifacts.py`, `/api/evaluation` routes, the Evaluate page, `experiments/{run_benchmarks,verify_results,plot_results,report_results}.py`, and `docs/evaluation/`. Reported results come from the extended run in `experiments/results/`.

**Stage 3 built, 11 Nov 2026.** The crisis simulator: `simulation/fsm.py`, `events.py`, `reducer.py`, `session.py`, `compare.py`, `store.py`, the `/api/simulation` routes and the dashboard Simulate page (see `docs/simulation/` and `docs/decisions/0005-*`).

**Stage 2 built, 11 Nov 2026.** On top of Stage 1 and 1.5 (landing story, dashboard, fixtures, FCFS): the fuzzy urgency engine (`ai/fuzzy.py`, zero-order Sugeno, rules in `config/fuzzy_rules.json`), the CP-SAT allocator (`ai/constraints.py`, policies `aidos` and `aidos_balanced`), the urgency-greedy baseline, the independent validator (`evaluation/invariants.py`), the pipeline (`pipeline.py`), the urgency and comparison APIs, and the experiment interface (`evaluation/generator.py`, `runner.py`, `exports.py`). See `docs/algorithms/`, `docs/architecture.md`, `docs/api-contract.md` and `docs/decisions/0004-*`.

## Session start checklist

1. Read `AidOS project info.md`, `README.md` and `docs/architecture.md`.
2. Inspect the files you are about to change before you edit them.
3. State a short plan and the acceptance criteria.

## Layout and commands

- Backend: `apps/api/` (uv, Python 3.11, non-package project). Run `uv sync`, `uv run pytest`, `uv run ruff check ../..` from `apps/api/`. Tests live in the repo-root `tests/`.
- Frontend: `apps/web/` (React, TypeScript, Vite, React Router, Recharts, Lucide). Run `npm ci`, `npm run typecheck`, `npm run lint` and `npm run build` from `apps/web/`.
- Styling: plain CSS design tokens in `apps/web/src/styles/tokens.css`. No CSS framework.
- Env: the root `.env` file (template: `.env.example`). Vite reads `VITE_*` variables from the repo root.

## Non-negotiable rules

- **There is one canonical engine, in the backend.** `apps/web` never implements allocation or scoring logic.
- Domain and algorithm code runs without FastAPI, React or the network, and keeps no mutable global state. FastAPI only adapts input and output.
- Hard invariants: integer allocations, `0 <= x[z,r] <= d[z,r]`, `sum_z x[z,r] <= S[r]`, no substitution between resources, deterministic tie-breaks, and comparing plans never mutates the snapshot.
- The fuzzy logic and the solver are never mocked in final code. Report solver statuses truthfully.
- Every number shown in the dashboard comes from the backend. Never show placeholder metrics as if they were real.
- Never invent results, commits, approvals, endorsements or contributions. Use synthetic data only.
- Do not add auth, a database, cloud deployment, an LLM API, RL or GPU libraries unless the team approves it.
- Do not commit or push unless the user explicitly asks. Student contributors commit under their own identities.

## End of every session

Report: (1) the files changed, (2) the commands actually run and their results, (3) known gaps, (4) the next one or two tasks.
