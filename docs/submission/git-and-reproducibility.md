# Git, reproducibility and contribution workflow

## Current state (12 Nov 2026)

- The project folder was **not** under version control until Stage 5. A local repository was initialised with `git init -b main`. There are **no commits** and no remote.
- The course requires a shared Git repository whose history "is used as evidence of individual contribution" and must "show contributions from all members" (guidelines 2 and 4.3). This is the most serious open submission risk: the code so far was produced in AI-assisted sessions without per-student history.
- **Do not fabricate history.** No backdated commits, no commits authored under another member's name, no squashed "contribution" commits that misrepresent who did what.

## What is versioned

| Path | Versioned | Why |
|---|---|---|
| Source: `apps/api/aidos`, `apps/web/src`, `tests/`, `scripts/`, `experiments/*.py` | yes | the system |
| Lockfiles: `apps/api/uv.lock`, `apps/web/package-lock.json` | yes | pinned dependency versions |
| `data/scenarios/`, `data/simulations/` | yes | synthetic inputs |
| `docs/` (including `docs/evaluation/figures/`) | yes | design, results, figures |
| `experiments/results/standard-*`, `extended-*` (Stage 4), `supplementary-*` (Stage 5), `stage2-smoke.*` | **yes**, about 7 MB in total | the reported evidence; each run has `config.json`, `manifest.json` (versions and SHA-256 per file), raw CSV and `summary.json` |
| `experiments/results/smoke-*` | no | throwaway pipeline checks |
| `.venv/`, `node_modules/`, `apps/web/dist/`, caches, `.env` | no | regenerated or secret |
| `.impeccable/` (design-tool state, mockups, review captures) | yes, except `hook.cache.json` | design history; about 2.8 MB |

`.gitattributes` marks `experiments/results/**` as `-text`. Their checksums are byte-exact, so line-ending conversion would break `verify_results.py` on other machines.

CI (`.github/workflows/ci.yml`) runs once the repository is pushed to GitHub: backend lint and tests, artifact verification, frontend typecheck, lint, tests and build.

## Reproducing everything from a fresh clone

```bash
cd apps/api && uv sync --all-groups          # Python 3.11, pinned by uv.lock
uv run pytest && uv run ruff check ../..
cd ../web && npm ci && npm test && npm run build
cd ../api
# Verify the committed Stage 4 evidence (checksums, summaries, pairing, reproducibility)
uv run python ../../experiments/verify_results.py extended-20261112T100136Z --against standard-20261112T100617Z
# Re-run (writes NEW timestamped directories; never overwrites)
uv run python ../../experiments/run_benchmarks.py --preset extended
uv run python ../../experiments/greedy_equivalence.py
uv run --group analysis python ../../experiments/floor_sweep.py
uv run --group analysis python ../../experiments/fuzzy_sensitivity.py
uv run --group analysis python ../../experiments/dynamic_controlled.py
uv run --group analysis python ../../experiments/runtime_benchmark.py
```

Logical results (plans, scores, metrics, outcome hashes) are deterministic. Timings are not.

## Proposed commit plan (for the team to execute under their own accounts)

The team decides who commits what. A suggestion that keeps history truthful:

1. **One initial import commit, by the member who will own repository administration.** Its message should state plainly that it imports the AI-assisted prototype as developed so far, for example: *"Import AidOS prototype (Stages 1–5, developed with AI coding assistance; see docs/contribution-log.md)"*. Do not attribute this code to individuals after the fact.
2. **Push to a shared GitHub or GitLab repository**, and add every member as a collaborator. Record the URL in the report's Appendix A.
3. **From then on, every change goes through a branch and a pull request by the member who makes it**, under their own Git identity (`git config user.name` and `user.email` set per person). Examples of genuine remaining work:
   - the report sections;
   - the screenshots for the report;
   - demo rehearsal fixes;
   - reviewing and extending tests;
   - any new experiment (for example, running the dynamic scenarios with a capacity extension);
   - fuzzy-rule review with the instructor.
4. Keep `docs/contribution-log.md` as a factual, dated log: who did what, with links to commits or PRs.
5. Disclose AI-tool use according to the **subject descriptor's** rules. The guidelines defer to it, and it was not available to this audit. Each member should read it before the report is written.

## Contribution evidence each member will need

- **Reflection (guidelines 6.2):** "what you personally built or wrote, with evidence (e.g. Git commits, specific functions, report sections)". Statements must match the repository; claims contradicted by it fall into the lowest band.
- **Viva (6.1):** each member must explain parts they did not build; use `docs/submission/viva-preparation.md`.

## Stage 6 update (13 Nov 2026): steps for the team

The repository still has **no commits and no remote**. Stage 6 added `docs/report/` (the editable Word report, a PDF preview, the figures and the evidence map) and further files in `docs/submission/`. None of it is committed.

1. **Each member sets their own identity** on their own machine before any commit: `git config user.name "<your name>"` and `git config user.email "<your university email>"`.
2. **Create the shared repository** on GitHub or GitLab (one member), with every member added as a collaborator. Then, from the project root:
   ```bash
   git add -A
   git status            # check: no .env, node_modules, .venv or dist
   git commit -m "Import AidOS prototype (Stages 1-6, developed with AI coding assistance; see docs/contribution-log.md)"
   git remote add origin <shared-repository-URL>
   git push -u origin main
   ```
3. **Paste the repository URL** into the report (cover page and Appendix A) and into `README.md`.
4. **Real work from here goes in on branches, one person per change**, merged by pull request. Examples:
   - completing the placeholders in the report;
   - reviewing and editing the sections each member presents;
   - adding missing screenshots or recordings for the demo fallback;
   - rehearsal fixes;
   - extra tests.
5. **Fill Appendix A** from the repository and `docs/contribution-log.md`, not from memory. Shares and signatures must be agreed by the whole team.
6. **Never** rewrite history to change authorship or dates, and never commit under another member's identity.
