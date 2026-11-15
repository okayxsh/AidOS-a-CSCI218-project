"""Sensitivity of urgency scores and AidOS plans to the fuzzy design (supplementary, Stage 5).

    cd apps/api
    uv run --group analysis python ../../experiments/fuzzy_sensitivity.py

The production configuration (aidos/config/fuzzy_rules.json) is NOT modified: every variant
below is built in memory from a copy. Variants were declared before running:

  P1 shift-down     input breakpoints 2/5/8 -> 1/4/7
  P2 shift-up       input breakpoints 2/5/8 -> 3/6/9
  P3 narrow-medium  medium set 3-5-7 (low ends at 5, high starts at 5)
  P4 wide-medium    medium set 1-5-9
  P5 outputs-spread rule outputs 0 / 33.3 / 66.7 / 100 (instead of 12.5 / 37.5 / 62.5 / 87.5)
  P6 outputs-narrow rule outputs 20 / 40 / 60 / 80
  P7 no-vulnerability     high vulnerability no longer raises the urgency level
  P8 vulnerability-medium medium vulnerability also raises the level by one
  P9 lenient-rules  severity+time level sum 1 maps to "moderate" instead of "low"
  P10 min-tnorm     rule strength = min of degrees instead of product (Sugeno-min)

Scenarios: indices 1000-1039 of families A-G (280; outside the frozen Stage 4 benchmark).
For each variant and scenario: score change, Kendall tau-b of zone scores against the
production scores, whether the urgency order changes, whether the AidOS plan changes and by
how much, urgency-weighted coverage measured with the PRODUCTION scores (a fixed yardstick),
and the external equity metrics. Plus a monotonicity sweep of each variant.
"""

from __future__ import annotations

import copy
import itertools
import json
import math
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from aidos.ai.baseline_greedy import urgency_rank  # noqa: E402
from aidos.ai.constraints import allocate_aidos  # noqa: E402
from aidos.ai.fuzzy import CONFIG_PATH, INPUT_TERMS, INPUTS, OUTPUT_TERMS, parse_config  # noqa: E402
from aidos.evaluation import supplementary as sup  # noqa: E402
from aidos.evaluation.families import STATIC_FAMILIES, generate  # noqa: E402
from aidos.evaluation.metrics import compute_metrics  # noqa: E402
from aidos.evaluation.stats import describe  # noqa: E402

RAW = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
LEVEL = {"low": 0, "medium": 1, "high": 2}
SUM_TO_TERM = {0: "low", 1: "low", 2: "moderate", 3: "high", 4: "critical"}


def rules(sum_map=SUM_TO_TERM, vul_raise=("high",)):
    out = []
    for i, (s, t, v) in enumerate(itertools.product(INPUT_TERMS, repeat=3)):
        level = OUTPUT_TERMS.index(sum_map[LEVEL[s] + LEVEL[t]])
        if v in vul_raise:
            level = min(level + 1, 3)
        out.append(
            {
                "id": f"R{i + 1:02d}",
                "if": {"severity": s, "time_criticality": t, "vulnerability": v},
                "then": OUTPUT_TERMS[level],
            }
        )
    return out


def with_sets(raw, low, med, high):
    raw = copy.deepcopy(raw)
    for name in INPUTS:
        raw["inputs"][name]["terms"] = {
            "low": {"shape": "trapezoid", "points": low},
            "medium": {"shape": "triangle", "points": med},
            "high": {"shape": "trapezoid", "points": high},
        }
    return raw


def with_outputs(raw, values):
    raw = copy.deepcopy(raw)
    for term, value in zip(OUTPUT_TERMS, values, strict=True):
        raw["output"]["terms"][term]["value"] = value
    return raw


def with_rules(raw, rule_list):
    raw = copy.deepcopy(raw)
    raw["rules"] = rule_list
    return raw


VARIANTS = {
    "P0 production": (RAW, "product"),
    "P1 shift-down": (with_sets(RAW, [0, 0, 1, 4], [1, 4, 7], [4, 7, 10, 10]), "product"),
    "P2 shift-up": (with_sets(RAW, [0, 0, 3, 6], [3, 6, 9], [6, 9, 10, 10]), "product"),
    "P3 narrow-medium": (with_sets(RAW, [0, 0, 3, 5], [3, 5, 7], [5, 7, 10, 10]), "product"),
    "P4 wide-medium": (with_sets(RAW, [0, 0, 1, 5], [1, 5, 9], [5, 9, 10, 10]), "product"),
    "P5 outputs-spread": (with_outputs(RAW, [0, 33.3333, 66.6667, 100]), "product"),
    "P6 outputs-narrow": (with_outputs(RAW, [20, 40, 60, 80]), "product"),
    "P7 no-vulnerability": (with_rules(RAW, rules(vul_raise=())), "product"),
    "P8 vulnerability-medium": (with_rules(RAW, rules(vul_raise=("medium", "high"))), "product"),
    "P9 lenient-rules": (with_rules(RAW, rules(sum_map={**SUM_TO_TERM, 1: "moderate"})), "product"),
    "P10 min-tnorm": (RAW, "min"),
}


def score(ratings, cfg, tnorm):
    mu = {n: {t: cfg.input_terms[n][t].degree(ratings[n]) for t in INPUT_TERMS} for n in INPUTS}
    num = den = 0.0
    for rule in cfg.rules:
        degrees = [mu[n][t] for n, t in rule.antecedent]
        w = math.prod(degrees) if tnorm == "product" else min(degrees)
        num += w * cfg.output_terms[rule.consequent].value
        den += w
    return round(num / den, 4)


def kendall_tau_b(a, b):
    pairs = list(itertools.combinations(range(len(a)), 2))
    conc = disc = ties_a = ties_b = 0
    for i, j in pairs:
        da, db = a[i] - a[j], b[i] - b[j]
        if da == 0 and db == 0:
            continue
        if da == 0:
            ties_a += 1
        elif db == 0:
            ties_b += 1
        elif (da > 0) == (db > 0):
            conc += 1
        else:
            disc += 1
    denom = math.sqrt((conc + disc + ties_a) * (conc + disc + ties_b))
    return (conc - disc) / denom if denom else None


def monotonicity_dips(cfg, tnorm):
    vals = [i / 2 for i in range(21)]
    dips = steps = 0
    for name in INPUTS:
        others = [n for n in INPUTS if n != name]
        for a, b in itertools.product(vals[::2], vals[::2]):
            prev = None
            for v in vals:
                s = score({name: v, others[0]: a, others[1]: b}, cfg, tnorm)
                if prev is not None:
                    steps += 1
                    dips += s < prev - 1e-9
                prev = s
    return dips, steps


def main() -> int:
    started = datetime.now(UTC)
    out = sup.new_run_dir(ROOT / "experiments" / "results", "fuzzy-sensitivity", started)
    configs = {k: (parse_config(raw), tnorm) for k, (raw, tnorm) in VARIANTS.items()}
    production = configs["P0 production"][0]
    assert [r.consequent for r in parse_config(with_rules(RAW, rules())).rules] == [
        r.consequent for r in production.rules
    ], "the rule generator must reproduce the production table"

    rows = []
    for family in STATIC_FAMILIES:
        for i in range(1000, 1040):
            sc = generate(family, i)
            ratings = {
                z.id: {
                    "severity": z.severity,
                    "time_criticality": z.time_criticality,
                    "vulnerability": z.vulnerability,
                }
                for z in sc.zones
            }
            base_scores = {z: score(r, production, "product") for z, r in ratings.items()}
            base_plan = allocate_aidos(sc, base_scores)
            base_cells = {(c.zone_id, c.resource_id): c.allocated for c in base_plan.cells}
            base_order = urgency_rank(sc, base_scores)
            zone_ids = sorted(ratings)
            for name, (cfg, tnorm) in configs.items():
                scores = {z: score(r, cfg, tnorm) for z, r in ratings.items()}
                result = allocate_aidos(sc, scores)
                cells = {(c.zone_id, c.resource_id): c.allocated for c in result.cells}
                moved = sum(abs(cells[k] - base_cells[k]) for k in cells)
                allocated = sum(cells.values())
                m_fixed = asdict(compute_metrics(sc, result, base_scores))
                rows.append(
                    {
                        "variant": name,
                        "family": family,
                        "scenario_id": sc.scenario_id,
                        "mean_abs_score_change": sum(
                            abs(scores[z] - base_scores[z]) for z in zone_ids
                        )
                        / len(zone_ids),
                        "kendall_tau_b": kendall_tau_b(
                            [base_scores[z] for z in zone_ids], [scores[z] for z in zone_ids]
                        ),
                        "order_changed": int(urgency_rank(sc, scores) != base_order),
                        "plan_changed": int(moved > 0),
                        "moved_share": moved / (2 * allocated) if allocated else None,
                        "uwc_production_scores": m_fixed["urgency_weighted_coverage"],
                        "min_zone_coverage": m_fixed["min_zone_coverage"],
                        "starved_share": m_fixed["starved_zones"] / m_fixed["zones_with_demand"]
                        if m_fixed["zones_with_demand"]
                        else None,
                        "jain_fairness": m_fixed["jain_fairness"],
                        "status": result.status.value,
                    }
                )
    sup.write_csv(out / "fuzzy_sensitivity.csv", rows)

    summary = {"variants": {}, "scenarios": len(rows) // len(configs)}
    for name, (cfg, tnorm) in configs.items():
        sel = [r for r in rows if r["variant"] == name]
        dips, steps = monotonicity_dips(cfg, tnorm)
        summary["variants"][name] = {
            "tnorm": tnorm,
            "monotonicity_dips": dips,
            "monotonicity_steps": steps,
            "order_changed_scenarios": sum(r["order_changed"] for r in sel),
            "plan_changed_scenarios": sum(r["plan_changed"] for r in sel),
            "statuses": {
                s: sum(1 for r in sel if r["status"] == s) for s in {r["status"] for r in sel}
            },
            **{
                k: describe([r[k] for r in sel]).as_dict()
                for k in (
                    "mean_abs_score_change",
                    "kendall_tau_b",
                    "moved_share",
                    "uwc_production_scores",
                    "min_zone_coverage",
                    "starved_share",
                    "jain_fairness",
                )
            },
        }
    sup.write_json(out / "summary.json", summary)
    sup.write_json(
        out / "config.json",
        {
            "variants": {
                k: {
                    "tnorm": t,
                    "inputs": raw["inputs"]["severity"]["terms"],
                    "outputs": {
                        term: raw["output"]["terms"][term]["value"] for term in OUTPUT_TERMS
                    },
                    "rules": {r["id"]: r["then"] for r in raw["rules"]},
                }
                for k, (raw, t) in VARIANTS.items()
            },
            "indices": [1000, 1039],
            "families": list(STATIC_FAMILIES),
        },
    )

    names = list(configs)
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), sharey=True)
    v = summary["variants"]
    axes[0].barh(
        names,
        [v[n]["order_changed_scenarios"] / summary["scenarios"] for n in names],
        color="#56B4E9",
    )
    axes[0].set_title("Urgency order changed\n(share of scenarios)")
    axes[1].barh(
        names,
        [v[n]["plan_changed_scenarios"] / summary["scenarios"] for n in names],
        color="#009E73",
    )
    axes[1].set_title("AidOS plan changed\n(share of scenarios)")
    axes[2].barh(names, [v[n]["moved_share"]["mean"] for n in names], color="#E69F00")
    axes[2].set_title("Share of allocated units that move\n(mean over scenarios)")
    for ax in axes:
        ax.set_xlim(0, 1)
    axes[0].invert_yaxis()
    fig.suptitle(
        "Fuzzy design sensitivity (280 supplementary scenarios; production config unchanged)",
        fontsize=9,
    )
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(out / f"fig10_fuzzy_sensitivity.{ext}", dpi=200)
    sup.finalize(
        out,
        name="fuzzy-sensitivity",
        started=started,
        counts={"rows": len(rows)},
        notes="Exploratory; variants declared in advance; production rules untouched.",
    )
    print(f"wrote {out}")
    for n in names:
        x = v[n]
        print(
            f"{n:24} dips {x['monotonicity_dips']:4}/{x['monotonicity_steps']} order {x['order_changed_scenarios']:3} "
            f"plan {x['plan_changed_scenarios']:3} tau {x['kendall_tau_b']['mean']:.3f} "
            f"moved {x['moved_share']['mean']:.3f} uwc {x['uwc_production_scores']['mean']:.3f} "
            f"minzone {x['min_zone_coverage']['mean']:.3f} starved {x['starved_share']['mean']:.3f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
