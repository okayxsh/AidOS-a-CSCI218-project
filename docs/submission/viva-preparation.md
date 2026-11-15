# Viva preparation

Short, factual answers to questions an examiner is likely to ask. Every number comes from a saved run (paths given) and can be shown live. The rubric (CSCI218 guidelines, section 6.1) says at least one question will be about a part of the system **you did not build**, so every member should be able to answer all of these.

Abbreviations: **UWC** = urgency-weighted coverage; **FCFS** = first come, first served.

## The AI techniques

**Q: What problem does AidOS solve?**
A coordinator has less stock than the zones request. AidOS scores how urgent each zone is, then proposes a whole-unit allocation per resource that never exceeds the stock or any request. It explains every number, and it recomputes when the crisis changes. It is a simulation on synthetic data, not a dispatch system.

**Q: Why fuzzy logic for urgency?**
Field ratings such as "severity 7" are imprecise. Fuzzy sets let a 7 be partly "medium" and partly "high", so a small change in a rating changes the score smoothly instead of jumping between hard categories. The 27 rules are readable sentences ("IF severity is high AND time criticality is high THEN urgency is critical"), so a coordinator can audit why a zone scored what it did.

**Q: Why Sugeno and not Mamdani?**
- **Monotonicity.** We measured both on our own rules (`experiments/fuzzy_method_comparison.py`). Mamdani min/max lowered the score on 2.0% of small rating *increases*, by up to 0.9 points. Zero-order Sugeno with a product AND never did, and it cannot: with membership degrees that sum to 1 per input and a rule table that never lowers urgency when an input rises, the score is a weighted average that can only rise.
- **Exact explanations.** The rule strengths sum to 1, so each rule's contribution (strength × output) adds up to the score.
- **The cost.** We lose Mamdani's "clipped sets and centroid" picture.
- **Status.** The choice is documented in `docs/decisions/0004-*`. It is **pending instructor confirmation**.

**Q: How is a score computed, step by step?**
For Zone C of the demo (severity 7, time criticality 7, vulnerability 5):
1. Severity 7 is 1/3 medium and 2/3 high; time criticality is the same; vulnerability 5 is fully medium.
2. Four rules fire, with strengths 4/9, 2/9, 2/9 and 1/9 (products of degrees).
3. The score is the weighted average of their outputs (87.5, 62.5, 62.5, 37.5) = **70.83**, category "high". (`docs/algorithms/fuzzy-logic.md`, section 7.)

**Q: Do the urgency scores represent real need?**
No. The membership functions, rules and output values are design assumptions. Monotonicity and readable rules make the scores *consistent and explainable*, not *correct*.
- In the sensitivity study (`supplementary-fuzzy-sensitivity-*`), shifting the membership breakpoints by one point changed the zone ranking in about half of 280 scenarios (142–144), and the AidOS plan in 103–113 of them (about 37–40%). Across all ten variants the plan changed in 0–41% of scenarios, and only 2–6% of units moved.
- Changing the output values changed nothing, because AidOS only uses the *order* of the scores.

**Q: What does the CP-SAT optimiser maximise?**
Σ over zones and resources of w_r × (urgency_z + ε) × x_{z,r}, in exact integers (scores × 10,000). Ties are then broken by a second solve that prefers earlier arrival. The hard constraints are whole units, 0 ≤ x ≤ request, and Σ_zones x ≤ stock per resource. (`docs/algorithms/allocation-formulation.md`.)

**Q: Why does urgency greedy give exactly the same plans as CP-SAT?**
Because, for our objective, it has to:
- Every constraint concerns one resource, so the problem splits into independent "knapsacks" with unit weights.
- With positive coefficients, the optimum fills zones in coefficient order. Moving a unit from a lower to a higher coefficient always improves the objective.
- Within a resource, the coefficient order equals the urgency order, and the tie-break is the same as greedy's.

So the optimum *is* the greedy plan. We checked 36,240 small instances exhaustively and 700 random ones with random weights, with 100% agreement. (`docs/algorithms/greedy-vs-cpsat-analysis.md`.)

**Q: Then why use CP-SAT at all?**
- It proves the plan is optimal for the stated objective.
- It handles the balanced mode, whose floor constraint couples the zones.
- Constraints that make greedy wrong can be added without redesigning the algorithm. For example, with a per-zone vehicle capacity our counterexample has CP-SAT delivering 20 units where greedy delivers 10.

We do not claim CP-SAT finds better urgency-first plans than greedy.

**Q: Why does AidOS balanced improve the equity metrics?**
It first maximises, per resource, a common floor: every requesting zone gets at least f × its request, with f up to the target (25% by default). Only then does it allocate the rest by urgency. No zone can be left with nothing while the stock allows any floor.
- On the 504-scenario benchmark: starved zones 0, lowest-zone coverage 0.360 (vs 0.180 for AidOS), Jain index 0.860 (vs 0.735).
- The cost: UWC 0.734 vs 0.765.

**Q: What happens when the minimum coverage is infeasible?**
The floor is not a hard guarantee. CP-SAT finds the largest common floor the stock allows, up to the target, and it is reported per resource. In the floor sweep (`supplementary-floor-sweep-*`) a 25% target had to be reduced on 5 of 1,003 resource cases; a 40% target on 136. A 10% floor already removed all starvation in those 280 scenarios.

**Q: How are the hard constraints enforced?**
Twice, independently:
1. **In the model:** variable domains and one stock constraint per resource.
2. **In a separate validator** (`evaluation/invariants.py`): it re-checks every returned plan against the *scenario* (not the policy's own numbers) for whole units, non-negativity, ≤ request, ≤ stock, and exactly one cell per zone and resource. A violation is reported as an error, never a lower score.

All 2,016 Stage 4 plans passed.

## Simulation

**Q: How does the simulation handle a new event?**
1. The event is validated against the current state.
2. It is applied to a *copy* of the scenario.
3. The copy is re-validated.
4. Fuzzy scores are recomputed, all four policies re-run, and every plan is validated.
5. A new step is appended with a version number.

If anything fails, nothing changes (atomic). An invalid event gets a specific error, such as "insufficient_stock" when a loss is larger than the stock.

**Q: What is a recommendation versus a dispatch?**
- **A recommendation** is a candidate plan. Computing it never touches stock.
- **A dispatch** ("plan_committed") removes the plan's units from stock and from the open requests, exactly once, and records them in an append-only ledger. It names the snapshot hash it was computed for, so a stale or repeated dispatch is rejected.

**Q: What is deterministic replay?**
The same initial scenario, the same events in the same order, and the same configuration give the same snapshot hash, scores, plans and *outcome hash* at every step. Timings are excluded. Reset followed by replay reproduces every hash, and an exported JSON file re-imports with verification. The committed demo script is checked by a test.

## Evaluation

**Q: Why can late, urgent arrivals disadvantage FCFS?**
FCFS serves zones in arrival order, so a zone that reports after the stock has been allocated gets nothing, however urgent it is. Our Stage 4 dynamic scripts always added a *high-urgency* late zone, which made AidOS look fairer than FCFS.

The Stage 5 controlled experiment (`supplementary-dynamic-controlled-*`) varied the late zone's urgency:
- FCFS never served it at any level.
- AidOS served it roughly in proportion to its urgency: new-zone coverage 0 (low), 0.39 (moderate) and 0.95 (high) in recommendation mode.
- AidOS left the *original* zones' worst coverage **lower** than FCFS at every level.

So urgency-first is not "fairer"; it redistributes towards whoever scores urgent.

**Q: What do the experiments show?**
On 504 synthetic scenarios (seven families), 60 Stage 4 event scripts and 120 controlled Stage 5 scripts:
- Every plan from every policy is feasible, and every CP-SAT solve is proven optimal.
- All policies deliver the same number of units.
- Urgency-based policies raise UWC (+0.102 vs FCFS, 95% CI 0.092 to 0.112) and critical-zone coverage (+0.288).
- They do not improve the worst-off zone, starvation or the Jain index (CIs around 0).
- The coverage floor removes starvation at a measured cost in UWC.
- AidOS is about 100× slower than greedy, at the millisecond scale.

**Q: What do they not show?**
- That AidOS is "better" overall. Its advantage is on UWC, which it maximises by construction, and that metric is defined by our own urgency model.
- Anything about real people, real disasters, or lives saved.
- How the system behaves outside the generator's ranges: more than 50 zones, correlated arrival and urgency, other rule bases.

**Q: Why can't synthetic evaluation establish real humanitarian effectiveness?**
The scenarios come from distributions we chose, the urgency ratings are invented, and the scoring rules are our assumptions. The confidence intervals only describe variation *within that synthetic world*. Real effectiveness would need real (authorised, anonymised) data, validated urgency criteria, and comparison against expert decisions or outcomes.

**Q: What would be needed before real deployment?**
- Validated urgency criteria agreed with humanitarian experts, and calibration against real cases.
- Real logistics constraints: transport capacity, routes, delivery times, bundles, perishability.
- Field-tested data quality and uncertainty handling.
- Persistent, secure, audited storage with authentication; a multi-user, multi-process design.
- Legal, ethical and accountability review.
- Mandatory human approval of every dispatch.

None of this exists, and AidOS does not claim it.

**Q: If the problem doubled in size, what happens?**
The engine accepts at most 50 zones and 10 resources (input validation). In the benchmarks, runtime grew roughly linearly with zones for the heuristics, and faster for CP-SAT (see the Stage 5 runtime benchmark).

At the largest size the API accepts (50 zones × 10 resources), balanced mode can reach its 5 s limit. One check with every entry at the 1,000,000-unit cap finished in about 2.6 s, but random requests at that size stopped at the limit with a valid plan labelled FEASIBLE, not proven optimal. Urgency-first AidOS stayed OPTIMAL. The status is always reported truthfully.
