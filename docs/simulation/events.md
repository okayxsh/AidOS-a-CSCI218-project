# Crisis events and inventory accounting

Schema: `apps/api/aidos/simulation/events.py`. Application: `reducer.py`. Comparison and explanations: `compare.py`.

## Event types

All events are sent as `{"type": "...", ...}` inside `POST /api/simulation/sessions/{id}/events` with the session's `expected_version`. Unknown fields are rejected.

| Type | Fields | Effect | Rejected when |
|---|---|---|---|
| `zone_added` | `zone: {id, name, severity, vulnerability, time_criticality, population?, demand}` | A new zone joins, active immediately, with `arrival_order` after every existing (and previously resolved) zone. | id already used (now or before); unknown resource; ratings outside 0–10; more than 50 zones |
| `urgency_changed` | `zone_id`, any of `severity`, `vulnerability`, `time_criticality` (new values, 0–10) | Sets the given ratings, e.g. a severity escalation. | unknown zone; no rating given; every given rating equals the current one |
| `supply_arrived` | `resource_id`, `quantity ≥ 1` | Stock rises by `quantity`. | unknown resource |
| `supply_lost` | `resource_id`, `quantity ≥ 1` | Stock falls by `quantity`. | unknown resource; `quantity` > current stock (stock never goes negative; it is rejected, not clipped) |
| `request_updated` | `zone_id`, `resource_id`, `quantity ≥ 0` (the new total request) | Sets the zone's request; 0 withdraws it. | unknown zone or resource; no change |
| `zone_resolved` | `zone_id` | The zone leaves the allocation problem; its open requests are dropped. | unknown zone; it is the last zone |
| `time_advanced` | — | The scenario clock moves one step; zones whose `activation_step` equals the new step become active. | — |
| `plan_committed` | `policy` (default `aidos`), `expected_snapshot_hash` | Dispatches that policy's current plan (see below). | hash differs from the current snapshot (`stale_plan`); no plan; the plan dispatches nothing |

Only `time_advanced` moves the scenario clock (`sim_step`). The event sequence number (`seq`) counts every accepted event. A zone added during the run is active from the step it is added.

Absolute values (`urgency_changed`, `request_updated`) were chosen over deltas so that an event says exactly what the new state is, and replaying it cannot drift.

## Inventory and allocation semantics

The simulator separates **recommended** plans from **dispatched** units.

**Recommendations (every step, never consume anything).**

- After each event, all four policies compute a candidate plan on the new snapshot.
- Computing, recomputing or replaying plans never changes stock or requests. The same state always gives the same plans (a test re-evaluates a state three times and compares).
- A new recommendation replaces the previous one; nothing accumulates.
- Requests are not reduced because a plan recommends units for them.

**Dispatch (only through `plan_committed`).**

- The event names the policy and the snapshot hash the plan was computed for. If the hash is not the current one, nothing happens (`stale_plan`, HTTP 409).
- On success, for every cell of that plan: stock of the resource falls by the units, and the zone's open request falls by the same units. The validated plan guarantees neither goes negative; the reducer checks again.
- A ledger entry records the step, event ID, policy, the snapshot hash and every dispatched cell. The ledger is append-only.
- Because dispatch changes the snapshot, committing the same plan twice is impossible: the second attempt names an old hash and is rejected. The specification's "never double-consumes stock" gate rests on this.
- After a dispatch, the next recommendation only covers what is still open with what is still in stock.

**Resolution (`zone_resolved`).** The zone and its open requests leave the problem. Units already dispatched to it stay dispatched: they are **not** returned to the depot, and the ledger keeps them. The zone ID cannot be reused.

**Supply events** are the only other way stock changes.

## What is recomputed, and when

| After | Fuzzy scores | Plans (all policies) | Validation | Diff and explanation |
|---|---|---|---|---|
| any accepted event | recomputed for every zone | recomputed | every plan | previous step → new step |
| pause, resume, complete | no change | no change | — | — |
| reset | restored step 0 | restored step 0 | — | none |

Scores are recomputed for every zone after every event, not only the zone an event names; ratings that did not change give the same score, because the engine is deterministic.

## Explanations

For each step the engine compares it with the previous one (`compare.diff_steps`) and builds the explanation only from the two stored steps:

1. the input changes the reducer recorded (e.g. `Zone B severity 6 → 9.`);
2. every zone whose urgency changed, appeared or left (score and category before and after); if a rating changed but the score did not, that is stated;
3. the urgency order before and after, or that it is unchanged;
4. each resource whose stock or requests changed: its new shortfall, or that stock now covers every request;
5. the recommended plan: every changed cell (`Zone C medical kits 15 → 0`), or that **it did not change** with the reason that applies (order, stock and requests unchanged; stock covers everything; or "the changed inputs do not alter which zones the stock reaches");
6. totals before and after: units allocated, unmet units, urgency-weighted coverage;
7. FCFS on the same state: how many of its cells changed, or that it did not change (and, for rating-only events, that it ignores urgency);
8. units dispatched, if any.

A priority change is never assumed to move the plan: in the triage demo, Zone B's escalation does change the plan, but an escalation of a zone that already ranks first, or one that stays below the same zones, does not, and the explanation says so.

The diff is also returned as data (`urgency`, `order_before/after`, `resources`, `policies[].cells`) so the dashboard draws before/after values without computing anything.

## Executed example (`triage-demo-001`, demo script `data/simulations/triage-demo-escalation.json`)

Produced by the engine (0.3.0) and reproduced by every replay; outcome hashes in the file.

Starting stock: 90 medical kits, 180 water packs, 60 shelter kits. Allocations are medical · water · shelter.

| Step | Event | Urgency A / B / C / D | AidOS plan A | B | C | D | Allocated / unmet | FCFS plan A | B | C | D |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | initial | 87.5 / 62.5 / 70.8 / – | 75·100·30 | 0·20·0 | 15·60·30 | – | 330 / 230 | 75·100·30 | 15·80·30 | 0·0·0 | – |
| 1 | Zone B severity 6 → 9 | 87.5 / **79.2** / 70.8 / – | 75·100·30 | **15·80·30** | **0·0·0** | – | 330 / 230 | unchanged | | | |
| 2 | Zone D added (8, 9, 9; asks 40·50·10) | 87.5 / 79.2 / 70.8 / **87.5** | 75·100·30 | **0·30·20** | 0·0·0 | **15·50·10** | 330 / 330 | 75·100·30 | 15·80·30 | 0·0·0 | 0·0·0 |
| 3 | 30 medical kits lost (stock 60) | unchanged | **60**·100·30 | 0·30·20 | 0·0·0 | **0**·50·10 | 300 / 360 | **60**·100·30 | **0**·80·30 | 0·0·0 | 0·0·0 |

Reading it:

- **Step 1.** B's severity rises from 6 to 9; its urgency rises from 62.5 (high) to 79.2 (critical) and B now outranks C. AidOS moves C's 15 medical kits, 60 water packs and 30 shelter kits to B. FCFS does not change: it ignores urgency. After this step AidOS and FCFS happen to give the same plan, because the urgency order (A, B, C) now equals the arrival order.
- **Step 2.** Zone D arrives last but is critical (87.5, tied with A; A keeps priority by earlier arrival). AidOS gives D what remains after A, taking it from B. FCFS serves D last, so D gets nothing.
- **Step 3.** Losing 30 medical kits leaves 60: A (first by urgency) takes them all; D's 15 kits disappear. Remaining stock is 0 for every resource in every step: all policies hand out everything. The difference is who receives it.
- Urgency-weighted coverage of the AidOS plan: 0.646 → 0.619 → 0.530 → 0.481 (FCFS: 0.625 → 0.619 → 0.518 → 0.472). The metric is recomputed with each step's own scores, so it is not comparable across steps when scores change.

## Limitations

- Events are instantaneous. There are no deliveries in transit, travel times or delays (`SHIPMENT_DELAYED` from the specification is not implemented).
- Resources are fixed for a session; an event cannot add a new resource type.
- `urgency_changed` sets ratings directly; there is no model of how a crisis evolves on its own.
- Dispatch is a single, whole-plan operation; partial commits are not supported.
