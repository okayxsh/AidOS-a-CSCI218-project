# Demo scenarios

All scenarios are synthetic (`data/scenarios/`, `"synthetic": true`). Behaviour noted below was produced by running the engine (0.3.0); it is what the dashboard shows for these inputs, not a claim about real crises.

## The live demonstration

**Scenario: `triage-demo-001`** (the dashboard default). **Script: `data/simulations/triage-demo-escalation.json`.**

| # | Action | What to point at |
|---|---|---|
| 1 | Open the Simulation page, create a session, Start | Step 0: AidOS serves A, C, B by urgency; FCFS serves A, B and leaves C with nothing |
| 2 | Event: Zone B severity 6 → 9 | B 62.5 → 79.2 (critical); B now outranks C; C's units move to B. FCFS does not move |
| 3 | Event: add Zone D (8, 9, 9; 40·50·10) | D is critical but arrives last: AidOS serves it after A, FCFS gives it nothing |
| 4 | Event: lose 30 medical kits | Medical stock 90 → 60; A's kits 75 → 60; D's kits 15 → 0; unmet 330 → 360 |
| 5 | Reset | Back to step 0, history and ledger cleared |
| 6 | Replay (or load the demo script) | Every step's outcome hash matches the original run |
| 7 | Optional: Dispatch the recommended plan | Stock and open requests drop once; a second dispatch of the same plan is rejected as stale |

The full step-by-step numbers are in `events.md` ("Executed example").

## Scenario catalogue

| Scenario | Purpose | Suggested event | Observed result |
|---|---|---|---|
| `triage-demo-001` | Default demo: 3 zones, 3 resources, every resource short | Zone B severity → 9 | AidOS moves C's share to B; FCFS unchanged |
| `medical-escalation-006` | Medical kits and shelter short; Zone C starts least urgent (31.9) | Zone C severity → 10, time criticality → 9 | C 31.9 → 87.5, ranks first; C's medical kits 5 → 35, B's 25 → 0; FCFS unchanged |
| `supply-arrival-007` | Water (110 short) and medical kits (15 short) | 110 water packs arrive | water now covers every request; B water 0 → 70, C 40 → 80; unmet 125 → 15 |
| `severe-shortage-008` | 5 zones, 4 resources, stock about a third of requests (330 of 930) | 40 medical kits arrive | medical shortfall 95 → 55; A's kits 0 → 20, D's 15 → 35; allocated 330 → 370; FCFS changes 3 cells |
| `competing-emergency-009` | Stock covers the 3 active zones exactly; a critical Zone D (9, 9, 10) is scheduled for step 1 | Advance time | D appears and ranks first; AidOS gives it 45·60·20, taken from A and C; FCFS serves it last and gives it nothing |
| `no-scarcity` | Stock covers every request | Lose 20 medical kits, then 100 more | first loss: plan unchanged ("stock covers every request before and after"); second: medical becomes 15 short and C's kits drop 25 → 10 |
| `zero-stock` | Empty depot | A dispatch first, then 30 medical kits arrive | the dispatch is rejected (the plan dispatches no units); after the shipment A gets 20 kits, C 10, B none |
| `late-critical-arrival` | Most critical zone arrives last | Zone D resolved | its 240 open units leave the problem; stock then covers every remaining request; unmet 165 → 0 |
| `coastal-storm-005` | 6 zones, 4 resources; Zone F scheduled for step 1 | Advance time | Zone F (87.5) ranks third; AidOS gives it 25·50·15·30, taken from A and D; FCFS does not change (F arrives last) |

The four Stage 3 fixtures (`-006` to `-009`) were added for the simulator; the five earlier fixtures are unchanged.
