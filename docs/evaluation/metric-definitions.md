# Metric definitions

Code: `apps/api/aidos/evaluation/metrics.py` (per plan), `dynamic.py` (dynamic modes), `analysis.py` (aggregation), `stats.py` (statistics). Metrics are computed from a plan's cells and the scenario, independently of the policy that produced the plan.

Notation for one scenario and one plan:

- Z: zones with positive total request.
- R: resources.
- d_{z,r}: request.
- x_{z,r}: allocation.
- S_r: stock.
- u_z: fuzzy urgency score (0–100), the same scores every policy saw.

**Objective-aligned** metrics are those the AidOS objective, or the urgency model it uses, favours by construction. Higher values for AidOS on them show that the optimiser does what it is told; they are not independent evidence of better outcomes. **External** metrics are not part of any policy's objective.

**N/A** means a ratio has a zero denominator. It is recorded as empty in the CSV files and excluded from means (so `n` can be smaller than the number of scenarios), never counted as 0 or 1.

## A. Feasibility (`valid`)

- **Definition.** 1 if the plan passes every hard check of the independent validator (integer, 0 ≤ x ≤ d, Σ_z x ≤ S_r per resource, exactly one cell per active zone and resource), else 0. Reported as valid plans / plans returned, and plans returned / runs.
- **Direction.** Must be 1 for every returned plan. Any violation is a correctness failure, not a low score.
- **Edge cases.** A policy that returns no plan (a solver failure) is counted separately, never as valid.

## B. Unit coverage (`unit_coverage`)

- **Definition.** Σ x / Σ d over all zones and resources. Unit: fraction.
- **Direction.** Higher.
- **Edge case.** N/A if Σ d = 0.
- **Limitation.** It adds units of different resources (a medical kit and a water pack count the same). Read it with B2.

**B2. Mean resource coverage (`mean_resource_coverage`)**

- **Definition.** The mean over resources with demand of Σ_z x_{z,r} / Σ_z d_{z,r}. Unit-free.
- **Direction.** Higher.
- **Edge case.** N/A when nothing is requested.

All four policies are non-wasteful (no stock is held back while a zone lacks it), so B and B2 are identical across policies on every scenario. Policies differ in **who** receives units, not **how many**.

## C. Urgency-weighted coverage (`urgency_weighted_coverage`), objective-aligned

- **Definition.** Σ_{z,r} u_z x_{z,r} / Σ_{z,r} u_z d_{z,r}. Unit: fraction, 0–1.
- **Direction.** Higher.
- **Edge case.** N/A if the denominator is 0.
- **Limitation.** The AidOS objective is Σ (u_z + ε) x_{z,r}, and the denominator is a constant of the scenario. So AidOS maximises this metric almost exactly (ε = 1 point barely matters), and any policy that serves urgent zones first scores well. It measures agreement with the fuzzy model, whose rules and parameters are design assumptions.

**C2. Critical-zone coverage (`critical_coverage`), objective-aligned**

- **Definition.** Σ x / Σ d over zones with u_z ≥ 75 (the "critical" band).
- **Edge case.** N/A when no zone is critical (n is reported).

## D. Per-zone coverage (`coverage_by_zone`, `static_zones.csv`)

- **Definition.** f_z = Σ_r x_{z,r} / Σ_r d_{z,r} for each zone with demand.
- **Data.** Stored per scenario, policy and zone, together with the zone's urgency and total request. Resource-specific coverage is in `coverage_by_resource`.

## E. Equity and starvation, external

| Metric | Definition | Direction |
|---|---|---|
| `min_zone_coverage` | min_z f_z | higher |
| `starved_zones` | number of zones with Σ d > 0 and Σ x = 0 | lower |
| `starved_share` | starved_zones / zones with demand | lower |
| `coverage_gap` | max_z f_z − min_z f_z | lower |
| `jain_fairness` | (Σ f_z)² / (n Σ f_z²), over zones with demand; N/A if every f_z = 0 | higher (1 = equal coverage) |

Equal coverage is not humanitarian fairness. Zones differ in need, and an urgency-first policy *intends* unequal coverage. These metrics describe distribution; they do not rank policies ethically. Jain's index can be high when every zone receives very little, so it is always read with `min_zone_coverage`.

## F. Utilisation, external

- **`usable_stock_utilization`.**
  - Definition: Σ x / Σ_r min(S_r, Σ_z d_{z,r}). Stock that nobody requested is not counted as waste.
  - Direction: higher. A value of 1 means no stock was idle while a request for it was unmet.
  - Edge case: N/A when nothing is both stocked and requested (for example, a zero-stock scenario).
- **`stock_utilization`** (Stage 2, kept for continuity): Σ x / Σ S. It is below 1 whenever stock exceeds requests, which is not a failure.

## G. Computational performance

| Field | Definition |
|---|---|
| `runtime_ms` | wall-clock time of the policy call, measured with `perf_counter`. The median of the repeated timings per scenario (3 in the standard and extended presets); `runtime_ms_min` is also stored |
| `solver_ms` | the sum of CP-SAT's reported wall time over the solve phases (AidOS policies only) |
| `status`, `optimal_proven` | the solver status, and whether every phase was proven optimal |

Timings vary between runs and machines. They are reported as distributions (median and percentiles), and are never part of any reproducibility check or outcome hash. The scaling study (`scaling.csv`) times each policy on 5–50-zone scenarios with repeats.

## H. Dynamic response, recommendation mode (shared state)

For each script step t ≥ 1, and each policy, comparing step t with step t − 1:

| Metric | Definition |
|---|---|
| `reallocated_units` | Σ_{z,r} \|x_t − x_{t−1}\|, where cells that are absent count as 0 (a zone that leaves or joins counts fully) |
| `reallocated_share` | reallocated_units / (allocated_{t−1} + allocated_t) |
| `plan_changed` | 1 if reallocated_units > 0 |
| `unmet_change` | unmet_t − unmet_{t−1} |
| `mean_abs_zone_coverage_change` | the mean over zones present at both steps of \|f_z,t − f_z,t−1\| |
| `max_urgency_change` | the largest score change of any zone present at both steps (the same for every policy) |
| `uwc_after`, `min_zone_coverage_after`, `starved_zones_after` | the plan metrics at step t |

More reallocation is not better or worse in itself. A policy that ignores an escalation reallocates nothing.

For comparisons, a script is the unit: each policy's per-step values are averaged within the script, then paired across policies by script. Steps of one script are not independent observations.

## I. Dispatch mode (policy-specific trajectories)

Each policy commits its own plan after each round, so later states differ by policy. Measured at the end of the script:

| Metric | Definition |
|---|---|
| `dispatched_units` | total units in the ledger |
| `fulfilment` | Σ_z dispatched_z / Σ_z (dispatched_z + open request_z at the end) |
| `urgency_weighted_fulfilment` | the same, weighted by each zone's final urgency (objective-aligned) |
| `min_zone_fulfilment` | the lowest zone fulfilment |
| `zones_never_served` | zones with need that received nothing over the whole script |
| `inventory_conserved` | for every resource, initial stock + arrivals − losses − dispatched = final stock |
| `ledger_consistent` | ledger total = dispatched units, and ledger entries = successful commits |
| `double_dispatch_blocked` | after every commit, re-sending the same commit is rejected as `stale_plan` |
| `rejected_events` | script events the engine refused (0 by design: the script only contains events that are valid on every trajectory) |

Dispatch-mode results are never pooled with recommendation-mode or static results.
