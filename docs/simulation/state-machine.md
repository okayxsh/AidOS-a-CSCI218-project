# Simulation state machine and sessions

Code: `apps/api/aidos/simulation/fsm.py` (states and transitions), `session.py` (the engine), `store.py` (in-memory sessions). Tests: `tests/unit/test_fsm.py`, `tests/unit/test_simulation.py`, `tests/integration/test_simulation_api.py`.

**What the simulator is.** It applies *hypothetical* changes to a synthetic scenario (a new zone, an escalation, a lost shipment) and shows how the recommendations respond. It does not predict how a real disaster unfolds; nothing in it is fitted to real data, and every event is something a user (or a replay file) explicitly applies.

## States

```text
                  start                 pause
        READY ──────────────▶ ACTIVE ─────────────▶ PAUSED
          ▲                    │  ▲ │  ◀─────────────  │
          │                    │  │ │     resume       │
          │        apply_event │  │ │                  │
          │        (stays      └──┘ │ complete         │
          │         ACTIVE)         ▼                  │
          │                     COMPLETED              │
          │                         │                  │
          │       fail (engine      │                  │
          │       invariant broke)  │                  │
          │   ACTIVE ──────▶ ERROR  │                  │
          │                    │    │                  │
          └──── reset ─────────┴────┴──────────────────┘
               (from every state, including READY)
```

| State | Meaning | Allowed actions |
|---|---|---|
| `READY` | Scenario loaded; step 0 is scored and allocated. No event applied. | start, reset |
| `ACTIVE` | Accepts events. | pause, complete, reset, apply_event |
| `PAUSED` | Frozen: events are refused until resumed. There is no running clock, so pausing only locks the session against changes. | resume, reset |
| `COMPLETED` | The user ended the run. Read-only. | reset |
| `ERROR` | A computed plan failed the independent validator (an engine defect, never a user error). The event that caused it was **not** applied. Read-only. | reset |

The table in `fsm.py` (`TRANSITIONS`) is the only definition; every other (state, action) pair raises `InvalidTransitionError` (HTTP 409 `invalid_transition`). Reading a session, its history, any step, a diff or an export is allowed in every state.

**Reset** restores the initial snapshot and its stored step-0 result, and clears the history, the dispatch ledger, resolved zones and any error. Nothing stale survives it.

**Completion** is an explicit user action. The simulator has no built-in end condition, because there is no model of how a crisis ends; a session also refuses events beyond 200 (`too_many_events`).

**ERROR** is entered only through `fail`, when a plan computed after an event breaks a hard constraint according to `evaluation/invariants.py`. This should never happen; it exists so that a defect is reported and the session is locked, rather than a bad plan being stored. It is tested by forcing the validator to report a violation.

## How this relates to the specification's lifecycle

The specification (section 5.3) sketches a *plan* lifecycle: `DRAFT → READY → ALLOCATED → COMMITTED → UPDATED`, where an event makes the current plan stale until it is recomputed. The Stage 3 brief asked for the *session* lifecycle above. Both are covered:

| Specification | Implementation |
|---|---|
| `DRAFT` (editing) | events change the scenario inside an `ACTIVE` session |
| `READY` (validated snapshot) | every stored step is a validated snapshot; the session state `READY` is the loaded initial one |
| `ALLOCATED` (candidate, stock not consumed) | every step stores the candidate plans of all four policies; running them consumes nothing |
| `COMMITTED` (plan accepted, stock applied once) | the `plan_committed` event dispatches the recommendation once and records it in the ledger |
| `UPDATED` (event makes the plan stale) | an event immediately produces a new step with recomputed plans, so a stale plan is never shown; a commit that names an old snapshot is rejected as `stale_plan` |

## One step = one recomputation

Every accepted event runs the full pipeline on the new snapshot, in this order (`session.apply`):

1. Check the session state allows `apply_event`, and the 200-event limit.
2. Apply the event to a **copy** of the current scenario (`reducer.apply_event`), rejecting unknown zones or resources, negative stock and no-op changes.
3. Re-validate the whole copy with `parse_scenario`, the same validation fixtures go through.
4. Score every zone with the fuzzy engine (scores are always recomputed; unchanged ratings give unchanged scores).
5. Run all four policies (FCFS, urgency greedy, AidOS, AidOS balanced) on the new snapshot.
6. Validate every plan independently.
7. Hash the logical outcome (section "Determinism").
8. Append the step to a **new** session state with `version + 1`.

If any step fails, an exception is raised and the stored session is untouched (the engine is a set of pure functions and the store swaps the new state in only on success). Specifically:

| Failure | Result | HTTP |
|---|---|---|
| state does not allow events | rejected, unchanged | 409 `invalid_transition` |
| malformed event (types, ranges, unknown type) | rejected, unchanged | 422 `validation_error` |
| event invalid for this scenario | rejected, unchanged | 422 (`unknown_zone`, `unknown_resource`, `insufficient_stock`, `no_change`, `last_zone`, `duplicate_zone`, `invalid_result`, `too_many_events`) |
| commit names the wrong snapshot | rejected, unchanged | 409 `stale_plan` |
| the recommended policy returns no plan (`UNKNOWN`, `INFEASIBLE`, …) | rejected, unchanged | 503 `solver_failed` |
| a plan breaks a hard constraint | event not applied; session moves to `ERROR` | 500 `engine_invariant` |

## Sessions, versions and concurrency

- Sessions live in a dictionary in the API process (`store.py`). They **do not survive a restart**, are not shared between processes, and expire after 2 hours idle (at most 200 are kept; the oldest idle one is evicted). Run the API with a single worker. Export a session to keep it.
- Every session has a `version`, starting at 1 and increasing by one with each accepted change. Every change request must send `expected_version`; a mismatch is rejected with 409 `version_conflict` and changes nothing. So two browser tabs cannot silently overwrite each other: the second one is told to reload.
- Changes to one session are serialised by a per-session lock, and the new state is computed off the old one before it is stored, so each change is atomic. A test fires four simultaneous changes with the same version: exactly one succeeds.
- Not implemented: persistence, multi-process or multi-machine safety, authentication. They are out of scope for the prototype.

## Determinism

The same initial scenario, ordered events and configuration produce the same:

- snapshot hash at every step (SHA-256 of the canonical scenario JSON);
- fuzzy scores, plans and statuses of every policy;
- event IDs (`e003-c79dc657`: sequence number plus a hash of the event and the snapshot it was applied to);
- **outcome hash** per step: SHA-256 over the snapshot hash, every zone's score, every policy's status and cells, and the units dispatched.

Wall-clock timings (`runtime_ms`, solver `wall_time_ms`) vary and are excluded from every hash. Determinism rests on the Stage 2 engine: scores rounded to 4 decimals, exact integer coefficients, a single CP-SAT worker with a fixed seed, and a lexicographic tie-break that makes the optimal plan unique. This holds whenever every solve phase is proven OPTIMAL, as in every evaluated run. If the time limit stops a phase (possible for balanced mode near the 50 × 10 size limit), the plan is valid and labelled FEASIBLE, but it may depend on timing, and a replay could then report a mismatch. The only randomness in a session is the session ID itself (`sim-` plus 12 random hex characters), which is not part of any outcome.
