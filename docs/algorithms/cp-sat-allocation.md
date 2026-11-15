# CP-SAT allocation engine and decision pipeline

The mathematics is in [`allocation-formulation.md`](allocation-formulation.md). This file describes how it is implemented, how the solver is configured, how statuses are handled and how a scenario moves through the whole pipeline.

## 1. Pipeline

```text
Scenario (validated, immutable)
   │
   ├─ assess_urgency ........ fuzzy score + rule trace per zone        aidos/ai/fuzzy.py
   │
   ├─ run_policy ............ one of four policies, same inputs        aidos/ai/*
   │     fcfs             arrival order, ignores urgency               baseline_fcfs.py
   │     greedy           urgency order, no optimiser                  baseline_greedy.py
   │     aidos            CP-SAT, urgency-first objective              constraints.py
   │     aidos_balanced   CP-SAT, coverage floor then urgency          constraints.py
   │
   ├─ validate_allocation ... hard constraints, checked independently  aidos/evaluation/invariants.py
   │
   ├─ compute_metrics ....... coverage, urgency-weighted coverage, …   aidos/evaluation/metrics.py
   │
   └─ Comparison ............ urgency + every run, one snapshot hash   aidos/pipeline.py
```

`aidos/pipeline.py::compare` is the single entry point. The API route and the experiment runner both call it, so the dashboard and the experiments cannot drift apart. Each step is a separate function that can be tested alone, and none of them imports FastAPI or keeps global state.

Fair comparison is structural: `compare` scores urgency once and passes the same scenario object and the same scores to every policy. FCFS ignores the scores by design. Nothing mutates the scenario; a test asserts the snapshot hash is unchanged after a comparison.

## 2. Model construction (`allocate_aidos`)

| Step | What the code does |
|---|---|
| Variables | `new_int_var(0, d[z,r])` for each active zone and resource with `d > 0` and stock `> 0`. Cells without a variable are reported as 0. |
| Stock | `add(sum(x[·,r]) <= S[r])` per resource. |
| Coefficients | `w_r * (10,000·p_z + round(10,000·ε))`, exact integers because scores have 4 decimals. |
| Balanced only | one `floor[r]` variable in `[0, 1000·target]` per resource, with `1000·x[z,r] >= d[z,r]·floor[r]` for each requesting zone. |
| Phases | maximise one objective, read the solution, add `objective >= value reached`, hint the next phase with the current solution, repeat. |

Phases, in order:

| Policy | Phase 1 | Phase 2 | Phase 3 |
|---|---|---|---|
| `aidos` | urgency | tie-break | |
| `aidos_balanced` | coverage floor | urgency | tie-break |

Model size on `triage-demo-001`: 9 variables and 5 constraints for `aidos` after both phases; 12 variables and 15 constraints for `aidos_balanced`.

## 3. Solver configuration

| Parameter | Value | Why |
|---|---|---|
| `num_workers` | 1 | a single search thread; parallel search can return different optimal plans between runs |
| `random_seed` | 0 | fixed |
| `max_time_in_seconds` | 5.0 total, shared by all phases (API allows 0.01–10) | the request cannot hang |

Determinism does not rest on solver internals alone: the lexicographic tie-break makes the optimal plan unique (formulation, section 5), so any correct solver run that proves every phase OPTIMAL returns the same allocations. Wall-clock time is the only field that varies between such runs. If the time limit stops a phase first (possible for balanced mode near the 50 × 10 size limit), the plan is still valid and is reported as FEASIBLE, but which feasible plan is returned can depend on timing. Every evaluated run was OPTIMAL.

Scale: the built-in scenarios solve in milliseconds. The model is small by construction (at most 50 zones × 10 resources).

## 4. Status handling

| What CP-SAT returns | What AidOS reports |
|---|---|
| every phase `OPTIMAL` | status `OPTIMAL` |
| phase 1 has a solution, a later phase is `FEASIBLE` or stops without one | status `FEASIBLE`, message "valid but not proven optimal for the full lexicographic objective"; the plan from the last successful phase is returned |
| phase 1 `INFEASIBLE`, `UNKNOWN` or `MODEL_INVALID` | that status, **no cells**, `has_plan: false`, a message; metrics are `null` and validation is "not applicable" |

Rules the code follows:

- `OPTIMAL` is reported only when CP-SAT proved every phase. A feasible plan is never labelled optimal.
- When no plan exists, none is invented. The response says which status occurred.
- Each phase's own status, objective value and bound are returned under `solver.phases`, so the summary status can be audited.
- A plan is validated independently even when the status is `OPTIMAL`.

Tests force each failure path by substituting the status CP-SAT returns (`tests/unit/test_constraints.py`), since a valid scenario cannot make this model infeasible on its own.

Invalid input is a different path: a malformed scenario or setting is rejected before any solve, with HTTP 422 (`validation_error`, `invalid_scenario` or `invalid_config`).

## 5. Explanations per cell

Each cell (zone, resource) carries a `limit` and a `reason` built from quantities in the solved model.

| `limit` | When | Example reason |
|---|---|---|
| `met` | allocated = requested | "Request met in full." |
| `no_demand` | requested = 0 | "No units requested." |
| `zero_stock` | the depot has none | "The depot holds no units of this resource (20 unmet)." |
| `stock_exhausted` | the resource's stock is fully allocated | "All 90 units are allocated (45 unmet). Zones with higher urgency (Zone A, Zone C) received 90 units." |
| `not_proven` | stock remains in a plan not proven optimal | states the idle units and the status |

For `stock_exhausted` the reason states only facts of the solved plan: the stock is used up, which zones have a higher urgency coefficient and how many units they hold, whether a tie-break applied, and in balanced mode how many units the floor reserved. It does not claim what "would have happened" under other inputs.

Two kinds of explanation are kept apart in the API and the dashboard:

- **From the fuzzy rules** (per zone): why the urgency score is what it is.
- **From the allocation constraints** (per cell): why the quantity is what it is, given every zone's score and the stock limit. This is a property of the whole plan, not of one zone's rules.

## 6. Edge cases

| Case | Behaviour | Test |
|---|---|---|
| Zero stock | no variables, all cells 0 with `zero_stock`, status `OPTIMAL` | `test_zero_stock_…` |
| Zero total demand | all cells 0 with `no_demand`; ratio metrics are `null` (N/A), never 0 | `test_zero_total_demand`, `test_zero_demand_metrics_…` |
| One zone, one resource | min(stock, request) | `test_single_zone_single_resource` |
| Stock exceeds demand | every request met exactly | `test_stock_exceeding_demand_…` |
| All zones want one scarce resource | served in urgency order | `test_all_zones_compete_…` |
| Highly unequal priorities | the low zone can get nothing (urgency-first); balanced gives it the floor | `test_highly_unequal_priorities_…` |
| Identical priorities | earlier arrival first, same result on every run | `test_equal_priorities_…` |
| Several resources | independent; surplus of one never covers another | `test_resources_never_substitute` |
| Large values (10⁶ units, weight 100) | solved, no overflow | `test_large_demand_values_…` |
| Inactive zone | no cells, no stock | `test_inactive_zones_…` |
| Malformed scenario or config | rejected with a clear error | API tests |

Objective correctness is checked against exhaustive search: on eight small random instances, the solver's objective equals the best value over every feasible integer plan.

## 7. Baselines kept for comparison

- **FCFS** is unchanged from Stage 1. It was not adjusted to make any other policy look better, and no correctness issue was found in it.
- **Urgency greedy** uses the same fuzzy scores as AidOS without an optimiser.
- All four policies return the same result type and go through the same validator and metrics.

## 8. Metrics

| Metric | Formula | Notes |
|---|---|---|
| Unit coverage | Σx / Σd | N/A when nothing is requested |
| Urgency-weighted coverage | Σ p·x / Σ p·d | the urgency-first objective maximises this (formulation, section 4) |
| Stock utilisation | Σx / Σ stock | N/A when the depot is empty |
| Lowest zone coverage | min over zones of that zone's unit coverage | |
| Jain fairness | (Σf)² / (n·Σf²) over zones with demand, f = zone unit coverage | N/A when every f is 0; can be high when everyone gets little |
| Unmet high-urgency | Σ(d − x) over zones with p ≥ 50 | threshold = lower edge of the "high" band |
| Remaining by resource | stock − Σx | |

Under scarcity, total allocated units are usually identical across policies, because each one hands out all the stock. The difference is distribution.

## 9. Experiment interface (prepared for Stage 4)

| Piece | Purpose |
|---|---|
| `aidos/evaluation/generator.py` | `generate_scenario(seed, scarcity)`: the same seed and class always give the same scenario |
| `aidos/evaluation/runner.py` | `run_experiment(scenarios, policies, config)` → records with snapshot hash, seed, policy, status, validity, metrics, config, engine / fuzzy-config / OR-Tools versions |
| `aidos/evaluation/exports.py` | JSON with a manifest, and flat CSV rows |
| `experiments/run_benchmarks.py --smoke` | the Stage 2 correctness smoke run |

### Smoke run recorded in Stage 2

25 scenarios (5 fixtures + 20 generated: seeds 11–15 × none / mild / severe / zero scarcity), 4 policies each. Output in `experiments/results/stage2-smoke.{json,csv}`.

| Policy | Plans | Valid | Statuses | Mean urgency-weighted coverage | Mean Jain |
|---|---|---|---|---|---|
| fcfs | 25 | 25 | COMPLETE | 0.562 | 0.800 |
| greedy | 25 | 25 | COMPLETE | 0.622 | 0.805 |
| aidos | 25 | 25 | OPTIMAL | 0.622 | 0.805 |
| aidos_balanced | 25 | 25 | OPTIMAL | 0.602 | 0.896 |

What this supports: all 100 plans passed the independent validator and every CP-SAT run was proven optimal. What it does not support: any claim that one policy is better. The sample is small, the scenarios are synthetic, AidOS optimises the very metric in the fourth column, and no statistical test was run. Means exclude scenarios where the metric is N/A.

## 10. Limitations

- One depot, one decision at one moment. No routing, capacity, timing or multi-period planning.
- The urgency-first optimum always equals urgency greedy; the solver's contribution today is the proof of optimality and the balanced variant.
- Urgency-first can leave low-urgency zones with nothing.
- The balanced floor is a single fraction per resource; it is not an equity optimum.
- Urgency scores have 4 decimals; differences smaller than 0.0001 points are treated as ties.
- Plans are candidates. Nothing is committed and stock is not consumed until Stage 3.
