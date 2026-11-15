# Submission readiness audit

**Against:** the official *CSCI218 Group Project: Guidelines and Grading Criteria, Autumn 2026* (parent folder, `CSCI218_Project_Guidelines_Grading_Criteria_AUT26.docx`), sections 4–6. Audited on 12 Nov 2026, at the end of Stage 5.

**Status values:**
- **PASS:** evidence exists in the repository.
- **PARTIAL:** evidence exists but something required is missing.
- **BLOCKED:** cannot be completed without a team or instructor action.
- **N/A:** not applicable.

No grade is predicted. **The group report itself has not been written** (Stage 6). Rows about the report assess whether the *material* for it exists.

## Deliverables (guidelines section 4)

| Requirement | Evidence | Location | Status | Gap | Action |
|---|---|---|---|---|---|
| 4.1 Group report with the ten prescribed sections | Material exists for every section; the report has not been written | `docs/` (see the mapping below); a template at `../AidOS_Group_Project_Report.docx` | BLOCKED (Stage 6) | The report | Write it from the evidence map below |
| 4.1 Appendix A: Git link and contribution table | Local repository only; no remote, no commits | `docs/submission/git-and-reproducibility.md` | BLOCKED | Shared repository, real contribution table | Team creates the remote and commits under their own identities |
| 4.1 Appendix B/C (bonus): meeting log, mentor form | None | — | N/A unless a partner was approved by Week 3 | — | Do not claim a partner |
| 4.3 Code via Git with a README for install and run | README with setup, run and test commands; lockfiles; CI workflow | `README.md`, `apps/api/uv.lock`, `apps/web/package-lock.json`, `.github/workflows/ci.yml` | PARTIAL | Not pushed; **"history must show contributions from all members"** | Push; every member contributes genuinely from now on |
| 4.4 Live online demo and individual viva | A working system; smoke test; runbook; viva notes | `scripts/smoke_test.py`, `docs/submission/demo-runbook.md`, `docs/submission/viva-preparation.md` | PARTIAL | Rehearsal, timing, screenshots for the fallback | Rehearse; capture screenshots |
| 4.5 Individual contribution and reflection statement | — | — | BLOCKED | Written by each student about their own work | Each member, from real evidence |

## Group criteria (section 5.1)

### 1. Problem understanding and motivation (10%)

| Requirement | Evidence | Location | Status | Gap or action |
|---|---|---|---|---|
| Defines the problem and its significance | Problem statement, scope, synthetic-data stance | `AidOS project info.md` §0–1, `PRODUCT.md`, the landing story | PASS | Turn into the report's Motivation section |
| Measurable objectives and scope, placed within AI foundations | An objectives table with evidence; non-goals | spec §2–3; `docs/evaluation/experimental-protocol.md` "Questions" | PASS | — |
| Why this approach suits the problem better than alternatives | Sugeno vs Mamdani (measured); CP-SAT vs greedy (proved equivalent under the linear objective, with the conditions where it is not); the floor trade-off | `docs/decisions/0004-*`, `docs/algorithms/greedy-vs-cpsat-analysis.md`, `docs/evaluation/stage5-supplementary.md` | PASS | State honestly that the optimiser's advantage over greedy is not in plan quality under this objective |
| Honest scope and limitations | Limitation sections in every evaluation doc; the dashboard limitations panel | `docs/evaluation/results.md` §5, `scientific-review.md` | PASS | — |

### 2. Technical depth and algorithm design (25%)

| Requirement | Evidence | Location | Status | Gap or action |
|---|---|---|---|---|
| Correct, complete formulation | Sets, variables, constraints, lexicographic objectives, integer scaling, balanced floor | `docs/algorithms/allocation-formulation.md` | PASS | — |
| Rule base and membership functions | 27 rules, partitions, inference, worked example | `docs/algorithms/fuzzy-logic.md`, `apps/api/aidos/config/fuzzy_rules.json` | PASS | — |
| Justified design choices | Method choice (measured), objective choice, tie-break, floor | decisions 0004–0006 | PARTIAL | The Sugeno choice and the 25% default await instructor input (`instructor-review.md`) |
| Trade-offs, complexity, limitations | Complexity per policy; solver overhead; floor trade-off curve; fuzzy sensitivity | `docs/evaluation/policies.md`, `stage5-supplementary.md` | PASS | — |
| Standard variants or hybrids | Mamdani vs Sugeno-min vs Sugeno-product; urgency-first vs balanced; greedy vs exact | as above | PASS | — |
| Constraint validation | Independent validator; property tests; zero violations across all runs | `apps/api/aidos/evaluation/invariants.py`, `tests/` | PASS | — |
| State machine (simulation) | FSM, events, atomicity, replay | `docs/simulation/*` | PASS | — |

### 3. Implementation quality (15%)

| Requirement | Evidence | Location | Status | Gap or action |
|---|---|---|---|---|
| Modular, readable code with docstrings | Domain / ai / evaluation / simulation / api layers; module docstrings | `apps/api/aidos/`, `apps/web/src/` | PASS | — |
| Reproducible: seeds, configuration, dependencies, README | Seeded generators; config files; lockfiles; manifests with checksums; README | `docs/submission/git-and-reproducibility.md` | PASS | — |
| Tested and validated (edge cases) | 288+ backend tests, 81 frontend tests; randomized invariants; exhaustive equivalence checks; smoke test | `tests/`, `apps/web/src/test/`, `scripts/smoke_test.py` | PASS | Final counts in the Stage 5 handoff |
| Reasonable runtime efficiency | Benchmark: AidOS 6–125 ms, heuristics < 1 ms, up to 50 zones | `stage5-supplementary.md` §5 | PASS | — |
| Repository history shows all members | None yet | — | BLOCKED | Team action (see 4.3) |

### 4. Results and analysis (10%)

| Requirement | Evidence | Location | Status | Gap or action |
|---|---|---|---|---|
| Meaningful metrics | Feasibility, coverage, urgency-weighted coverage (flagged as objective-aligned), equity, starvation, runtime, dynamic and dispatch metrics | `docs/evaluation/metric-definitions.md` | PASS | — |
| Fair setup, multiple runs, mean and sd | 504 paired scenarios, 60 + 120 scripts; mean, sd, percentiles; bootstrap CIs; Holm-adjusted tests | `results-tables.md` | PASS | — |
| Interpretation against baselines; threats to validity | Better / similar / worse table; scientific review; the dynamic-bias correction | `results.md`, `scientific-review.md`, `stage5-supplementary.md` | PASS | — |
| Replication materials provided | Raw CSV, configs, manifests, scripts, verification | `experiments/results/`, `experiments/*.py` | PASS | Ensure they are pushed (about 7 MB) |

### 5. Report structure and presentation (10%)

| Requirement | Evidence | Location | Status | Gap or action |
|---|---|---|---|---|
| Follows the section 4 structure | — | — | BLOCKED (Stage 6) | Write the report |
| Captioned figures and tables | Figures 1–12 (PNG and SVG) with titles and axes; generated tables | `docs/evaluation/figures/`, `results-tables.md` | PASS (material) | Add captions in the report |
| Citations and references; data sources disclosed | Data is synthetic and disclosed; the official guidelines and the Project C sheet are listed in spec §12 | `data/README.md` | PARTIAL | No academic references compiled. **Do not invent any.** Cite only sources the team actually consulted (for example the OR-Tools documentation, and course texts on fuzzy logic) |
| Screenshots | Captures exist only in a temporary folder | — | PARTIAL | Capture final screenshots into the repository for the report |

### 6. Project demonstration (10%)

| Requirement | Evidence | Location | Status | Gap or action |
|---|---|---|---|---|
| Runs live and reliably; shows key AI behaviours, including dynamic ones | Journeys A–D pass; smoke test passes | `docs/submission/frontend-audit.md`, `scripts/smoke_test.py` | PASS | — |
| Organised, within time, links demo to design and results | 14-step runbook with fallbacks | `docs/submission/demo-runbook.md` | PARTIAL | Rehearse against the time limit |
| Answers questions accurately | Viva preparation | `docs/submission/viva-preparation.md` | PARTIAL | Every member studies it, including parts they did not build |

## Individual criteria (section 6)

| Requirement | Status | Note |
|---|---|---|
| 6.1 Viva: explain own and others' parts | PARTIAL | Material exists. The viva cap rule (group mark capped at 55/80 for a student who cannot explain their own contribution) makes genuine ownership essential |
| 6.2 Reflection statement with evidence (commits, functions, report sections) | BLOCKED | Requires real per-member history; claims contradicted by the repository fall into the lowest band |

## Items outside the rubric that affect submission

| Item | Status | Action |
|---|---|---|
| AI-tool use policy (the guidelines defer to the subject descriptor) | BLOCKED | Read the descriptor; disclose as required (`docs/contribution-log.md`) |
| Topic registration and technique combination | Unconfirmed | `docs/submission/instructor-review.md` §2 |
| Sugeno vs Mamdani | Pending instructor | `instructor-review.md` §1 |
| Due dates | Unknown (Moodle/Turnitin) | Record them in the README once known |

## Evidence map for the report (sections in guidelines order)

| Report section | Source material |
|---|---|
| Executive summary | `results.md` summary table; `stage5-supplementary.md` "What changes in the conclusions" |
| Motivation | spec §0–1, `PRODUCT.md` |
| Technical requirements | spec §3, §7; `docs/architecture.md`; README prerequisites |
| Main constructs | `docs/algorithms/*` (fuzzy, formulation, greedy vs CP-SAT), `docs/simulation/*`, `docs/evaluation/policies.md` |
| Implementation | `docs/architecture.md`, `docs/frontend.md`, code excerpts from `aidos/ai/*.py`, screenshots |
| Experiments and results | `experimental-protocol.md`, `metric-definitions.md`, `results-tables.md`, figures 1–12, `stage5-supplementary.md` |
| Limitations | `results.md` §5, `scientific-review.md`, viva "what they do not show" |
| Conclusion | as above, with no claims beyond the evidence |
| References | only genuinely consulted sources |
| Appendices | repository URL; contribution table; optional run manifests |
