# 0006 — Stage 5: scientific hardening, artifact versioning and git

Date: 12 November 2026. Status: accepted.

## Decisions

1. **The CP-SAT and greedy equivalence is reported, not engineered away.** It is proven, and checked exhaustively, in `docs/algorithms/greedy-vs-cpsat-analysis.md`. No constraint was added to the main benchmark to create a difference. A per-zone vehicle-capacity constraint is documented as a *proposed extension*, with a worked counterexample computed in isolation, because the scenario data has no capacity information.
2. **Supplementary experiments are separate from the frozen benchmark.**
   - They cover the floor sweep, fuzzy sensitivity, controlled dynamic scripts, the runtime benchmark and the equivalence checks.
   - They use new seeds (family indices 1000–1039, 3000–3099, 4000+; dynamic seeds from 1,100,000) and write new `supplementary-*` directories with their own manifests and checksums.
   - The Stage 4 runs `extended-20261112T100136Z` and `standard-20261112T100617Z` are not modified.
3. **No production parameter was changed.** The fuzzy configuration v1.0, the 25% floor default and ε = 1 are unchanged. The floor sweep and the fuzzy variants are exploratory and are not used to pick new defaults.
4. **The dynamic evaluation is corrected by addition, not replacement.** The Stage 4 late-urgent-zone scripts stay in the record, alongside their bias analysis. The Stage 5 controlled scripts vary the new zone's urgency (low, moderate, high, random) and the initial zone count (3, 5, 8).
5. **Evidence is versioned in git.**
   - `experiments/results/` (about 7 MB of CSV and JSON) is tracked, except throwaway `smoke-*` runs.
   - `.gitattributes` marks it `-text`, so the SHA-256 checksums in each manifest stay valid across platforms.
6. **A local git repository was initialised with no commits.** Committing, the remote, and per-member history are left to the team (`docs/submission/git-and-reproducibility.md`). No history is fabricated.
7. **CI is added for GitHub Actions** (lint, tests, artifact verification, frontend build), consistent with specification section 7. It runs only once the team pushes.
