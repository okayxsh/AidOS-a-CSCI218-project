# 0005 — Stage 3: simulation states, inventory semantics and sessions

Date: 11 November 2026. Status: accepted.

## Context

Stage 3 adds the crisis simulator. The specification (section 5.3) and the Stage 3 brief describe it differently in two places, and the specification asks for conflicts to be flagged rather than reinterpreted quietly.

## Decisions

### 1. Session state machine READY / ACTIVE / PAUSED / COMPLETED / ERROR

The specification sketches a plan lifecycle (`DRAFT → READY → ALLOCATED → COMMITTED → UPDATED`). The brief asks for a session lifecycle. The session machine is implemented; the plan lifecycle is covered by how steps work (`docs/simulation/state-machine.md`, "How this relates to the specification's lifecycle"):

- every event immediately produces a new step with recomputed candidate plans, so a stale plan is never displayed;
- `COMMITTED` is the `plan_committed` event.

`PAUSED` only locks the session against changes, because there is no running clock. `ERROR` is reached only when the independent validator rejects a computed plan, an engine defect, and the triggering event is never applied. Ordinary failures (invalid events, solver timeouts) leave the session unchanged instead.

### 2. Recommendation-only by default, plus an explicit dispatch event

The brief prefers recommendation-only semantics. The specification requires commit in Stage 3: section 5.3 `COMMITTED`, section 6.2 "commit action", section 6.3 "candidate or committed", and the gate "never double-consumes stock". Both are satisfied:

- Computing plans never changes stock or requests.
- Only `plan_committed` dispatches. It names the snapshot hash its plan was computed for, so a stale or repeated commit is rejected.
- Dispatched units are recorded in an append-only ledger, which the brief allows ("an explicit dispatch event and a separate immutable ledger").
- Resolving a zone never returns dispatched units to the depot.

### 3. The clock moves only on `time_advanced`

The existing schema already has `activation_step`. Only `time_advanced` advances the scenario clock, so a scheduled zone cannot appear as a side effect of an unrelated event. The event sequence number counts all events separately.

### 4. Absolute values and explicit rejections

`urgency_changed` and `request_updated` carry new values, not deltas. No-op events, stock losses larger than the stock, unknown zones and resources, reused zone IDs and resolving the last zone are rejected with a specific code, never corrected silently.

### 5. In-memory sessions with optimistic versions

Sessions live in one process, expire after 2 hours idle, and are lost on restart. Every change carries `expected_version`, and a mismatch returns 409. A per-session lock makes each change atomic. There is no database, persistence or multi-process support, which keeps the prototype's scope. Exported replay documents are how a run is kept.

### 6. Endpoint shape

The specification proposed `POST /api/simulation/transition` and `POST /api/allocations/commit`. They are realised as session routes under `/api/simulation/sessions/{id}`:

- `/events` covers transitions;
- the `plan_committed` event covers commit;
- additional routes provide replay, history, steps, diff, export and import.

### 7. Every policy, every step

Each step runs all four policies, not only the recommendation, so FCFS is compared on the same post-event state. One step costs tens of milliseconds on the fixtures.

## Consequences

- The dashboard's Simulate page and the landing copy use the session states above, not the specification's plan-state names.
- Stage 4 can drive the simulator offline (`aidos.simulation.session` needs no API) to study how policies respond to events.
