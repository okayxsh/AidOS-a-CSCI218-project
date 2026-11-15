# AGENTS.md — instructions for Codex

**Canonical specification: [`AidOS project info.md`](AidOS%20project%20info.md).** Read it, along with the source and tests related to your task, before making changes. If anything here conflicts with it, the spec wins.

## Role

Codex handles **small, clearly scoped tasks**: targeted unit tests, type or lint fixes, accessibility and responsive-layout improvements, API error states, benchmark plotting, documentation cleanup, rubric checks, and code review with concrete file and line references.

**Claude Code owns the architecture and the core engine:** the domain models, fuzzy system, CP-SAT solver, baselines, simulation FSM and API design. Do not change these without an explicit assignment.

## Working rules

- Work on one assigned issue and file set, on its own branch or worktree. Never edit files that another agent is changing at the same time.
- Make the smallest patch that meets the acceptance criteria. Do not refactor beyond the scope.
- The frontend never implements allocation or scoring logic; it only calls the backend API.
- Never fabricate data, results, screenshots or contributions. Use synthetic data only.
- Do not commit or push unless you are instructed to.

## Commands

- Backend (from `apps/api/`): `uv sync`, `uv run pytest`, `uv run ruff check ../..`
- Frontend (from `apps/web/`): `npm ci`, `npm run typecheck`, `npm run lint`, `npm run format:check`, `npm run build`

## Report back

Report the files changed, the checks you ran with their output, and any remaining limitations.
