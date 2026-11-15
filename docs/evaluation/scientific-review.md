# Scientific review of the evaluation

An analytical self-review, written by taking five perspectives in turn. **No external experts were consulted.** For each concern: what was checked, what was found, and what was changed.

## 1. AI algorithms lecturer: are the baselines and the comparison fair?

| Concern | Finding | Action |
|---|---|---|
| Is FCFS weakened to make AidOS look good? | FCFS is unchanged since Stage 1. In generated scenarios, arrival order is the zone index and ratings are random, so arrival is independent of urgency. FCFS is neither helped nor handicapped. | None needed; documented in `policies.md`. |
| Do policies see different information? | Yes: FCFS ignores urgency by design. | The comparison is decomposed. Greedy vs FCFS is the information effect; AidOS vs greedy the optimisation effect (zero). |
| Is the strongest relevant baseline included? | Urgency greedy uses exactly AidOS's information without a solver. | Included. It ties with AidOS everywhere, which is reported as a central result. |
| Are the dynamic scripts neutral? | **No.** Each adds a late, highly urgent zone, which FCFS can never serve. | Kept, because it is the specified use case. The bias is quantified (results-tables.md, section 8) and dynamic equity results are explicitly not generalised (results.md, section 3). |

## 2. Optimisation researcher: are the objectives stated correctly, and is optimisation doing anything?

| Concern | Finding | Action |
|---|---|---|
| Does the documented objective match the code? | Checked against `constraints.py`: lexicographic urgency then tie-break, integer coefficients at 10⁴ × score, as documented. The reported objective value is recomputed exactly from each solution. | None. |
| Is optimality claimed honestly? | All 1,008 CP-SAT runs report `OPTIMAL` for every phase; no `FEASIBLE` or timeouts occurred, so no unproven plan is mislabelled. | None. |
| Does the solver add value? | Not for the urgency-first objective: the problem is separable and linear, so greedy is optimal. Balanced mode is the only place the model matters, and even it could be computed by water-filling. | Stated plainly in `policies.md` and `results.md`. Not presented as a weakness hidden in the appendix. |
| Is urgency-weighted coverage circular? | Yes: it is the AidOS objective, up to ε. | Marked objective-aligned everywhere: tables, figures, dashboard. Conclusions rest on external metrics. |

## 3. Statistician: do the summaries match the data, and is inference appropriate?

| Concern | Finding | Action |
|---|---|---|
| Do summaries reconcile with raw rows? | `summary.json` is recomputed from the CSVs and compared byte-for-byte (`verify_results.py`; a unit test does the same on a small run). | Automated. |
| Paired design? | Every static comparison pairs the four policies on the same scenario (one snapshot hash per scenario, verified). | — |
| Independence of dynamic observations | **Problem found:** the first analysis paired dynamic results by step, treating the 7 steps of a script as independent. That understates uncertainty. | Fixed before the reported run: comparisons use one mean per script (n = 60). Tested. |
| Multiple comparisons | Many comparisons are computed. | Only four pre-declared tests carry p-values (exact sign test, Holm-adjusted). Everything else is reported as effect sizes with bootstrap CIs and no p-values. |
| Ties | Many paired differences are exactly 0 (for example, 302 of 504 for lowest zone coverage). | W/T/L counts are reported. The sign test excludes ties. The median difference shows when most pairs are tied. |
| Effect sizes when variance is 0 | AidOS vs greedy differences are identically 0. | d_z is reported as N/A, not as infinity or 0. |
| Pooling across families | "All families" weights each family equally (72 each), an arbitrary mix. | Per-family results are always reported beside the pooled ones. |
| Scope of inference | The CIs describe the generator's distribution only. | Stated in the protocol, results, dashboard and figures. |
| Reproducibility | An independent standard run reproduces 1,120 logical rows exactly; the summary for the same seeds is deterministic. | Automated (`--against`). |

## 4. Humanitarian operations analyst: are quantities and conclusions meaningful?

| Concern | Finding | Action |
|---|---|---|
| Adding different resources | Unit coverage sums kits and packs. | Mean resource coverage (unit-free) is reported beside it. Both are identical across policies anyway. |
| "Fairness" | Equal coverage is not fair when needs differ; the Jain index can be high when everyone gets little. | Equity metrics are described as distribution measures, read alongside lowest-zone coverage. No ethical ranking is claimed. |
| Who is starved | Similar starvation counts hide different victims: late arrivals under FCFS, low scores under AidOS. | Shown in figure 8 and discussed. A low score comes from a design-assumption model, which matters if the ratings are wrong. |
| Urgency model dependence | Every urgency metric uses the same Sugeno model the policies use. If the ratings or rules are wrong, the "gains" are wrong in the same direction. | Stated as a limitation. External metrics are given priority in the conclusions. |
| Realism | Synthetic families with uniform ratings and arbitrary ranges; no logistics, travel time or delivery uncertainty. | Stated. No humanitarian effectiveness is claimed. |

## 5. Software reliability engineer: can the results be trusted as artefacts?

| Concern | Finding | Action |
|---|---|---|
| Hidden failures | 0 failures recorded. The runner records exceptions instead of skipping silently (tested by forcing a failure). | — |
| Overwritten results | Run directories are created with `exist_ok=False` (tested). | — |
| Tampering or corruption | A SHA-256 per file in the manifest, re-checked by `verify_results.py`. | — |
| Timing noise | The extended run took 279 s, against 146 s in an earlier development run of the same preset. Background desktop load (browser, editor) was present; 50-zone timings vary widely. | Runtimes are reported as medians and percentiles from one machine, never as deterministic values. They are excluded from all reproducibility checks. |
| Source provenance | The folder was not a git repository during Stage 4, so no commit hash could be recorded. | Recorded as "unavailable" in every manifest. A local repository was initialised in Stage 5 (no commits yet); see `docs/submission/git-and-reproducibility.md`. |
| API safety | Run ids are validated by regex, directories must be direct children of the results root, and only fixed file names are read. | Tested (invalid id, missing run, traversal attempt). |

## Changes made as a result of the review

1. **Dynamic comparisons:** now clustered by script instead of by step.
2. **Dispatch mode redesigned:** starting at 30% stock with supply waves, so that events between dispatches can matter.
3. **The late-urgent-zone bias:** quantified in the generated tables, and the dynamic equity conclusion was restricted accordingly.
4. **Objective-aligned metrics:** labelled throughout, so the reports and dashboard do not present them as independent evidence.

## Open issues

These three were addressed in Stage 5 as **supplementary, exploratory** experiments, on new seeds and without changing the frozen Stage 4 data ([`stage5-supplementary.md`](stage5-supplementary.md)):

- **Late-zone bias:** the new zone's urgency became an experimental factor (low, moderate, high, random) × initial zone count (3, 5, 8), 120 scripts in both modes. The arrival position stays last, because the engine always appends new reports. Result: the Stage 4 dynamic "equity advantage" of AidOS does not hold. AidOS serves a late zone in proportion to its urgency, and leaves the worst-off original zone *worse* off than FCFS at every level.
- **Runtime:** a dedicated benchmark with warm-ups, 15 interleaved repeats and recorded CPU load.
- **Sensitivity:** a coverage-floor sweep (0–40%) and ten fuzzy-design variants.
