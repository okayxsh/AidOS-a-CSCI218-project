# Final demo runbook (live online demonstration + viva)

Builds on [`demo-runbook.md`](demo-runbook.md) and [`../simulation/demo-scenarios.md`](../simulation/demo-scenarios.md). Every observed value below was produced by the running engine (v0.4.0) on 13 Nov 2026, through the dashboard and through the API. All data is synthetic.

The guidelines set no time limit. The durations below are suggestions only (about 12–15 minutes in total, then individual viva questions).

## Before the demo

**Start (two terminals, about 20 minutes before):**

```bash
# Terminal 1, from apps/api/   (one worker, and no --reload: sessions live in memory)
uv sync
uv run uvicorn aidos.main:app --port 8000

# Terminal 2, from apps/web/
npm ci          # first time only
npm run dev     # Vite on http://localhost:5173
```

**Health and pre-flight checks.** These were run on 13 Nov 2026, with the results shown:

| Check | Command | Result recorded |
|---|---|---|
| Backend health | `curl http://127.0.0.1:8000/api/health` | `{"status":"ok","version":"0.4.0","engine_stage":4,...}`, with 4 policies all `available: true` |
| Frontend up | `curl -o /dev/null -w "%{http_code}" http://localhost:5173/` | `200` |
| Scenarios listed | `curl http://127.0.0.1:8000/api/scenarios` | 9 scenarios, including `triage-demo-001` |
| Scenario loads | `curl http://127.0.0.1:8000/api/scenarios/triage-demo-001` | stock 330, requested 560, shortfall 230, 3 zones, `synthetic: true` |
| Allocation works | `POST /api/allocations/compare` with that scenario and all 4 policies | FCFS and greedy COMPLETE; AidOS and balanced OPTIMAL; validator valid for all 4 |
| Simulation works | `POST /api/simulation/sessions`, then `/start`, then `/events` (Zone B severity 9) | 201 READY, then ACTIVE; explanation "Zone B urgency 62.5 → 79.2 (high → critical)" |
| Replay works | `POST …/replay` with the session's own events | all outcome hashes match; export → `POST /api/simulation/import` gives `matches: true` |
| Demo script imports | `POST /api/simulation/import` with `data/simulations/triage-demo-escalation.json` | 201, `matches: true`, ACTIVE, 3 events |
| Evaluation artifacts load | `curl http://127.0.0.1:8000/api/evaluation/runs` | `extended-20261112T100136Z` (504 scenarios, 0 failures) and `standard-20261112T100617Z`, both complete |
| All in one | `python scripts/smoke_test.py` (from the repository root) | ends with `smoke test passed` |

**Pre-flight checklist:**

- [ ] Both terminals are running, and `smoke test passed` appears.
- [ ] The sidebar footer on `/dashboard` reads "Engine online · v0.4.0".
- [ ] These tabs are open: `/`, `/dashboard?scenario=triage-demo-001`, `/dashboard/allocate?scenario=triage-demo-001`, `/dashboard/simulate?scenario=triage-demo-001` (no `session=` in the URL), and `/dashboard/evaluate`.
- [ ] The browser zoom is 100%, notifications are off, and only the browser window is shared.
- [ ] The folder `docs/report/figures/screenshots/` is open in a file viewer as the fallback.

## Part 1: Introduction (about 1 min)

- **Screen:** the landing page `/` (screenshot `s01_landing.png`).
- **Clicks:** none, or scroll a little into the story. Then click **Launch Dashboard**.
- **Observed:** a static hero headline. The tagline reads "CSCI218 student prototype · synthetic scenarios only · not a real dispatch system". A preview window shows `triage-demo-001` (3 zones, 330 in stock, 560 requested).
- **Say:**
  - The problem: there are fewer relief supplies than requests, and someone must decide who gets what.
  - AidOS combines fuzzy urgency scoring with a CP-SAT allocator, and compares them with FCFS and urgency greedy.
  - It is an academic simulator on synthetic data, not a dispatch system.

## Part 2: Dashboard, scenarios and inventory (about 1.5 min)

- **Screen:** Overview `/dashboard?scenario=triage-demo-001` (`s02_overview.png`), then Resource inventory (`s09_inventory.png`).
- **Clicks:** the scenario picker in the top bar shows "Three-zone shortage · triage-demo-001". Then open **Emergency scenarios** briefly (the 9 fixtures), then **Resource inventory**.
- **Observed:**
  - The tiles read 3 zones, 330 in stock, 560 requested, 230 shortfall, "Shortage".
  - Medical 90/150, water 180/290, shelter 60/120.
  - Zone urgencies: A 87.5 critical, B 62.5 high, C 70.8 high.
  - The inventory bars show the teal "in stock" marker: everything past it cannot be served by any policy.
  - The "Synthetic data" badge and "Validated by engine" are visible.
- **Say:**
  - Every number comes from the backend engine. The frontend has no allocation logic.
  - Resources never substitute for one another; each one is a separate limit.
  - Ratings are simulated inputs from 0 to 10, not triage grades.

## Part 3: Allocation, four policies (about 2.5 min)

- **Screen:** Allocation results `/dashboard/allocate?scenario=triage-demo-001` (`s04_allocation.png`, `s05_comparison.png`).
- **Clicks:** **Run allocation**. Then click the policy tabs in turn: **First come, first served**, **Urgency greedy**, **AidOS (fuzzy + CP-SAT)**, **AidOS balanced (coverage floor)**. Then scroll to **Baseline comparison**.
- **Observed on `triage-demo-001`:**

| | FCFS | Urgency greedy | AidOS | AidOS balanced |
|---|---|---|---|---|
| Status | COMPLETE | COMPLETE | OPTIMAL | OPTIMAL |
| Serve order | A, B, C (arrival) | A, C, B (urgency) | A, C, B | A, C, B |
| Units allocated / unmet | 330 / 230 | 330 / 230 | 330 / 230 | 330 / 230 |
| Urgency-weighted coverage | 62.5% | 64.6% | 64.6% | 63.6% |
| Lowest zone coverage | 0% (Zone C gets nothing) | 8.9% | 8.9% | 25.8% |
| Jain index | 0.616 | 0.722 | 0.722 | 0.804 |
| Coverage A / B / C | 100 / 55.6 / 0% | 100 / 8.9 / 80.8% | 100 / 8.9 / 80.8% | 97.6 / 25.8 / 55.4% |

- **Also observed:**
  - AidOS cells: A 75/100/30, C 15/60/30, B 0/20/0.
  - Balanced cells: A 70/100/30, B 12/33/13, C 8/47/17.
  - Constraint checks read 5/5.
  - Status OPTIMAL, in about 8–90 ms on the engine (the first run is slower).
- **Say:**
  - Stock is fixed and every policy uses all of it. What differs is *who* receives it.
  - FCFS ignores urgency, so Zone C (high urgency, but last to arrive) gets nothing.
  - AidOS equals urgency greedy exactly. That is expected: the urgency-first objective is linear and separable, so its optimum is the greedy order. CP-SAT adds a proof of optimality, not a different plan.
  - Balanced first guarantees every zone up to 25% of its request, then follows urgency. It trades a little urgency-weighted coverage for equity.

## Part 4: Explainability (about 2 min)

- **Screen:** the same page. Scroll to **Fuzzy urgency** (`s03_urgency.png`); the **Explanation**, **Constraint validation** and **Solver diagnostics** panels are on the same page.
- **Clicks:** click a matrix cell (the default is Zone B · Medical kits). Expand **Memberships and all 4 fired rules** under Zone C.
- **Observed:**
  - Zone C scores 70.8. The rules that fired:

    | Rule | Strength | Points |
    |---|---|---|
    | R26 | 0.44 × 87.5 | +38.9 |
    | R17 | 0.22 × 62.5 | +13.9 |
    | R23 | 0.22 × 62.5 | +13.9 |
    | R14 | 0.11 × 37.5 | +4.2 |

  - Its memberships: severity 7 → medium 0.33 / high 0.67; vulnerability 5 → medium 1.00.
  - The method label reads `sugeno-0-product-weighted-average · rules v1.0`.
  - The explanation for Zone B medical kits reads "Stock exhausted… Zones with higher urgency (Zone A, Zone C) received 90 units".
  - The validator lists whole units, no negatives, never above a request, never above stock, one cell per zone and resource: all Pass.
  - The solver shows two phases (urgency objective, then the earlier-arrival tie-break), both OPTIMAL.
- **Say:**
  - The model is zero-order Sugeno: each fired rule adds strength × a constant. The contributions sum to the score, so the score is fully traceable.
  - Fuzzy scores only weight zones. They never relax a hard limit: integer units, `0 ≤ x ≤ d`, `Σ x ≤ S` per resource.
  - An independent validator re-checks every plan; it does not trust the solver's own status.

## Part 5: Simulation (about 3 min)

- **Screen:** Simulation `/dashboard/simulate?scenario=triage-demo-001` (`s07_sim_before_after.png`, `s06_simulation.png`).
- **Clicks:** keep "Recommendation: AidOS (urgency first)", then **Load into simulator**, then **Start**. Then use **Apply an event**:
  1. **Escalate or ease urgency.** Zone B, Severity 6 → 9. Click **Apply event**.
     - **Observed:** B 62.5 → 79.2 (high → critical); the order becomes A, B, C.
     - AidOS moves C's 15/60/30 to B (B gets 15/80/30, C gets 0).
     - "Allocations changed": AidOS 6, FCFS 0, with "FCFS: no allocation changed" (it ignores urgency).
  2. **New emergency zone.** Zone id `zone-d`, Name "Zone D · Riverside clinic", Severity 8, Vulnerability 9, Time criticality 9, requesting 40 medical, 50 water and 10 shelter. Click **Apply event**.
     - **Observed:** D is critical at 87.5 and ranks 2nd. Requested 560 → 660.
     - AidOS gives D 15/50/10, taken from B (B now 0/30/20).
     - "FCFS on the same state did not change": D arrived last.
  3. **Supply lost or disrupted.** Medical kits, Units lost 30. Click **Apply event**.
     - **Observed:** medical stock 90 → 60. AidOS: A medical 75 → 60, D medical 15 → 0.
     - Allocated 330 → 300; unmet 330 → 360.
     - FCFS also changed 2 cells.
- **Optional:** set Event to "Dispatch the recommended plan", then click **Dispatch plan**.
  - **Observed through the API, on a fresh session with no events:** 330 units dispatched, stock 0, requests 560 → 230.
  - After the three events above, the Stage 5 audit's UI run (`frontend-audit.md`, journey C) dispatched 300 units: stock fell to 0 and requests to 360.
  - A second dispatch of the same plan is rejected (`stale_plan`, 409).
- **Point at:** "Why the plan changed" (the engine's own sentences), "Before and after" (urgency, rank, AidOS next to FCFS, changed cells), the **Event timeline** (each step has a snapshot and outcome hash) and "Dispatch ledger: Nothing dispatched".
- **Say:**
  - Every event triggers an atomic recomputation: rescore urgency, re-run all four policies, re-validate, explain the difference.
  - Candidate plans never consume stock. Only a dispatch does, and only once.
  - **Replay** reproduces every outcome hash, so the simulation is deterministic.
  - Caveat: a late zone gets served by AidOS only because it is urgent. A low-urgency late zone would also get nothing.

## Part 6: Evaluation (about 2 min)

- **Screen:** `/dashboard/evaluate` (`s08_evaluation.png`).
- **Clicks:** none needed. The evaluation run defaults to `extended-20261112T100136Z · 504 scenarios · complete`. Scroll to **Paired comparisons** and **What these results do and do not show**.
- **Observed:**
  - 504 static scenarios, 2,016 policy runs, 60 event scripts, 240 dispatch trajectories, 0 failures.
  - "AidOS and Urgency greedy produced the identical allocation in 504 of 504 scenarios."
  - Urgency-weighted coverage: FCFS 66.3%, greedy and AidOS 76.5%, balanced 73.4%.
  - Lowest zone coverage: 18.6%, 18.0%, 18.0% and 36.0%. Starved-zone share: balanced 0.0%, versus 13.3–13.5% for the others.
  - Jain index: 0.737, 0.735, 0.735 and 0.860.
  - Runtime median: 0.11 ms for the heuristics, 12.1 ms for AidOS and 16.0 ms for balanced.
- **Say:**
  - AidOS beats FCFS on urgency-weighted and critical-zone coverage, but those metrics are *objective-aligned*: optimisation success, not independent evidence.
  - On the external equity measures, AidOS and FCFS show no clear difference (the confidence intervals sit around 0).
  - AidOS equals greedy in all 504 static scenarios, which is proven and observed. Balanced is the only policy that improves equity: it removes starvation, at a cost of about 3 percentage points of urgency-weighted coverage.

## Part 7: Limitations (about 1 min)

- **Screen:** the **What these results do and do not show** panel on Evaluate.
- **Say:**
  - Synthetic data only. The urgency model and the rule base are our own assumptions, not validated triage.
  - No claim of humanitarian benefit, and no deployment. "Optimal" means optimal for the stated objective only.
  - There is no transport, routing or time dimension within a step, and resources do not substitute for each other.
  - CP-SAT costs about 100× the heuristics for the same urgency-first plan. That is still fine for interactive use (up to 50 zones).

## Reset procedure (between rehearsals, or before the real run)

1. **On Simulate:** click **Reset**. The session returns to READY with 0 events and an empty ledger. Or remove `&session=…` from the URL and reload to get the "Load into simulator" panel again.
2. **On Allocate:** reload the page. The plan clears ("No plan computed for this snapshot yet"). Plans are never stored, and nothing is consumed.
3. **Scenario:** re-select "Three-zone shortage · triage-demo-001" in the top-bar picker, or open the URLs with `?scenario=triage-demo-001`.
4. **Full reset:** stop and restart the engine (Ctrl+C, then the same start command). All in-memory sessions are dropped; scenario fixtures and evaluation runs are files, so they are unaffected.

## Troubleshooting and fallbacks

Fallbacks never use fake API responses. The only fallbacks are restarting the engine, the prepared screenshots in `docs/report/figures/screenshots/`, and the evaluation figures in `docs/evaluation/figures/`.

| Problem | What you see | Do this |
|---|---|---|
| Backend unavailable | Sidebar "Engine offline"; the dashboard shows "The AidOS engine is not running" with the start command. The landing page still works. | Restart the engine in terminal 1. Click retry, or reload. Meanwhile narrate over `s02`–`s05`. |
| Session expired, or 404 after an engine restart | "That simulation session no longer exists" with **Start a new session**. The API returns `session_not_found` (404). | Click **Start a new session**, or **Load demo script**: it imports `triage-demo-escalation.json` (3 events) and verifies the hashes (`matches: true`). |
| Browser refresh mid-simulation | The `?session=` URL parameter reopens the same session ("Reopening the session…"). | Nothing to do while the engine is up. If the engine was restarted, see the row above. |
| Version conflict (two tabs, or a double click) | An error message; the API returns `version_conflict` (409). | Reload the tab so it picks up the latest session version, then continue. |
| Internet instability | The demo runs entirely on localhost; only the screen share needs the internet. | Keep going locally. If the share drops, rejoin and resume from the current screen. Have a teammate ready to share the screenshots. |
| WebGL failure on the landing page | The hero is static SVG and does not need WebGL. The 3D story scene falls back to an SVG poster automatically (`NetworkPoster`), and all content stays in the text. | Nothing to do. The dashboard does not use WebGL. |
| Demo scenario inconsistency (numbers differ from this runbook) | The tiles differ from the tables above. | Check the scenario id in the top bar, and that `?session=` is absent or new. Run `python scripts/smoke_test.py`. If the fixture or engine changed, say so; do not quote these numbers. |
| Laptop failure | — | A teammate presents the screenshots below and the figures in `docs/evaluation/figures/`. |

## Backup material to prepare

Captured on 13 Nov 2026 in `docs/report/figures/screenshots/`:

| File | Shows |
|---|---|
| `s01_landing.png` | The landing hero |
| `s02_overview.png` | The Overview on `triage-demo-001` |
| `s03_urgency.png` | Fuzzy urgency: rules, contributions, Zone C memberships |
| `s04_allocation.png` | The AidOS matrix, tiles (OPTIMAL, 5/5) and the cell explanation |
| `s05_comparison.png` | The four-policy baseline comparison |
| `s06_simulation.png` | Simulate after the escalation, new-zone and supply-loss events (the timeline) |
| `s07_sim_before_after.png` | The before/after diff for the Zone B escalation (FCFS unchanged) |
| `s08_evaluation.png` | Evaluate: the extended run and the policy comparison table |
| `s09_inventory.png` | The Resource inventory |

Still to prepare (the team):

- [ ] A 3–4 minute screen recording of Parts 3–5 (Allocate run, three events, Replay), as an MP4 kept offline.
- [ ] A screenshot of the Replay result (all hashes match) and one after a dispatch (the ledger filled).
- [ ] A screenshot of the Evaluate **Paired comparisons** and **Limitations** panels.
- [ ] Copies of `docs/evaluation/figures/` on the presenting laptop.

## Do not say

- "AidOS is fairer" or "better", without qualification.
- "Optimal", in a humanitarian sense.
- "Saves lives", "deployed", or "validated by" any organisation.
- Any number you have not just shown on screen or in the saved run.
