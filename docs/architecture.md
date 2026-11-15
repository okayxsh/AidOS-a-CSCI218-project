# Architecture

> Canonical source: `AidOS project info.md` Section 7. This file records the architecture *as implemented* (Stage 4).

## Overview

```text
apps/web (React)  ──HTTP/JSON──>  apps/api (FastAPI adapter)  ──>  aidos engine (pure Python)
   landing "/"                       aidos/main.py                    domain/      models, validation, snapshots
   dashboard "/dashboard"            aidos/api/*                      ai/          fuzzy, constraints (CP-SAT),
                                                                                   baseline_fcfs, baseline_greedy, policies
                                                                      evaluation/  invariants, metrics, generator,
                                                                                   runner, exports, families, stats,
                                                                                   dynamic, analysis, campaign, artifacts
                                                                      pipeline.py  the decision pipeline
                                                                      simulation/  fsm, events, reducer, session,
                                                                                   compare, store (in memory)
                                                                      config/      fuzzy_rules.json (versioned)
data/scenarios/*.json  <── read by the engine (and, for the landing illustration only, by the web build)
experiments/*.py       ──> call the same engine offline
```

## Request path (Stage 2)

```text
Dashboard opens ?scenario=<id>
  -> GET /api/scenarios/{id}
       load fixture -> parse_scenario (schema + cross-field checks) -> immutable Scenario
  <- { snapshot_hash, scenario, summary }

  -> POST /api/urgency/evaluate { scenario }
       pipeline.assess_urgency -> fuzzy.evaluate per zone
  <- per-zone score, category, memberships, fired rules, contributions

User clicks "Run allocation"
  -> POST /api/allocations/compare { scenario, policies: [fcfs, greedy, aidos, aidos_balanced] }
       pipeline.compare:
         check_scenario_consistency
         assess_urgency                      (once; shared by every policy)
         for each policy: run_policy  ->  validate_allocation  ->  compute_metrics
  <- { snapshot_hash, urgency, config, results: [ cells, metrics, validation, solver, runtime ] }
```

Full step-by-step description: `docs/algorithms/cp-sat-allocation.md`.

## Module boundaries

- `aidos/domain`, `aidos/ai`, `aidos/evaluation` and `aidos/pipeline.py` import nothing from FastAPI, React or the network and hold no mutable global state. Domain models are frozen Pydantic models. The fuzzy configuration is read once and is immutable.
- `aidos/api` only adapts: request schemas in, one pipeline call, response schemas out, one error shape.
- `aidos/pipeline.py` is the single place that sequences urgency → policy → validation → metrics. The API and `evaluation/runner.py` both call it.
- Every policy returns the same `AllocationResult` type (`aidos/ai/policies.py`). FCFS takes the scenario; greedy and the CP-SAT policies also take the shared urgency scores.
- `evaluation/invariants.py` validates a plan against the scenario and does not import any policy.
- `apps/web` never computes allocations, scores, metrics or validation for the dashboard. It renders backend responses. The landing page restates fixture inputs and the published fuzzy configuration as illustrations so it can render without the backend; it shows no allocation results.

## Simulation request path (Stage 3)

```text
POST /api/simulation/sessions/{id}/events { expected_version, event }
  routes_simulation  ->  store.mutate(id, expected_version, ...)      version check + per-session lock
    session.apply:
      fsm.transition(state, apply_event)                             READY/PAUSED/... -> 409
      reducer.apply_event(copy of scenario)  -> parse_scenario        invalid -> 422, nothing stored
      evaluate_step -> pipeline.compare (fuzzy + 4 policies + validator) -> outcome hash
      new SessionState(version + 1, steps + [step], ledger, ...)
    store swaps the new state in only on success
  <- SessionOut (current step, diff vs previous step, history, ledger)
```

- `aidos/simulation` imports the engine (`pipeline`, `domain`) but nothing from FastAPI. Every engine function returns a new immutable `SessionState`; the only mutable object is the `SessionStore`, held by the API app (`app.state.sessions`).
- Sessions are in memory, single-process, and lost on restart (`docs/simulation/state-machine.md`).

## Evaluation path (Stage 4)

```text
experiments/run_benchmarks.py --preset P
  campaign.run_campaign
    families.generate(family, i)  ->  pipeline.compare (all 4 policies, one snapshot)  -> rows
    dynamic.recommendation_rows / dispatch_run (Stage 3 simulator, offline)            -> rows
    families.generate_sized + repeated timing                                          -> rows
    CSV files -> analysis.summarize_* (stats.describe / paired / holm) -> summary.json
    manifest.json (versions, counts, failures, checksums)
GET /api/evaluation/...  ->  artifacts.py (validated run id, fixed file names)  ->  Evaluate page
```

The evaluation code imports the engine but nothing from FastAPI; the API only reads finished artifacts.

## Out of scope

Persistence of simulation sessions, authentication and multi-process deployment are out of scope. The group report draft (Stage 6) is in `docs/report/`.
