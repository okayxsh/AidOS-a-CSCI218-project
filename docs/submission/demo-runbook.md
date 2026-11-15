# Live demonstration runbook

> **Superseded by [`docs/submission/final-demo-runbook.md`](final-demo-runbook.md)** (Stage 6, with pre-flight checks actually run). The guidelines set no demo time limit, so any time budget below is only a suggestion.

**Time budget:** about 10 minutes for the system, then questions. Rubric criterion 6: "runs live and reliably, shows its key AI behaviours, well organised, within time".

The scenarios below were chosen because they show **genuine behavioural differences**. They are not representative of every case. Say so if asked: on average, AidOS does *not* improve the worst-off zone over FCFS (`docs/evaluation/results.md`).

## Before the session (15 minutes earlier)

1. **Start the engine.** From `apps/api/`: `uv sync`, then `uv run uvicorn aidos.main:app --port 8000`. Use one worker; sessions live in memory.
2. **Start the web app.** From `apps/web/`: `npm ci` (first time only), then `npm run dev`, then open <http://localhost:5173/>.
3. **Run the smoke test.** From the repository root: `python scripts/smoke_test.py`. It must end with "smoke test passed". It exercises all fixtures, all four policies, the full simulation demo with reset, replay and import, and the evaluation API.
4. Open these tabs: the landing page; `/dashboard/allocate?scenario=triage-demo-001`; `/dashboard/simulate?scenario=triage-demo-001`; `/dashboard/evaluate`.
5. Have this repository's `docs/evaluation/figures/` folder open as a backup.

## Sequence

| # | Show | Say (and what to point at) |
|---|---|---|
| 1 | Landing hero, then scroll the story to "First, how urgent is each zone?" | The problem: three zones request 560 units, the depot holds 330. Labels say Built, or Illustration where something is an example. Synthetic data only. |
| 2 | Launch Dashboard → Allocate, Run allocation | Four policies on one snapshot. Every policy hands out all 330 units; who receives them differs. |
| 3 | Fuzzy urgency panel, Zone C | 70.8 "high"; four rules, contributions add to the score. Rules are readable sentences. |
| 4 | Matrix: FCFS vs AidOS (policy switcher) | FCFS gives Zone C nothing (it arrived last); AidOS serves A, then C, then B by urgency. |
| 5 | Comparison table | AidOS equals urgency greedy exactly (the proof is a viva topic). Balanced gives every zone at least 25%, at a small cost in urgency-weighted coverage. |
| 6 | Validation checklist and solver panel | The independent validator passes every check; CP-SAT reports OPTIMAL, with two phases. |
| 7 | Simulate: Load into simulator, Start | Candidate plans never consume stock. |
| 8 | Event: Zone B severity 6 → 9 | B 62.5 → 79.2; B now outranks C; AidOS moves C's share to B; **FCFS does not change** (it ignores urgency). Read the engine's explanation aloud. |
| 9 | Event: add Zone D (8, 9, 9; 40 · 50 · 10) | A critical late arrival: AidOS serves it after A; FCFS gives it nothing. Caveat: if the new zone were low-urgency, AidOS would also give it nothing (Stage 5 controlled experiment). |
| 10 | Event: lose 30 medical kits | Stock 90 → 60; A's kits 75 → 60; D's 15 → 0. |
| 11 | Dispatch the recommended plan | Stock and requests drop once; the ledger records it. A second identical dispatch is rejected as stale. |
| 12 | Reset, then Replay | Every outcome hash matches the original run: deterministic replay. |
| 13 | Evaluate page | The 504-scenario benchmark. Objective-aligned vs external metrics. "No clear difference" on equity for AidOS vs FCFS. Balanced removes starvation. |
| 14 | Limitations panel | Synthetic; urgency model is an assumption; no humanitarian effectiveness claimed. |

## If something fails

| Problem | Fallback |
|---|---|
| Engine not reachable | The dashboard shows "engine not running" with the start command. Restart it. The landing page works without it. |
| A simulation session has vanished (engine restarted) | "Start a new session", or "Load demo script": it imports `data/simulations/triage-demo-escalation.json` and verifies it. |
| WebGL is unavailable on the presentation machine | The story shows its SVG fallback automatically; all content is in the text. |
| Network or laptop failure | Show the figures in `docs/evaluation/figures/` and the screenshots in `docs/submission/` (to be captured by the team before the demo). |
| A question about a number | Every number is traceable: dashboard → API → `experiments/results/<run>/summary.json` → CSV. |

## Do not say

- "AidOS is fairer" or "better", without qualification.
- "Optimal allocation", in a humanitarian sense. It is optimal only for the stated objective.
- "Saves lives", "deployed", or "validated by Dubai Humanitarian".
- That the instructor approved the Sugeno choice (pending).
