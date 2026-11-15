"""Coverage-floor sensitivity of AidOS balanced (supplementary, Stage 5).

    cd apps/api
    uv run --group analysis python ../../experiments/floor_sweep.py

Pre-declared floor targets: 0, 10, 20, 25, 30, 40 % of each request. Scenarios: indices
1000-1039 of every family A-G (280 scenarios), i.e. NOT the frozen Stage 4 benchmark
(indices 0-71), so nothing is tuned on the reported evaluation set. The default (25 %) is not
re-selected from these results.

What the floor means (constraints.py): for each resource r, CP-SAT maximises one common floor
f_r <= target such that every zone requesting r receives x >= f_r * d (in whole units, i.e.
ceil). When stock cannot give every requesting zone `target`, f_r shrinks to the largest value
the stock allows: the target is relaxed, not guaranteed. This script records how often that
happens.
"""

from __future__ import annotations

import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from aidos.ai.constraints import AidosConfig, allocate_aidos  # noqa: E402
from aidos.evaluation import supplementary as sup  # noqa: E402
from aidos.evaluation.families import STATIC_FAMILIES, generate  # noqa: E402
from aidos.evaluation.invariants import validate_allocation  # noqa: E402
from aidos.evaluation.metrics import compute_metrics  # noqa: E402
from aidos.evaluation.stats import describe, paired  # noqa: E402
from aidos.pipeline import assess_urgency  # noqa: E402

FLOORS = (0.0, 0.10, 0.20, 0.25, 0.30, 0.40)
INDICES = range(1000, 1040)
METRICS = (
    "urgency_weighted_coverage",
    "critical_coverage",
    "min_zone_coverage",
    "starved_share",
    "jain_fairness",
    "coverage_gap",
    "unit_coverage",
    "runtime_ms",
)


def main() -> int:
    started = datetime.now(UTC)
    out = sup.new_run_dir(ROOT / "experiments" / "results", "floor-sweep", started)
    rows = []
    for family in STATIC_FAMILIES:
        for i in INDICES:
            sc = generate(family, i)
            urgency = {u.zone_id: u.result.score for u in assess_urgency(sc)}
            urgency_first = allocate_aidos(sc, urgency)
            for floor in FLOORS:
                t0 = perf_counter()
                res = allocate_aidos(
                    sc, urgency, AidosConfig(min_coverage=floor), objective="balanced"
                )
                ms = (perf_counter() - t0) * 1000
                m = asdict(compute_metrics(sc, res, urgency))
                achieved = res.solver.coverage_floor
                requesting = [
                    r
                    for r in sc.resource_ids()
                    if any(sc.demand_of(z, r) for z in sc.active_zones()) and sc.stock[r] > 0
                ]
                relaxed = [r for r in requesting if achieved.get(r, 0.0) < floor - 1e-9]
                same_as_urgency_first = {
                    (c.zone_id, c.resource_id): c.allocated for c in res.cells
                } == {(c.zone_id, c.resource_id): c.allocated for c in urgency_first.cells}
                rows.append(
                    {
                        "family": family,
                        "scenario_id": sc.scenario_id,
                        "floor_target": floor,
                        "status": res.status.value,
                        "valid": int(validate_allocation(sc, res).valid),
                        "resources_requested": len(requesting),
                        "resources_relaxed": len(relaxed),
                        "min_achieved_floor": min(
                            (achieved.get(r, 0.0) for r in requesting), default=None
                        ),
                        "same_plan_as_urgency_first": int(same_as_urgency_first),
                        "urgency_weighted_coverage": m["urgency_weighted_coverage"],
                        "critical_coverage": m["critical_coverage"],
                        "min_zone_coverage": m["min_zone_coverage"],
                        "starved_share": m["starved_zones"] / m["zones_with_demand"]
                        if m["zones_with_demand"]
                        else None,
                        "jain_fairness": m["jain_fairness"],
                        "coverage_gap": m["coverage_gap"],
                        "unit_coverage": m["unit_coverage"],
                        "runtime_ms": round(ms, 3),
                    }
                )
    sup.write_csv(out / "floor_sweep.csv", rows)

    summary: dict = {"floors": list(FLOORS), "scenarios": len(rows) // len(FLOORS), "per_floor": {}}
    by_floor = {f: [r for r in rows if r["floor_target"] == f] for f in FLOORS}
    base = {r["scenario_id"]: r for r in by_floor[0.0]}
    for f, sel in by_floor.items():
        stats = {k: describe([r[k] for r in sel]).as_dict() for k in METRICS}
        diffs = {
            k: paired(
                {r["scenario_id"]: r[k] for r in sel}, {s: base[s][k] for s in base}, resamples=4000
            ).as_dict()
            for k in (
                "urgency_weighted_coverage",
                "min_zone_coverage",
                "starved_share",
                "jain_fairness",
            )
        }
        summary["per_floor"][str(f)] = {
            "valid": sum(r["valid"] for r in sel),
            "runs": len(sel),
            "statuses": {
                s: sum(1 for r in sel if r["status"] == s) for s in {r["status"] for r in sel}
            },
            "scenarios_with_relaxed_floor": sum(1 for r in sel if r["resources_relaxed"]),
            "resources_relaxed": sum(r["resources_relaxed"] for r in sel),
            "resources_requested": sum(r["resources_requested"] for r in sel),
            "same_plan_as_urgency_first": sum(r["same_plan_as_urgency_first"] for r in sel),
            "metrics": stats,
            "paired_vs_floor_0": diffs,
        }
    sup.write_json(out / "summary.json", summary)
    sup.write_json(
        out / "config.json",
        {
            "floors": list(FLOORS),
            "indices": [INDICES.start, INDICES.stop - 1],
            "families": list(STATIC_FAMILIES),
            "other_settings": "AidosConfig defaults",
        },
    )

    # Figure: priority vs equity as the floor rises (means with 95% bootstrap CI over scenarios)
    rng = np.random.default_rng(1)

    def ci(values):
        arr = np.asarray([v for v in values if v is not None], float)
        boots = arr[rng.integers(0, len(arr), (3000, len(arr)))].mean(axis=1)
        return arr.mean(), np.quantile(boots, 0.025), np.quantile(boots, 0.975)

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
    pct = [int(f * 100) for f in FLOORS]
    for ax, keys in zip(
        axes,
        [
            (
                ("urgency_weighted_coverage", "Urgency-weighted coverage*", "#009E73"),
                ("critical_coverage", "Critical-zone coverage*", "#56B4E9"),
            ),
            (
                ("min_zone_coverage", "Lowest zone coverage", "#CC79A7"),
                ("starved_share", "Share of zones starved", "#E69F00"),
                ("jain_fairness", "Jain index", "#555555"),
            ),
        ],
        strict=True,
    ):
        for key, label, color in keys:
            stats = [ci([r[key] for r in by_floor[f]]) for f in FLOORS]
            ax.errorbar(
                pct,
                [s[0] for s in stats],
                yerr=[[s[0] - s[1] for s in stats], [s[2] - s[0] for s in stats]],
                marker="o",
                capsize=2,
                color=color,
                label=label,
            )
        ax.set_xlabel("Coverage-floor target (% of each request)")
        ax.set_ylim(0, 1.02)
        ax.set_xticks(pct)
        ax.legend(frameon=False, fontsize=7)
    axes[0].set_title("Priority (objective-aligned*)")
    axes[1].set_title("Equity (external)")
    axes[0].set_ylabel("Mean over 280 scenarios (95% CI)")
    fig.suptitle(
        "AidOS balanced: effect of the coverage-floor target (supplementary scenarios)", fontsize=9
    )
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(out / f"fig9_floor_tradeoff.{ext}", dpi=200)
    sup.finalize(
        out,
        name="floor-sweep",
        started=started,
        counts={"runs": len(rows)},
        notes="Pre-declared floors; scenarios outside the frozen benchmark; default not re-selected.",
    )
    print(f"wrote {out}")
    for f in FLOORS:
        p = summary["per_floor"][str(f)]
        m = p["metrics"]
        print(
            f,
            "valid",
            p["valid"],
            "relaxed scen",
            p["scenarios_with_relaxed_floor"],
            "same as UF",
            p["same_plan_as_urgency_first"],
            {
                k: round(m[k]["mean"], 3)
                for k in (
                    "urgency_weighted_coverage",
                    "critical_coverage",
                    "min_zone_coverage",
                    "starved_share",
                    "jain_fairness",
                )
            },
            "runtime med",
            round(m["runtime_ms"]["median"], 1),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
