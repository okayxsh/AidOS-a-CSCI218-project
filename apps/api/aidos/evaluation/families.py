"""Scenario families for the Stage 4 evaluation (docs/evaluation/experimental-protocol.md).

Each family is a seeded generator: `generate(family, seed)` returns the same validated
Scenario for the same arguments (it draws from its own random.Random, never the global one).

Design rules that keep the comparison fair:
- Arrival order is the zone index; zones are created in random rating order, so arrival
  order and urgency are independent. FCFS is not systematically handed bad orders.
- Every value is drawn from the documented ranges below; nothing depends on any policy.
- Stock is set per resource as (factor x total requested), so scarcity is controlled.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass

from aidos.domain.models import Scenario
from aidos.domain.validation import parse_scenario
from aidos.evaluation.generator import CATALOGUE

Ratings = tuple[int, int, int]  # severity, vulnerability, time criticality


@dataclass(frozen=True)
class Family:
    key: str
    name: str
    description: str
    seed_base: int  # family seeds are seed_base + i, so families never share a seed
    zones: tuple[int, int]
    resources: tuple[int, int]
    stock_factor: tuple[float, float]  # per resource, unless `stock_rule` overrides it
    ratings: str  # "uniform" | "bimodal" | "equal"
    demand: str  # "uniform" | "skewed"
    mixed_shortage: bool = False


FAMILIES: dict[str, Family] = {
    f.key: f
    for f in (
        Family(
            "A",
            "Low scarcity",
            "Stock is 85-110% of requests per resource.",
            100_000,
            (3, 8),
            (3, 4),
            (0.85, 1.10),
            "uniform",
            "uniform",
        ),
        Family(
            "B",
            "Moderate scarcity",
            "Stock is 60-85% of requests per resource.",
            200_000,
            (3, 8),
            (3, 4),
            (0.60, 0.85),
            "uniform",
            "uniform",
        ),
        Family(
            "C",
            "Severe scarcity",
            "Stock is 25-50% of requests per resource.",
            300_000,
            (3, 8),
            (3, 4),
            (0.25, 0.50),
            "uniform",
            "uniform",
        ),
        Family(
            "D",
            "Unequal urgency",
            "Half the zones are rated 7-10 on every input, half 0-3; stock 50-80%.",
            400_000,
            (4, 8),
            (3, 4),
            (0.50, 0.80),
            "bimodal",
            "uniform",
        ),
        Family(
            "E",
            "Equal or near-equal urgency",
            "All zones share one rating triple (even seeds) or differ by at most 1 point "
            "per input (odd seeds); stock 50-80%.",
            500_000,
            (3, 8),
            (3, 4),
            (0.50, 0.80),
            "equal",
            "uniform",
        ),
        Family(
            "F",
            "Unequal demand",
            "One or two zones request 4-8 times more than the others; stock 50-80%.",
            600_000,
            (4, 8),
            (3, 4),
            (0.50, 0.80),
            "uniform",
            "skewed",
        ),
        Family(
            "G",
            "Multiple resource shortages",
            "Four resources: three are short (30-60%), one is ample (100-130%).",
            700_000,
            (3, 8),
            (4, 4),
            (0.30, 0.60),
            "uniform",
            "uniform",
            mixed_shortage=True,
        ),
    )
}
STATIC_FAMILIES = tuple(FAMILIES)


def _ratings(family: Family, rng: random.Random, n: int) -> list[Ratings]:
    if family.ratings == "uniform":
        return [(rng.randint(0, 10), rng.randint(0, 10), rng.randint(0, 10)) for _ in range(n)]
    if family.ratings == "bimodal":
        high = n // 2
        out = [
            (rng.randint(7, 10), rng.randint(7, 10), rng.randint(7, 10))
            if i < high
            else (rng.randint(0, 3), rng.randint(0, 3), rng.randint(0, 3))
            for i in range(n)
        ]
        rng.shuffle(out)  # arrival order independent of urgency
        return out
    base = (rng.randint(2, 8), rng.randint(2, 8), rng.randint(2, 8))
    exact = rng.random() < 0.5
    if exact:
        return [base] * n
    jitter: Callable[[int], int] = lambda v: min(10, max(0, v + rng.choice((-1, 0, 1))))  # noqa: E731
    return [(jitter(base[0]), jitter(base[1]), jitter(base[2])) for _ in range(n)]


def _demand(family: Family, rng: random.Random, n: int, resources: list[str]) -> list[dict]:
    if family.demand == "uniform":
        return [
            {r: 0 if rng.random() < 0.1 else rng.randint(1, 120) for r in resources}
            for _ in range(n)
        ]
    large = set(rng.sample(range(n), k=rng.randint(1, 2)))
    out = []
    for i in range(n):
        factor = rng.randint(4, 8) if i in large else 1
        out.append({r: rng.randint(5, 40) * factor for r in resources})
    return out


def generate(family_key: str, index: int) -> Scenario:
    """The index-th scenario of a family (seed = seed_base + index)."""
    family = FAMILIES[family_key]
    seed = family.seed_base + index
    rng = random.Random(seed)
    n_zones = rng.randint(*family.zones)
    n_resources = rng.randint(*family.resources)
    catalogue = list(CATALOGUE[:n_resources])
    resource_ids = [r["id"] for r in catalogue]

    ratings = _ratings(family, rng, n_zones)
    demands = _demand(family, rng, n_zones, resource_ids)
    zones = [
        {
            "id": f"zone-{i + 1:02d}",
            "name": f"Zone {i + 1}",
            "arrival_order": i + 1,
            "severity": ratings[i][0],
            "vulnerability": ratings[i][1],
            "time_criticality": ratings[i][2],
            "demand": demands[i],
        }
        for i in range(n_zones)
    ]

    ample = rng.randrange(n_resources) if family.mixed_shortage else None
    stock = {}
    for index_r, rid in enumerate(resource_ids):
        low, high = (1.0, 1.3) if index_r == ample else family.stock_factor
        total = sum(z["demand"][rid] for z in zones)
        stock[rid] = int(total * rng.uniform(low, high))

    return parse_scenario(
        {
            "schema_version": "1.0",
            "scenario_id": f"fam-{family.key.lower()}-{seed}",
            "title": f"Family {family.key} ({family.name}), seed {seed}",
            "description": family.description,
            "seed": seed,
            "synthetic": True,
            "resources": catalogue,
            "stock": stock,
            "zones": zones,
        }
    )


def generate_sized(n_zones: int, seed: int, n_resources: int = 4) -> Scenario:
    """Moderate-scarcity scenario with a fixed number of zones (runtime scaling study)."""
    rng = random.Random(900_000 + n_zones * 1000 + seed)
    catalogue = list(CATALOGUE[:n_resources])
    zones = [
        {
            "id": f"zone-{i + 1:02d}",
            "name": f"Zone {i + 1}",
            "arrival_order": i + 1,
            "severity": rng.randint(0, 10),
            "vulnerability": rng.randint(0, 10),
            "time_criticality": rng.randint(0, 10),
            "demand": {r["id"]: rng.randint(1, 120) for r in catalogue},
        }
        for i in range(n_zones)
    ]
    stock = {
        r["id"]: int(sum(z["demand"][r["id"]] for z in zones) * rng.uniform(0.6, 0.85))
        for r in catalogue
    }
    return parse_scenario(
        {
            "schema_version": "1.0",
            "scenario_id": f"size-{n_zones}-{seed}",
            "title": f"Scaling study, {n_zones} zones, seed {seed}",
            "seed": seed,
            "synthetic": True,
            "resources": catalogue,
            "stock": stock,
            "zones": zones,
        }
    )
