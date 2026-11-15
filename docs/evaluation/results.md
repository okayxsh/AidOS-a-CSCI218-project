# Evaluation results

**Run:** `extended-20261112T100136Z`. All numbers below are copied from the generated tables in [`results-tables.md`](results-tables.md), which are produced from the run's CSV files by `experiments/report_results.py`.

- **Reproduced:** the independent run `standard-20261112T100617Z` reproduces every logical value on the 560 static and 560 dynamic rows the two runs share (`verify_results.py --against`).
- **Figures:** [`figures/`](figures/), PNG and SVG.
- **Methods:** [`experimental-protocol.md`](experimental-protocol.md) and [`metric-definitions.md`](metric-definitions.md).

**Scope.** These are results on synthetic scenarios drawn from distributions the authors chose, scored with a fuzzy urgency model the authors designed. They describe how the policies behave under those assumptions. They do not show that any policy would serve real people better.

## Summary

| | AidOS vs FCFS | Evidence |
|---|---|---|
| **Better** | Urgency-weighted coverage* +0.102 [0.092, 0.112]; critical-zone coverage* +0.288 [0.255, 0.321]. Never worse on either (0 losses in 504 and 325 scenarios). | Strong, but **objective-aligned**: AidOS maximises the first by construction, and both use the same fuzzy scores. This is optimisation success, not independent evidence. |
| **Similar** | Total units, unit and per-resource coverage, usable-stock utilisation (identical in all 504 scenarios). Lowest zone coverage −0.006 [−0.016, 0.004]. Starved zones +0.022 [−0.042, 0.085]. Jain index −0.003 [−0.011, 0.006]. Coverage gap +0.007 [−0.004, 0.017]. | Strong for "no meaningful difference on these external measures" (narrow CIs around 0, Holm-adjusted p 0.42–1.0). |
| **Worse** | Runtime: median 12.1 ms vs 0.11 ms per scenario, about 100×; 335 ms at 50 zones. Lowest zone coverage in family A (low scarcity): −0.033 [−0.072, −0.002]. | Clear on runtime (absolute times are small). The family-A difference is small and at the edge of its CI. |
| **Identical to greedy** | Every plan, in all 504 static scenarios, 420 dynamic steps and 60 dispatch trajectories. | Proven (allocation-formulation.md, section 4) and observed. The optimiser adds a proof of optimality, not a different allocation. |
| **Insufficient evidence** | Any humanitarian benefit; behaviour outside the generator's ranges (more than 50 zones, correlated arrival and urgency, other urgency models). | Not testable with this design. |

\* objective-aligned metric.

**AidOS balanced** (coverage floor, then urgency) is the only policy whose plans differ from greedy in an external direction. Against AidOS:

- lowest zone coverage +0.180 [0.171, 0.189];
- starved zones −0.82 per scenario (none in any of the 504 scenarios);
- coverage gap −0.232 [−0.245, −0.218];
- Jain index +0.125 [0.114, 0.137].

It pays for this with urgency-weighted coverage −0.031 [−0.034, −0.028] and critical-zone coverage −0.068 [−0.079, −0.057]. It is still above FCFS on both: +0.071 and +0.220.

## 1. Correctness and optimisation (internal evaluation)

- **Feasibility:** 2,016 of 2,016 static plans (504 scenarios × 4 policies) passed every hard check; so did all 1,680 recommendation-mode plans. No policy ever failed to return a plan.
- **Optimality:** every AidOS and AidOS-balanced solve was proven `OPTIMAL` (504/504 each). The time limit was never reached.
- **Dispatch integrity** (240 trajectories): inventory conserved 240/240, ledger consistent 240/240, double dispatch blocked 240/240, no script event rejected.
- **AidOS ≡ urgency greedy:** identical plans on 504/504 scenarios. The urgency-first objective is linear and separable by resource, so its optimum fills zones in urgency order, which is greedy's rule with the same tie-break. Every difference between AidOS and FCFS is therefore **an information effect** (using the urgency model), not an optimisation effect.

## 2. Static benchmark (external behaviour)

All four policies hand out exactly the same number of units in every scenario (usable-stock utilisation 1.000 for all; unit coverage 0.655 for all). None of them leaves stock idle while a zone lacks it. **The policies differ only in who receives the stock.**

AidOS (and greedy) concentrate stock on high-urgency zones:

- critical-zone coverage 0.959 vs 0.671 for FCFS;
- urgency-weighted coverage 0.765 vs 0.663.

That does not make the worst-served zone better off. The lowest zone coverage is 0.180 for AidOS and 0.186 for FCFS, and the share of zones starved is 0.135 and 0.133. FCFS starves whoever arrives late; AidOS starves whoever scores low. The numbers are similar; the *identity* of the starved zones differs (figure 8: under AidOS, zero-coverage zones sit at low urgency; under FCFS they appear at every urgency).

**By family** (results-tables.md, section 5):

- **The AidOS − FCFS gain in urgency-weighted coverage grows with scarcity:** +0.016 in A (low scarcity), +0.112 in B, +0.129 in C (severe). It is largest in D, unequal urgency (+0.236), and smallest in E, equal urgency (+0.017), where there is little urgency difference to exploit. In the 44 of 72 E scenarios where every zone has identical ratings, AidOS, greedy and FCFS give identical plans (the tie-break is arrival order); AidOS balanced still differs, because its floor changes the plan.
- **Equity.** On equity metrics the AidOS − FCFS confidence intervals include 0 in every family except A. There, AidOS is slightly worse on lowest zone coverage (−0.033) and the Jain index (−0.006).
- **AidOS balanced.** Its lowest-zone coverage stays between 0.25 and 0.36 in every family with scarcity (B–G), against 0.005–0.19 for the other policies. In C (severe) it has no starved zone, while the others average about 0.34–0.35 starved share.

## 3. Dynamic events

**Recommendation mode** (shared state; 60 scripts, 420 steps): how much each event changes each plan, in mean units moved (share of steps with any change):

| Event | FCFS | AidOS (= greedy) | AidOS balanced |
|---|---|---|---|
| urgency escalation | 0 (0.00) | 71.8 (0.38) | 59.6 (0.45) |
| new zone (arrives last) | 0 (0.00) | 236.2 (1.00) | 220.6 (1.00) |
| supply lost | 56.9 (1.00) | 56.9 (1.00) | 56.9 (1.00) |
| supply arrived | 47.1 (1.00) | 47.1 (1.00) | 47.1 (1.00) |
| request raised | 22.8 (0.55) | 17.4 (0.45) | 20.6 (0.88) |
| time advanced | 0 | 0 | 0 |
| zone resolved | 252.6 (0.90) | 197.2 (0.78) | 211.5 (1.00) |

- **FCFS never reacts** to an escalation or a new zone: neither changes arrival order or the zones ahead in it. AidOS changes its plan after 38% of escalations. After the other 62%, the optimal plan was the same: the escalation did not change which zones the stock reaches (for example, the zone was already fully served, or kept its position relative to the zones it competes with).
- **Supply changes** move every policy's plan by the same amount.
- **Unmet demand changes identically** for all policies (paired difference exactly 0 in all 60 scripts), because all are non-wasteful.
- **Reallocation size is not a quality measure.** AidOS moves 35.3 [26.1, 45.4] more units per step than FCFS. That is responsiveness to the urgency model, and also churn for anyone planning around the previous recommendation.

**Dispatch mode** (60 scripts; each policy follows its own trajectory). All four dispatch the same total (701.8 units on average); fulfilment is 0.602–0.603 for all. AidOS has:

- higher urgency-weighted fulfilment than FCFS: +0.167 [0.140, 0.195];
- fewer zones never served: −0.57 [−0.73, −0.40].

**This equity result must not be generalised.** Every script introduces a new zone that arrives *last* with *high* ratings (6–10): a late critical emergency, the case the specification asks the simulator to show. FCFS never serves it (60 of 60 scripts); AidOS always does. Among the *original* zones the order reverses: FCFS left 27 zones never served across the 60 scripts, AidOS 53. The same holds in recommendation mode. Before the new zone appears, AidOS starves slightly more zones than FCFS (0.43 vs 0.37 per step). See results-tables.md, section 8. The dynamic "equity advantage" is therefore a consequence of the scripted late urgent arrival, which is consistent with the static finding of no overall equity difference.

**Stage 5 follow-up** (supplementary; [`stage5-supplementary.md`](stage5-supplementary.md)). With the new zone's urgency varied independently (120 scripts), FCFS never served the late zone at any level. AidOS served it in proportion to its urgency (recommendation-mode coverage 0.00 low, 0.39 moderate, 0.95 high). At every level AidOS left the worst-off *original* zone lower than FCFS did. For example, at high urgency, dispatch-mode lowest original-zone fulfilment was −0.048 [−0.077, −0.022] versus FCFS, with more original zones never served. AidOS balanced never left any zone unserved.

## 4. Computational cost

Measured on one laptop with normal desktop load (figure 5; results-tables.md, section 9):

- **Static benchmark:** median runtime per scenario of 0.11 ms (FCFS), 0.12 ms (greedy), 12.1 ms (AidOS) and 16.0 ms (AidOS balanced). The 90th percentiles are 0.16, 0.16, 19.2 and 24.1 ms.
- **Scaling study:** AidOS's median rises from 14.8 ms at 5 zones to 107.8 ms at 40 and 334.5 ms at 50 zones (20 to 200 variables). Balanced is similar. The 50-zone figures vary widely between repeats (figure 5 band), which is consistent with background load on the machine.

All solves stayed well inside the 5 s limit. For the scenario sizes the system accepts (at most 50 zones), CP-SAT's cost is acceptable for interactive use but about 100× that of the heuristics, for the identical plan in the urgency-first case.

## 5. What this supports, and what it does not

**Supported, within the synthetic setup:**

- All four policies are correct: feasible, deterministic, reproducible. The CP-SAT models are solved to proven optimality.
- Using the fuzzy urgency model shifts stock towards zones the model rates as urgent (large, consistent gains on objective-aligned metrics) without losing any units.
- The urgency-first optimiser gives exactly the urgency-greedy plan. The comparison AidOS vs greedy isolates the optimiser's contribution, and it is nil for this objective.
- The coverage floor (AidOS balanced) removes starvation and halves the gap between the best- and worst-served zones, at a measured cost in urgency priority.

**Not supported:**

- That AidOS is "better" overall. On external equity measures it matches FCFS, and its advantage is on metrics defined by its own urgency model.
- Any claim about real disasters, real needs or lives. The urgency model, rule base, scenario distributions and the 25% floor are design assumptions.
- That the dynamic equity gains generalise beyond late, urgent arrivals.

Significance testing was limited to four pre-declared AidOS-vs-FCFS tests (Holm-adjusted). Only urgency-weighted coverage differs (p < 0.0001); lowest zone coverage (p = 0.42), starved zones (p = 1.0) and the Jain index (p = 1.0) do not.
