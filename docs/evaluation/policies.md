# The four policies under evaluation

Described from the code (`apps/api/aidos/ai/`), not from intentions. All four receive the same validated `Scenario` and, where they use it, the same fuzzy urgency scores computed once per scenario (`aidos/pipeline.py::compare`). All four return one cell per (active zone, resource), checked by the same independent validator.

| | FCFS | Urgency greedy | AidOS | AidOS balanced |
|---|---|---|---|---|
| ID | `fcfs` | `greedy` | `aidos` | `aidos_balanced` |
| Code | `baseline_fcfs.py` | `baseline_greedy.py` | `constraints.py` (`objective="urgency_first"`) | `constraints.py` (`objective="balanced"`) |
| Uses fuzzy urgency | no | yes | yes | yes |
| Uses optimisation | no | no | yes, OR-Tools CP-SAT | yes, OR-Tools CP-SAT |
| Status reported | `COMPLETE` | `COMPLETE` | CP-SAT status | CP-SAT status |

## Inputs and hard constraints (shared)

- **Inputs:** active zones with ratings and requests per resource; stock per resource. Urgency policies also receive each zone's score (0–100).
- **Hard constraints:**
  - whole units;
  - 0 ≤ x ≤ request;
  - Σ_zones x ≤ stock per resource;
  - no substitution between resources.

## FCFS: first come, first served

- **Rule.** Zones in `arrival_order` (ties: zone ID). For each zone, and each resource in catalogue order, allocate min(remaining stock, request).
- **Tie-breaking.** Arrival order, then ID.
- **Complexity.** O(Z·R).
- **Strengths.** Simple and transparent, needs no urgency model, and is predictable for requesters.
- **Limitations.** Ignores urgency entirely: a critical zone that reports last can receive nothing.
- **Fairness note.** In the evaluation, arrival order is independent of urgency by construction (`families.py`), so FCFS is neither helped nor handicapped by correlated arrivals.

## Urgency greedy

- **Rule.** Zones by urgency descending (ties: arrival order, then ID). Same per-resource filling as FCFS.
- **Complexity.** O(Z log Z + Z·R).
- **Strengths.** Uses the same information as AidOS with no solver.
- **Limitations.** Serves zones strictly in urgency order, so low-urgency zones can starve under scarcity.
- **Role.** It isolates the effect of the urgency information (greedy vs FCFS) from the effect of optimisation (AidOS vs greedy).

## AidOS (urgency-first CP-SAT)

**Objective (lexicographic):**
1. Maximise Σ w_r (U_z + E) x[z,r], with U_z = 10⁴ · score, E = 10⁴ · ε, ε = 1, w_r = 1.
2. Then maximise the tie-break term Σ ρ_z x[z,r], which favours earlier arrival.

**Tie-breaking.** By the second objective, so the optimum is unique and deterministic. One worker, seed 0.

**Complexity.**
- Model size: Z·R integer variables plus R constraints.
- CP-SAT is exponential in the worst case in general. Here each phase is a small LP-like integer program that is solved to proven optimality in milliseconds; measured runtimes are in the results.

**Equivalence with greedy.**
- The objective is linear and resources are separable, so the optimum fills zones in coefficient order.
- Both policies use the same tie order.
- So **AidOS and urgency greedy return identical plans**. This is proven in `docs/algorithms/allocation-formulation.md` section 4 and confirmed on every evaluated scenario.

**Strengths.** A proof of optimality for a stated objective; a declarative model that can take coupling constraints later; exact explanations.

**Limitations.**
- Identical plans to greedy, at a higher computational cost.
- Inherits greedy's starvation behaviour.

## AidOS balanced (coverage floor, then urgency)

**Objective (lexicographic):**
1. Maximise Σ_r f_r, where every requesting zone gets x ≥ f_r·d / 1000. The floor f_r is capped at 25% of each request.
2. Then the urgency objective.
3. Then the tie-break.

**What it guarantees.** Every zone that requests a resource gets at least the largest common fraction the stock allows, up to 25%.

**Complexity.** As AidOS, plus one floor variable and one constraint per (zone, resource).

**Strengths.** Prevents starvation whenever stock allows any positive floor.

**Limitations.**
- Gives up some urgency-weighted coverage.
- The 25% target is a design choice, not tuned or validated.
- The same result could also be computed with a water-filling heuristic. The solver is a convenience here, not a necessity.

## Information advantage, stated plainly

FCFS sees arrival order but not urgency. The other three also see the fuzzy scores. A difference between FCFS and greedy is therefore an **information effect**, using the urgency model. A difference between greedy and AidOS would be an **optimisation effect**; under the urgency-first objective there is none.

Every urgency-based metric (urgency-weighted coverage, critical-zone coverage) is computed with the same fuzzy scores the urgency policies use, so those metrics measure agreement with the urgency model, not humanitarian outcomes.
