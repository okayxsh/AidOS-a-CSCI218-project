"""Dedicated runtime benchmark (supplementary, Stage 5). Does not replace the Stage 4 timings.

    cd apps/api
    uv run --group analysis python ../../experiments/runtime_benchmark.py

Protocol: sizes 3, 5, 10, 20, 30, 40, 50 zones (50 is the engine's validation limit), 4
resources, moderate scarcity, 5 scenarios per size (generate_sized seeds 100-104, not the Stage
4 scaling seeds). Per scenario: urgency is computed once; each policy gets 3 untimed warm-up
runs, then 15 timed repeats, interleaved round-robin across policies so drift affects all of
them alike. Recorded per repeat:
  policy_ms      the allocation call only (as in Stage 4)
  end_to_end_ms  allocation + independent validation + metrics (pipeline.run_policy)
  solver_ms      CP-SAT's own reported wall time, summed over phases (AidOS policies)
CPU load (Windows Win32_Processor.LoadPercentage) is sampled before and after each size. If it
is not near idle, the numbers are reported as measured on a loaded machine.
"""

from __future__ import annotations

import statistics
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from aidos.ai.constraints import AidosConfig  # noqa: E402
from aidos.evaluation import supplementary as sup  # noqa: E402
from aidos.evaluation.families import generate_sized  # noqa: E402
from aidos.pipeline import POLICY_ORDER, assess_urgency, run_policy  # noqa: E402

SIZES = (3, 5, 10, 20, 30, 40, 50)
SEEDS = range(100, 105)
WARMUP, REPEATS = 3, 15
NAME = {
    "fcfs": "FCFS",
    "greedy": "Urgency greedy",
    "aidos": "AidOS",
    "aidos_balanced": "AidOS balanced",
}
COLOR = {"fcfs": "#E69F00", "greedy": "#56B4E9", "aidos": "#009E73", "aidos_balanced": "#CC79A7"}


def main() -> int:
    started = datetime.now(UTC)
    out = sup.new_run_dir(ROOT / "experiments" / "results", "runtime-benchmark", started)
    config = AidosConfig()
    rows, loads = [], []
    for size in SIZES:
        load_before = sup.cpu_load_percent()
        for seed in SEEDS:
            sc = generate_sized(size, seed)
            scores = {u.zone_id: u.result.score for u in assess_urgency(sc)}
            for _ in range(WARMUP):
                for policy in POLICY_ORDER:
                    run_policy(policy, sc, scores, config)
            for repeat in range(REPEATS):
                for policy in POLICY_ORDER:
                    t0 = perf_counter()
                    run = run_policy(policy, sc, scores, config)
                    e2e = (perf_counter() - t0) * 1000
                    solver = run.result.solver
                    rows.append(
                        {
                            "zones": size,
                            "seed": seed,
                            "repeat": repeat,
                            "policy": policy.value,
                            "policy_ms": round(run.runtime_ms, 4),
                            "end_to_end_ms": round(e2e, 4),
                            "solver_ms": round(sum(p.wall_time_ms for p in solver.phases), 4)
                            if solver
                            else "",
                            "variables": solver.variables if solver else "",
                            "status": run.result.status.value,
                            "valid": int(run.validation.valid),
                        }
                    )
        loads.append(
            {
                "zones": size,
                "cpu_load_before": load_before,
                "cpu_load_after": sup.cpu_load_percent(),
            }
        )
        print(f"{size} zones done; cpu load {loads[-1]}")
    sup.write_csv(out / "runtime.csv", rows)
    sup.write_csv(out / "cpu_load.csv", loads)

    summary: dict = {
        "sizes": list(SIZES),
        "warmup": WARMUP,
        "repeats": REPEATS,
        "scenarios_per_size": len(SEEDS),
        "cpu_load": loads,
        "points": [],
    }
    for size in SIZES:
        medians = {}
        for policy in (p.value for p in POLICY_ORDER):
            sel = [r for r in rows if r["zones"] == size and r["policy"] == policy]
            pm = np.asarray([r["policy_ms"] for r in sel])
            e2e = np.asarray([r["end_to_end_ms"] for r in sel])
            solver = [r["solver_ms"] for r in sel if r["solver_ms"] != ""]
            medians[policy] = float(np.median(pm))
            summary["points"].append(
                {
                    "zones": size,
                    "policy": policy,
                    "n": len(sel),
                    "policy_ms": {
                        "median": float(np.median(pm)),
                        "p25": float(np.percentile(pm, 25)),
                        "p75": float(np.percentile(pm, 75)),
                        "p90": float(np.percentile(pm, 90)),
                        "min": float(pm.min()),
                        "max": float(pm.max()),
                        "cv": float(pm.std(ddof=1) / pm.mean()),
                    },
                    "end_to_end_ms_median": float(np.median(e2e)),
                    "solver_ms_median": float(statistics.median(solver)) if solver else None,
                    "statuses": {
                        s: sum(1 for r in sel if r["status"] == s)
                        for s in {r["status"] for r in sel}
                    },
                    "valid": sum(r["valid"] for r in sel),
                }
            )
        summary.setdefault("aidos_over_greedy_median_ratio", {})[size] = (
            medians["aidos"] / medians["greedy"]
        )
    sup.write_json(out / "summary.json", summary)
    sup.write_json(
        out / "config.json",
        {
            "sizes": list(SIZES),
            "seeds": [SEEDS.start, SEEDS.stop - 1],
            "warmup": WARMUP,
            "repeats": REPEATS,
            "resources": 4,
            "interleaving": "round-robin across policies per repeat",
        },
    )

    fig, ax = plt.subplots(figsize=(6, 3.6))
    for policy in (p.value for p in POLICY_ORDER):
        pts = [p for p in summary["points"] if p["policy"] == policy]
        ax.plot(
            [p["zones"] for p in pts],
            [p["policy_ms"]["median"] for p in pts],
            marker="o",
            color=COLOR[policy],
            label=NAME[policy],
        )
        ax.fill_between(
            [p["zones"] for p in pts],
            [p["policy_ms"]["p25"] for p in pts],
            [p["policy_ms"]["p75"] for p in pts],
            color=COLOR[policy],
            alpha=0.15,
        )
    ax.set_yscale("log")
    ax.set_xlabel("Active zones (4 resources)")
    ax.set_ylabel("Allocation call, ms (log scale)")
    load = [
        x for ld in loads for x in (ld["cpu_load_before"], ld["cpu_load_after"]) if x is not None
    ]
    note = f"CPU load during run {min(load)}-{max(load)}%" if load else "CPU load not recorded"
    ax.set_title(
        f"Runtime benchmark: {WARMUP} warm-ups, {REPEATS} interleaved repeats x 5 scenarios per size\n"
        f"median, band 25th-75th percentile; {note}",
        fontsize=8,
    )
    ax.legend(frameon=False, fontsize=7)
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(out / f"fig12_runtime_benchmark.{ext}", dpi=200)
    sup.finalize(
        out,
        name="runtime-benchmark",
        started=started,
        counts={"timed_runs": len(rows)},
        notes=f"{note}. Supplements, and does not replace, the Stage 4 timings.",
    )
    print(f"wrote {out}")
    for p in summary["points"]:
        if p["policy"] in ("greedy", "aidos", "aidos_balanced"):
            print(
                p["zones"],
                p["policy"],
                round(p["policy_ms"]["median"], 3),
                "e2e",
                round(p["end_to_end_ms_median"], 3),
                "solver",
                p["solver_ms_median"] and round(p["solver_ms_median"], 2),
                "cv",
                round(p["policy_ms"]["cv"], 2),
                p["statuses"],
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
