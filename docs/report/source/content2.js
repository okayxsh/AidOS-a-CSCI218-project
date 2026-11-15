// Sections 6–8 of the AidOS final report. Numeric tables are read from the generated result
// documents (themselves generated from the run artifacts), never retyped.
module.exports = function part2(D) {
  const { P, H1, H2, H3, B, T, F, E, V, md, pick } = D;
  const RT = 'docs/evaluation/results-tables.md';
  const S5 = 'docs/evaluation/stage5-supplementary.md';
  const GE = 'docs/algorithms/greedy-vs-cpsat-analysis.md';

  // --- tables pulled from the generated documents ---
  const feas = md(RT, '## 1. Feasibility', 0);
  const ident = md(RT, '## 1. Feasibility', 1);
  const means = md(RT, '## 2. Static benchmark', 0);
  const paired = md(RT, '## 3. Paired differences', 0);
  const tests = md(RT, '## 4. Pre-declared hypothesis', 0);
  const famUwc = md(RT, '**Urgency-weighted coverage***', 0);
  const famLow = md(RT, '**Lowest zone coverage**', 0);
  const recEvents = md(RT, '## 6. Dynamic, recommendation mode', 0);
  const recPaired = md(RT, '## 6. Dynamic, recommendation mode', 1);
  const disp = md(RT, '## 7. Dynamic, dispatch mode', 0);
  const dispPaired = md(RT, '## 7. Dynamic, dispatch mode', 2);
  const decompRec = md(RT, '## 8. Decomposition', 0);
  const decompDisp = md(RT, '## 8. Decomposition', 1);
  const floor = md(S5, '## 2. Coverage-floor sweep', 0);
  const floorPaired = md(S5, '## 2. Coverage-floor sweep', 1);
  const fuzzy = md(S5, '## 3. Fuzzy design sensitivity', 0);
  const ctrl = md(S5, '## 4. Controlled dynamic scripts', 0);
  const ctrlPaired = md(S5, '## 4. Controlled dynamic scripts', 1);
  const runtime = md(S5, '## 5. Runtime benchmark', 0);
  const equiv = md(GE, '## 3. Exhaustive and random checks', 0);

  const pairedSel = paired.rows.filter((r) => /^(AidOS - FCFS|AidOS balanced - AidOS)$/.test(r[0]) && !/Unit coverage/.test(r[1]));

  return [
    // ===================================================================== 6
    H1('Experiments and Results', 'experiments'),
    P('All results in this section come from saved, versioned run artifacts; the tables are generated from them and reproduced here without retyping. The main evidence is the Stage 4 extended run `extended-20261112T100136Z`; an independent run, `standard-20261112T100617Z`, reproduces every logical value on the 560 static and 560 dynamic rows the two share. The project was built in stages; "Stage 4" denotes this main evaluation and "Stage 5" the later supplementary experiments, which are exploratory, use new seeds, and are reported separately. **Scope of every result:** these are measurements on synthetic scenarios drawn from distributions the team chose, scored with an urgency model the team designed. They describe how the policies behave under those assumptions; they do not show that any policy would serve real people better.'),
    F({ id: 'd_eval', path: V.diag('d6_evaluation_method'), widthCm: 16, caption: 'Evaluation methodology: seeded scenario families, all four policies on identical inputs, independent validation, metrics, paired statistics and versioned artifacts. The Stage 5 supplementary experiments form a separate branch with their own seeds and manifests.' }),
    H2('Experimental setup', 'setup'),
    P('**Scenario families.** `aidos/evaluation/families.py` generates seven static families of 72 scenarios each (504 in total). Scenario i of a family uses seed `seed_base + i` and its own random generator, so every scenario is reproducible and families never share seeds ({tab:families}). Arrival order is independent of urgency, so FCFS faces no systematic disadvantage, and every generated scenario is reported; none were selected or dropped.'),
    T({
      id: 'families', caption: 'Static scenario families (72 scenarios each).',
      cols: [0.4, 1.6, 0.7, 0.7, 1.4, 2.3],
      header: ['', 'Purpose', 'Zones', 'Resources', 'Stock (share of requests)', 'Ratings / requests'],
      rows: [
        ['A', 'Low scarcity', '3–8', '3–4', '85–110%', 'Uniform 0–10; requests 1–120, 10% zero'],
        ['B', 'Moderate scarcity', '3–8', '3–4', '60–85%', 'Uniform'],
        ['C', 'Severe scarcity', '3–8', '3–4', '25–50%', 'Uniform'],
        ['D', 'Unequal urgency', '4–8', '3–4', '50–80%', 'Half the zones 7–10 on every input, half 0–3'],
        ['E', 'Equal or near-equal urgency', '3–8', '3–4', '50–80%', 'One shared rating triple (44 of 72 scenarios) or ±1 per input'],
        ['F', 'Unequal demand', '4–8', '3–4', '50–80%', '1–2 zones request 4–8× more'],
        ['G', 'Multiple resource shortages', '3–8', '4', 'Three at 30–60%, one at 100–130%', 'Uniform'],
      ],
      note: 'Seed bases: A 100000, B 200000, …, G 700000. Source: docs/evaluation/experimental-protocol.md.',
    }),
    P('**Policies and frozen configuration.** All four policies ran on every scenario with ε = 1, all resource weights 1, a 25% floor target, CP-SAT with one worker, seed 0 and a 5 s limit, and fuzzy configuration v1.0. No parameter of any policy or of the fuzzy model was changed during the evaluation, and nothing was tuned on evaluation data.'),
    P('**Dynamic scripts (family H).** Sixty base scenarios (family-B generator, seeds 800000 + i) were run in two modes. In **recommendation mode**, seven events are drawn from the current shared state: an escalation to severity or time criticality 10; a new zone with high ratings; a 30% supply loss; a shipment; a request increase; a time step; and the resolution of one zone. All four policies are evaluated on the same snapshot at every step (one outcome hash per step), giving 420 steps. In **dispatch mode**, the depot starts at 30% of requests and receives three supply waves, and each policy runs its own trajectory with four dispatches, giving 240 trajectories. Every exogenous event is valid whatever was dispatched before, so all policies receive the identical script.'),
    H2('Metrics', 'metrics'),
    P('Metrics are computed from a plan\'s cells and the scenario, independently of the policy that produced the plan ({tab:metrics}). A distinction runs through the whole analysis. **Objective-aligned** metrics (marked †) are those the AidOS objective, or the urgency model it uses, favours by construction: a higher value shows that the optimiser does what it is told, not that outcomes are better. **External** metrics are not part of any policy\'s objective.'),
    T({
      id: 'metrics', caption: 'Metrics. f_{z} = Σ_{r} x_{z,r} / Σ_{r} d_{z,r} is the coverage of zone z.',
      cols: [1.7, 3.2, 1.3],
      header: ['Metric', 'Definition', 'Direction'],
      rows: [
        ['Validity', 'Passes every hard check of the independent validator', 'Must be 1'],
        ['Unit coverage', 'Σ x / Σ d over all zones and resources', 'Higher'],
        ['Urgency-weighted coverage †', 'Σ u_{z}x_{z,r} / Σ u_{z}d_{z,r}; AidOS maximises this almost exactly', 'Higher'],
        ['Critical-zone coverage †', 'Σ x / Σ d over zones with u_{z} ≥ 75 (defined in 325 of 504 scenarios)', 'Higher'],
        ['Lowest zone coverage', 'min_{z} f_{z}, the worst-served zone', 'Higher'],
        ['Starved zones / share', 'Zones with demand that receive nothing (count, and share of zones with demand)', 'Lower'],
        ['Coverage gap', 'max_{z} f_{z} − min_{z} f_{z}', 'Lower'],
        ['Jain index [@jain]', '(Σ f_{z})^{2} / (n Σ f_{z}^{2}), from 1/n to 1 (equal coverage); read with lowest-zone coverage', 'Higher'],
        ['Usable-stock utilisation', 'Σ x / Σ_{r} min(S_{r}, Σ_{z} d_{z,r}): 1 means no stock idle while a request is unmet', 'Higher'],
        ['Runtime', 'Wall-clock time of the policy call (median of repeats); CP-SAT solve time separately', 'Lower'],
        ['Dynamic response', 'Units reallocated between steps; whether the plan changed; metrics after each step', 'Descriptive'],
        ['Dispatch outcomes', 'Fulfilment, urgency-weighted fulfilment †, lowest-zone fulfilment, zones never served', 'As above'],
        ['Inventory integrity', 'Conservation identity {eq:conserve}; ledger consistency; repeated commit rejected', 'Must hold'],
      ],
    }),
    P('Two caveats apply to the zone-level metrics. First, zone coverage f_{z} adds units of different resources (a water pack counts like a medical kit), so a zone that received only water can appear well covered; lowest-zone coverage, the coverage gap, the Jain index and critical-zone coverage inherit this. Second, objective-aligned metrics are marked † in tables and * in the generated figures.'),
    P('Equal coverage is not humanitarian fairness. Zones differ in need, and an urgency-first policy *intends* unequal coverage. The equity metrics describe the distribution; they do not rank policies ethically. When a denominator is zero the metric is recorded as not applicable and excluded from means, never counted as 0 or 1.'),
    H2('Statistical methods', 'stats'),
    P('Every policy saw every scenario, so comparisons are **paired**: for each scenario (or script) the difference between two policies is computed, and the distribution of differences is summarised. The analysis reports the mean and median difference; wins, ties and losses (tolerance 10^{−9}); a 95% percentile-bootstrap confidence interval of the mean difference with 5,000 resamples and seed 20261111 [@efron]; and the paired effect size d_{z} = mean / sd of the differences [@lakens]. Formal hypothesis tests were limited to a family of **four pre-declared** AidOS-versus-FCFS comparisons (urgency-weighted coverage, lowest-zone coverage, starved zones and Jain index), using an exact two-sided sign test with Holm\'s step-down correction [@holm]; all other comparisons are descriptive. For the dynamic experiments the **script** is the unit of analysis: steps of one script are averaged before pairing. The intervals describe variation within the generator\'s distribution, which the team chose; they do not generalise to real crises, and a statistically clear difference is not evidence of practical humanitarian value.'),
    H2('Correctness and solver status', 'correct'),
    T({ id: 'feas', caption: 'Feasibility and solver status over 504 static scenarios.', cols: [1.5, 1.2, 1.1, 1.2, 1.5], align: ['l', 'r', 'r', 'r', 'l'], header: feas.header, rows: feas.rows }),
    P('Every policy returned a valid plan for every scenario: 2,016 of 2,016 plans passed every hard check, as did all 1,680 recommendation-mode plans. Every AidOS and AidOS-balanced solve was proven `OPTIMAL`, and the time limit was never reached. The heuristics report `COMPLETE`, never `OPTIMAL`, because they make no optimality claim.'),
    H2('Static benchmark: urgency-aware allocation versus FCFS (RQ1)', 'static'),
    T({ id: 'means', caption: 'Static benchmark: mean (sd) per policy over 504 scenarios. † objective-aligned. Runtime in ms.', cols: [2.0, 0.7, 1.1, 1.1, 1.1, 1.2], align: ['l', 'l', 'r', 'r', 'r', 'r'], header: means.header, rows: means.rows, size: 16, note: 'Critical-zone coverage is defined only for the 325 scenarios with a zone scoring at least 75. Source: results-tables.md §2, generated from summary.json.' }),
    P('**All four policies allocate the same number of units in every scenario.** Unit coverage (0.655) and usable-stock utilisation (1.000) are identical across policies in all 504 scenarios: none leaves stock idle while a zone lacks it. Optimisation does not create supplies; **the policies differ only in who receives the stock.**'),
    P('AidOS (and greedy) concentrate stock on zones the urgency model rates highly. Urgency-weighted coverage rises from 0.663 to 0.765, and critical-zone coverage from 0.671 to 0.959 ({fig:r_policy}). AidOS never does worse than FCFS on either: 0 losses in 504 and 325 scenarios ({tab:paired}). These are the metrics AidOS optimises, so the result confirms that the optimiser works rather than demonstrating independent benefit.'),
    F({ id: 'r_policy', path: V.res('fig1_policy_metrics'), widthCm: 15.5, caption: 'Static benchmark, mean over 504 scenarios with 95% bootstrap confidence intervals. Unit coverage is identical; AidOS and greedy coincide; balanced trades urgency-weighted coverage for equity.' }),
    P('On the **external** equity measures, the worst-served zone is no better off. Lowest-zone coverage is 0.180 for AidOS against 0.186 for FCFS, and the paired difference of −0.006 has a confidence interval that includes zero; the same holds for starved zones, the coverage gap and the Jain index. FCFS starves whoever arrives late, while AidOS starves whoever scores low. The numbers are similar but the *identity* of the starved zones differs: under AidOS zero-coverage zones sit at low urgency, while under FCFS they appear at every urgency level ({fig:r_zone}). Of the four pre-declared tests, only urgency-weighted coverage differs after Holm correction ({tab:htests}).'),
    T({ id: 'paired', caption: 'Paired differences on the same scenarios (first policy minus second), 95% bootstrap CI. Wins/ties/losses count scenarios where the first value is higher/equal/lower.', cols: [1.4, 1.6, 0.45, 1.75, 0.75, 1.2, 0.5], align: ['l', 'l', 'r', 'r', 'r', 'r', 'r'], header: paired.header, rows: pairedSel, size: 15 }),
    T({ id: 'htests', caption: 'Pre-declared hypothesis tests, AidOS versus FCFS (exact sign test, Holm-adjusted, n = 504).', cols: [2.4, 1.2, 1.4], align: ['l', 'r', 'r'], header: tests.header, rows: tests.rows }),
    F({ id: 'r_paired', path: V.res('fig2_paired_vs_fcfs'), widthCm: 14.5, caption: 'Each policy minus FCFS, paired on the same scenarios, with 95% bootstrap CIs. AidOS and greedy gain only on objective-aligned metrics (†); balanced also moves every equity metric in the favourable direction.' }),
    P('**By family** ({tab:family}), the AidOS − FCFS gain in urgency-weighted coverage grows with scarcity (+0.016 in A, +0.112 in B, +0.129 in C) and is largest when urgency is unequal (D, +0.236) and smallest when it is nearly equal (E, +0.017), where there is little urgency difference to exploit. In the 44 E scenarios where every zone has identical ratings, AidOS, greedy and FCFS give identical plans, because the tie-break is arrival order. On lowest-zone coverage, the AidOS − FCFS interval includes zero in every family except A (low scarcity), where AidOS is slightly worse (−0.033 [−0.072, −0.002]). AidOS balanced keeps lowest-zone coverage between 0.25 and 0.35 in every family with scarcity (B–G), against 0.005–0.19 for the other policies.'),
    T({
      id: 'family', caption: 'Per-family means: urgency-weighted coverage † and lowest zone coverage, with the AidOS − FCFS difference [95% CI].',
      cols: [1.75, 0.6, 0.6, 0.6, 1.3, 0.6, 0.6, 0.6, 1.3], align: ['l', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'], size: 15,
      header: ['Family', 'UWC FCFS', 'UWC AidOS', 'UWC bal.', 'UWC AidOS − FCFS', 'Low FCFS', 'Low AidOS', 'Low bal.', 'Low AidOS − FCFS'],
      rows: famUwc.rows.map((r, i) => [r[0], r[1], r[3], r[4], r[5], famLow.rows[i][1], famLow.rows[i][3], famLow.rows[i][4], famLow.rows[i][5]]),
    }),
    F({ id: 'r_zone', path: V.res('fig8_zone_coverage'), widthCm: 15.5, caption: 'Per-zone coverage against fuzzy urgency, family B (each dot is one zone in one scenario). In this family the zones AidOS leaves uncovered all have low urgency; FCFS leaves zones uncovered at every urgency level; the balanced floor lifts every zone to at least about 0.25. Across all families, 41 of the 414 zones AidOS leaves uncovered score 50 or more (families C, E and F).' }),

    H2('CP-SAT versus greedy: an equivalence result (RQ2)', 'equiv'),
    P('The most consequential finding of the evaluation is that **AidOS (urgency-first CP-SAT) and urgency greedy produced identical allocations in 504 of 504 static scenarios**, and also on every dynamic step and dispatch trajectory ({tab:ident}). The team investigated whether this was a bug, an artefact of the scenario distribution, or a mathematical property. It is the last.'),
    T({ id: 'ident', caption: 'Scenarios (of 504) in which two policies produced identical plans.', cols: [3, 2], align: ['l', 'r'], header: ident.header, rows: ident.rows }),
    H3('Why the two must agree'),
    P('The argument follows the classical analysis of the knapsack problem [@dantzig, @kellerer], specialised to this model:'),
    B([
      '**Separability.** Every constraint ({eq:dom}, {eq:stock}) involves one resource only, and the objective {eq:obj} is a sum over resources. The problem splits into |R| independent subproblems, and a plan is optimal exactly when it is optimal for each resource.',
      '**Each subproblem is a unit-weight knapsack.** For a fixed resource: maximise Σ_{z} c_{z}x_{z} subject to 0 ≤ x_{z} ≤ d_{z} and Σ x_{z} ≤ S, with every c_{z} > 0. Because coefficients are positive, an optimum never leaves stock unused while some x_{z} < d_{z}.',
      '**Exchange argument.** If c_{i} > c_{j}, x_{i} < d_{i} and x_{j} > 0, moving one unit from j to i raises the objective by c_{i} − c_{j} > 0. So at an optimum a lower-coefficient zone receives units only after every higher-coefficient zone is full, which is exactly "fill zones in decreasing coefficient order". Since S and every d_{z} are integers, the LP relaxation already has this integral optimum.',
      '**Same order.** Within one resource, c_{z,r} = w_{r}(10^{4}u_{z} + E), where E = round(10^{4}ε), with w_{r} > 0 constant across zones, so ordering zones by coefficient is ordering them by u_{z}, for any positive weight and any ε. Greedy sorts by u_{z}.',
      '**Same tie-break, unique optimum.** Zones with equal scores have equal coefficients; phase 2 maximises Σ ρ_{z}x_{z} on the optimal face, and by the same exchange argument gives units to earlier arrivals first, exactly greedy\'s secondary key. With every ρ_{z} distinct, the lexicographic optimum is unique, so CP-SAT can return only the greedy plan.',
    ], true),
    P('A corollary is that AidOS depends only on the **order** of the urgency scores, not their values: any strictly increasing transformation of the scores leaves the plan unchanged (tested in `test_stage5.py`, and used in {sec:sensitivity}). The argument was checked independently by brute force: exhaustive enumeration of every feasible integer plan, taking the lexicographic maximum, makes no use of separability ({tab:equiv}).'),
    T({ id: 'equiv', caption: 'Exhaustive and randomised checks of the equivalence (supplementary run supplementary-greedy-equivalence-20261112T164930Z).', cols: [3.0, 1.05, 1.15, 0.85, 1.1], align: ['l', 'r', 'r', 'r', 'r'], header: equiv.header, rows: equiv.rows, size: 15 }),
    P('On the 700 random scenarios, the median AidOS call took 11.9 ms, of which CP-SAT\'s reported solve time was 8.1 ms (69%), against 0.12 ms for greedy: about 100 times slower for an identical plan.'),
    H3('When an optimiser would be necessary'),
    P('Greedy stays optimal only while the problem remains a set of independent, linear, unit-weight knapsacks. It loses optimality as soon as something **couples** decisions or makes the objective non-linear. Examples are a per-zone vehicle capacity Σ_{r} x_{z,r} ≤ K_{z}, which couples resources; bundled kits; minimum lot sizes; shared route capacity; or a concave, diminishing-returns objective. The coverage floor already couples zones, which is why AidOS balanced differs from greedy in 450 of 504 scenarios. A worked counterexample, computed in isolation and **not** part of AidOS or any benchmark, illustrates the vehicle-capacity case ({tab:counter}).'),
    T({
      id: 'counter', caption: 'Counterexample for a proposed extension: a vehicle capacity of 10 units per zone, and objective weights w_{r} = 3 for medical kits and 1 for water. Zone A (urgency 87.5) requests 10 water and 10 medical kits; Zone B (urgency 37.5) requests 10 water; stock is 10 of each.',
      cols: [1.4, 1.6, 1.6, 1.1, 1.4], align: ['l', 'l', 'l', 'r', 'r'],
      header: ['Method', 'Zone A', 'Zone B', 'Units', 'Objective'],
      rows: [
        ['Greedy (urgency order)', '10 water, 0 medical', 'nothing', '10', '8,850,000'],
        ['CP-SAT (OPTIMAL)', '0 water, 10 medical', '10 water', '20', '30,400,000'],
      ],
    }),
    P('The greedy shown is the project\'s baseline applied unchanged: zones in urgency order, resources in catalogue order (water first). A weight-aware greedy would solve this small instance. The general point is that once a constraint couples resources, the per-resource exchange argument of {sec:equiv} no longer applies, and greedy loses its optimality guarantee. The scenario schema has no capacity data, so adding such a constraint to the benchmark would mean inventing one to manufacture an advantage; it is left as future work. The honest conclusion for RQ2 is therefore: **under the implemented formulation, CP-SAT does not produce different urgency-first allocations from greedy, and provably cannot.** What it contributes is a declarative model with explicit hard constraints, a proof of optimality for a stated objective, exact lexicographic tie-breaking, a single framework that already handles the coupled balanced model, and the ability to add coupling constraints without redesign. In effect, the optimiser certifies that the transparent greedy rule is optimal for this objective.'),

    H2('The urgency–equity trade-off (RQ3)', 'tradeoff'),
    P('AidOS balanced is the only policy whose plans differ from greedy in an external direction. Against AidOS it raises lowest-zone coverage by +0.180 [0.171, 0.189], removes starvation in all 504 benchmark scenarios (−0.82 starved zones per scenario), narrows the coverage gap by −0.232 [−0.245, −0.218] and raises the Jain index by +0.125 [0.114, 0.137] ({tab:paired}). It pays with urgency-weighted coverage −0.031 [−0.034, −0.028] and critical-zone coverage −0.068 [−0.079, −0.057], while remaining above FCFS on both (+0.071 and +0.220).'),
    P('To see whether 25% is special, a supplementary sweep re-ran AidOS balanced on 280 new scenarios (families A–G, indices 1000–1039) with pre-declared targets of 0, 10, 20, 25, 30 and 40%. All 1,680 runs were valid and `OPTIMAL` ({tab:floor}, {fig:r_floor}).'),
    T({ id: 'floor', caption: 'Coverage-floor sweep over 280 supplementary scenarios. † objective-aligned. "Floor reduced" counts resource cases where the stock could not meet the target.', cols: [1.05, 1.05, 1.0, 0.95, 0.75, 0.6, 1.2, 1.2], align: ['l', 'r', 'r', 'r', 'r', 'r', 'r', 'r'], header: floor.header, rows: floor.rows, size: 15, emphRows: [3] }),
    F({ id: 'r_floor', path: V.res('fig9_floor_tradeoff'), widthCm: 15.5, caption: 'Effect of the coverage-floor target (280 supplementary scenarios, 95% CI). Priority metrics fall slowly and monotonically; equity metrics rise; starvation disappears from a 10% floor onwards.' }),
    P('Paired against no floor, each step costs urgency-weighted coverage and buys lowest-zone coverage, monotonically: 10% costs −0.011 and buys +0.074; 25% costs −0.031 and buys +0.181; 40% costs −0.058 and buys +0.286 (all with narrow intervals). Three points follow. First, **a 10% floor already removed starvation** in every one of these scenarios. That is a property of the tested scenarios, whose scarcest family still supplies at least 25% of requests; a resource with fewer units than requesting zones admits no floor above 0 ({sec:balanced}). Second, **25% is a design choice inside a smooth trade-off**, not an optimum; the data does not single it out, and it is not an independently validated humanitarian standard. Third, the floor is reduced more often as the target rises (5 of 1,003 resource cases at 25%, 136 at 40%), and the generator\'s scarcest family still supplies 25–50% of requests, so in scarcer real situations the target would be unreachable more often. Runtime rises modestly with the extra phase: in the Stage 5 benchmark the balanced median is 10.4 ms at 3 zones against 6.3 ms for AidOS, and the two are similar at larger sizes ({tab:runtime}).'),

    H2('Fuzzy design sensitivity', 'sensitivity'),
    P('Because the urgency model is a design assumption, a supplementary experiment measured how much the plans depend on it. Ten pre-declared variants of the fuzzy system were built in memory, without changing the production file, and run on the same 280 scenarios ({tab:fuzzy}). Three effects must be distinguished: a change in the **scores**, a change in the **priority order**, and a change in the **allocation**. To compare plans on a common scale, urgency-weighted coverage is always measured with the production scores.'),
    T({ id: 'fuzzy', caption: 'Fuzzy design variants (280 scenarios; counts out of 280 unless stated). † measured with production scores.', cols: [1.85, 0.85, 0.75, 0.75, 0.85, 0.8, 0.8, 0.65, 0.7], align: ['l', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'], header: fuzzy.header, rows: fuzzy.rows, size: 14 }),
    F({ id: 'r_fuzzy', path: V.res('fig10_fuzzy_sensitivity'), widthCm: 15.5, caption: 'Fuzzy design sensitivity: share of scenarios whose urgency order changed, whose AidOS plan changed, and the mean share of allocated units that move.' }),
    B([
      '**Score changes alone do not matter.** Changing only the rule-output constants (P5: 0/33/67/100; P6: 20/40/60/80) changes every score but no order and no plan, which confirms the order-only corollary of {sec:equiv}.',
      '**Order changes do matter, modestly.** Shifting all breakpoints by one rating point (P1, P2) reorders zones in 142–144 scenarios and changes the plan in 103–113 (about 37–40%), but moves only about 5% of allocated units; external equity metrics are essentially unchanged. Ignoring vulnerability (P7) has a similar effect.',
      '**Monotonicity depends on the t-norm.** Every product-Sugeno variant stayed monotone (0 dips in 7,260 checks), while the min-t-norm variant (P10) produced 132 dips, consistent with the Stage 2 measurement ({tab:mamdani}).',
    ]),
    P('The implication is that *which* zones are served first is sensitive to unvalidated modelling choices; this, rather than the optimiser, is the main source of uncertainty in the recommendations.'),

    H2('Dynamic evaluation (RQ4)', 'dynamic'),
    H3('Stage 4: responses to events'),
    P('In recommendation mode ({tab:recevents}), FCFS never reacts to an escalation or a new zone, because neither changes arrival order. AidOS changes its plan after 38% of escalations; after the other 62% the optimal plan was unchanged, because the escalation did not change which zones the stock reaches. Supply events move every policy\'s plan by the same amount, and unmet demand changes identically for all policies because all are non-wasteful. Reallocation size is not a quality measure: AidOS moves 35.3 [26.1, 45.4] more units per step than FCFS, which is responsiveness to the urgency model but also churn for anyone planning around the previous recommendation.'),
    T({ id: 'recevents', caption: 'Recommendation mode (60 scripts, 420 steps): mean units reallocated per event (share of steps in which the plan changed).', cols: [1.6, 1.1, 1.2, 1.1, 1.3], align: ['l', 'r', 'r', 'r', 'r'], header: recEvents.header, rows: recEvents.rows }),
    P('In dispatch mode ({tab:disp}) all four policies dispatch the same total (701.8 units on average), and AidOS had higher urgency-weighted fulfilment than FCFS (+0.167 [0.140, 0.195]) and fewer zones never served (−0.57 [−0.73, −0.40]). Integrity held in every trajectory: inventory conserved, ledger consistent and double dispatch blocked in 240 of 240, with no script event rejected.'),
    T({ id: 'disp', caption: 'Dispatch mode (60 scripts per policy): outcomes at the end of each trajectory.', cols: [2.0, 1.0, 1.1, 1.0, 1.2], align: ['l', 'r', 'r', 'r', 'r'], header: disp.header, rows: disp.rows }),
    H3('The late-arrival bias'),
    P('A review of the Stage 4 design found a bias. Every dynamic script added a new zone that arrives **last** with **high** ratings (6–10), a late critical emergency, which is exactly the case FCFS can never serve. Decomposing the results by zone ({tab:decomp}) shows that the dynamic "equity advantage" of AidOS came entirely from this one zone: FCFS never served the late zone (60 of 60 scripts) while AidOS always did, but among the *original* zones the order reverses, with FCFS leaving 27 never served and AidOS 53. Before the new zone appears, AidOS starves slightly more zones than FCFS (0.43 against 0.37 per step).'),
    T({ id: 'decomp', caption: 'Decomposition of the Stage 4 dynamic results: the late, urgent zone versus the original zones.', cols: [2.6, 0.9, 1.1, 0.9, 1.2], align: ['l', 'r', 'r', 'r', 'r'], header: ['Measure', 'FCFS', 'Urgency greedy', 'AidOS', 'AidOS balanced'], rows: [...decompRec.rows.map((r) => ['Recommendation: starved zones per step, ' + r[0].replace(/^Step/, 'step').replace(/^Steps/, 'steps'), ...r.slice(1)]), ...decompDisp.rows.map((r) => ['Dispatch: zones never served, ' + r[0].toLowerCase(), ...r.slice(1)])] }),
    H3('Stage 5: a controlled experiment'),
    P('To remove the bias, a supplementary experiment made the new zone\'s urgency an experimental factor: its ratings were drawn from low (0–3), moderate (4–6), high (7–10) or random (0–10), crossed with 3, 5 or 8 initial zones and 10 seeds per cell, for 120 scripts in both modes. The arrival position stays last, because the engine always appends new reports. Integrity held throughout: inventory conserved and double dispatch blocked in 480 of 480 dispatch runs, identical exogenous scripts for all policies (verified by hash), and 2,400 of 2,400 recommendation plans valid.'),
    T({ id: 'ctrl', caption: 'Controlled dynamic experiment (30 scripts per urgency level). Values are FCFS / AidOS / AidOS balanced.', cols: [1.0, 1.6, 1.6, 1.6, 1.5], align: ['l', 'c', 'c', 'c', 'c'], header: ctrl.header, rows: ctrl.rows, size: 15 }),
    F({ id: 'r_dyn', path: V.res('fig11_dynamic_controlled'), widthCm: 15.5, caption: 'Controlled dynamic experiments (120 scripts): coverage and fulfilment of the late zone, and the lowest fulfilment among the original zones, by the late zone\'s urgency level.' }),
    P('In dispatch mode FCFS never served the late zone (0 of 120 scripts); in recommendation mode it gave the late zone some stock in only 12 of 480 steps (at most 17% coverage), when earlier zones were already covered. AidOS serves it in proportion to the fuzzy model\'s urgency: almost never when it is low and almost always when it is high. The units AidOS gives the newcomer come from the original zones. In every condition AidOS leaves the worst-off original zone at or below FCFS\'s level, and at high urgency the paired difference in lowest original-zone fulfilment is −0.048 [−0.077, −0.022] ({tab:ctrlpaired}). AidOS balanced serves every zone, including the newcomer at every urgency level, with new-zone fulfilment of about 0.37 regardless of level because the floor and the remaining stock are shared.'),
    P('The comparison above is restricted to the *original* zones. Counting every zone, including the late one that FCFS never serves, the worst-served zone receives almost nothing under both policies (AidOS − FCFS at most +0.01), and AidOS leaves fewer zones never served only at high urgency (−0.30 [−0.53, −0.07] per script; the intervals include zero at the other levels). These all-zone figures were recomputed from the run\'s `dispatch.csv` (`docs/report/source/derived_stats.py`).'),
    T({ id: 'ctrlpaired', caption: 'Paired by script, AidOS − FCFS, dispatch mode: lowest original-zone fulfilment (95% CI).', cols: [2, 3], align: ['l', 'r'], header: ctrlPaired.header, rows: ctrlPaired.rows }),
    P('**Revised conclusion for RQ4.** Urgency-first allocation responds to changing conditions by redistributing towards whatever the urgency model rates highly, including late arrivals, at the expense of the worst-off original zones; counted over all zones, it is no worse than FCFS. The Stage 4 claim that AidOS is "fairer in dynamic crises" does not survive the controlled experiment and has been withdrawn; the Stage 4 artifacts remain unchanged, alongside their bias analysis. FCFS is unresponsive by design; AidOS balanced is the only policy that responds to new needs without abandoning any zone.'),

    H2('Runtime', 'runtime'),
    P('A dedicated benchmark measured the policies on moderate-scarcity scenarios with 4 resources and 3 to 50 zones (50 is the validation limit), 5 scenarios per size, 3 warm-up runs and 15 interleaved timed repeats per policy (75 timings per policy and size). It ran on the development laptop (Windows, Python 3.11.9, OR-Tools 9.15.6755) with sampled CPU load between 1% and 15%: a lightly loaded laptop, not an isolated benchmark machine. Every CP-SAT run was `OPTIMAL` and every plan valid ({tab:runtime}, {fig:r_runtime}).'),
    T({ id: 'runtime', caption: 'Runtime benchmark: median allocation-call time [25th, 75th percentile].', cols: [0.7, 1.7, 1.2, 1.8, 1.4, 1.1], align: ['r', 'r', 'r', 'r', 'r', 'r'], header: runtime.header, rows: runtime.rows }),
    F({ id: 'r_runtime', path: V.res('fig12_runtime_benchmark'), widthCm: 14, caption: 'Runtime benchmark (log scale): median and interquartile band per policy and size. CP-SAT is two orders of magnitude slower than the heuristics, and stays well under the 5 s limit.' }),
    P('CP-SAT\'s own solve time is about 62–78% of the AidOS call; the rest is Python model construction and explanation building. At the largest size the API accepts (50 zones × 10 resources), balanced mode can reach its 5 s limit. One check with every entry at the 1,000,000-unit cap finished in about 2.6 s, while random requests at that size stopped at the limit with a valid plan labelled FEASIBLE rather than OPTIMAL. Urgency-first AidOS remained OPTIMAL. Every run in the benchmarks above was OPTIMAL. The Stage 4 scaling study measured 334.5 ms for AidOS at 50 zones under heavier background load (its tables are in the run directory). The two studies were run under different machine conditions and **should not be compared directly**; the Stage 5 figures supersede them for absolute times.'),

    H2('Discussion of results', 'discussion'),
    T({
      id: 'demonstrates', caption: 'What the evidence supports, and what it does not.',
      cols: [3.1, 3.1],
      header: ['AidOS demonstrates (within the synthetic setup)', 'AidOS does not demonstrate'],
      rows: [
        ['Reproducible, deterministic urgency-based allocation: identical logical results across independent runs and replays', 'Superiority over urgency greedy under the current objective: the plans are provably identical'],
        ['Valid constrained optimisation: zero hard-constraint violations; every evaluated solve proven optimal', 'An independently validated humanitarian urgency model: the rules, sets and floor are design assumptions'],
        ['Adaptive recommendations under events, with conserved inventory and blocked double dispatch', 'Better real-world disaster outcomes, or any effect on real people'],
        ['An explicit, tunable urgency–equity trade-off: a smooth, monotonic floor curve', 'That AidOS is "fairer" than FCFS: equity is indistinguishable unless the floor is used'],
        ['Explainable outputs: exact rule contributions, per-cell allocation reasons, event diffs', 'Operational readiness: no persistence, transport model, multi-user safety or practitioner validation'],
      ],
    }),
    P('**RQ1.** Using the urgency model shifts stock towards zones the model rates urgent, with large and consistent gains on objective-aligned metrics and no loss of units, but with no measurable improvement for the worst-served zone. **RQ2.** Under the implemented separable linear formulation, CP-SAT and greedy are provably identical; every AidOS-versus-FCFS difference is an *information effect* of the urgency model, not an *optimisation effect*. **RQ3.** A coverage floor converts urgency priority into equity smoothly and monotonically; in the tested scenarios even a 10% floor removed starvation. **RQ4.** Urgency-first allocation is responsive but redistributes towards newcomers at the expense of the original zones; the balanced variant is the only one that adapts without starving anyone.'),
    H3('Threats to validity'),
    B([
      '**Construct validity.** Urgency-weighted and critical-zone coverage are defined by the same fuzzy scores AidOS optimises; they are labelled objective-aligned throughout and are not used as independent evidence.',
      '**Internal validity.** All policies saw identical inputs (verified by one outcome hash per step), configuration was frozen before the reported runs, and an independent audit recomputed the Stage 4 statistics through a separate code path (21 of 21 checks passed). The late-arrival bias was a genuine threat; it was found, quantified and corrected by an additional experiment rather than by editing the original results.',
      '**External validity.** The scenario distributions were chosen by the team and are bounded (at most 50 zones). Correlations between arrival and urgency, real request patterns and other urgency models were not studied.',
      '**Statistical conclusion validity.** Paired analysis, script-level clustering for dynamic data, a small pre-declared test family with Holm correction, and effect sizes reported alongside intervals. Many descriptive comparisons were made; they are not treated as confirmatory.',
      '**Measurement.** Timings depend on the machine and its load; they are reported as distributions with recorded conditions and are excluded from every reproducibility check.',
    ]),

    // ===================================================================== 7
    H1('Limitations, Difficulties and Constraints', 'limitations'),
    H2('Modelling limitations', 'modellimits'),
    B([
      '**Synthetic data.** Every scenario is synthetic. Results describe the policies under the team\'s assumptions, not real crises.',
      '**Assumed fuzzy parameters.** Membership functions, rules and output constants were chosen for interpretability, not fitted or validated. Low and medium vulnerability are treated alike, and scores saturate at 87.5. Allocation order is sensitive to these choices ({sec:sensitivity}).',
      '**Sensitivity of definitions.** What counts as "urgent" and as "fair" is defined by the team. Different, equally defensible definitions would change who is served.',
      '**Separable formulation.** Resources never interact, which is precisely why greedy is optimal. There is no transport, vehicle capacity, routing, travel time, delivery deadline, spoilage or multi-depot logistics.',
      '**Instantaneous events.** Events take effect immediately; there are no shipments in transit or delays, and crises do not evolve on their own.',
      '**Full-plan dispatch.** A dispatch commits a whole plan; partial commits are not supported, and dispatched units are never returned.',
      '**Equity–urgency tension.** The linear objective permits starvation; the balanced variant mitigates it at a measured cost but does not resolve the underlying value judgement.',
      '**Frequent ties.** The engine produced only 26 distinct scores across the benchmark, and 390 of 504 scenarios contain zones with identical urgency (113 have two or more zones at the 87.5 maximum). Ties are broken by arrival order, so within an urgency level AidOS behaves like first-come-first-served. Under severe scarcity AidOS can also leave high-urgency zones without stock (41 of the 414 uncovered zones score 50 or more).',
    ]),
    H2('Engineering constraints'),
    B([
      '**In-memory sessions.** Simulation sessions live in one API process, expire after two hours idle and are lost on restart; run the API with a single worker. Export a session to keep it.',
      '**CP-SAT overhead.** About 100 times the cost of greedy for the same urgency-first plan; acceptable at this scale (a median of about 124 ms at 50 zones), but unnecessary for this objective.',
      '**Small-scale academic environment.** No authentication, persistence, multi-user safety or deployment, by design and by the team\'s constraints.',
      '**Version labels.** The engine reports version 0.4.0 and "stage 4" because the later stages added experiments, documentation and hardening fixes, but no engine feature.',
    ]),
    H2('Difficulties encountered and how they were resolved', 'difficulties'),
    P('{tab:difficulties} lists difficulties recorded in the project\'s development records (decision records, the experimental protocol and the review documents). Personal or team-process difficulties are for the individual reflection statements and are not reported here.'),
    T({
      id: 'difficulties', caption: 'Recorded technical difficulties and their resolution.',
      cols: [2.0, 2.6, 1.6],
      header: ['Difficulty', 'Resolution', 'Record'],
      rows: [
        ['The specified Mamdani design could lower urgency when a rating rose', 'Measured on the rule base; switched to product-Sugeno, which is provably monotone here', 'Decision record 0004; fuzzy-logic.md §5'],
        ['Floating-point noise (25.000000000000004) could flip categories and break ties', 'Scores rounded to 4 decimals at the source; exact integer coefficients (×10^{4})', 'fuzzy-logic.md "Resolution"'],
        ['The first dispatch design emptied the depot at the first dispatch, so later events had no effect', 'Redesigned before the reported runs: 30% initial stock and three supply waves', 'experimental-protocol.md, deviations'],
        ['Dynamic comparisons paired by step overstated precision', 'Script-level aggregation (n = 60 in Stage 4; 30 per urgency level in the controlled experiment)', 'experimental-protocol.md; scientific-review.md'],
        ['The dynamic scripts always made the late zone urgent, which biased the equity comparison', 'Decomposed, then re-run with late-zone urgency as a controlled factor; the claim was withdrawn', 'stage5-supplementary.md §4'],
        ['CP-SAT and greedy always agreed, raising the question of a defect', 'Proved equivalent; checked exhaustively; reframed the role of the optimiser', 'greedy-vs-cpsat-analysis.md'],
      ],
    }),
    H2('Future work'),
    P('The following are **not implemented**; they are directions the evidence suggests:'),
    B([
      'Coupling constraints where an optimiser genuinely matters: per-zone vehicle or route capacity, bundled kits, minimum lot sizes; this requires capacity data in the scenario schema.',
      'An urgency model elicited and validated with practitioners, and a sensitivity analysis of the resulting order.',
      'A coverage floor chosen with stakeholders, possibly per resource or per urgency band, or a concave (diminishing-returns) objective as an alternative to the floor.',
      'Multi-period planning with deliveries in transit, delays and partial dispatch.',
      'Persistent, multi-user sessions with authentication, if the prototype were ever to leave the classroom.',
    ]),

    // ===================================================================== 8
    H1('Conclusion and Discussion', 'conclusion'),
    P('AidOS set out to show how three foundational AI techniques could support a transparent decision about scarce relief supplies. It delivers a working, tested system: a zero-order Sugeno engine whose every score decomposes exactly into rule contributions; a CP-SAT allocation model with explicit hard constraints, truthful statuses and an independent validator; and a finite-state simulator with atomic events, an append-only dispatch ledger, conserved inventory and deterministic replay. The experiments covered 504 static scenarios, 180 dynamic scripts across both evaluation stages and six supplementary studies, all from versioned artifacts with checksums.'),
    P('Measured against its objectives, the project met its engineering goals: every plan satisfied every hard constraint (2,016/2,016 static and 1,680/1,680 dynamic plans), results reproduced across two independent runs, the urgency model is explainable and monotone on this rule base (0 dips in 52,920 steps), and RQ1–RQ4 were each answered with paired evidence ({sec:static} to {sec:dynamic}). One expectation was not supported: the optimiser does not improve the urgency-first allocation. Real-world validity was out of scope.'),
    P('The most instructive result was negative. The optimiser, intended as the project\'s centrepiece, adds nothing to the urgency-first plan, and the reason is structural: when resources do not interact and value is linear per unit, filling the most urgent zones first is optimal, which is the classical greedy result for knapsack problems with unit weights. Recognising this changed the project\'s framing. CP-SAT now serves as a certificate that a transparent rule is optimal, and as the framework in which the coupled balanced model, and any future coupling constraints, can be expressed. A second lesson concerns where the uncertainty actually lies: the plans depend only on the *order* of urgency scores, and that order depends on unvalidated membership and rule choices, so a more sophisticated solver would not have made the recommendations more trustworthy.'),
    P('The balanced variant deserves consideration in any real use because it makes a value judgement explicit and adjustable. In the tested scenarios a small floor removed starvation at a modest, measured cost in urgency priority. Where that dial should be set is not a technical question, and the system\'s job is to show the consequences of each setting honestly. More broadly, the project showed that a decision-support system earns trust through properties that are easy to overlook: determinism, independent validation, labelling objective-aligned metrics as such, and willingness to withdraw a claim (the dynamic equity advantage) when a better-controlled experiment contradicts it.'),
    P('Future work should introduce constraints that couple resources or zones, where optimisation matters, and replace the assumed urgency model with one elicited and validated with practitioners. Until then, AidOS should be read as what it is: a reproducible teaching prototype that makes the trade-offs of humanitarian allocation visible, not a tool for real relief decisions.'),
  ];
};
