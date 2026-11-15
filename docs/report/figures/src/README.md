# Report figure sources

Generators for the figures in `docs/report/figures/`. These are report tools only; the engine does not use them.

- `d1_arch.py` … `d6_eval.py` (with `lib.py`): hand-authored SVG diagrams, rendered to 2x PNG with headless Microsoft Edge. Several scripts check their numbers against the repository (the fuzzy configuration and run manifests) and stop if they disagree.
- `mf_plot.py`: the membership-function chart, drawn from `apps/api/aidos/config/fuzzy_rules.json`. Run from `apps/api/`: `uv run --group analysis python ../../docs/report/figures/src/mf_plot.py ../.. ../../docs/report/figures/diagrams/mf_membership.png`.
- `crop_report_shots.py`: crops the report screenshots (`screenshots/report/sc1`–`sc6`) from 2x full-page dashboard captures; the docstring lists the capture settings and steps. It needs Pillow, which comes with matplotlib. The uncropped `screenshots/s01`–`s09` files are kept for the demo runbook.

The experiment figures in `results/` are byte-identical copies of the run figures in `experiments/results/`, produced by `experiments/plot_results.py` and the Stage 5 scripts.
