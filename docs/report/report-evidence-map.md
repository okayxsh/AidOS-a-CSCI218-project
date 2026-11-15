# Report evidence map

Traceability for `docs/report/AidOS_Final_Group_Report.docx` (56 pages). Every figure, table and headline number is linked to the artifact it comes from.

- **Generated tables.** Tables marked as coming from `results-tables.md` or `stage5-supplementary.md` are read by the report builder directly from those files, which are themselves generated from the run CSV/JSON. They are never retyped.
- **Checks.** `experiments/audit_stage4.py` independently recomputed the Stage 4 numbers (21/21 checks passed). The builder also recomputed every result checksum (8/8 folders match).

## Frozen and supplementary runs

| Run | Role |
|---|---|
| `extended-20261112T100136Z` | Stage 4 main evidence (504 scenarios, 60 scripts, 240 trajectories) |
| `standard-20261112T100617Z` | Stage 4 independent re-run; 560 + 560 shared rows identical |
| `supplementary-greedy-equivalence-20261112T164930Z` | Proof checks (36,240 exhaustive, 700 random), counterexample |
| `supplementary-floor-sweep-20261112T165054Z` | Coverage floor 0–40% (280 scenarios × 6) |
| `supplementary-fuzzy-sensitivity-20261112T165230Z` | Ten fuzzy variants (280 scenarios) |
| `supplementary-dynamic-controlled-20261112T165434Z` | Late-zone urgency controlled (120 scripts) |
| `supplementary-runtime-benchmark-20261112T170741Z` | Runtime benchmark (3–50 zones) |
| `supplementary-stage4-audit-20261112T170734Z` | Independent recomputation of Stage 4 statistics |

## Headline numbers

| Claim in the report | Value | Source |
|---|---|---|
| Valid static plans | 2,016 / 2,016 | `docs/evaluation/results-tables.md` (generated from `experiments/results/extended-20261112T100136Z/summary.json`) §1 |
| Valid recommendation-mode plans | 1,680 / 1,680 | `docs/evaluation/results.md` §1 |
| AidOS proven OPTIMAL | 504 / 504 (balanced 504 / 504) | `docs/evaluation/results-tables.md` (generated from `experiments/results/extended-20261112T100136Z/summary.json`) §1 |
| AidOS = greedy plans | 504 / 504 | `docs/evaluation/results-tables.md` (generated from `experiments/results/extended-20261112T100136Z/summary.json`) §1; `audit_stage4.py` |
| Urgency-weighted coverage, AidOS − FCFS | +0.1020 [0.0922, 0.1119], d_z 0.91 | `docs/evaluation/results-tables.md` (generated from `experiments/results/extended-20261112T100136Z/summary.json`) §3 |
| Critical-zone coverage, AidOS − FCFS | +0.2877 [0.2552, 0.3212], n = 325 | `docs/evaluation/results-tables.md` (generated from `experiments/results/extended-20261112T100136Z/summary.json`) §3 |
| Lowest-zone coverage, AidOS − FCFS | −0.0059 [−0.0158, 0.0039]; Holm p = 0.4180 | `docs/evaluation/results-tables.md` (generated from `experiments/results/extended-20261112T100136Z/summary.json`) §3–4 |
| Balanced − AidOS: lowest zone / UWC | +0.1801 [0.1714, 0.1886] / −0.0307 [−0.0339, −0.0276] | `docs/evaluation/results-tables.md` (generated from `experiments/results/extended-20261112T100136Z/summary.json`) §3 |
| Starved zones under balanced | 0.000 (sd 0.000) in all 504 | `docs/evaluation/results-tables.md` (generated from `experiments/results/extended-20261112T100136Z/summary.json`) §2 |
| Exhaustive equivalence | E1 24,576/24,576; E2 11,664/11,664; random 700/700 | `supplementary-greedy-equivalence-*/summary.json` |
| Counterexample objectives | greedy 8,850,000 (10 units); CP-SAT 30,400,000 (20 units) | same file |
| Floor sweep: floor reduced at 25% / 40% | 5 / 1,003 and 136 / 1,003 resource cases | `supplementary-floor-sweep-*/summary.json` |
| Mamdani dips | 1,062 / 52,920 (2.01%, worst 0.8947) | `docs/algorithms/fuzzy-logic.md` §5 |
| Product-Sugeno dips (variants) | 0 / 7,260; min t-norm 132 / 7,260 | `docs/evaluation/stage5-supplementary.md` §3 |
| Breakpoint shift: plan changed | 113 (P1) and 103 (P2) of 280 | `docs/evaluation/stage5-supplementary.md` §3 |
| Controlled dynamic, high urgency, lowest original-zone fulfilment AidOS − FCFS | −0.048 [−0.077, −0.022] | `docs/evaluation/stage5-supplementary.md` §4 |
| Late-zone decomposition (Stage 4 dispatch) | late zone never served: FCFS 60, AidOS 0; original zones never served: FCFS 27, AidOS 53 | `docs/evaluation/results-tables.md` (generated from `experiments/results/extended-20261112T100136Z/summary.json`) §8 |
| Runtime medians (Stage 5) | AidOS 6.3 ms (3 zones) to 124 ms (50); greedy 0.05 to 0.81 ms; CPU load 1–15% | `supplementary-runtime-benchmark-*/summary.json` |
| Static runtime (Stage 4) | AidOS median 12.06 ms, mean 12.43 (sd 5.85); FCFS 0.114 ms | `extended-*/summary.json` (`runtime_ms`) |
| Tests | 288 backend passed; 81 frontend passed | Final verification, 13 Nov 2026 |

## Figures

| Figure | Caption (short) | File | Source |
|---|---|---|---|
| 1 | System architecture as implemented | `docs/report/figures/diagrams/d1_architecture.png` | Hand-drawn from `docs/architecture.md`, `apps/api/aidos/main.py`, `api/routes_*.py`, `pipeline.py`, `simulation/store.py`, `evaluation/{campaign,artifacts}.py`, `apps/web/src/app/Router.tsx`, `api/client.ts` |
| 2 | The zero-order Sugeno inference pipeline, from three crisp ratings to a score and an exact | `docs/report/figures/diagrams/d2_fuzzy_pipeline.png` | `apps/api/aidos/config/fuzzy_rules.json` (breakpoints, outputs), `ai/fuzzy.py`; the generator checks the values against the config |
| 3 | Membership functions of the three input terms (left), drawn from the production configurat | `docs/report/figures/diagrams/mf_membership.png` | Plotted directly from `fuzzy_rules.json` by `docs/report/figures/src/mf_plot.py` |
| 4 | Allocation workflow for the AidOS policies: integer coefficients from the fuzzy scores, a  | `docs/report/figures/diagrams/d3_cpsat_workflow.png` | `ai/constraints.py`, `ai/baseline_greedy.py`, `ai/policies.py`, `evaluation/invariants.py`, `docs/algorithms/allocation-formulation.md` |
| 5 | The simulation session state machine, as defined by the TRANSITIONS table in aidos/simulat | `docs/report/figures/diagrams/d4_fsm.png` | `simulation/fsm.py` (`TRANSITIONS`), `docs/simulation/state-machine.md` |
| 6 | Event-processing pipeline | `docs/report/figures/diagrams/d5_event_pipeline.png` | `simulation/{events,reducer,session,store}.py`, `main.py` (HTTP codes), `docs/simulation/events.md`, `replay.md` |
| 7 | Landing page (first viewport) | `docs/report/figures/screenshots/s01_landing.png` | Live capture, `/`, engine 0.4.0, 13 Nov 2026 |
| 8 | Dashboard overview for triage-demo-001: stock against requests, the 230-unit shortfall, an | `docs/report/figures/screenshots/s02_overview_report.png` | Live capture, `/dashboard?scenario=triage-demo-001` |
| 9 | Fuzzy urgency explanation for Zone C: memberships of each rating and the four fired rules  | `docs/report/figures/screenshots/s03_urgency_report.png` | Live capture, Allocate page → Run allocation → Fuzzy urgency panel, Zone C |
| 10 | AidOS allocation for triage-demo-001: 330 of 560 units allocated, 5/5 independent checks p | `docs/report/figures/screenshots/s04_allocation_report.png` | Live capture, `/dashboard/allocate?scenario=triage-demo-001` → Run allocation (AidOS tab) |
| 11 | Baseline comparison on the same snapshot: urgency-weighted coverage 62.5% (FCFS), 64.6% (g | `docs/report/figures/screenshots/s05_comparison_report.png` | Live capture, same page, Baseline comparison |
| 12 | Rule firing and the Sugeno weighted average (aidos/ai/fuzzy.py, evaluate). | `(code excerpt)` | `apps/api/aidos/ai/fuzzy.py`, `evaluate()` (abridged) |
| 13 | CP-SAT variables, stock constraints and lexicographic phases (aidos/ai/constraints.py, all | `(code excerpt)` | `apps/api/aidos/ai/constraints.py`, `allocate_aidos()` (abridged) |
| 14 | The state-transition table and the stale-plan guard (aidos/simulation/fsm.py and reducer.p | `(code excerpt)` | `apps/api/aidos/simulation/fsm.py` (`TRANSITIONS`) and `reducer.py` (`PlanCommitted` branch) |
| 15 | Simulation after three events on triage-demo-001 | `docs/report/figures/screenshots/s06_simulation_report.png` | Live capture, Simulate: Zone B severity 9; Zone D added (8/9/9; 40/50/10); 30 medical kits lost |
| 16 | Before and after a single escalation (Zone B severity 6 → 9): B's urgency rises from 62.5  | `docs/report/figures/screenshots/s07_sim_before_after_report.png` | Live capture, Simulate: Zone B severity 6 → 9 only |
| 17 | The Evaluate page reading the frozen run extended-20261112T100136Z (504 scenarios, 2,016 p | `docs/report/figures/screenshots/s08_evaluation_report.png` | Live capture, `/dashboard/evaluate`, run `extended-20261112T100136Z` |
| 18 | Evaluation methodology: seeded scenario families, all four policies on identical inputs, i | `docs/report/figures/diagrams/d6_evaluation_method.png` | `evaluation/{families,campaign,dynamic,stats,analysis}.py`; counts from `extended-20261112T100136Z/manifest.json` and `config.json` |
| 19 | Static benchmark, mean over 504 scenarios with 95% bootstrap confidence intervals | `docs/report/figures/results/fig1_policy_metrics.png` | `experiments/results/extended-20261112T100136Z/figures/fig1_policy_metrics.png` (byte-identical copy) |
| 20 | Each policy minus FCFS, paired on the same scenarios, with 95% bootstrap CIs | `docs/report/figures/results/fig2_paired_vs_fcfs.png` | `extended-20261112T100136Z/figures/fig2_paired_vs_fcfs.png` |
| 21 | Per-zone coverage against fuzzy urgency, family B (each dot is one zone in one scenario) | `docs/report/figures/results/fig8_zone_coverage.png` | `extended-20261112T100136Z/figures/fig8_zone_coverage.png` |
| 22 | Effect of the coverage-floor target (280 supplementary scenarios, 95% CI) | `docs/report/figures/results/fig9_floor_tradeoff.png` | `supplementary-floor-sweep-20261112T165054Z/fig9_floor_tradeoff.png` |
| 23 | Fuzzy design sensitivity: share of scenarios whose urgency order changed, whose AidOS plan | `docs/report/figures/results/fig10_fuzzy_sensitivity.png` | `supplementary-fuzzy-sensitivity-20261112T165230Z/fig10_fuzzy_sensitivity.png` |
| 24 | Controlled dynamic experiments (120 scripts): coverage and fulfilment of the late zone, an | `docs/report/figures/results/fig11_dynamic_controlled.png` | `supplementary-dynamic-controlled-20261112T165434Z/fig11_dynamic_controlled.png` |
| 25 | Runtime benchmark (log scale): median and interquartile band per policy and size | `docs/report/figures/results/fig12_runtime_benchmark.png` | `supplementary-runtime-benchmark-20261112T170741Z/fig12_runtime_benchmark.png` |
| 26 | Stage 4: metrics by scarcity family (A low, B moderate, C severe). | `docs/report/figures/results/fig3_scarcity.png` | `extended-20261112T100136Z/figures/fig3_scarcity.png` |
| 27 | Stage 4: urgency-weighted coverage against lowest-zone coverage, family means | `docs/report/figures/results/fig4_tradeoff.png` | `extended-20261112T100136Z/figures/fig4_tradeoff.png` |
| 28 | Stage 4 scaling study (heavier background load; see {sec:runtime}). | `docs/report/figures/results/fig5_runtime.png` | `extended-20261112T100136Z/figures/fig5_runtime.png` |
| 29 | Stage 4 recommendation mode: units reallocated per event type. | `docs/report/figures/results/fig6_dynamic_reallocation.png` | `extended-20261112T100136Z/figures/fig6_dynamic_reallocation.png` |
| 30 | Stage 4 dispatch mode: outcomes per policy | `docs/report/figures/results/fig7_dispatch.png` | `extended-20261112T100136Z/figures/fig7_dispatch.png` |

## Tables

| Table | Caption (short) | Source |
|---|---|---|
| 1 | Research questions, measurable criteria and where each is answered. | `docs/evaluation/experimental-protocol.md` (questions); report sections |
| 2 | Alternatives considered for each component. | `docs/decisions/0001-*`, `0004-*`; `docs/algorithms/greedy-vs-cpsat-analysis.md` |
| 3 | Functional requirements and the evidence that each is met. | Code paths listed in the table; `tests/` |
| 4 | Non-functional requirements and how they are met. | `docs/architecture.md`; final verification (13 Nov 2026) |
| 5 | Technology stack, versions and justification. | `apps/api/uv.lock`, `apps/web/package-lock.json`, `.venv` Python version |
| 6 | Notation. | `docs/algorithms/allocation-formulation.md` §1 |
| 7 | Rule consequents | `apps/api/aidos/config/fuzzy_rules.json` |
| 8 | Rules fired for Zone C of triage-demo-001 (severity 7, time criticality 7, vulnerability 5 | `docs/algorithms/fuzzy-logic.md` §7; re-computed by the engine (contributions 38.8889 + 13.8889 + 13.8889 + 4.1667) |
| 9 | Measured monotonicity of three inference methods on the AidOS rule base (52,920 single-rat | `experiments/fuzzy_method_comparison.py` output, recorded in `docs/algorithms/fuzzy-logic.md` §5 |
| 10 | Policy statuses and their meaning. | `docs/algorithms/allocation-formulation.md` §9; `ai/constraints.py` `_STATUS` |
| 11 | The four allocation policies. | `docs/evaluation/policies.md`; `ai/baseline_*.py` |
| 12 | Allocations on triage-demo-001 (medical · water · shelter) and plan metrics, produced by t | Re-run on 13 Nov 2026 via `POST /api/allocations/compare` (engine 0.4.0); identical to `allocation-formulation.md` §10 |
| 13 | Session states. | `docs/simulation/state-machine.md` |
| 14 | Event types. | `docs/simulation/events.md`; `simulation/events.py`, `reducer.py` |
| 15 | What AidOS explains, how, and the limits of each explanation. | `ai/fuzzy.py` (`explain`), `ai/constraints.py` (`_explain_cells`), `simulation/compare.py` |
| 16 | Repository layout. | Repository tree |
| 17 | API route groups. | `apps/api/aidos/api/routes_*.py` |
| 18 | Simulation failure handling. | `docs/simulation/state-machine.md`; `main.py` error handlers |
| 19 | Final verification results (13 November 2026). | Final verification log, 13 Nov 2026 (commands run in this session) |
| 20 | Static scenario families (72 scenarios each). | `docs/evaluation/experimental-protocol.md`; `evaluation/families.py` |
| 21 | Metrics | `docs/evaluation/metric-definitions.md`; `evaluation/metrics.py` |
| 22 | Feasibility and solver status over 504 static scenarios. | `docs/evaluation/results-tables.md` (generated from `experiments/results/extended-20261112T100136Z/summary.json`) §1 |
| 23 | Static benchmark: mean (sd) per policy over 504 scenarios | `docs/evaluation/results-tables.md` (generated from `experiments/results/extended-20261112T100136Z/summary.json`) §2 |
| 24 | Paired differences on the same scenarios (first policy minus second), 95% bootstrap CI | `docs/evaluation/results-tables.md` (generated from `experiments/results/extended-20261112T100136Z/summary.json`) §3 (AidOS − FCFS and balanced − AidOS rows) |
| 25 | Pre-declared hypothesis tests, AidOS versus FCFS (exact sign test, Holm-adjusted, n = 504) | `docs/evaluation/results-tables.md` (generated from `experiments/results/extended-20261112T100136Z/summary.json`) §4 |
| 26 | Per-family means: urgency-weighted coverage † and lowest zone coverage, with the AidOS − F | `docs/evaluation/results-tables.md` (generated from `experiments/results/extended-20261112T100136Z/summary.json`) §5 |
| 27 | Scenarios (of 504) in which two policies produced identical plans. | `docs/evaluation/results-tables.md` (generated from `experiments/results/extended-20261112T100136Z/summary.json`) §1 |
| 28 | Exhaustive and randomised checks of the equivalence (supplementary run supplementary-greed | `docs/algorithms/greedy-vs-cpsat-analysis.md` §3; `supplementary-greedy-equivalence-20261112T164930Z/summary.json` |
| 29 | Counterexample for a proposed extension (vehicle capacity 10 units per zone; medical kits  | `supplementary-greedy-equivalence-20261112T164930Z/summary.json` (`counterexample_proposed_extension`) |
| 30 | Coverage-floor sweep over 280 supplementary scenarios | `docs/evaluation/stage5-supplementary.md` §2; `supplementary-floor-sweep-20261112T165054Z/summary.json` |
| 31 | Fuzzy design variants (280 scenarios; counts out of 280 unless stated) | `docs/evaluation/stage5-supplementary.md` §3; `supplementary-fuzzy-sensitivity-20261112T165230Z/summary.json` |
| 32 | Recommendation mode (60 scripts, 420 steps): mean units reallocated per event (share of st | `docs/evaluation/results-tables.md` (generated from `experiments/results/extended-20261112T100136Z/summary.json`) §6 |
| 33 | Dispatch mode (60 scripts per policy): outcomes at the end of each trajectory. | `docs/evaluation/results-tables.md` (generated from `experiments/results/extended-20261112T100136Z/summary.json`) §7 |
| 34 | Decomposition of the Stage 4 dynamic results: the late, urgent zone versus the original zo | `docs/evaluation/results-tables.md` (generated from `experiments/results/extended-20261112T100136Z/summary.json`) §8 |
| 35 | Controlled dynamic experiment (30 scripts per urgency level) | `docs/evaluation/stage5-supplementary.md` §4; `supplementary-dynamic-controlled-20261112T165434Z/summary.json` |
| 36 | Paired by script, AidOS − FCFS, dispatch mode: lowest original-zone fulfilment (95% CI). | `docs/evaluation/stage5-supplementary.md` §4 |
| 37 | Runtime benchmark: median allocation-call time [25th, 75th percentile]. | `docs/evaluation/stage5-supplementary.md` §5; `supplementary-runtime-benchmark-20261112T170741Z/summary.json` |
| 38 | What the evidence supports, and what it does not. | `docs/evaluation/results.md` §5; `docs/evaluation/stage5-supplementary.md` (conclusions) |
| 39 | Recorded technical difficulties and their resolution. | Decision record 0004; `experimental-protocol.md` (deviations); `scientific-review.md`; `docs/evaluation/stage5-supplementary.md` |
| 40 | Objectives revisited. | Report sections 6.4–6.9 |
| 41 | Team contribution table (template from the CSCI218 guidelines, Appendix A). | CSCI218 guidelines, Appendix A template |
| 42 | The 27 rules of the production fuzzy configuration (apps/api/aidos/config/fuzzy_rules.json | `apps/api/aidos/config/fuzzy_rules.json` (generated at build time) |
| 43 | Complete list of API endpoints. | `apps/api/aidos/api/routes_*.py`, `main.py` |
| 44 | Commands to install, run, test and reproduce (from the repository root unless stated). | `README.md`; `docs/submission/git-and-reproducibility.md` |
| 45 | Result directories and checksum verification. | Manifests in `experiments/results/*/manifest.json`; SHA-256 recomputed at build time |
| 46 | Stage 4 scaling study: median runtime (ms) by number of zones. | `docs/evaluation/results-tables.md` (generated from `experiments/results/extended-20261112T100136Z/summary.json`) §9 |

## References

The 24 references were each checked on 13 Nov 2026 against Crossref (`api.crossref.org/works/<DOI>`), arXiv, zbMATH Open, the Library of Congress or Open Library, the publisher, or official documentation. The two course documents are cited as supplied.

Notes from the check:
- the Holm (1979) issue number was left out because it could not be confirmed from a fetched source;
- Russell and Norvig is dated 2021, from the Library of Congress record (the retail release was 2020);
- the OR-Tools citations use version 9.15, the version the project runs; the official citation page shows 9.12 as its example.

## Known gaps

- **Team details still to complete:** student names and IDs, lab group, instructor, repository URL and submission date (cover, Appendix A).
- **Pending confirmations:** the instructor's decision on Sugeno versus Mamdani, the topic registration, and the AI-tool policy (Appendix A, Appendix E).
- **Screenshot dependency:** the screenshots show engine version 0.4.0. Recapture them if the UI changes before submission.
