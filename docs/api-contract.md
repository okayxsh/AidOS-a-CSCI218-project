# API contract

> Canonical source: `AidOS project info.md` Section 7 (API contract). Examples here match the tests in `tests/integration/test_api_flow.py`. Engine version 0.4.0 (Stage 4).

All endpoints use the `/api` prefix. Interactive OpenAPI docs: `http://localhost:8000/docs`.

| Method | Path | Purpose | Status |
|---|---|---|---|
| GET | `/api/health` | Status, version, engine stage, policy availability | Implemented |
| GET | `/api/scenarios` | Built-in scenario manifests | Implemented |
| GET | `/api/scenarios/{id}` | Validated fixture + snapshot hash + backend summary | Implemented |
| POST | `/api/urgency/evaluate` | Fuzzy urgency + rule trace for every zone of a scenario, or for one set of ratings | Implemented (Stage 2) |
| GET | `/api/urgency/config` | The versioned membership functions, output terms and 27 rules | Implemented (Stage 2) |
| POST | `/api/allocations/compare` | Run one or more policies on one submitted snapshot | Implemented for `fcfs`, `greedy`, `aidos`, `aidos_balanced` |
| POST | `/api/simulation/sessions` | Create a simulation session from a built-in or submitted scenario | Implemented (Stage 3) |
| GET | `/api/simulation/sessions/{id}` | Current state, step, diff, history, ledger | Implemented (Stage 3) |
| POST | `/api/simulation/sessions/{id}/{start,pause,resume,complete,reset}` | State-machine actions | Implemented (Stage 3) |
| POST | `/api/simulation/sessions/{id}/events` | Apply one crisis event (or a plan commit) atomically | Implemented (Stage 3) |
| POST | `/api/simulation/sessions/{id}/replay` | Reset and re-apply an event list, all or nothing | Implemented (Stage 3) |
| GET | `/api/simulation/sessions/{id}/history` | Step-by-step event history | Implemented (Stage 3) |
| GET | `/api/simulation/sessions/{id}/steps/{seq}` | One recorded step in full | Implemented (Stage 3) |
| GET | `/api/simulation/sessions/{id}/diff?before&after` | Before/after comparison of two steps | Implemented (Stage 3) |
| GET | `/api/simulation/sessions/{id}/export` | Replay document (JSON) | Implemented (Stage 3) |
| POST | `/api/simulation/import` | New session from a replay document, with verification | Implemented (Stage 3) |
| GET | `/api/evaluation/runs` | Completed evaluation runs, newest first | Implemented (Stage 4) |
| GET | `/api/evaluation/runs/{run_id}` | A run's manifest, configuration, summary statistics and failures | Implemented (Stage 4) |
| GET | `/api/evaluation/runs/{run_id}/tables/{table}` | Raw rows (`static`, `static_zones`, `recommendation`, `dispatch`, `dispatch_zones`, `scaling`), filterable by `family`, `policy`, `scenario_id`, paged by `limit`/`offset` | Implemented (Stage 4) |

The specification proposed `POST /api/simulation/transition` and `POST /api/allocations/commit`. They are realised as `…/events` (one event per call) and the `plan_committed` event, which carries the snapshot hash the plan was computed for and is rejected if it is stale.

"Run the AI allocation" and "compare with the baseline" are the same endpoint: send `policies: ["aidos"]` or several policy IDs. One response therefore always shares one snapshot and one set of fuzzy scores.

## `GET /api/health`

```json
{
  "status": "ok",
  "version": "0.4.0",
  "engine_stage": 4,
  "policies": [
    { "id": "fcfs", "label": "First come, first served", "available": true, "planned_stage": null },
    { "id": "greedy", "label": "Urgency greedy", "available": true, "planned_stage": null },
    { "id": "aidos", "label": "AidOS (fuzzy + CP-SAT)", "available": true, "planned_stage": null },
    { "id": "aidos_balanced", "label": "AidOS balanced (coverage floor)", "available": true, "planned_stage": null }
  ]
}
```

## `GET /api/scenarios` and `GET /api/scenarios/{id}`

Unchanged from Stage 1. The list returns `{scenario_id, title, description, seed, synthetic, zone_count, resource_count}` per fixture. The detail returns:

```json
{
  "snapshot_hash": "<sha256 of the canonical scenario JSON>",
  "scenario": { "...": "the validated fixture, see data/README.md" },
  "summary": {
    "resources": [{ "resource_id": "medical_kits", "stock": 90, "requested": 150, "shortfall": 60, "surplus": 0 }],
    "zones": [{ "zone_id": "zone-a", "active": true, "requested_units": 205 }],
    "totals": { "stock": 330, "requested": 560, "shortfall": 230, "zones": 3, "active_zones": 3 },
    "supply_status": "shortage"
  }
}
```

`requested` and `shortfall` count active zones only. `shortfall` is summed per resource: surplus of one resource never offsets a shortage of another. `supply_status` is `no_demand`, `covered`, `depot_empty` or `shortage`.

## `POST /api/urgency/evaluate`

Request: exactly one of `{ "scenario": <Scenario> }` or `{ "ratings": { "severity": 7, "time_criticality": 7, "vulnerability": 5 } }`. Ratings are numbers from 0 to 10.

```json
{
  "method": "sugeno-0-product-weighted-average",
  "config_version": "1.0",
  "scenario_id": null,
  "snapshot_hash": null,
  "zones": [
    {
      "zone_id": null,
      "active": null,
      "score": 70.8333,
      "category": "high",
      "inputs": { "severity": 7.0, "time_criticality": 7.0, "vulnerability": 5.0 },
      "normalized": { "severity": 0.7, "time_criticality": 0.7, "vulnerability": 0.5 },
      "memberships": { "severity": { "low": 0.0, "medium": 0.333, "high": 0.667 }, "...": {} },
      "activations": [
        {
          "rule_id": "R26",
          "text": "IF severity is high AND time criticality is high AND vulnerability is medium THEN urgency is critical",
          "consequent": "critical", "strength": 0.444, "output": 87.5, "contribution": 38.889
        }
      ],
      "term_support": { "low": 0.0, "moderate": 0.111, "high": 0.444, "critical": 0.444 },
      "explanation": "Urgency 70.8 (high). Severity 7/10 is mostly high (0.67); ..."
    }
  ]
}
```

(Decimals shortened here.) With a scenario, `zones` has one entry per zone in scenario order, with `zone_id` and `active` set; inactive zones are scored and flagged. `activations` lists every fired rule, strongest first; the `contribution` values sum to `score` (which is rounded to 4 decimals). See `docs/algorithms/fuzzy-logic.md`.

## `GET /api/urgency/config`

`{ method, version, inputs: { <input>: { label, range, terms: { low|medium|high: { shape, points } } } }, output: { <term>: { value, band } }, rules: [{ id, antecedent, consequent, text }] }`.

## `POST /api/allocations/compare`

Request:

```json
{
  "scenario": { "...": "a full Scenario" },
  "policies": ["fcfs", "greedy", "aidos", "aidos_balanced"],
  "config": { "epsilon": 1.0, "resource_weights": {}, "min_coverage": 0.25, "time_limit_s": 5.0 }
}
```

`policies` defaults to `["fcfs"]` (1–4 entries; duplicates are run once). `config` is optional; every field has the default shown. Ranges: `epsilon` in (0, 100], `resource_weights` integers 1–100 for known resources, `min_coverage` in [0, 1], `time_limit_s` in [0.01, 10]. The solver seed (0) and worker count (1) are fixed and echoed back. The snapshot is never mutated.

Response (shortened; the real response lists every zone and cell at full precision):

```json
{
  "scenario_id": "triage-demo-001",
  "snapshot_hash": "...",
  "engine_version": "0.4.0",
  "fuzzy": { "method": "sugeno-0-product-weighted-average", "config_version": "1.0" },
  "urgency": [ { "zone_id": "zone-a", "active": true, "score": 87.5, "category": "critical", "...": "as in /urgency/evaluate" } ],
  "urgency_ms": 0.1,
  "config": { "epsilon": 1.0, "resource_weights": {}, "min_coverage": 0.25, "time_limit_s": 5.0, "random_seed": 0, "workers": 1 },
  "results": [
    {
      "policy_id": "aidos",
      "label": "AidOS (fuzzy + CP-SAT)",
      "status": "OPTIMAL",
      "has_plan": true,
      "message": "",
      "zone_order": ["zone-a", "zone-c", "zone-b"],
      "cells": [
        {
          "zone_id": "zone-b", "resource_id": "medical_kits",
          "requested": 45, "allocated": 0, "unmet": 45,
          "limit": "stock_exhausted",
          "reason": "All 90 units are allocated (45 unmet). Zones with higher urgency (Zone A, Zone C) received 90 units."
        }
      ],
      "metrics": {
        "unit_coverage": 0.589, "coverage_by_resource": { "medical_kits": 0.6 },
        "coverage_by_zone": { "zone-a": 1.0, "zone-c": 0.808, "zone-b": 0.089 },
        "allocated_units": 330, "unmet_units": 230, "feasibility_violations": 0,
        "allocated_by_resource": { "medical_kits": 90 }, "remaining_by_resource": { "medical_kits": 0 },
        "stock_utilization": 1.0, "urgency_weighted_coverage": 0.6461,
        "min_zone_coverage": 0.089, "jain_fairness": 0.722, "unmet_high_urgency": 230
      },
      "validation": {
        "applicable": true, "valid": true,
        "checks": [ { "name": "within_stock", "passed": true, "hard": true, "detail": "No resource is allocated beyond the depot's stock." } ],
        "violations": []
      },
      "solver": {
        "engine": "OR-Tools CP-SAT", "status": "OPTIMAL", "objective": "urgency_first",
        "objective_value": 269549965, "objective_scale": 10000,
        "phases": [
          { "name": "urgency", "status": "OPTIMAL", "objective_value": 269549965.0, "best_bound": 269549965.0, "wall_time_ms": 1.2 },
          { "name": "tie_break", "status": "OPTIMAL", "objective_value": 760.0, "best_bound": 760.0, "wall_time_ms": 0.9 }
        ],
        "variables": 9, "constraints": 5,
        "parameters": { "max_time_in_seconds": 5.0, "num_workers": 1, "random_seed": 0 },
        "coefficients": { "zone-a": { "medical_kits": 885000 } },
        "coverage_floor": {},
        "message": ""
      },
      "runtime_ms": 4.0
    }
  ]
}
```

Field notes:

- `status`: `COMPLETE` (FCFS, greedy), or the CP-SAT outcome `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, `UNKNOWN`, `MODEL_INVALID`. `OPTIMAL` means every solve phase was proven optimal.
- `has_plan` is false for `INFEASIBLE`, `UNKNOWN` and `MODEL_INVALID`. Then `cells` is empty, `metrics` is `null`, `validation.applicable` is false and `message` says what happened. No allocation is invented.
- `zone_order`: the order zones were served (FCFS, greedy) or ranked by urgency (AidOS).
- `limit`: `met`, `no_demand`, `stock_exhausted`, `zero_stock` or `not_proven`.
- `validation`: produced by a validator independent of the policy. Hard checks: `integer`, `non_negative`, `within_demand`, `within_stock`, `complete`. Quality check (`hard: false`): `no_idle_stock`.
- `solver` is `null` for FCFS and greedy. `objective_value / objective_scale` is in urgency·units. `coverage_floor` is filled for `aidos_balanced`.
- Ratios with a zero denominator are `null` (shown as N/A), never 0.
- `urgency_ms`, `runtime_ms` and `wall_time_ms` vary between runs; everything else is reproducible for the same snapshot, config and engine version.

## Error responses

Every error uses one shape:

```json
{ "error": { "code": "invalid_scenario", "message": "The scenario failed validation.", "details": [{ "path": "zones.0.demand.fuel", "message": "unknown resource 'fuel'" }] } }
```

| Status | `code` | When |
|---|---|---|
| 404 | `scenario_not_found` | Unknown built-in scenario id |
| 422 | `validation_error` | Field-level schema failure (negative units, rating outside 0–10, unknown policy ID, `epsilon: 0`, both or neither of `scenario` / `ratings`, ...) |
| 422 | `invalid_scenario` | Cross-field failure (unknown resource, missing stock, duplicate ids) |
| 422 | `invalid_config` | An AidOS setting that names an unknown resource or is out of range |
| 422 | `invalid_ratings` | Ratings rejected by the fuzzy engine (not reachable through the typed API; kept as a safeguard) |

| 404 | `session_not_found` | Unknown or expired simulation session (sessions are in memory and lost on restart) |
| 404 | `not_found` | Unknown simulation step |
| 409 | `version_conflict` | `expected_version` is not the session's current version; nothing changed |
| 409 | `invalid_transition` | The action or event is not allowed in the session's state |
| 409 | `stale_plan` | `plan_committed` named a snapshot that is not the current one |
| 422 | `invalid_event`, `unknown_zone`, `unknown_resource`, `insufficient_stock`, `no_change`, `last_zone`, `duplicate_zone`, `no_plan`, `invalid_plan`, `invalid_result`, `too_many_events` | The event cannot be applied to the current scenario; nothing changed |
| 422 | `replay_failed` | A replay or import failed; `details[0].path` is `events.<i>` or `document` |
| 503 | `solver_failed` | The recommended policy returned no plan for the new state; the event was not applied |
| 500 | `engine_invariant` | A computed plan broke a hard constraint (an engine defect); the session moved to ERROR |
| 422 | `invalid_run_id` | Evaluation run id does not match `<preset>-<YYYYMMDD>T<HHMMSS>Z` |
| 404 | `run_not_found` | No evaluation run with that id in `experiments/results/` |

The Stage 1 `501 policy_not_implemented` response no longer occurs: all four policies exist.

## Simulation

Details: `docs/simulation/state-machine.md`, `events.md`, `replay.md`.

**Create.** `POST /api/simulation/sessions {"scenario_id": "triage-demo-001"}` (or `"scenario": {...}`), optional `"policy": "aidos" | "aidos_balanced"` (the recommendation; all four policies are always computed) and `"config"` (as for compare). Returns 201 and a session in `READY`.

**Change.** Every change sends the version it expects:

```json
POST /api/simulation/sessions/sim-1a2b3c4d5e6f/events
{ "expected_version": 2, "event": { "type": "urgency_changed", "zone_id": "zone-b", "severity": 9 } }
```

State actions take the same body without `event`: `POST …/start {"expected_version": 1}`.

**Session response** (every create, read and change returns it; shortened):

```json
{
  "session_id": "sim-1a2b3c4d5e6f",
  "scenario_id": "triage-demo-001",
  "state": "ACTIVE",
  "version": 3,
  "allowed_actions": ["pause", "complete", "reset", "apply_event"],
  "policy": "aidos",
  "config": { "epsilon": 1.0, "min_coverage": 0.25, "...": "..." },
  "event_count": 1,
  "max_events": 200,
  "error": null,
  "current": {
    "seq": 1, "event_id": "e001-6cc0a746", "event": { "type": "urgency_changed", "...": "..." },
    "sim_step": 0, "snapshot_hash": "...", "outcome_hash": "5cbedce6...",
    "changes": ["Zone B severity 6 → 9."], "dispatch": [],
    "scenario": { "...": "the validated scenario after the event" },
    "summary": { "...": "as in GET /api/scenarios/{id}" },
    "comparison": { "...": "exactly the POST /api/allocations/compare response, all four policies" }
  },
  "diff": {
    "before_seq": 0, "after_seq": 1, "events": ["urgency_changed"],
    "urgency": [{ "zone_id": "zone-b", "score_before": 62.5, "score_after": 79.1667, "category_before": "high", "category_after": "critical", "rank_before": 3, "rank_after": 2 }],
    "order_before": ["zone-a", "zone-c", "zone-b"], "order_after": ["zone-a", "zone-b", "zone-c"],
    "resources": [{ "resource_id": "medical_kits", "stock_before": 90, "stock_after": 90, "shortfall_before": 60, "shortfall_after": 60, "...": "..." }],
    "policies": [{ "policy_id": "aidos", "changed_cells": 6, "cells": [{ "zone_id": "zone-b", "resource_id": "medical_kits", "allocated_before": 0, "allocated_after": 15, "...": "..." }], "...": "..." },
                 { "policy_id": "fcfs", "changed_cells": 0, "...": "..." }],
    "recommendation_changed": true,
    "explanation": ["Zone B severity 6 → 9.", "Zone B urgency 62.5 → 79.2 (high → critical).", "..."]
  },
  "history": [{ "seq": 0, "type": null, "summary": "Initial snapshot loaded.", "changed_cells": 0, "...": "..." },
              { "seq": 1, "type": "urgency_changed", "summary": "Zone B severity 6 → 9.", "changed_cells": 6, "...": "..." }],
  "ledger": [],
  "dispatched_units": 0,
  "resolved_zones": []
}
```

**Replay.** `POST …/replay {"expected_version": n, "events": [...]}` resets and re-applies the list; all or nothing.

**Evaluation.** Read-only. Runs are produced offline (`experiments/run_benchmarks.py`), never by an HTTP request. Run ids must match `^(smoke|standard|extended|custom)-\d{8}T\d{6}Z$`; the directory must sit directly in `experiments/results/`; only fixed file names are read. `summary` is `summary.json` exactly as written by the campaign (see `docs/evaluation/metric-definitions.md`).

**Export / import.** `GET …/export` returns an `aidos-simulation` 1.0 document; `POST /api/simulation/import <document>` returns 201 `{session, verification: {checked, matches, first_mismatch_seq, engine_version_recorded}}`.
