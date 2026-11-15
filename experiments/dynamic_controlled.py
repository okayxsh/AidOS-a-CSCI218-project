"""Controlled dynamic experiments (supplementary, Stage 5): new-zone urgency as a factor.

    cd apps/api
    uv run --group analysis python ../../experiments/dynamic_controlled.py

Design: new-zone urgency level {low, moderate, high, random} x initial zones {3, 5, 8} x 10
seeds = 120 scripts, each run in recommendation mode (shared state) and in dispatch mode (each
policy's own trajectory). Comparisons are paired by script, with bootstrap CIs (exploratory; no
hypothesis tests). See aidos/evaluation/dynamic_controlled.py for the generator.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from aidos.evaluation import dynamic_controlled as dc  # noqa: E402
from aidos.evaluation import supplementary as sup  # noqa: E402
from aidos.evaluation.stats import describe, paired  # noqa: E402
from aidos.pipeline import POLICY_ORDER  # noqa: E402

SEEDS = range(10)
NAME = {
    "fcfs": "FCFS",
    "greedy": "Urgency greedy",
    "aidos": "AidOS",
    "aidos_balanced": "AidOS balanced",
}
COLOR = {"fcfs": "#E69F00", "greedy": "#56B4E9", "aidos": "#009E73", "aidos_balanced": "#CC79A7"}


def script_means(rows, metric, where=lambda r: True):
    acc = defaultdict(list)
    for r in rows:
        if where(r) and r[metric] is not None:
            acc[(r["policy"], r["script_id"])].append(r[metric])
    out = defaultdict(dict)
    for (policy, script), values in acc.items():
        out[policy][script] = sum(values) / len(values)
    return out


def main() -> int:
    started = datetime.now(UTC)
    out = sup.new_run_dir(ROOT / "experiments" / "results", "dynamic-controlled", started)
    rec, dsp = [], []
    for level in dc.LEVELS:
        for zones in dc.ZONE_COUNTS:
            for i in SEEDS:
                rec += dc.recommendation(level, zones, i)
                for policy in POLICY_ORDER:
                    dsp.append(dc.dispatch(level, zones, i, policy))
    sup.write_csv(out / "recommendation.csv", rec)
    sup.write_csv(out / "dispatch.csv", dsp)

    # Integrity: every policy saw the same exogenous script; accounting holds.
    hashes = defaultdict(set)
    for r in dsp:
        hashes[r["script_id"]].add(r["exogenous_script_hash"])
    integrity = {
        "identical_exogenous_scripts": all(len(h) == 1 for h in hashes.values()),
        "inventory_conserved": sum(r["inventory_conserved"] for r in dsp),
        "dispatch_runs": len(dsp),
        "double_dispatch_blocked": sum(r["double_dispatch_blocked"] for r in dsp),
        "rejected_events": sum(r["rejected_events"] for r in dsp),
        "recommendation_valid_rows": sum(r["valid"] for r in rec),
        "recommendation_rows": len(rec),
    }

    summary: dict = {"integrity": integrity, "scripts": len(hashes), "by_level": {}}
    for level in dc.LEVELS:
        lr = [r for r in rec if r["level"] == level]
        ld = [r for r in dsp if r["level"] == level]
        new_cov = script_means(lr, "new_zone_coverage")
        orig_min = script_means(lr, "original_min_coverage")
        orig_starved = script_means(lr, "original_starved")
        responsive = script_means(
            lr, "plan_changed", lambda r: r["event_type"] == "urgency_changed"
        )
        block = {"recommendation": {}, "dispatch": {}, "paired": {}}
        for p in (p.value for p in POLICY_ORDER):
            block["recommendation"][p] = {
                "new_zone_coverage": describe(list(new_cov[p].values())).as_dict(),
                "original_min_coverage": describe(list(orig_min[p].values())).as_dict(),
                "original_starved_per_step": describe(list(orig_starved[p].values())).as_dict(),
                "replans_after_escalation": describe(list(responsive[p].values())).as_dict(),
            }
            sel = [r for r in ld if r["policy"] == p]
            block["dispatch"][p] = {
                k: describe([r[k] for r in sel]).as_dict()
                for k in (
                    "new_zone_fulfilment",
                    "new_zone_never_served",
                    "original_min_fulfilment",
                    "original_mean_fulfilment",
                    "original_never_served",
                    "dispatched_units",
                )
            }
        for a, b in (("aidos", "fcfs"), ("aidos_balanced", "aidos"), ("aidos_balanced", "fcfs")):
            dsel = {p: {r["script_id"]: r for r in ld if r["policy"] == p} for p in (a, b)}
            block["paired"][f"{a}-{b}"] = {
                "rec_new_zone_coverage": paired(new_cov[a], new_cov[b], resamples=4000).as_dict(),
                "rec_original_min_coverage": paired(
                    orig_min[a], orig_min[b], resamples=4000
                ).as_dict(),
                "dsp_new_zone_fulfilment": paired(
                    {k: v["new_zone_fulfilment"] for k, v in dsel[a].items()},
                    {k: v["new_zone_fulfilment"] for k, v in dsel[b].items()},
                    resamples=4000,
                ).as_dict(),
                "dsp_original_min_fulfilment": paired(
                    {k: v["original_min_fulfilment"] for k, v in dsel[a].items()},
                    {k: v["original_min_fulfilment"] for k, v in dsel[b].items()},
                    resamples=4000,
                ).as_dict(),
                "dsp_original_never_served": paired(
                    {k: v["original_never_served"] for k, v in dsel[a].items()},
                    {k: v["original_never_served"] for k, v in dsel[b].items()},
                    resamples=4000,
                ).as_dict(),
            }
        summary["by_level"][level] = block
    sup.write_json(out / "summary.json", summary)
    sup.write_json(
        out / "config.json",
        {
            "levels": dc.LEVELS,
            "initial_zones": dc.ZONE_COUNTS,
            "seeds_per_cell": len(SEEDS),
            "seed_base": dc.SEED_BASE,
        },
    )

    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4), sharey=True)
    levels = list(dc.LEVELS)
    panels = [
        ("recommendation", "new_zone_coverage", "New zone coverage\n(recommendation mode)"),
        ("dispatch", "new_zone_fulfilment", "New zone fulfilment\n(dispatch mode)"),
        ("dispatch", "original_min_fulfilment", "Lowest original-zone fulfilment\n(dispatch mode)"),
    ]
    for ax, (mode, key, title) in zip(axes, panels, strict=True):
        for j, p in enumerate(p.value for p in POLICY_ORDER):
            means = [summary["by_level"][lv][mode][p][key]["mean"] or 0 for lv in levels]
            ax.bar(
                [i + (j - 1.5) * 0.2 for i in range(len(levels))],
                means,
                0.2,
                color=COLOR[p],
                label=NAME[p],
            )
        ax.set_xticks(range(len(levels)), [f"{lv}\nurgency" for lv in levels])
        ax.set_title(title, fontsize=9)
        ax.set_ylim(0, 1.05)
    axes[0].set_ylabel("Mean over 30 scripts per level")
    axes[0].legend(frameon=False, fontsize=7)
    fig.suptitle(
        "Controlled dynamic experiments: the late zone's urgency is varied (120 scripts)",
        fontsize=9,
    )
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(out / f"fig11_dynamic_controlled.{ext}", dpi=200)
    sup.finalize(
        out,
        name="dynamic-controlled",
        started=started,
        counts={"scripts": len(hashes), "recommendation_rows": len(rec), "dispatch_runs": len(dsp)},
        notes="Exploratory; corrects the Stage 4 late-urgent-zone design; Stage 4 data untouched.",
    )
    print(f"wrote {out}")
    print(integrity)
    for lv in levels:
        b = summary["by_level"][lv]
        print(
            lv,
            "rec new-zone cov",
            {
                p: round(b["recommendation"][p]["new_zone_coverage"]["mean"], 3)
                for p in b["recommendation"]
            },
            "| dsp new",
            {p: round(b["dispatch"][p]["new_zone_fulfilment"]["mean"], 3) for p in b["dispatch"]},
            "| dsp orig min",
            {
                p: round(b["dispatch"][p]["original_min_fulfilment"]["mean"], 3)
                for p in b["dispatch"]
            },
            "| orig never",
            {p: round(b["dispatch"][p]["original_never_served"]["mean"], 2) for p in b["dispatch"]},
            "| replan esc",
            {
                p: round(b["recommendation"][p]["replans_after_escalation"]["mean"], 2)
                for p in b["recommendation"]
            },
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
