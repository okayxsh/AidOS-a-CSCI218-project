"""Numbers the report derives directly from the frozen result CSVs (read-only).

Run from the repository root:
    python docs/report/source/derived_stats.py > docs/report/source/derived_stats.txt

- Urgency ties and high-urgency starvation: extended-20261112T100136Z/static_zones.csv.
- All-zone figures for the controlled dynamic experiment:
  supplementary-dynamic-controlled-20261112T165434Z/{dispatch,recommendation}.csv.

Percentile bootstrap: 5,000 resamples, seed 20261111, the same settings as the protocol.
"""

import csv
import random
import statistics
from collections import defaultdict
from pathlib import Path

RESULTS = Path(__file__).resolve().parents[3] / "experiments" / "results"
STATIC = RESULTS / "extended-20261112T100136Z" / "static_zones.csv"
CONTROLLED = RESULTS / "supplementary-dynamic-controlled-20261112T165434Z"


def rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def bootstrap(values: list[float], resamples: int = 5000, seed: int = 20261111):
    rng = random.Random(seed)
    n = len(values)
    means = sorted(sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(resamples))
    return statistics.mean(values), means[int(0.025 * resamples)], means[int(0.975 * resamples) - 1]


def main() -> None:
    zones = [r for r in rows(STATIC) if r["policy"] == "aidos"]
    by_scenario = defaultdict(list)
    for r in zones:
        by_scenario[r["scenario_id"]].append(float(r["urgency"]))
    tied = sum(1 for scores in by_scenario.values() if len(scores) != len(set(scores)))
    at_max = sum(1 for scores in by_scenario.values() if scores.count(87.5) >= 2)
    print(f"static scenarios: {len(by_scenario)}")
    print(f"distinct urgency scores: {len({float(r['urgency']) for r in zones})}")
    print(f"scenarios with tied urgency: {tied}; with two or more zones at 87.5: {at_max}")
    uncovered = [r for r in zones if int(r["requested"]) > 0 and int(r["allocated"]) == 0]
    urgent = [r for r in uncovered if float(r["urgency"]) >= 50]
    families = defaultdict(int)
    for r in urgent:
        families[r["family"]] += 1
    print(
        f"AidOS zones left uncovered: {len(uncovered)}; with urgency >= 50: {len(urgent)} {dict(families)}"
    )

    dispatch = rows(CONTROLLED / "dispatch.csv")
    index = {(r["script_id"], r["policy"]): r for r in dispatch}
    for level in ("low", "moderate", "high", "random"):
        scripts = sorted({r["script_id"] for r in dispatch if r["level"] == level})
        lowest, never = [], []
        for sid in scripts:
            a, f = index[sid, "aidos"], index[sid, "fcfs"]
            low_a = min(float(a["new_zone_fulfilment"]), float(a["original_min_fulfilment"]))
            low_f = min(float(f["new_zone_fulfilment"]), float(f["original_min_fulfilment"]))
            lowest.append(low_a - low_f)
            never_a = int(a["new_zone_never_served"]) + int(a["original_never_served"])
            never_f = int(f["new_zone_never_served"]) + int(f["original_never_served"])
            never.append(never_a - never_f)
        m, lo, hi = bootstrap(lowest)
        n_m, n_lo, n_hi = bootstrap(never)
        print(
            f"{level}: n={len(scripts)} all-zone lowest fulfilment AidOS-FCFS {m:.3f} [{lo:.3f}, {hi:.3f}]; "
            f"zones never served AidOS-FCFS {n_m:.2f} [{n_lo:.2f}, {n_hi:.2f}]"
        )
    fcfs = [r for r in dispatch if r["policy"] == "fcfs"]
    served = sum(1 for r in fcfs if r["new_zone_never_served"] in ("0", "False", "false"))
    print(f"dispatch: FCFS served the late zone in {served} of {len(fcfs)} scripts")
    rec = rows(CONTROLLED / "recommendation.csv")
    cov = [
        float(r["new_zone_coverage"])
        for r in rec
        if r["policy"] == "fcfs" and r["new_zone_coverage"] not in ("", "nan")
    ]
    print(
        f"recommendation: FCFS late-zone coverage > 0 in {sum(1 for v in cov if v > 0)} of {len(cov)} steps; max {max(cov):.3f}"
    )


if __name__ == "__main__":
    main()
