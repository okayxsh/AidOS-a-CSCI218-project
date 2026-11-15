"""Writes docs/report/report-evidence-map.md from the builder's label export and a source table."""

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
labels = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
pages = sys.argv[3]

RT = "`docs/evaluation/results-tables.md` (generated from `experiments/results/extended-20261112T100136Z/summary.json`)"
S5 = "`docs/evaluation/stage5-supplementary.md`"
SRC = {
    # figures
    "d_arch": "Hand-drawn from `docs/architecture.md`, `apps/api/aidos/main.py`, `api/routes_*.py`, `pipeline.py`, `simulation/store.py`, `evaluation/{campaign,artifacts}.py`, `apps/web/src/app/Router.tsx`, `api/client.ts`",
    "d_fuzzy": "`apps/api/aidos/config/fuzzy_rules.json` (breakpoints, outputs), `ai/fuzzy.py`; the generator checks the values against the config",
    "mf": "Plotted directly from `fuzzy_rules.json` by `docs/report/figures/src/mf_plot.py`",
    "d_cpsat": "`ai/constraints.py`, `ai/baseline_greedy.py`, `ai/policies.py`, `evaluation/invariants.py`, `docs/algorithms/allocation-formulation.md`",
    "d_fsm": "`simulation/fsm.py` (`TRANSITIONS`), `docs/simulation/state-machine.md`",
    "d_events": "`simulation/{events,reducer,session,store}.py`, `main.py` (HTTP codes), `docs/simulation/events.md`, `replay.md`",
    "d_eval": "`evaluation/{families,campaign,dynamic,stats,analysis}.py`; counts from `extended-20261112T100136Z/manifest.json` and `config.json`",
    "s_landing": "Live capture, `/`, engine 0.4.0, 13 Nov 2026",
    "s_overview": "Live capture, `/dashboard?scenario=triage-demo-001`",
    "s_urgency": "Live capture, Allocate page → Run allocation → Fuzzy urgency panel, Zone C",
    "s_alloc": "Live capture, `/dashboard/allocate?scenario=triage-demo-001` → Run allocation (AidOS tab)",
    "s_compare": "Live capture, same page, Baseline comparison",
    "s_sim": "Live capture, Simulate: Zone B severity 9; Zone D added (8/9/9; 40/50/10); 30 medical kits lost",
    "s_simdiff": "Live capture, Simulate: Zone B severity 6 → 9 only",
    "s_eval": "Live capture, `/dashboard/evaluate`, run `extended-20261112T100136Z`",
    "c_fuzzy": "`apps/api/aidos/ai/fuzzy.py`, `evaluate()` (abridged)",
    "c_cpsat": "`apps/api/aidos/ai/constraints.py`, `allocate_aidos()` (abridged)",
    "c_fsm": "`apps/api/aidos/simulation/fsm.py` (`TRANSITIONS`) and `reducer.py` (`PlanCommitted` branch)",
    "r_policy": "`experiments/results/extended-20261112T100136Z/figures/fig1_policy_metrics.png` (byte-identical copy)",
    "r_paired": "`extended-20261112T100136Z/figures/fig2_paired_vs_fcfs.png`",
    "r_zone": "`extended-20261112T100136Z/figures/fig8_zone_coverage.png`",
    "r_floor": "`supplementary-floor-sweep-20261112T165054Z/fig9_floor_tradeoff.png`",
    "r_fuzzy": "`supplementary-fuzzy-sensitivity-20261112T165230Z/fig10_fuzzy_sensitivity.png`",
    "r_dyn": "`supplementary-dynamic-controlled-20261112T165434Z/fig11_dynamic_controlled.png`",
    "r_runtime": "`supplementary-runtime-benchmark-20261112T170741Z/fig12_runtime_benchmark.png`",
    "r_scarcity": "`extended-20261112T100136Z/figures/fig3_scarcity.png`",
    "r_tradeoff": "`extended-20261112T100136Z/figures/fig4_tradeoff.png`",
    "r_runtime4": "`extended-20261112T100136Z/figures/fig5_runtime.png`",
    "r_realloc": "`extended-20261112T100136Z/figures/fig6_dynamic_reallocation.png`",
    "r_dispatch": "`extended-20261112T100136Z/figures/fig7_dispatch.png`",
    # tables
    "rq": "`docs/evaluation/experimental-protocol.md` (questions); report sections",
    "alternatives": "`docs/decisions/0001-*`, `0004-*`; `docs/algorithms/greedy-vs-cpsat-analysis.md`",
    "fr": "Code paths listed in the table; `tests/`",
    "nfr": "`docs/architecture.md`; final verification (13 Nov 2026)",
    "stack": "`apps/api/uv.lock`, `apps/web/package-lock.json`, `.venv` Python version",
    "notation": "`docs/algorithms/allocation-formulation.md` §1",
    "rules": "`apps/api/aidos/config/fuzzy_rules.json`",
    "fuzzyex": "`docs/algorithms/fuzzy-logic.md` §7; re-computed by the engine (contributions 38.8889 + 13.8889 + 13.8889 + 4.1667)",
    "mamdani": "`experiments/fuzzy_method_comparison.py` output, recorded in `docs/algorithms/fuzzy-logic.md` §5",
    "status": "`docs/algorithms/allocation-formulation.md` §9; `ai/constraints.py` `_STATUS`",
    "policies": "`docs/evaluation/policies.md`; `ai/baseline_*.py`",
    "triage": "Re-run on 13 Nov 2026 via `POST /api/allocations/compare` (engine 0.4.0); identical to `allocation-formulation.md` §10",
    "states": "`docs/simulation/state-machine.md`",
    "events": "`docs/simulation/events.md`; `simulation/events.py`, `reducer.py`",
    "xai": "`ai/fuzzy.py` (`explain`), `ai/constraints.py` (`_explain_cells`), `simulation/compare.py`",
    "repo": "Repository tree",
    "api": "`apps/api/aidos/api/routes_*.py`",
    "errors": "`docs/simulation/state-machine.md`; `main.py` error handlers",
    "tests": "Final verification log, 13 Nov 2026 (commands run in this session)",
    "families": "`docs/evaluation/experimental-protocol.md`; `evaluation/families.py`",
    "metrics": "`docs/evaluation/metric-definitions.md`; `evaluation/metrics.py`",
    "feas": RT + " §1",
    "means": RT + " §2",
    "paired": RT + " §3 (AidOS − FCFS and balanced − AidOS rows)",
    "htests": RT + " §4",
    "family": RT + " §5",
    "ident": RT + " §1",
    "equiv": "`docs/algorithms/greedy-vs-cpsat-analysis.md` §3; `supplementary-greedy-equivalence-20261112T164930Z/summary.json`",
    "counter": "`supplementary-greedy-equivalence-20261112T164930Z/summary.json` (`counterexample_proposed_extension`)",
    "floor": S5 + " §2; `supplementary-floor-sweep-20261112T165054Z/summary.json`",
    "fuzzy": S5 + " §3; `supplementary-fuzzy-sensitivity-20261112T165230Z/summary.json`",
    "recevents": RT + " §6",
    "disp": RT + " §7",
    "decomp": RT + " §8",
    "ctrl": S5 + " §4; `supplementary-dynamic-controlled-20261112T165434Z/summary.json`",
    "ctrlpaired": S5 + " §4",
    "runtime": S5 + " §5; `supplementary-runtime-benchmark-20261112T170741Z/summary.json`",
    "demonstrates": "`docs/evaluation/results.md` §5; " + S5 + " (conclusions)",
    "difficulties": "Decision record 0004; `experimental-protocol.md` (deviations); `scientific-review.md`; "
    + S5,
    "objectives": "Report sections 6.4–6.9",
    "contrib": "CSCI218 guidelines, Appendix A template",
    "allrules": "`apps/api/aidos/config/fuzzy_rules.json` (generated at build time)",
    "endpoints": "`apps/api/aidos/api/routes_*.py`, `main.py`",
    "commands": "`README.md`; `docs/submission/git-and-reproducibility.md`",
    "runs": "Manifests in `experiments/results/*/manifest.json`; SHA-256 recomputed at build time",
    "scaling": RT + " §9",
}

figs = [x for x in labels if x["kind"] == "Figure"]
tabs = [x for x in labels if x["kind"] == "Table"]
missing = [
    x["id"]
    for x in figs + tabs
    if x["id"] not in SRC and not (x["kind"] == "Table" and x["id"] == "tests" and "tests_h" in SRC)
]


def src(x):
    if x["kind"] == "Table" and x["id"] == "tests" and "results tables" in x["caption"].lower():
        return SRC["tests_h"]
    if x["kind"] == "Table" and x["id"] == "tests" and "verification" in x["caption"].lower():
        return SRC["tests"]
    return SRC.get(x["id"], "**(no source recorded)**")


lines = [
    "# Report evidence map",
    "",
    f"Traceability for `docs/report/AidOS_Final_Group_Report.docx` ({pages} pages). Every figure, table and headline number is linked to the artifact it comes from.",
    "",
    "- **Generated tables.** Tables marked as coming from `results-tables.md` or `stage5-supplementary.md` are read by the report builder directly from those files, which are themselves generated from the run CSV/JSON. They are never retyped.",
    "- **Checks.** `experiments/audit_stage4.py` independently recomputed the Stage 4 numbers (21/21 checks passed). The builder also recomputed every result checksum (8/8 folders match).",
    "",
    "## Frozen and supplementary runs",
    "",
    "| Run | Role |",
    "|---|---|",
    "| `extended-20261112T100136Z` | Stage 4 main evidence (504 scenarios, 60 scripts, 240 trajectories) |",
    "| `standard-20261112T100617Z` | Stage 4 independent re-run; 560 + 560 shared rows identical |",
    "| `supplementary-greedy-equivalence-20261112T164930Z` | Proof checks (36,240 exhaustive, 700 random), counterexample |",
    "| `supplementary-floor-sweep-20261112T165054Z` | Coverage floor 0–40% (280 scenarios × 6) |",
    "| `supplementary-fuzzy-sensitivity-20261112T165230Z` | Ten fuzzy variants (280 scenarios) |",
    "| `supplementary-dynamic-controlled-20261112T165434Z` | Late-zone urgency controlled (120 scripts) |",
    "| `supplementary-runtime-benchmark-20261112T170741Z` | Runtime benchmark (3–50 zones) |",
    "| `supplementary-stage4-audit-20261112T170734Z` | Independent recomputation of Stage 4 statistics |",
    "",
    "## Headline numbers",
    "",
    "| Claim in the report | Value | Source |",
    "|---|---|---|",
    "| Valid static plans | 2,016 / 2,016 | " + RT + " §1 |",
    "| Valid recommendation-mode plans | 1,680 / 1,680 | `docs/evaluation/results.md` §1 |",
    "| AidOS proven OPTIMAL | 504 / 504 (balanced 504 / 504) | " + RT + " §1 |",
    "| AidOS = greedy plans | 504 / 504 | " + RT + " §1; `audit_stage4.py` |",
    "| Urgency-weighted coverage, AidOS − FCFS | +0.1020 [0.0922, 0.1119], d_z 0.91 | "
    + RT
    + " §3 |",
    "| Critical-zone coverage, AidOS − FCFS | +0.2877 [0.2552, 0.3212], n = 325 | " + RT + " §3 |",
    "| Lowest-zone coverage, AidOS − FCFS | −0.0059 [−0.0158, 0.0039]; Holm p = 0.4180 | "
    + RT
    + " §3–4 |",
    "| Balanced − AidOS: lowest zone / UWC | +0.1801 [0.1714, 0.1886] / −0.0307 [−0.0339, −0.0276] | "
    + RT
    + " §3 |",
    "| Starved zones under balanced | 0.000 (sd 0.000) in all 504 | " + RT + " §2 |",
    "| Exhaustive equivalence | E1 24,576/24,576; E2 11,664/11,664; random 700/700 | `supplementary-greedy-equivalence-*/summary.json` |",
    "| Counterexample objectives | greedy 8,850,000 (10 units); CP-SAT 30,400,000 (20 units) | same file |",
    "| Floor sweep: floor reduced at 25% / 40% | 5 / 1,003 and 136 / 1,003 resource cases | `supplementary-floor-sweep-*/summary.json` |",
    "| Mamdani dips | 1,062 / 52,920 (2.01%, worst 0.8947) | `docs/algorithms/fuzzy-logic.md` §5 |",
    "| Product-Sugeno dips (variants) | 0 / 7,260; min t-norm 132 / 7,260 | " + S5 + " §3 |",
    "| Breakpoint shift: plan changed | 113 (P1) and 103 (P2) of 280 | " + S5 + " §3 |",
    "| Controlled dynamic, high urgency, lowest original-zone fulfilment AidOS − FCFS | −0.048 [−0.077, −0.022] | "
    + S5
    + " §4 |",
    "| Late-zone decomposition (Stage 4 dispatch) | late zone never served: FCFS 60, AidOS 0; original zones never served: FCFS 27, AidOS 53 | "
    + RT
    + " §8 |",
    "| Runtime medians (Stage 5) | AidOS 6.3 ms (3 zones) to 124 ms (50); greedy 0.05 to 0.81 ms; CPU load 1–15% | `supplementary-runtime-benchmark-*/summary.json` |",
    "| Static runtime (Stage 4) | AidOS median 12.06 ms, mean 12.43 (sd 5.85); FCFS 0.114 ms | `extended-*/summary.json` (`runtime_ms`) |",
    "| Tests | 288 backend passed; 81 frontend passed | Final verification, 13 Nov 2026 |",
    "",
    "## Figures",
    "",
    "| Figure | Caption (short) | File | Source |",
    "|---|---|---|---|",
]
for x in figs:
    cap = x["caption"].split(". ")[0][:90]
    lines.append(f"| {x['num']} | {cap} | `{x['path'] or '(code excerpt)'}` | {src(x)} |")
lines += ["", "## Tables", "", "| Table | Caption (short) | Source |", "|---|---|---|"]
for x in tabs:
    cap = x["caption"].split(". ")[0][:90]
    lines.append(f"| {x['num']} | {cap} | {src(x)} |")
lines += [
    "",
    "## References",
    "",
    "The 24 references were each checked on 13 Nov 2026 against Crossref (`api.crossref.org/works/<DOI>`), arXiv, zbMATH Open, the Library of Congress or Open Library, the publisher, or official documentation. The two course documents are cited as supplied.",
    "",
    "Notes from the check:",
    "- the Holm (1979) issue number was left out because it could not be confirmed from a fetched source;",
    "- Russell and Norvig is dated 2021, from the Library of Congress record (the retail release was 2020);",
    "- the OR-Tools citations use version 9.15, the version the project runs; the official citation page shows 9.12 as its example.",
    "",
    "## Known gaps",
    "",
    "- **Team details still to complete:** student names and IDs, lab group, instructor, repository URL and submission date (cover, Appendix A).",
    "- **Pending confirmations:** the instructor's decision on Sugeno versus Mamdani, the topic registration, and the AI-tool policy (Appendix A, Appendix E).",
    "- **Screenshot dependency:** the screenshots show engine version 0.4.0. Recapture them if the UI changes before submission.",
]
if missing:
    lines += ["", "**Builder warning: no source recorded for:** " + ", ".join(missing)]
out = root / "docs/report/report-evidence-map.md"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("wrote", out, "figures", len(figs), "tables", len(tabs), "missing", missing)
