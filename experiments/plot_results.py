"""Report figures from one evaluation run (reads only the run's CSV files).

    cd apps/api
    uv run --group analysis python ../../experiments/plot_results.py <run_id>

Writes PNG (200 dpi) and SVG files to experiments/results/<run_id>/figures/. Colours are the
Okabe-Ito palette (colour-blind safe); fraction axes start at 0; every figure says what its
error bars are.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from aidos.evaluation.stats import paired  # noqa: E402

POLICIES = ["fcfs", "greedy", "aidos", "aidos_balanced"]
LABEL = {
    "fcfs": "FCFS",
    "greedy": "Urgency greedy",
    "aidos": "AidOS",
    "aidos_balanced": "AidOS balanced",
}
COLOR = {"fcfs": "#E69F00", "greedy": "#56B4E9", "aidos": "#009E73", "aidos_balanced": "#CC79A7"}
FAMILY = {
    "A": "A low\nscarcity",
    "B": "B moderate",
    "C": "C severe",
    "D": "D unequal\nurgency",
    "E": "E equal\nurgency",
    "F": "F unequal\ndemand",
    "G": "G mixed\nshortage",
}
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def num(value: str) -> float | None:
    return None if value in ("", None) else float(value)


def save(fig, out: Path, name: str) -> None:
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(out / f"{name}.{ext}", dpi=200)
    plt.close(fig)


def mean_ci(values: list[float], seed: int = 1) -> tuple[float, float, float]:
    arr = np.asarray(values)
    rng = np.random.default_rng(seed)
    boots = arr[rng.integers(0, len(arr), (4000, len(arr)))].mean(axis=1)
    return float(arr.mean()), float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))


def fig_policy_metrics(static, out):
    metrics = [
        ("unit_coverage", "Unit coverage"),
        ("urgency_weighted_coverage", "Urgency-weighted\ncoverage*"),
        ("min_zone_coverage", "Lowest zone\ncoverage"),
        ("jain_fairness", "Jain index of\nzone coverage"),
        ("starved_share", "Share of zones\nstarved (lower is better)"),
    ]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    width = 0.2
    for i, policy in enumerate(POLICIES):
        means, lows, highs = [], [], []
        for key, _ in metrics:
            values = [
                num(r[key]) for r in static if r["policy"] == policy and num(r[key]) is not None
            ]
            m, lo, hi = mean_ci(values)
            means.append(m)
            lows.append(m - lo)
            highs.append(hi - m)
        x = np.arange(len(metrics)) + (i - 1.5) * width
        ax.bar(
            x, means, width, yerr=[lows, highs], capsize=2, color=COLOR[policy], label=LABEL[policy]
        )
        for xi, mi in zip(x, means, strict=True):
            if mi == 0:  # a zero-height bar is invisible; label it
                ax.text(xi, 0.01, "0", ha="center", va="bottom", fontsize=7, color=COLOR[policy])
    ax.set_xticks(np.arange(len(metrics)), [m[1] for m in metrics])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Mean over scenarios (0-1)")
    n = len({r["scenario_id"] for r in static})
    ax.set_title(
        f"Static benchmark: {n} scenarios, families A-G\nerror bars: 95% bootstrap CI of the mean"
    )
    ax.legend(ncol=4, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.18))
    fig.text(0.01, 0.01, "* AidOS maximises this metric by design (objective-aligned).", fontsize=7)
    save(fig, out, "fig1_policy_metrics")


def fig_paired_vs_fcfs(static, out):
    metrics = [
        ("urgency_weighted_coverage", "Urgency-weighted coverage*"),
        ("critical_coverage", "Critical-zone coverage*"),
        ("min_zone_coverage", "Lowest zone coverage"),
        ("starved_share", "Share of zones starved"),
        ("coverage_gap", "Coverage gap (max - min)"),
        ("jain_fairness", "Jain index"),
        ("unit_coverage", "Unit coverage"),
    ]
    by = defaultdict(dict)
    for r in static:
        by[r["policy"]][r["scenario_id"]] = r
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    for j, policy in enumerate(["greedy", "aidos", "aidos_balanced"]):
        for i, (key, _) in enumerate(metrics):
            a = {k: num(v[key]) for k, v in by[policy].items()}
            b = {k: num(v[key]) for k, v in by["fcfs"].items()}
            res = paired(a, b, resamples=4000)
            y = i + (j - 1) * 0.25
            lo, hi = res.ci_mean
            ax.errorbar(
                res.mean_diff,
                y,
                xerr=[[res.mean_diff - lo], [hi - res.mean_diff]],
                fmt="o",
                color=COLOR[policy],
                capsize=2,
                label=LABEL[policy] if i == 0 else None,
            )
    ax.axvline(0, color="#555", linewidth=0.8)
    ax.set_yticks(range(len(metrics)), [m[1] for m in metrics])
    ax.invert_yaxis()
    ax.set_xlabel("Paired mean difference vs FCFS (same scenarios), with 95% bootstrap CI")
    ax.set_title(
        "Each policy minus FCFS, paired on the same scenarios\ncoverage and Jain: right is better; starved share and gap: left is better"
    )
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig.text(
        0.01,
        0.01,
        "* objective-aligned (defined by the same fuzzy scores AidOS optimises).",
        fontsize=7,
    )
    save(fig, out, "fig2_paired_vs_fcfs")


def fig_scarcity(static, out):
    fams = ["A", "B", "C"]
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.2), sharex=True)
    for ax, (key, title) in zip(
        axes,
        [
            ("urgency_weighted_coverage", "Urgency-weighted coverage*"),
            ("min_zone_coverage", "Lowest zone coverage"),
        ],
        strict=True,
    ):
        for policy in POLICIES:
            stats = [
                mean_ci([num(r[key]) for r in static if r["family"] == f and r["policy"] == policy])
                for f in fams
            ]
            means = [s[0] for s in stats]
            err = [[s[0] - s[1] for s in stats], [s[2] - s[0] for s in stats]]
            ax.errorbar(
                range(3),
                means,
                yerr=err,
                marker="o",
                capsize=2,
                color=COLOR[policy],
                label=LABEL[policy],
            )
        ax.set_xticks(range(3), ["A: 85-110%", "B: 60-85%", "C: 25-50%"])
        ax.set_xlabel("Stock as a share of requests")
        ax.set_ylim(0, 1.05)
        ax.set_title(title)
    axes[0].set_ylabel("Mean (95% bootstrap CI)")
    axes[1].legend(frameon=False, fontsize=7)
    save(fig, out, "fig3_scarcity")


def fig_tradeoff(static, out):
    fig, ax = plt.subplots(figsize=(5.5, 4))
    for policy in POLICIES:
        for f in sorted(FAMILY):
            sel = [r for r in static if r["family"] == f and r["policy"] == policy]
            x = np.mean([num(r["urgency_weighted_coverage"]) for r in sel])
            y = np.mean([num(r["min_zone_coverage"]) for r in sel])
            ax.scatter(x, y, color=COLOR[policy], s=24, label=LABEL[policy] if f == "A" else None)
            ax.annotate(
                f, (x, y), textcoords="offset points", xytext=(3, 2), fontsize=6, color="#444"
            )
    ax.set_xlabel("Urgency-weighted coverage* (family mean)")
    ax.set_ylabel("Lowest zone coverage (family mean)")
    ax.set_xlim(0, 1.02)
    ax.set_ylim(0, 1.02)
    ax.set_title(
        "Urgency priority vs the worst-served zone\nfamily means; letters = scenario family"
    )
    fig.text(
        0.01, 0.01, "Urgency greedy is hidden under AidOS: their plans are identical.", fontsize=7
    )
    ax.legend(frameon=False, fontsize=7)
    save(fig, out, "fig4_tradeoff")


def fig_runtime(scaling, out):
    fig, ax = plt.subplots(figsize=(5.5, 3.4))
    for policy in POLICIES:
        sizes = sorted({int(r["zones"]) for r in scaling})
        med, p25, p75 = [], [], []
        for n in sizes:
            v = [
                float(r["runtime_ms"])
                for r in scaling
                if r["policy"] == policy and int(r["zones"]) == n
            ]
            med.append(np.median(v))
            p25.append(np.percentile(v, 25))
            p75.append(np.percentile(v, 75))
        ax.plot(sizes, med, marker="o", color=COLOR[policy], label=LABEL[policy])
        ax.fill_between(sizes, p25, p75, color=COLOR[policy], alpha=0.15)
    ax.set_yscale("log")
    ax.set_xlabel("Active zones (4 resources)")
    ax.set_ylabel("Policy runtime, ms (log scale)")
    ax.set_title(
        "Runtime vs problem size\nmedian; band: 25th-75th percentile; one laptop, normal desktop load"
    )
    ax.legend(frameon=False, fontsize=7)
    save(fig, out, "fig5_runtime")


def fig_dynamic(rec, out):
    events = [
        "urgency_changed",
        "zone_added",
        "supply_lost",
        "supply_arrived",
        "request_updated",
        "time_advanced",
        "zone_resolved",
    ]
    fig, ax = plt.subplots(figsize=(8, 3.3))
    width = 0.2
    for i, policy in enumerate(POLICIES):
        means = []
        for e in events:
            v = [
                float(r["reallocated_units"])
                for r in rec
                if r["event_type"] == e and r["policy"] == policy
            ]
            means.append(np.mean(v) if v else 0)
        ax.bar(
            np.arange(len(events)) + (i - 1.5) * width,
            means,
            width,
            color=COLOR[policy],
            label=LABEL[policy],
        )
    ax.set_xticks(range(len(events)), [e.replace("_", "\n") for e in events])
    ax.set_ylabel("Units reallocated vs previous step\n(mean over scripts)")
    scripts = len({r["script_id"] for r in rec})
    ax.set_title(
        f"Recommendation mode (shared state, {scripts} scripts)\nunits each event moves in each policy's plan"
    )
    ax.legend(ncol=4, frameon=False, fontsize=7)
    fig.text(0.01, 0.01, "More reallocation is not better or worse in itself.", fontsize=7)
    save(fig, out, "fig6_dynamic_reallocation")


def fig_dispatch(dispatch, out):
    metrics = [
        ("fulfilment", "Fulfilment"),
        ("urgency_weighted_fulfilment", "Urgency-weighted\nfulfilment*"),
        ("min_zone_fulfilment", "Lowest zone\nfulfilment"),
    ]
    fig, ax = plt.subplots(figsize=(6.5, 3.3))
    width = 0.2
    for i, policy in enumerate(POLICIES):
        stats = [
            mean_ci([float(r[k]) for r in dispatch if r["policy"] == policy and r[k] != ""])
            for k, _ in metrics
        ]
        means = [s[0] for s in stats]
        err = [[s[0] - s[1] for s in stats], [s[2] - s[0] for s in stats]]
        ax.bar(
            np.arange(len(metrics)) + (i - 1.5) * width,
            means,
            width,
            yerr=err,
            capsize=2,
            color=COLOR[policy],
            label=LABEL[policy],
        )
    ax.set_xticks(range(len(metrics)), [m[1] for m in metrics])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Mean over scripts (95% bootstrap CI)")
    ax.set_title(
        "Dispatch mode: each policy's own trajectory\n4 dispatch rounds; the same script for every policy"
    )
    ax.legend(ncol=4, frameon=False, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.15))
    save(fig, out, "fig7_dispatch")


def fig_zone_coverage(zones, out, family="B"):
    fig, axes = plt.subplots(1, 3, figsize=(9, 3), sharey=True)
    for ax, policy in zip(axes, ["fcfs", "aidos", "aidos_balanced"], strict=True):
        sel = [
            r
            for r in zones
            if r["family"] == family and r["policy"] == policy and r["coverage"] != ""
        ]
        ax.scatter(
            [float(r["urgency"]) for r in sel],
            [float(r["coverage"]) for r in sel],
            s=8,
            alpha=0.5,
            color=COLOR[policy],
        )
        ax.set_title(LABEL[policy])
        ax.set_xlabel("Zone urgency (fuzzy score)")
        ax.set_xlim(0, 100)
        ax.set_ylim(-0.02, 1.02)
    axes[0].set_ylabel("Zone coverage")
    fig.suptitle(
        f"Per-zone coverage vs urgency, family {family}: each dot is one zone in one scenario",
        fontsize=9,
    )
    save(fig, out, "fig8_zone_coverage")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("run_id")
    parser.add_argument("--results", type=Path, default=ROOT / "experiments" / "results")
    args = parser.parse_args()
    run = args.results / args.run_id
    out = run / "figures"
    out.mkdir(exist_ok=True)
    static = rows(run / "static_records.csv")
    fig_policy_metrics(static, out)
    fig_paired_vs_fcfs(static, out)
    fig_scarcity(static, out)
    fig_tradeoff(static, out)
    fig_runtime(rows(run / "scaling.csv"), out)
    fig_dynamic(rows(run / "dynamic_recommendation.csv"), out)
    fig_dispatch(rows(run / "dynamic_dispatch.csv"), out)
    fig_zone_coverage(rows(run / "static_zones.csv"), out)
    print(f"figures written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
