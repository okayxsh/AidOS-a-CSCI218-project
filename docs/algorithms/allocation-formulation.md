# Allocation problem: mathematical formulation

This is the problem every AidOS policy solves, and the exact model the CP-SAT policies optimise. It matches the code in `apps/api/aidos/ai/constraints.py`; if the two ever disagree, the code is wrong or this file is, and one of them must be fixed.

All data is synthetic. Thresholds, weights and coefficients are design assumptions for an academic simulation, not humanitarian standards.

## 1. Sets and inputs

| Symbol | Meaning | Source |
|---|---|---|
| $Z$ | active emergency zones (activation step ≤ scenario step) | scenario |
| $R$ | resource types (medical kits, water packs, …) | scenario |
| $d_{z,r} \in \mathbb{Z}_{\ge 0}$ | units of $r$ requested by zone $z$ | scenario |
| $s_r \in \mathbb{Z}_{\ge 0}$ | units of $r$ in the depot | scenario |
| $p_z \in [0, 100]$ | urgency score of zone $z$ | fuzzy engine (`fuzzy-logic.md`) |
| $w_r \in \{1, \dots, 100\}$ | resource weight, default 1 | configuration |
| $\varepsilon > 0$ | urgency bonus, default 1 point | configuration |

Limits enforced by validation: at most 50 zones, 10 resources, and 1,000,000 units per request or stock entry.

## 2. Decision variable

$x_{z,r} \in \mathbb{Z}$: units of resource $r$ allocated to zone $z$.

## 3. Hard constraints

Every policy (FCFS, urgency greedy, AidOS, AidOS balanced) must satisfy all of these. They are checked after the fact by a validator that does not trust the policy (section 8).

| # | Constraint | Formula | In the CP-SAT model |
|---|---|---|---|
| C1 | Non-negativity | $x_{z,r} \ge 0$ | variable domain lower bound |
| C2 | Demand limit | $x_{z,r} \le d_{z,r}$ | variable domain upper bound |
| C3 | Stock limit | $\sum_{z \in Z} x_{z,r} \le s_r$ for every $r$ | one linear constraint per resource |
| C4 | Integrality | $x_{z,r} \in \mathbb{Z}$ | CP-SAT variables are integers |
| C5 | No substitution | units of $r$ serve only demand for $r$ | each variable belongs to one resource and appears only in that resource's C3 |

C5 is structural: there is no variable or constraint that lets a water pack count toward a medical-kit request, so substitution cannot be expressed in the model.

**Not modelled.** Transport capacity, routes, travel time, delivery deadlines and multi-period arrivals are not in the data model, so the formulation has none of them. Adding any of them would be a new model, not a parameter change.

## 4. Primary objective: urgency first

$$\max \; \sum_{z \in Z} \sum_{r \in R} w_r \,(p_z + \varepsilon)\, x_{z,r}$$

Each allocated unit is worth its zone's urgency (plus $\varepsilon$), times its resource weight.

### Why this objective and not weighted coverage

Two candidates were considered.

| Candidate | Coefficient of $x_{z,r}$ | Behaviour |
|---|---|---|
| **Urgency-weighted units (chosen)** | $w_r (p_z + \varepsilon)$ | A unit is worth the same wherever in a request it lands; urgent zones are served first. |
| Urgency-weighted coverage fraction | $w_r (p_z + \varepsilon) / d_{z,r}$ | A unit is worth more the *smaller* the request it belongs to. |

The coverage-fraction form rewards filling small requests: a zone asking for 2 units would outrank a more urgent zone asking for 200, because each of its units moves "coverage" by 50%. That favours zones for asking for little, which is not what urgency means here. It also needs rational coefficients, which CP-SAT cannot take directly.

The chosen form has a direct reading in the evaluation metric. Urgency-weighted coverage (spec 5.5) is

$$\text{UWC} = \frac{\sum_{z,r} p_z\, x_{z,r}}{\sum_{z,r} p_z\, d_{z,r}}$$

and its denominator is a constant of the scenario. So with $w_r = 1$, maximising the objective is (up to the small $\varepsilon$ term) maximising UWC. The policy optimises the same quantity it is later measured on, which is stated openly wherever the two are compared.

### What each requirement in the brief maps to

| Concern | How the formulation handles it |
|---|---|
| Different demand magnitudes | Coefficients do not depend on $d$; large requests are not favoured per unit, and C2 caps each one. |
| Different resource types | Resources never compete: C3 is per resource, so the problem separates into one sub-problem per resource. $w_r$ only changes the reported objective value, not the plan, unless a future constraint couples resources. |
| Zero-demand entries | No variable is created when $d_{z,r} = 0$ or $s_r = 0$; the cell is reported as 0 with limit `no_demand` or `zero_stock`. |
| Scarcity and utilisation | Every coefficient is positive, so at an optimum no unit stays in the depot while a request for it is unmet. |
| Low-urgency zones | $\varepsilon > 0$ keeps every coefficient positive even if a score were 0 (the shipped engine never goes below 12.5), so low-urgency zones still receive leftover stock. |
| Starvation | **Not prevented.** Under scarcity the least urgent zones can receive nothing. This is a known property of a linear objective and the reason the balanced variant exists (section 6). |
| Ties | Resolved by a second objective (section 5), not by solver internals. |

### A consequence worth stating: equivalence with urgency greedy

Because the objective is linear and resources are separable, the optimum for each resource is "serve zones in decreasing coefficient until the stock runs out". That is exactly what the urgency-greedy baseline does, and both break ties the same way (earlier arrival, then zone ID). So **AidOS urgency-first and urgency greedy always return the same plan.** A randomized test asserts it, and the Stage 4 benchmark (504 scenarios) and the Stage 5 equivalence run (36,240 exhaustive small instances and 700 random scenarios; `greedy-vs-cpsat-analysis.md`) found no difference. The specification names this as a planned experimental control. What the solver adds for this objective is a proof of optimality; it changes the plan only when the model contains something greedy cannot do, which in Stage 2 is the balanced variant.

## 5. Deterministic tie-breaking

Zones with equal coefficients make several plans optimal. To make the result unique, the model is solved lexicographically:

1. Maximise the urgency objective; let $V^*$ be its optimum. Add the constraint $\text{objective} \ge V^*$.
2. Maximise $\sum_{z,r} \rho_z\, x_{z,r}$, where $\rho_z = |Z| - (\text{position of } z \text{ in arrival order})$, so earlier arrival earns a larger weight (ties in `arrival_order` are broken by zone ID).

Phase 2 cannot reduce urgency value, because phase 1's optimum is frozen first. Among zones tied on urgency, earlier arrival wins. Since $\rho_z$ is distinct per zone, the final plan is unique.

## 6. Optional variant: balanced (coverage floor)

A separately named policy, `aidos_balanced`. It adds one variable per resource and one phase before the urgency phase.

- $f_r \in \{0, 1, \dots, 1000 \cdot \tau\}$: the coverage floor of resource $r$ in thousandths, where $\tau$ is the target (default 0.25).
- For every zone that requests $r$ (and $s_r > 0$): $1000\, x_{z,r} \ge f_r\, d_{z,r}$, i.e. $x_{z,r} / d_{z,r} \ge f_r / 1000$.

Lexicographic order: (0) maximise $\sum_r f_r$; (1) urgency objective; (2) tie-break.

**What is guaranteed, exactly:** every zone requesting resource $r$ receives at least $\lceil f_r\, d_{z,r} / 1000 \rceil$ units, where $f_r$ is the largest floor the stock allows, capped at the target. When stock is too low for the target, the floor shrinks (possibly to 0) rather than making the model infeasible.

**What is not guaranteed:** equal coverage, proportional shares, or a maximal Jain index. Above the floor, the remaining stock still goes by urgency. The floor costs urgency value by construction; the UI and the experiment records show both.

## 7. Integer scaling

CP-SAT needs integer coefficients. The fuzzy engine returns scores with exactly 4 decimals, so multiplying by 10,000 gives an exact integer and loses nothing:

$$c_{z,r} = w_r \cdot \big(10^4\, p_z + \operatorname{round}(10^4\, \varepsilon)\big)$$

Example: $p_z = 70.8333$, $\varepsilon = 1$, $w_r = 1$ gives $c = 708{,}333 + 10{,}000 = 718{,}333$. The reported `objective_value` is in these units; divide by `objective_scale` (10,000) for urgency·units.

Because the scale matches the score's resolution, two zones have equal coefficients exactly when they have equal scores. The solver and the urgency-greedy baseline therefore agree on what a tie is.

Worst-case magnitude: $c \le 100 \cdot 2 \times 10^6 = 2 \times 10^8$, $x \le 10^6$, at most 500 variables, so the objective is at most $10^{17}$, inside 64-bit integers ($9.2 \times 10^{18}$). Each phase's objective value is recomputed from the solution in exact integer arithmetic rather than read from the solver's floating-point report.

## 8. Independent validation

`apps/api/aidos/evaluation/invariants.py` checks a returned plan against the **scenario**, not against what the policy reports. A solver status of `OPTIMAL` is never accepted as proof of validity.

| Check | Verifies | Kind |
|---|---|---|
| `integer` | every allocation is a whole number | hard |
| `non_negative` | C1 | hard |
| `within_demand` | C2, against the scenario's demand (not the cell's own `requested` field) | hard |
| `within_stock` | C3, summed per resource with no netting between resources (so C5 cannot be bypassed) | hard |
| `complete` | exactly one cell per active zone and resource; no unknown zone/resource; reported requests equal the scenario's | hard |
| `no_idle_stock` | no resource keeps unused stock while a zone still lacks it | quality (reported, not a violation) |

## 9. Solver statuses

| Status | Meaning in AidOS | Plan returned? |
|---|---|---|
| `OPTIMAL` | every phase was proven optimal | yes |
| `FEASIBLE` | a valid plan exists but at least one phase was not proven optimal (for example, the time limit) | yes, labelled "not proven optimal" |
| `INFEASIBLE` | CP-SAT proved the model has no solution | no |
| `UNKNOWN` | no solution found within the limit | no |
| `MODEL_INVALID` | CP-SAT rejected the model | no |
| `COMPLETE` | a deterministic heuristic (FCFS, greedy) finished; no optimality claim | yes |

The hard constraints always admit the all-zero plan, so `INFEASIBLE` should not occur for a valid scenario. It is still handled: no plan is fabricated, and the response says why.

## 10. Worked example (`triage-demo-001`)

Numbers below were produced by running the engine (version 0.2.0), not written by hand.

Stock: 90 medical kits, 180 water packs, 60 shelter kits. Requests total 560 against 330 in stock.

| Zone (arrival) | Urgency $p_z$ | Coefficient | Medical | Water | Shelter |
|---|---|---|---|---|---|
| A (1st) | 87.5 critical | 885,000 | 75 | 100 | 30 |
| B (2nd) | 62.5 high | 635,000 | 45 | 130 | 50 |
| C (3rd) | 70.8333 high | 718,333 | 30 | 60 | 40 |

Allocated / requested per policy:

| Policy | Zone A | Zone B | Zone C | Status |
|---|---|---|---|---|
| FCFS | 75 · 100 · 30 | 15 · 80 · 30 | 0 · 0 · 0 | COMPLETE |
| Urgency greedy | 75 · 100 · 30 | 0 · 20 · 0 | 15 · 60 · 30 | COMPLETE |
| AidOS urgency-first | 75 · 100 · 30 | 0 · 20 · 0 | 15 · 60 · 30 | OPTIMAL (objective 269,549,965) |
| AidOS balanced (τ = 0.25) | 70 · 100 · 30 | 12 · 33 · 13 | 8 · 47 · 17 | OPTIMAL (objective 265,549,976) |

| Metric | FCFS | Greedy | AidOS | AidOS balanced |
|---|---|---|---|---|
| Units allocated | 330 | 330 | 330 | 330 |
| Unmet units | 230 | 230 | 230 | 230 |
| Urgency-weighted coverage | 0.6249 | 0.6461 | 0.6461 | 0.6364 |
| Lowest zone coverage | 0.000 | 0.089 | 0.089 | 0.258 |
| Jain fairness | 0.616 | 0.722 | 0.722 | 0.804 |

Reading it:

- **Every policy hands out all 330 units.** Optimisation does not create supplies; it changes who receives them.
- FCFS serves A then B and leaves **Zone C with nothing**, although C is more urgent than B.
- AidOS (and greedy) serve A, then C, then B. Medical kits: A takes 75 of 90, C takes the remaining 15, B gets 0.
- AidOS and greedy are identical here, as section 4 predicts.
- Balanced gives every zone at least 25% of each request (B's 12 of 45 medical kits is $\lceil 0.25 \times 45 \rceil$) and pays for it: the urgency objective drops from 269,549,965 to 265,549,976 (about 1.5%) and Zone A loses 5 medical kits.

This is one scenario. It shows how the policies differ, not that one is better in general; that question belongs to the Stage 4 experiments.
