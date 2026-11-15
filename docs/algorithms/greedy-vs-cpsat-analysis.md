# Why AidOS (CP-SAT) gives the same plans as urgency greedy

**Finding.** In all 504 scenarios of the Stage 4 benchmark, AidOS (urgency-first CP-SAT) and urgency greedy produced identical allocations, and the same held on every dynamic step and dispatch trajectory. This document shows the agreement is a **mathematical consequence of the formulation**, not an accident of the scenario distribution or a bug. It then gives the conditions under which the two would differ.

Evidence run: `experiments/results/supplementary-greedy-equivalence-20261112T164930Z/` (script `experiments/greedy_equivalence.py`).

## 1. The two procedures, exactly as implemented

**AidOS** (`apps/api/aidos/ai/constraints.py`, `objective="urgency_first"`). Integer variables x_{z,r} for active zones z and resources r with d_{z,r} > 0 and S_r > 0. The model is:

```text
0 <= x[z,r] <= d[z,r]               (variable domain)
sum_z x[z,r] <= S[r]                for each resource r
phase 1   maximise  sum c[z,r] x[z,r],   c[z,r] = w_r * (10^4 * u_z + round(10^4 * eps))
phase 2   keep phase 1 at its optimum; maximise  sum rho_z x[z,r]
          rho_z = |Z| - (position of z when sorted by arrival_order, then id)
```

The scores u_z have exactly 4 decimals, so 10⁴·u_z is an exact integer. The weights default to w_r = 1 and ε to 1.

**Urgency greedy** (`apps/api/aidos/ai/baseline_greedy.py`). Sort active zones by (−u_z, arrival_order, id). For each zone in that order, and each resource, allocate min(remaining stock, request).

## 2. Why they agree: a proof sketch

1. **Separability.** Every constraint involves one resource only, and the objective is a sum over resources. The problem therefore splits into |R| independent problems, one per resource. A plan is optimal overall exactly when it is optimal for each resource.
2. **One resource is a unit-weight knapsack.** For a fixed r: maximise Σ_z c_z x_z with 0 ≤ x_z ≤ d_z and Σ x_z ≤ S, where every c_z > 0.
   - Because c_z > 0, an optimum never leaves stock unused while some x_z < d_z. Adding a unit raises the objective.
   - An exchange argument: if c_i > c_j, x_i < d_i and x_j > 0, moving one unit from j to i raises the objective by c_i − c_j > 0. So at an optimum, **a lower-coefficient zone receives units only after every higher-coefficient zone is full.**
   - That is precisely "fill zones in decreasing coefficient order". The LP relaxation already has an integral optimum, since S and every d are integers.
3. **Same order.** Within one resource c_{z,r} = w_r(10⁴u_z + E), with w_r > 0 constant across zones. So sorting zones by c_{z,r} is the same as sorting by u_z, **for any positive weight and any ε**. Greedy sorts by u_z.
4. **Same tie-break.** Zones with equal u_z have equal coefficients, so phase 1 leaves their split open. Phase 2 maximises Σ ρ_z x_z on that optimal face, where ρ is strictly decreasing in (arrival_order, id). By the same exchange argument, units go to earlier arrivals first. That is exactly greedy's secondary sort key.
5. **Uniqueness.** With ρ distinct for every zone, the lexicographic optimum is unique, so CP-SAT can return only that plan. Greedy constructs the same plan.

**Conclusion.** For every scenario that passes validation, every positive resource weight and every ε > 0, the urgency-first CP-SAT optimum *is* the urgency-greedy plan. Two conditions are implicit. First, the scores have at most 4 decimals, as the fuzzy engine always produces: the solver compares round(10⁴·u), so two scores closer than 0.00005 would tie for CP-SAT but not for greedy. Second, both phases are solved to OPTIMAL, as in every evaluated run. The agreement is (1) a mathematical consequence of the objective and constraints, and (3) also a consequence of the tie-breaking, which was deliberately aligned. It is **not** (2) a property of the scenario distribution, and **not** (4) an implementation or evaluation error. The tests below support this.

A corollary used in the sensitivity analysis: AidOS depends only on the **order** of the urgency scores within each resource, not on their values. Any strictly increasing transformation of the scores that keeps them on the 4-decimal grid (so no two distinct scores merge) leaves the plan unchanged (`tests/unit/test_stage5.py`).

## 3. Exhaustive and random checks

| Set | Instances | Greedy = brute-force lexicographic optimum | Optimum unique | CP-SAT = greedy |
|---|---|---|---|---|
| E1: 3 zones × 1 resource; requests 0–3; stock 0–5; urgency ∈ {12.5, 37.5, 62.5, 87.5}³, so with many ties | 24,576 (all combinations) | 24,576 | 24,576 | 615 of 615 checked (every 40th) |
| E2: 2 zones × 2 resources; requests 0–2; stock 0–3; urgency ∈ {12.5, 62.5, 87.5}² | 11,664 (all combinations) | 11,664 | 11,664 | 292 of 292 |
| R: new scenarios from families A–G (indices 3000–3099), random weight 1–5 per resource, ε ∈ {0.01, 1, 10} | 700 | (not enumerable) | — | **700 of 700**; 550 of these had tied scores |

Brute force enumerates every feasible integer plan and takes the lexicographic maximum of (urgency objective, tie-break). It makes no use of the separability argument, so it checks that argument independently. Unit tests keep the claim under regression:

- `test_objective_equals_exhaustive_optimum_on_small_instances`;
- `test_urgency_first_matches_greedy_on_the_fixtures`;
- `test_cp_sat_equals_greedy_for_any_positive_weights_and_epsilon`;
- the randomized invariant test (`test_no_policy_ever_violates_a_hard_constraint`).

## 4. What the solver costs

On the 700 random scenarios (one laptop, normal desktop load):

| Measure | Median |
|---|---|
| Urgency greedy, whole allocation call | 0.12 ms |
| AidOS, whole allocation call | 11.9 ms |
| of which CP-SAT's reported solve time (two phases) | 8.1 ms |
| Solver share of the AidOS call | 69% |

The remaining time is model construction in Python (one variable per zone and resource, the expressions, two solver invocations with hints) and explanation building. AidOS is roughly 100 times slower for an identical plan. Absolute times are still small; see the runtime benchmark in `docs/evaluation/stage5-supplementary.md`.

## 5. When greedy and an optimiser would differ

Greedy stays optimal as long as the problem remains a set of independent, linear, unit-weight knapsacks. It loses optimality as soon as something **couples** decisions, or makes the objective **non-linear** in x. Examples:

| Change | Why greedy can fail | Status in AidOS |
|---|---|---|
| A coverage floor (AidOS balanced) | Constraints tie each zone's allocation to the others' (a common floor per resource) | **Implemented** (`aidos_balanced`). This is where the solver changes plans. A water-filling heuristic could also compute it. |
| Per-zone transport or vehicle capacity Σ_r x_{z,r} ≤ K_z | Couples resources: a unit of water now competes with a unit of medicine for the same truck | Proposed extension; not modelled (no capacity data in the scenario schema) |
| Shipment bundles or compatible kits (x_{z,med} = x_{z,water}) | Couples resources | Proposed extension |
| Minimum lot sizes (x ∈ {0} ∪ [m, d]) | Non-convex; greedy can strand stock | Proposed extension |
| Regional delivery restrictions or route capacity shared by zones | Couples zones across resources | Proposed extension; would need geography, which is out of scope |
| A concave (diminishing-returns) objective | The exchange argument breaks; spreading can beat filling | Not implemented; balanced mode is the linear alternative |
| A time-limited solve that stops at FEASIBLE | No optimality guarantee | Never observed: every solve was OPTIMAL |

**Worked counterexample** (computed in the supplementary run; an isolated model, **not** part of AidOS or any benchmark):

- **Setup.** Zone A has urgency 87.5 and zone B 37.5. Each zone can receive at most 10 units in total (a vehicle capacity). The stock is 10 water and 10 medical kits. Zone A requests 10 of each; zone B requests 10 water. Medical kits weigh 3 in the objective, water 1.
- **Greedy** (urgency order, catalogue order water then medical) fills A's truck with water. A gets 10 water and no medicine, and B gets nothing. That is 10 units delivered, objective 8,850,000.
- **CP-SAT** sends A the 10 medical kits and B the 10 water. That is 20 units delivered, objective 30,400,000 (OPTIMAL).

So a coupling constraint like vehicle capacity is exactly where an optimiser earns its cost. It is listed as future work, because the current scenario data has no capacity information. Adding it to the benchmark without data would mean inventing a constraint to manufacture an advantage.

## 6. Implications for the project

- **Do not claim** that CP-SAT finds better urgency-first allocations than a simple heuristic. It provably does not, and the report should say so.
- **What CP-SAT does contribute today:**
  - a declarative model whose hard constraints are explicit and checked;
  - a *proof* of optimality for a stated objective;
  - exact lexicographic tie-breaking;
  - a single framework that already handles the coupled balanced mode;
  - the ability to add coupling constraints (capacity, bundles) without redesigning the algorithm.
- **An academically honest framing:** "the optimiser certifies that the transparent greedy rule is optimal for our objective, and the system is built to grow into constraints where greedy fails". That is a legitimate and examinable finding, consistent with the specification's warning (Section 5.4) that greedy may tie with the optimiser under a linear objective.
