# Viva question bank

A practice bank for the individual viva after the group demo. It builds on [`viva-preparation.md`](viva-preparation.md) and is consistent with it.

## How to use this

- **Everyone prepares every question.** Each student gets 2–3 short questions, and at least one is about a part they did not build. If a student cannot explain their own contribution, the group mark is capped at 55/80. So nobody can skip the fuzzy engine, the solver, the simulator or the evaluation because "someone else did that part".
- **These are study notes, not a script.** Read an answer, close the file, and explain it aloud in your own words. Examiners notice recited text, and a follow-up question will expose it.
- **Numbers.** Every number here comes from a saved run or a doc in this repository, and the source is named. If you cannot remember a number, say so and say where it is recorded. Do not guess.
- **Layout.** The questions go from Foundation through Core to Challenging. Within each level they are grouped by topic: Fundamentals; Fuzzy inference; Optimisation; Fairness; Simulation; Evaluation; Architecture and engineering; Limitations and ethics. "If pushed" gives the next level of detail. "Where in the code" gives the file to open if the examiner asks you to show it.

Abbreviations: **UWC** = urgency-weighted coverage; **FCFS** = first come, first served. Code paths are relative to `apps/api/aidos/` unless they start with `apps/`, `tests/`, `experiments/` or `docs/`.

---

## Level 1: Foundation

### Fundamentals

**Q1. What problem does AidOS solve?**
A relief coordinator has less stock than the zones are asking for and has to decide who gets what. AidOS scores how urgent each zone is, then proposes a whole-unit allocation for each resource that never exceeds the stock or any zone's request, and explains every number. When the situation changes (a new zone, a lost shipment, an escalation), it recomputes. It is an academic decision-support prototype on synthetic data. It does not dispatch real aid.
*If pushed:* the output is a *recommendation*. Stock moves only when the user explicitly commits a plan in the simulator.
*Where in the code:* `pipeline.py` (`compare`) is the single entry point that runs urgency scoring, the policies, validation and metrics.

**Q2. What makes this AI rather than ordinary automation?**
Ordinary automation applies a fixed rule such as "first come, first served". AidOS uses two classic AI techniques. Fuzzy inference reasons with imprecise, partly true categories ("severity 7 is partly medium and partly high") through a readable rule base. Constraint optimisation searches a space of possible plans for the best one under hard constraints and proves it is optimal. A third component, a finite-state simulator, re-plans as the environment changes.
*If pushed:* be honest that for the urgency-first objective the optimiser returns the same plan as a simple greedy rule (Q25). The "intelligence" there is the proof of optimality and the ability to handle constraints greedy cannot, such as the balanced coverage floor.
*Where in the code:* `ai/fuzzy.py`, `ai/constraints.py`, `simulation/fsm.py`.

**Q3. What is a baseline, and which baselines does AidOS use?**
A baseline is a simple, well-understood method you compare against, so you can tell what your method actually adds. AidOS has two. FCFS serves zones in arrival order and ignores urgency. Urgency greedy uses the same fuzzy scores as AidOS but no optimiser. It serves zones from most to least urgent.
*If pushed:* FCFS has not been changed since Stage 1 and was not weakened. In the generated scenarios, arrival order is independent of urgency, so FCFS is neither helped nor handicapped (`docs/evaluation/policies.md`).
*Where in the code:* `ai/baseline_fcfs.py`, `ai/baseline_greedy.py`.

### Fuzzy inference

**Q4. Why use fuzzy logic for urgency?**
Field ratings such as "severity 7 out of 10" are imprecise. Hard thresholds would make a 6.9 and a 7.0 land in different categories. Fuzzy sets let a rating belong partly to "medium" and partly to "high", so a small change in a rating changes the score smoothly. The 27 rules are readable sentences, so a coordinator can audit why a zone got its score.
*If pushed:* each zone's explanation lists every rule that fired, its strength and how many points it contributed to the score.
*Where in the code:* `ai/fuzzy.py`; rules in `config/fuzzy_rules.json` (version 1.0).

**Q5. What are membership functions, and which ones does AidOS use?**
A membership function maps a crisp value to a degree between 0 and 1 of belonging to a fuzzy set. Each of the three inputs (severity, time criticality, vulnerability, each 0–10) uses the same three sets. "Low" is a trapezoid (0, 0, 2, 5), "medium" a triangle (2, 5, 8), and "high" a trapezoid (5, 8, 10, 10). The sets overlap, and at every rating the three degrees add up to exactly 1. For example, 7 is one third medium and two thirds high.
*If pushed:* that sum-to-1 property is called a Ruspini partition. A test checks it at 1,001 points per input, and the monotonicity proof depends on it.
*Where in the code:* `config/fuzzy_rules.json` (`inputs`); `tests/unit/test_fuzzy.py`.

**Q6. How are the rules activated?**
There are 27 rules, one for every combination of low, medium and high across the three inputs, so no input falls into a gap. A rule's firing strength is the product of its three antecedent degrees. If any one of them is 0, the rule does not fire. Because each input's degrees add to 1, the strengths of all 27 rules also add to 1.
*If pushed:* product is used as the AND operator, not min. With min the system is not monotone (Q20).
*Where in the code:* `ai/fuzzy.py` (`evaluate`: `math.prod` over the antecedent degrees).

**Q7. How is the urgency score computed? Walk through an example.**
Each rule outputs a constant: 12.5 for low, 37.5 for moderate, 62.5 for high and 87.5 for critical. The score is the strength-weighted average of the outputs of the rules that fired. For Zone C of the demo (severity 7, time criticality 7, vulnerability 5), four rules fire with strengths 4/9, 2/9, 2/9 and 1/9, giving outputs 87.5, 62.5, 62.5 and 37.5. The weighted average is 70.83, which falls in the "high" band (50 to under 75).
*If pushed:* the score is rounded to 4 decimal places, which removes floating-point noise at band edges and gives the solver exact integer coefficients. Scores can only lie between 12.5 and 87.5, because they are averages of band centres.
*Where in the code:* `ai/fuzzy.py`; worked example in `docs/algorithms/fuzzy-logic.md` section 7.

### Optimisation

**Q8. What is a constraint satisfaction problem?**
A CSP has variables, a domain of allowed values for each variable, and constraints that restrict which combinations are allowed. A solution assigns a value to every variable without breaking any constraint. When you also have an objective to maximise, it becomes a constraint *optimisation* problem, which is what AidOS solves. In AidOS the variables are x[z, r], the units of resource r for zone z. Each domain is 0 up to that zone's request, and the constraints are the stock limits.
*Where in the code:* `ai/constraints.py` (`allocate_aidos`).

**Q9. What is CP-SAT?**
CP-SAT is Google OR-Tools' solver for integer constraint programming. It combines constraint propagation, SAT-style clause learning and linear-programming bounds. Because it works only with integers, it fits whole-unit allocation. It reports a status, and OPTIMAL means it has proved no better solution exists. AidOS runs it with one worker and a fixed seed (0) so the search is reproducible.
*If pushed:* the time limit is 5 seconds in total, shared across the solve phases. The API accepts values from 0.01 to 10 s.
*Where in the code:* `ai/constraints.py`; configuration in `docs/algorithms/cp-sat-allocation.md` section 3.

**Q10. What does AidOS maximise?**
It maximises the sum over zones and resources of w_r × (urgency_z + ε) × x[z, r]. In words, every unit is worth its zone's urgency score, plus a small bonus ε of 1 point, times a resource weight, which is 1 by default. ε keeps every coefficient positive, so a low-urgency zone still receives leftover stock. Scores are multiplied by 10,000 so all the coefficients are exact integers. A second solve then breaks ties in favour of earlier arrival.
*If pushed:* a "coverage fraction" objective (dividing by the request) was rejected, because it rewards zones for asking for little (decision record 0004).
*Where in the code:* `ai/constraints.py` (`coefficients`); `docs/algorithms/allocation-formulation.md` section 4.

**Q11. What are the hard constraints?**
There are five. Allocations are whole units. They are not negative. No zone gets more than it requested. For each resource, the total allocated is at most the stock. There is no substitution between resources, so water never counts toward a medical-kit request. The first three come from the variable domains. The stock limit is one linear constraint per resource, and no substitution holds by construction, because each variable belongs to only one resource.
*If pushed:* every plan, whichever policy produced it, is re-checked by an independent validator against the scenario itself (Q30).
*Where in the code:* `ai/constraints.py`; `evaluation/invariants.py`.

### Fairness

**Q12. What is starvation?**
A zone is starved when it requested something and received nothing at all. Urgency-first allocation can starve the least urgent zones under scarcity, because the higher-urgency zones use up the stock first. FCFS starves whoever arrives late, however urgent they are. In the 504-scenario benchmark the share of zones starved was similar: 0.135 for AidOS and 0.133 for FCFS. Only the *identity* of the starved zones differs.
*If pushed:* AidOS balanced had zero starved zones in all 504 scenarios.
*Where in the code:* `evaluation/metrics.py` (`starved_zones`); `docs/evaluation/results.md` section 2.

### Simulation

**Q13. What is the difference between a recommendation and a dispatch?**
A recommendation is a candidate plan. All four policies compute one after every event, and computing it never touches stock or requests. A dispatch happens only through an explicit `plan_committed` event. It subtracts that plan's units from the stock and from the zones' open requests exactly once, and records them in an append-only ledger.
*If pushed:* resolving a zone later does not return dispatched units to the depot. The ledger keeps them.
*Where in the code:* `simulation/reducer.py` (the `PlanCommitted` branch); `docs/simulation/events.md`.

**Q14. How do events work? (Also asked as "What happens if the environment changes?")**
There are eight event types: zone added, urgency changed, supply arrived, supply lost, request updated, zone resolved, time advanced and plan committed. An event is checked against the current state and applied to a *copy* of the scenario, and the copy is re-validated. Then every zone is re-scored, all four policies re-run, every plan is validated, and a new step is appended with the version increased by one. If anything fails, the stored session is unchanged and the user gets a specific error, such as `insufficient_stock` when a loss is larger than the stock.
*If pushed:* `urgency_changed` and `request_updated` carry absolute new values, not deltas, so replaying them cannot drift. Only `time_advanced` moves the scenario clock.
*Where in the code:* `simulation/events.py` (schema), `simulation/reducer.py` (apply), `simulation/session.py` (`apply`).

### Evaluation

**Q15. Why compare four policies?**
Each pair isolates one effect. FCFS against urgency greedy shows the effect of the *information*: using the fuzzy urgency model. Greedy against AidOS shows the effect of the *optimiser*, and for the urgency-first objective that effect is zero, because they produce identical plans. AidOS against AidOS balanced shows the effect of the coverage floor, the trade-off between priority and equity. Without greedy, we might have credited the solver with gains that come entirely from the urgency scores.
*Where in the code:* `docs/evaluation/policies.md` ("Information advantage, stated plainly").

### Architecture and engineering

**Q16. Why FastAPI?**
The engine is pure Python, because OR-Tools and our fuzzy code are Python. FastAPI is a thin, typed way to expose it over HTTP. Its request and response schemas are Pydantic models, so malformed input is rejected with a clear 422 before any computation. It also generates interactive OpenAPI docs at `/docs`. FastAPI only adapts input and output. The domain and algorithm code never imports it, so the experiments call the same engine offline.
*Where in the code:* `main.py` (app, CORS, one error shape); `api/routes_*.py`; `api/schemas.py`.

**Q17. How does the React frontend talk to the backend?**
It sends JSON over HTTP with `fetch` to the FastAPI server, by default at `http://localhost:8000`, or at `VITE_API_BASE_URL` if that is set. The backend allows the Vite dev and preview origins through CORS. The frontend never computes allocations, scores or metrics. It renders what the backend returns, so every number on the dashboard comes from the engine. Errors come back in one shape, `{error: {code, message, details}}`, and the client tells "engine not running" apart from "engine said no".
*Where in the code:* `apps/web/src/api/client.ts`; `main.py` (`CORSMiddleware`).

### Limitations and ethics

**Q18. Why can't synthetic experiments show real-world impact?**
The scenarios come from distributions we chose, the ratings are random numbers, and the urgency rules are our own design assumptions. The confidence intervals describe variation *within that synthetic world* only. Showing real impact would need real (authorised, anonymised) data, urgency criteria validated with humanitarian experts, and comparison against expert decisions or real outcomes. None of that exists here, and we do not claim it.
*Where in the code:* `docs/evaluation/experimental-protocol.md` ("Scope of inference").

---

## Level 2: Core

### Fundamentals

**Q19. Why must allocations be whole numbers?**
You cannot send 2.4 medical kits or 0.7 of a shelter kit. Relief items are indivisible units. CP-SAT works only with integers, so integrality is built into the model rather than obtained by rounding afterwards. Rounding a fractional plan could push a total over the stock or a request. The independent validator also checks that every allocation is a whole number.
*If pushed:* for the urgency-first objective the LP relaxation already has an integral optimum, because the stock and requests are integers. The balanced floor, however, needs ceiling arithmetic: a zone gets at least ⌈f_r × d / 1000⌉ units.
*Where in the code:* `ai/constraints.py` (`new_int_var`); `evaluation/invariants.py` (the `integer` check).

### Fuzzy inference

**Q20. Why Sugeno instead of Mamdani?**
The specification preferred Mamdani but allowed "a fully documented zero-order Sugeno design". We chose Sugeno after measuring both on our own rules. Over 52,920 small single-rating increases, Mamdani min/max lowered the score 1,062 times (2.01%, worst dip 0.89 points). Sugeno with a min AND lowered it 968 times (worst 2.5 points). Sugeno with a product AND never lowered it. As a bonus, the rule contributions add up exactly to the score, which makes the explanations exact.
*If pushed:* the cost is losing Mamdani's "clipped output sets and centroid" picture. The choice is recorded in decision 0004, and **instructor approval is still pending** (`docs/submission/instructor-review.md`, item 1).
*Where in the code:* `experiments/fuzzy_method_comparison.py`; `docs/decisions/0004-stage2-fuzzy-method-and-objective.md`.

**Q21. What does monotonicity mean here, and why is it guaranteed?**
Monotonicity means that if a zone's severity, time criticality or vulnerability goes up, its urgency score never goes down. In plain words, a situation getting worse can never make a zone less urgent. With product-Sugeno it holds by construction. The rule strengths act like a probability distribution over rule outputs. Raising a rating shifts weight only toward higher terms, and the rule table never lowers urgency when an input rises. So the weighted average can only stay the same or go up.
*If pushed:* Mamdani dips because max aggregation keeps only the strongest rule per output term, so raising a rating can weaken that rule and pull the centroid down slightly. The test `test_monotone_in_every_input` checks the property on a grid. The proof is why it holds everywhere.
*Where in the code:* `tests/unit/test_fuzzy.py`; `docs/algorithms/fuzzy-logic.md` section 5.

**Q22. Why did your team choose this rule base?**
It is complete (all 27 combinations, so no gap), order-preserving (raising any one input by one level never lowers a rule's output, which the monotonicity proof needs), and readable. Severity and time criticality set the base level. High vulnerability raises it by one level, capped at critical, so a highly vulnerable zone is never rated "low". The config loader refuses a rule base with a missing or duplicate combination.
*If pushed:* one limitation is that low and medium vulnerability are treated the same. Another is that "population" is deliberately not an input, because a fourth input would raise the rule count from 27 to 81.
*Where in the code:* `config/fuzzy_rules.json`; `ai/fuzzy.py` (`parse_config`).

### Optimisation

**Q23. What does OPTIMAL mean, and which other statuses can appear?**
OPTIMAL means CP-SAT *proved* that no better plan exists for the stated objective, and AidOS reports it only if every solve phase was proven. FEASIBLE means a valid plan was found but not proven optimal, for example when the time limit ran out. The plan is still returned, labelled "not proven optimal". INFEASIBLE, UNKNOWN and MODEL_INVALID return no plan at all: no cells, metrics null, and a message saying why. FCFS and greedy report COMPLETE, which makes no optimality claim.
*If pushed:* each phase's own status, objective and bound are returned under `solver.phases`, so the summary can be audited. In the evaluation, all 1,008 CP-SAT runs were OPTIMAL.
*Where in the code:* `ai/policies.py` (`PolicyStatus`); `ai/constraints.py` (status handling after the phase loop).

**Q24. What does "lexicographic" solving mean in AidOS?**
AidOS solves in phases, and each phase's optimum is frozen before the next one starts. For `aidos`, phase 1 maximises urgency value. Its result becomes a constraint (objective ≥ that value), and phase 2 maximises a tie-break that favours earlier arrival. Phase 2 can therefore choose only among plans that are already urgency-optimal. Balanced mode adds a phase 0 that maximises the coverage floor first.
*If pushed:* because the tie-break weights differ for every zone, the final plan is unique, so any correct solver run returns the same allocation. That is part of why replay is deterministic.
*Where in the code:* `ai/constraints.py` (the `phases` list and `model.add(expr >= reached)`).

**Q25. Why does urgency greedy give exactly the same plans as CP-SAT?**
Because, for our objective, it has to. Each constraint involves only one resource, so the problem splits into a separate small problem for each resource. Within one resource, an exchange argument applies: if a more urgent zone is not full while a less urgent zone has a unit, moving that unit across increases the objective. So the best plan fills zones strictly in urgency order, which is exactly what greedy does. Both also break ties the same way, by earlier arrival and then zone ID.
*If pushed:* this was checked on 36,240 exhaustive small instances (greedy equals the unique brute-force optimum every time) and on 700 random scenarios with random resource weights and ε (100% identical). It also held in all 504 benchmark scenarios.
*Where in the code:* `docs/algorithms/greedy-vs-cpsat-analysis.md`; `tests/unit/test_stage5.py` (`test_cp_sat_equals_greedy_for_any_positive_weights_and_epsilon`).

**Q26. Then why use CP-SAT at all?**
It gives three things greedy does not. First, a *proof* that the plan is optimal for the stated objective. Second, the balanced mode, where a common coverage floor couples the zones together. Third, room to add constraints that break greedy without redesigning the algorithm. We do not claim CP-SAT finds better urgency-first plans than greedy. A fair summary: "the optimiser certifies that the transparent greedy rule is optimal for our objective, and the system can grow into constraints where greedy fails."
*If pushed:* even the balanced floor could be computed with a water-filling heuristic. The solver is a convenience there, not a necessity (`docs/evaluation/policies.md`).

### Fairness

**Q27. What is the Jain index?**
Jain's fairness index is (Σ f_z)² / (n × Σ f_z²), where f_z is each zone's coverage (units received ÷ units requested) and n is the number of zones with demand. It ranges from 1/n, when one zone gets everything and the rest get nothing, up to 1, when every zone has the same coverage. It is N/A if every zone's coverage is 0. It measures *equality* of coverage, not fairness in an ethical sense.
*If pushed:* Jain can be high when everyone gets very little, so we always read it together with the lowest zone coverage. Benchmark means: FCFS 0.737, AidOS 0.735, AidOS balanced 0.860.
*Where in the code:* `evaluation/metrics.py` (`compute_metrics`).

**Q28. Why does AidOS balanced improve the equity metrics?**
Before allocating by urgency, it maximises a common floor for each resource. Every zone that requests the resource gets at least that fraction of its request, up to a 25% target. Only the remaining stock then goes by urgency. So no zone is left with nothing while the stock allows any floor at all. On the 504-scenario benchmark, balanced had zero starved zones (AidOS: 0.821 per scenario), lowest zone coverage 0.360 (AidOS: 0.180) and a Jain index of 0.860 (AidOS: 0.735). The cost is UWC 0.734 against 0.765.
*If pushed:* in the paired comparison, balanced lost 0.031 UWC [−0.034, −0.028] and gained 0.180 lowest zone coverage [0.171, 0.189] against AidOS. It stays above FCFS on UWC (+0.071).
*Where in the code:* `ai/constraints.py` (`objective == "balanced"`); `docs/evaluation/results-tables.md` sections 2–3.

**Q29. Why isn't equal allocation automatically fair?**
Zones differ in need. Giving a critical zone and a mildly affected zone the same share of their requests ignores that difference. An urgency-first policy *intends* unequal coverage. On the other hand, purely urgency-driven allocation can starve low-scoring zones completely, and those scores come from an unvalidated model. So we report equity metrics as descriptions of the distribution, not as an ethical ranking. The coverage floor is a middle ground, and its level is a value judgement, not a technical result.
*Where in the code:* `docs/evaluation/metric-definitions.md` section E.

### Simulation

**Q30. How are the hard constraints guaranteed, even if the solver has a bug?**
They are enforced twice. They are built into the model, and they are re-checked afterwards by a separate validator that does not trust the policy. The validator compares every returned plan with the *scenario*, not with the policy's own numbers. It checks whole units, non-negativity, ≤ request, ≤ stock for each resource, and exactly one cell per active zone and resource. A status of OPTIMAL is never accepted as proof of validity, and any violation is reported as an error, never as a lower score.
*If pushed:* in the simulator, a plan that fails the validator puts the session into ERROR and the event is not applied. All 2,016 Stage 4 static plans passed.
*Where in the code:* `evaluation/invariants.py` (`validate_allocation`).

**Q31. How is inventory conserved?**
Only two things change stock: supply events and dispatch. A supply loss larger than the stock is rejected, never clipped, so stock never goes negative. A dispatch subtracts each cell's units from the stock and the same units from that zone's open request, and the reducer checks again that no cell exceeds either. The evaluation checks the identity "initial stock + arrivals − losses − dispatched = final stock" for every resource. It held in 240 of 240 Stage 4 dispatch runs and 480 of 480 Stage 5 runs.
*Where in the code:* `simulation/reducer.py`; `evaluation/dynamic.py` (`inventory_conserved`).

**Q32. What prevents double dispatch?**
Every `plan_committed` event must name the snapshot hash the plan was computed for. A dispatch changes the scenario, so it changes the snapshot hash. If someone sends the same commit again, it names the old hash and is rejected as `stale_plan` (HTTP 409), and nothing is dispatched. Separately, every change must carry the session's `expected_version`, and a per-session lock serialises changes, so two tabs cannot both commit.
*If pushed:* the evaluation re-sent every commit and confirmed the rejection: 240/240 in Stage 4 and 480/480 in Stage 5. A test fires four simultaneous changes with the same version, and exactly one succeeds.
*Where in the code:* `simulation/reducer.py` (`expected_snapshot_hash` check); `simulation/store.py` (`mutate`); `tests/unit/test_simulation.py` (`test_concurrent_changes_with_the_same_version_cannot_both_win`).

**Q33. How does replay stay deterministic?**
The same initial scenario, the same events in the same order and the same configuration produce the same snapshot hash, scores, plans and outcome hash at every step. Determinism rests on four things: scores rounded to 4 decimals, exact integer coefficients, a single CP-SAT worker with a fixed seed, and a lexicographic tie-break that makes the optimal plan unique. Event IDs are content-addressed rather than time-based. Wall-clock timings vary, so they are excluded from every hash.
*If pushed:* replay always resets first, so a replayed shipment is never counted twice. An exported JSON file re-imports and is verified step by step against the recorded outcome hashes. The committed demo script is checked by `test_the_recorded_demo_script_still_reproduces`.
*Where in the code:* `simulation/session.py` (`outcome_hash`, `replay`, `export_session`, `import_session`).

**Q34. What are the states of the simulator, and why a finite-state machine?**
The states are READY (scenario loaded and scored), ACTIVE (accepts events), PAUSED (locked against changes), COMPLETED (ended by the user, read-only) and ERROR (a computed plan failed the validator, read-only). Reset returns to READY from any state and clears the history and ledger. One transition table is the only definition, and anything not listed is rejected with 409 `invalid_transition`. An FSM makes illegal actions, such as applying an event to a completed session, impossible by construction instead of relying on scattered checks.
*If pushed:* PAUSED only locks the session, because there is no running clock. ERROR is reached only through an engine defect, never through a user mistake.
*Where in the code:* `simulation/fsm.py` (`TRANSITIONS`).

### Evaluation

**Q35. What do the 504 scenarios establish, and what don't they?**
They establish correctness within our synthetic setup. All 2,016 plans (504 × 4 policies) were valid, every CP-SAT solve was proven OPTIMAL, and all four policies handed out the same number of units. They show that urgency-based policies raise UWC (+0.102, 95% CI 0.092 to 0.112) and critical-zone coverage (+0.288) over FCFS without losing any units. They also show that AidOS does *not* improve the worst-off zone, starvation or the Jain index compared with FCFS: those confidence intervals sit around 0. They do not show that AidOS is "better" overall, anything about real disasters, or behaviour outside the generator's ranges.
*If pushed:* only four hypothesis tests were pre-declared (exact sign test, Holm-adjusted). Only UWC differs (p < 0.0001). Lowest zone coverage gives p = 0.42, and starved zones and Jain give p = 1.0.
*Where in the code:* `docs/evaluation/results.md`; run `experiments/results/extended-20261112T100136Z/`.

**Q36. What is a confidence interval, and how was it computed here?**
A 95% confidence interval is a range that, under the method's assumptions, would contain the true average difference in 95% of repeated experiments. It shows how precise an estimate is. We used a percentile bootstrap on paired differences. For each scenario we take policy A's value minus policy B's, resample those differences with replacement 5,000 times (seed 20261111), compute the mean each time, and take the 2.5th and 97.5th percentiles. The bootstrap makes no assumption that the differences are normally distributed.
*If pushed:* the unit of analysis is the scenario for static runs and the script for dynamic runs. An earlier analysis that paired dynamic results by step was fixed before the reported run, because the steps of one script are not independent.
*Where in the code:* `evaluation/stats.py` (`paired`, `holm`).

**Q37. Isn't UWC circular, since AidOS maximises it?**
Yes, and we say so. AidOS's objective is UWC up to the small ε term, and both use the same fuzzy scores. So a higher UWC for AidOS shows the optimiser does what it is told. It is not independent evidence of better outcomes. That is why UWC and critical-zone coverage are marked "objective-aligned" everywhere, and why our conclusions rest on the external metrics: lowest zone coverage, starvation, Jain index and utilisation.
*Where in the code:* `docs/evaluation/metric-definitions.md` section C.

### Architecture and engineering

**Q38. How is simulation state kept?**
Sessions live in memory, in a dictionary inside the single API process. They do not survive a restart, are not shared between processes, expire after 2 hours idle, and at most 200 are kept. Each session has a version number that rises by one with each accepted change, and every change must send `expected_version`. A mismatch returns 409 `version_conflict` and changes nothing. The engine functions are pure: they build a new immutable session state, and the store swaps it in only on success.
*If pushed:* there is no database by design, which is in scope for a prototype. Exported replay documents are how a run is kept.
*Where in the code:* `simulation/store.py` (`SessionStore.mutate`); `simulation/session.py`.

**Q39. How is correctness tested?**
At the Stage 5 final verification on 12 November 2026, there were 288 backend tests (pytest) and 81 frontend tests. They include hand-computed fuzzy examples, the monotonicity grid, randomized invariant tests that no policy ever breaks a hard constraint, exhaustive comparison of CP-SAT against brute-force optima on small instances, forced solver failures, simulation replay, concurrency and API error paths. On top of that, `scripts/smoke_test.py` runs the demo over HTTP, and `verify_results.py` re-checks every result file's checksum and recomputes summaries from the raw CSVs.
*If pushed:* an independent audit script (`experiments/audit_stage4.py`) recomputed the Stage 4 statistics with a separate code path and passed 21 of 21 checks. An independent standard run reproduced every logical value of the extended run on the 1,120 rows they share.
*Where in the code:* `tests/unit/`, `tests/integration/`, `apps/web/src/test/`.

### Limitations and ethics

**Q40. Can the urgency model be biased?**
Yes. The membership functions, rules and output values are design assumptions, not validated triage standards. Whoever scores low is the one who gets starved under urgency-first. If the ratings or rules are wrong, every "gain" is wrong in the same direction. The sensitivity study shows that the *ordering* of zones depends on modelling choices. Moving the membership breakpoints by one point changed the zone order in 142–144 of 280 scenarios and the AidOS plan in 103–113 of them. The rule base also builds in value choices: high vulnerability raises urgency, but low and medium vulnerability are treated alike.
*If pushed:* across all the redesigned variants, plans changed in 22–41% of scenarios but only 2–6% of units moved, and the external equity metrics barely changed. Changing only the output values (P5, P6) changed nothing, because AidOS depends only on the order of the scores.
*Where in the code:* `experiments/fuzzy_sensitivity.py`; `docs/evaluation/stage5-supplementary.md` section 3.

---

## Level 3: Challenging

### Fuzzy inference

**Q41. Your score never goes above 87.5. Isn't that a problem?**
It is a known property of zero-order Sugeno with band-centre outputs. The score is a weighted average of 12.5, 37.5, 62.5 and 87.5, so it cannot leave that range, and any zone rated 8 or more on all three inputs scores exactly 87.5. That compresses differences at the top: two very severe zones can tie. Ties are then broken by arrival order, which is deterministic and documented, but it is not a judgement of need. Because AidOS uses only the order of the scores, stretching the outputs (for example to 0/33/67/100) would change no plan (variant P5 in the sensitivity study).
*Where in the code:* `docs/algorithms/fuzzy-logic.md` sections 4 and 9.

### Optimisation

**Q42. When would CP-SAT become necessary?**
As soon as something *couples* decisions or makes the objective non-linear. Examples are a per-zone vehicle capacity shared across resources, bundled kits, minimum lot sizes, or shared route capacity. Our counterexample, computed in isolation and not part of AidOS: zone A (urgency 87.5) and zone B (37.5), each with a 10-unit truck, and stock of 10 water and 10 medical kits, where medical kits weigh 3. Greedy fills A's truck with water and delivers 10 units (objective 8,850,000). CP-SAT sends A the medical kits and B the water, delivering 20 units (objective 30,400,000, OPTIMAL).
*If pushed:* vehicle capacity is listed as future work, not added to the benchmark, because the scenario data has no capacity information. Adding it would mean inventing a constraint just to manufacture an advantage.
*Where in the code:* `experiments/greedy_equivalence.py`; `docs/algorithms/greedy-vs-cpsat-analysis.md` section 5.

**Q43. What happens if the solver fails or times out?**
The time limit is 5 s in total, shared by all phases. If the first phase finds a plan but a later phase cannot prove optimality, AidOS returns the last valid plan with status FEASIBLE and the message "valid but not proven optimal". It never labels that plan OPTIMAL. If the first phase finds nothing (INFEASIBLE, UNKNOWN or MODEL_INVALID), no plan is invented: no cells, metrics null, validation "not applicable", and a message saying what happened. In the simulator, if the recommended policy returns no plan, the event is rejected with 503 `solver_failed` and the session is unchanged.
*If pushed:* the all-zero plan always satisfies the constraints, so INFEASIBLE should never happen on a valid scenario. The tests force each failure path by substituting the status CP-SAT returns. No timeout or FEASIBLE result occurred in any evaluation run.
*Where in the code:* `ai/constraints.py` (after the phase loop); `simulation/session.py` (`evaluate_step`); `tests/unit/test_constraints.py`.

**Q44. What happens if the problem doubles in size?**
First, there is a hard limit: validation accepts at most 50 zones, 10 resources and 1,000,000 units per request or stock entry, so anything beyond that is rejected, not slowed down. Within the limit, the model grows linearly: one variable per zone and resource, and one stock constraint per resource. FCFS and greedy scale roughly linearly. In the Stage 4 scaling study, going from 20 to 40 zones roughly doubled greedy's time (0.37 to 0.72 ms) and roughly tripled AidOS's (36.6 to 107.8 ms), with the variables going from 80 to 160. The plans do not change in character, because the problem stays separable.
*If pushed:* those Stage 4 times were measured under heavier background load. For absolute times, quote the Stage 5 benchmark (Q45). CP-SAT is exponential in the worst case in general, but here each phase is a small, LP-like integer program.
*Where in the code:* `domain/models.py` (`MAX_ZONES`, `MAX_RESOURCES`, `MAX_UNITS`); `docs/evaluation/results-tables.md` section 9.

### Fairness

**Q45. What happens when the coverage floor cannot be met?**
The floor is not a hard guarantee, and the model is never made infeasible by it. In the code, the floor for each resource is a variable between 0 and the target (25%, in steps of 0.1%), and the first phase maximises the sum of the floors. When stock is too low for the target, the solver picks the largest common floor the stock allows, possibly 0, and reports it per resource as `coverage_floor`. Each requesting zone then gets at least ⌈floor × request⌉ units. In the floor sweep, a 25% target had to be reduced on 5 of 1,003 resource cases, a 30% target on 37, and a 40% target on 136.
*If pushed:* those counts are low partly because the generator's scarcest family still has 25–50% of the requested stock. In scarcer real situations the floor would be reduced more often. A 10% floor already removed all starvation in those 280 scenarios, so 25% is a design choice inside a smooth trade-off, not an optimum.
*Where in the code:* `ai/constraints.py` (`floors`, `model.add(FLOOR_SCALE * var >= demand * floors[rid])`); `docs/evaluation/stage5-supplementary.md` section 2.

### Simulation

**Q46. What happens if a route becomes blocked?**
Honestly, AidOS has no routes, transport, travel times or vehicles. It models one depot and one allocation decision at a time, so "a route is blocked" cannot be expressed directly. The closest analogues are events. If the blockage destroys or strands stock, a `supply_lost` event reduces it. If a zone can no longer receive a resource, a `request_updated` event can set its request to 0. Either way the engine re-scores and re-plans, and the explanation shows which cells moved. Modelling routes properly would need geography, capacities and a new model, which are out of scope.
*Where in the code:* `simulation/events.py`; `docs/algorithms/allocation-formulation.md` section 3 ("Not modelled").

### Evaluation

**Q47. Why does the late-arrival dynamic bias matter, and how was it corrected?**
In Stage 4, every dynamic script added a new zone that arrived *last* with *high* ratings. FCFS can never serve a late zone, so AidOS looked fairer in dynamic crises: in dispatch mode, FCFS never served the late zone (60 of 60 scripts) and AidOS always did. But among the *original* zones the order reversed: 27 zones were never served under FCFS and 53 under AidOS. Stage 5 added a controlled experiment without touching the frozen runs. It covered 120 scripts in which the newcomer's urgency was varied (low, moderate, high, random), crossed with 3, 5 or 8 initial zones. FCFS never served the late zone at any level. AidOS served it in proportion to its urgency (recommendation-mode coverage 0.00, 0.39 and 0.95 for low, moderate and high), and it left the worst-off original zone lower than FCFS at every level.
*If pushed:* at high urgency, dispatch-mode lowest original-zone fulfilment for AidOS minus FCFS was −0.048 [−0.077, −0.022]. The Stage 4 dynamic equity claim was withdrawn. Urgency-first allocation is not "fairer". It redistributes towards whoever scores urgent.
*Where in the code:* `experiments/dynamic_controlled.py`; `evaluation/dynamic_controlled.py`; `docs/evaluation/stage5-supplementary.md` section 4.

### Architecture and engineering

**Q48. What are the scalability limits?**
The engine accepts at most 50 zones and 10 resources. In the Stage 5 runtime benchmark (moderate scarcity, 4 resources, 3 warm-ups, 15 interleaved repeats, a lightly loaded laptop), AidOS had a median of 6.3 ms at 3 zones, 11.5 ms at 10 zones and 124 ms at 50 zones. Greedy took 0.05, 0.12 and 0.81 ms, so AidOS is about 94–153× slower for an identical plan. At 50 zones, AidOS balanced took 107 ms. CP-SAT's own solve is about 62–78% of the AidOS call, and the rest is Python model building and explanations. The worst case the API accepts (50 zones × 10 resources at the 1,000,000-unit cap) solved validly, but balanced mode took about 2.6 s of its 5 s limit, the closest the system comes to timing out.
*If pushed:* sessions are also single-process and in memory, so the system does not scale to many users or machines. That is a stated limitation, not an oversight.
*Where in the code:* `experiments/runtime_benchmark.py`; `docs/evaluation/stage5-supplementary.md` section 5.

### Limitations and ethics

**Q49. What would be needed before anyone used this for real?**
Urgency criteria validated with humanitarian experts and calibrated against real cases. Real logistics: transport capacity, routes, delivery times, bundles and perishability. Field-tested handling of bad or uncertain data. Persistent, secure, audited storage with authentication and a multi-user design. Legal, ethical and accountability review. And mandatory human approval of every dispatch. None of this exists, and AidOS does not claim it. The honest framing is that AidOS shows the methods work correctly and transparently on synthetic data.
*If pushed:* the human-in-the-loop design is already there in miniature. Nothing is dispatched until a person commits a specific plan for a specific snapshot. But a prototype's safeguard is not a deployment's safeguard.
*Where in the code:* `docs/submission/viva-preparation.md` ("What would be needed before real deployment?").

---

## Traps to avoid

- **Do not claim CP-SAT beats greedy.** For the urgency-first objective, it provably returns the same plan. Its value is the proof of optimality, the balanced mode and extensibility.
- **Do not claim real humanitarian validation.** The data is synthetic, and the rules, membership functions and 25% floor are design assumptions. Nothing was tested with real crises, real agencies or real people.
- **Do not say 25% coverage is guaranteed.** The floor is the largest common fraction the stock allows, *up to* 25%, and it can shrink to 0.
- **Do not say the instructor approved Sugeno.** The choice is documented and measured, and instructor confirmation is still pending.
- **Do not claim industry engagement.** No partner engagement with Dubai Humanitarian or anyone else has taken place.
- **Do not say AidOS is "fairer" than FCFS.** On external equity metrics it matches FCFS in the static benchmark, and in the controlled dynamic experiment it left the worst-off original zone *worse* off.
- **Do not present UWC gains as independent evidence.** AidOS maximises UWC by construction.
- **Do not say the solver "never fails".** Say that every evaluated solve was proven OPTIMAL, and that failures are handled without inventing a plan.
- **Do not describe the inference as Mamdani** or talk about "centroid defuzzification" for AidOS. It is a zero-order Sugeno weighted average.
- **Do not claim AidOS models routes, vehicles or travel time.** It does not.
- **Do not quote a number you are unsure of.** Say where it is recorded instead. The reported static results come from `extended-20261112T100136Z`; the supplementary results come from the `supplementary-*` runs.
- **Do not invent who built what.** Describe your own contribution accurately, and explain the rest as a team member who understands it.
