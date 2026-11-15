"""Why does AidOS (CP-SAT, urgency-first) give the same plans as urgency greedy?

    cd apps/api
    uv run python ../../experiments/greedy_equivalence.py

Supplementary Stage 5 experiment (writes experiments/results/supplementary-greedy-equivalence-*):

E1  exhaustive: 3 zones x 1 resource, every request in 0..3, stock 0..5, urgency in
    {12.5, 37.5, 62.5, 87.5}^3 (24,576 instances). Greedy is compared with the brute-force
    lexicographic optimum of the AidOS objective over every feasible integer plan; CP-SAT is run
    on a deterministic 1-in-40 sample.
E2  exhaustive: 2 zones x 2 resources, requests 0..2, stock 0..3, urgency in {12.5, 62.5, 87.5}^2
    (11,664 instances), same comparison.
R   random: 100 new scenarios per family A-G (indices 3000-3099, outside the Stage 4 benchmark),
    each with a random resource weight per resource (1-5) and epsilon in {0.01, 1, 10}.
O   solver overhead: AidOS policy time vs CP-SAT's own reported solve time.
X   proposed-extension counterexample (NOT part of AidOS or any benchmark): a per-zone vehicle
    capacity couples the resources; greedy is then no longer optimal.
"""

from __future__ import annotations

import itertools
import random
import statistics
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from ortools.sat.python import cp_model  # noqa: E402

from aidos.ai.baseline_greedy import allocate_greedy  # noqa: E402
from aidos.ai.constraints import SCALE, AidosConfig, allocate_aidos  # noqa: E402
from aidos.domain.validation import parse_scenario  # noqa: E402
from aidos.evaluation import supplementary as sup  # noqa: E402
from aidos.evaluation.families import STATIC_FAMILIES, generate  # noqa: E402
from aidos.pipeline import assess_urgency  # noqa: E402


def scenario(stock: dict[str, int], demands: list[dict[str, int]]):
    return parse_scenario(
        {
            "schema_version": "1.0",
            "scenario_id": "eq",
            "title": "eq",
            "seed": 0,
            "synthetic": True,
            "resources": [{"id": r, "label": r, "unit": "u"} for r in stock],
            "stock": stock,
            "zones": [
                {
                    "id": f"z{i}",
                    "name": f"z{i}",
                    "arrival_order": i + 1,
                    "severity": 5,
                    "vulnerability": 5,
                    "time_criticality": 5,
                    "demand": d,
                }
                for i, d in enumerate(demands)
            ],
        }
    )


def plan(result) -> dict[tuple[str, str], int]:
    return {(c.zone_id, c.resource_id): c.allocated for c in result.cells}


def brute_force(sc, urgency, config: AidosConfig | None = None) -> tuple[dict, bool]:
    """Lexicographic optimum (urgency objective, then earlier-arrival tie-break) by enumeration.
    Returns the optimum and whether it is unique."""
    zones = sorted(sc.active_zones(), key=lambda z: (z.arrival_order, z.id))
    rank = {z.id: len(zones) - i for i, z in enumerate(zones)}
    keys = [(z.id, r) for z in zones for r in sc.resource_ids()]
    ranges = [range(sc.demand_of(z, r) + 1) for z in zones for r in sc.resource_ids()]
    config = config or AidosConfig()
    best, best_val, count = None, None, 0
    bonus = round(config.epsilon * SCALE)
    for values in itertools.product(*ranges):
        x = dict(zip(keys, values, strict=True))
        if any(sum(x[(z.id, r)] for z in zones) > sc.stock[r] for r in sc.resource_ids()):
            continue
        u = sum(
            config.weight(r) * (round(urgency[z] * SCALE) + bonus) * v for (z, r), v in x.items()
        )
        t = sum(rank[z] * v for (z, _), v in x.items())
        val = (u, t)
        if best_val is None or val > best_val:
            best, best_val, count = x, val, 1
        elif val == best_val:
            count += 1
    return best, count == 1


def exhaustive(label, zones, resources, demand_max, stock_max, levels, cpsat_every):
    rows = []
    for demands_flat in itertools.product(range(demand_max + 1), repeat=zones * resources):
        demands = [
            {f"r{j}": demands_flat[i * resources + j] for j in range(resources)}
            for i in range(zones)
        ]
        for stock_vals in itertools.product(range(stock_max + 1), repeat=resources):
            stock = {f"r{j}": stock_vals[j] for j in range(resources)}
            sc = scenario(stock, demands)
            for urg in itertools.product(levels, repeat=zones):
                urgency = {f"z{i}": urg[i] for i in range(zones)}
                g = plan(allocate_greedy(sc, urgency))
                opt, unique = brute_force(sc, urgency)
                row = {
                    "set": label,
                    "greedy_optimal": int(g == opt),
                    "unique": int(unique),
                    "cpsat_checked": 0,
                    "cpsat_equal": "",
                }
                if len(rows) % cpsat_every == 0:
                    row["cpsat_checked"] = 1
                    row["cpsat_equal"] = int(plan(allocate_aidos(sc, urgency)) == g)
                rows.append(row)
    return rows


def random_set():
    rows = []
    rng = random.Random(20261112)
    for family in STATIC_FAMILIES:
        for i in range(3000, 3100):
            sc = generate(family, i)
            urgency = {u.zone_id: u.result.score for u in assess_urgency(sc)}
            weights = {r: rng.randint(1, 5) for r in sc.resource_ids()}
            eps = rng.choice([0.01, 1.0, 10.0])
            config = AidosConfig(epsilon=eps, resource_weights=weights)
            t0 = perf_counter()
            aidos = allocate_aidos(sc, urgency, config)
            aidos_ms = (perf_counter() - t0) * 1000
            t0 = perf_counter()
            greedy = allocate_greedy(sc, urgency)
            greedy_ms = (perf_counter() - t0) * 1000
            scores = sorted(urgency.values())
            rows.append(
                {
                    "family": family,
                    "scenario_id": sc.scenario_id,
                    "epsilon": eps,
                    "weights": "|".join(f"{k}:{v}" for k, v in weights.items()),
                    "zones": len(sc.zones),
                    "tied_scores": int(len(set(scores)) < len(scores)),
                    "identical": int(plan(aidos) == plan(greedy)),
                    "status": aidos.status.value,
                    "aidos_ms": round(aidos_ms, 3),
                    "solver_ms": round(sum(p.wall_time_ms for p in aidos.solver.phases), 3),
                    "greedy_ms": round(greedy_ms, 4),
                }
            )
    return rows


def counterexample():
    """Per-zone vehicle capacity couples resources: greedy (catalogue order) wastes capacity."""
    # Zone A (urgency 87.5) can receive at most 10 units in total; zone B (37.5) also 10.
    # Medical kits weigh 3 in the objective, water 1. Stock: 10 water, 10 medical.
    demand = {"A": {"water": 10, "medical": 10}, "B": {"water": 10, "medical": 0}}
    stock, cap = {"water": 10, "medical": 10}, {"A": 10, "B": 10}
    urgency, weight = {"A": 87.5, "B": 37.5}, {"water": 1, "medical": 3}
    coef = {(z, r): weight[r] * (round(urgency[z] * SCALE) + SCALE) for z in demand for r in stock}

    greedy: dict[tuple[str, str], int] = {}
    left = dict(stock)
    for z in sorted(demand, key=lambda z: -urgency[z]):
        room = cap[z]
        for r in ("water", "medical"):  # catalogue order, as urgency greedy does
            take = min(left[r], demand[z][r], room)
            greedy[(z, r)] = take
            left[r] -= take
            room -= take

    model = cp_model.CpModel()
    x = {(z, r): model.new_int_var(0, demand[z][r], f"x{z}{r}") for z in demand for r in stock}
    for r in stock:
        model.add(sum(x[z, r] for z in demand) <= stock[r])
    for z in demand:
        model.add(sum(x[z, r] for r in stock) <= cap[z])
    model.maximize(sum(coef[k] * v for k, v in x.items()))
    solver = cp_model.CpSolver()
    status = solver.status_name(solver.solve(model))
    optimal = {k: int(solver.value(v)) for k, v in x.items()}
    value = lambda p: sum(coef[k] * v for k, v in p.items())  # noqa: E731
    return {
        "status": status,
        "greedy_plan": {f"{z}/{r}": v for (z, r), v in greedy.items()},
        "cpsat_plan": {f"{z}/{r}": v for (z, r), v in optimal.items()},
        "greedy_objective": value(greedy),
        "cpsat_objective": value(optimal),
        "greedy_units": sum(greedy.values()),
        "cpsat_units": sum(optimal.values()),
    }


def main() -> int:
    started = datetime.now(UTC)
    out = sup.new_run_dir(ROOT / "experiments" / "results", "greedy-equivalence", started)
    e1 = exhaustive("E1 3x1", 3, 1, 3, 5, (12.5, 37.5, 62.5, 87.5), 40)
    e2 = exhaustive("E2 2x2", 2, 2, 2, 3, (12.5, 62.5, 87.5), 40)
    rnd = random_set()
    cx = counterexample()
    sup.write_csv(out / "exhaustive.csv", e1 + e2)
    sup.write_csv(out / "random.csv", rnd)

    def tally(rows):
        checked = [r for r in rows if r["cpsat_checked"]]
        return {
            "instances": len(rows),
            "greedy_equals_bruteforce_optimum": sum(r["greedy_optimal"] for r in rows),
            "unique_optimum": sum(r["unique"] for r in rows),
            "cpsat_checked": len(checked),
            "cpsat_equals_greedy": sum(int(r["cpsat_equal"]) for r in checked),
        }

    summary = {
        "E1": tally(e1),
        "E2": tally(e2),
        "random": {
            "instances": len(rnd),
            "identical": sum(r["identical"] for r in rnd),
            "with_tied_scores": sum(r["tied_scores"] for r in rnd),
            "identical_with_tied_scores": sum(r["identical"] for r in rnd if r["tied_scores"]),
            "statuses": {
                s: sum(1 for r in rnd if r["status"] == s) for s in {r["status"] for r in rnd}
            },
            "aidos_ms_median": statistics.median(r["aidos_ms"] for r in rnd),
            "solver_ms_median": statistics.median(r["solver_ms"] for r in rnd),
            "greedy_ms_median": statistics.median(r["greedy_ms"] for r in rnd),
            "solver_share_of_aidos_time_median": statistics.median(
                r["solver_ms"] / r["aidos_ms"] for r in rnd if r["aidos_ms"]
            ),
        },
        "counterexample_proposed_extension": cx,
    }
    sup.write_json(out / "summary.json", summary)
    sup.write_json(
        out / "config.json",
        {"seed": 20261112, "random_indices": [3000, 3099], "families": list(STATIC_FAMILIES)},
    )
    sup.finalize(
        out,
        name="greedy-equivalence",
        started=started,
        counts={"exhaustive": len(e1) + len(e2), "random": len(rnd)},
        notes="Checks a mathematical claim; no policy parameter was changed.",
    )
    print(f"wrote {out}")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
