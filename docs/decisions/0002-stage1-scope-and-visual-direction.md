# 0002 — Stage 1 scope and visual direction

- **Status:** Chosen in the 10 Nov 2026 build session; team review pending
- **Date:** 2026-11-10

## Context

The Stage 1 brief asked for a frontend-only build with mock data, while the spec (Section 9) and `CLAUDE.md` define Stage 1 as a vertical slice in which dashboard numbers come from a real backend. The brief also asked for a premium visual identity and supplied a reference image of a dark emergency-AI landing page.

## Decision

1. **Scope:** build the frontend plus a minimal real backend: scenario schema and fixtures, `GET /api/health`, `GET /api/scenarios`, `GET /api/scenarios/{id}` (with a backend-computed summary) and `POST /api/allocations/compare` for the FCFS baseline. Fuzzy scoring, CP-SAT and urgency-greedy remain Stage 2 and return 501 if requested.
2. **No dashboard mock layer:** the dashboard renders only engine responses. The landing page alone reads the demo fixture directly so it renders without the backend.
3. **Visual direction "Aurora Ridge":** dark night-navy world, subtle aurora, a fictional relief-operations ridge, centred sans headline with an italic serif accent, pill CTAs, dashboard window rising from the hero. Chosen by the user from three directions derived from their reference.
4. **Fonts self-hosted** (Mona Sans, Instrument Serif, JetBrains Mono via `@fontsource`) so a lab demo works offline.

## Consequences

- The dashboard needs the engine running; it shows a clear error state otherwise.
- Landing illustration numbers can only drift from the engine if the fixture's format changes; both read the same file.
- New dependencies: `@fontsource-variable/mona-sans`, `@fontsource/instrument-serif`, `@fontsource-variable/jetbrains-mono`; dev: `vitest`, `jsdom`, `@testing-library/react`, `@testing-library/dom`.
