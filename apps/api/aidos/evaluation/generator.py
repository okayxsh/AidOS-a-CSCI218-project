"""Seeded synthetic scenario generator (spec Section 5.5).

`generate_scenario(seed, scarcity)` always returns the same validated Scenario for the same
arguments: it draws from its own `random.Random(seed)`, never the global generator. The
values are synthetic test inputs, not modelled on any real crisis.
"""

from __future__ import annotations

import random
from typing import Literal

from aidos.domain.models import Scenario
from aidos.domain.validation import parse_scenario

Scarcity = Literal["none", "mild", "severe", "zero"]

# Stock as a fraction of total requested units, per resource.
STOCK_FACTOR: dict[str, tuple[float, float]] = {
    "none": (1.1, 1.5),
    "mild": (0.7, 0.95),
    "severe": (0.25, 0.5),
    "zero": (0.0, 0.0),
}

CATALOGUE = (
    {"id": "medical_kits", "label": "Medical kits", "unit": "kits"},
    {"id": "water_packs", "label": "Water packs", "unit": "packs"},
    {"id": "shelter_kits", "label": "Shelter kits", "unit": "kits"},
    {"id": "nutrition_packs", "label": "Nutrition packs", "unit": "packs"},
)


def generate_scenario(
    seed: int,
    scarcity: Scarcity = "severe",
    zones: int | None = None,
    resources: int | None = None,
    max_demand: int = 120,
    zero_demand_rate: float = 0.1,
) -> Scenario:
    rng = random.Random(seed)
    n_zones = zones if zones is not None else rng.randint(3, 8)
    n_resources = resources if resources is not None else rng.randint(3, 4)
    catalogue = CATALOGUE[:n_resources]

    zone_list = []
    for index in range(n_zones):
        demand = {
            r["id"]: 0 if rng.random() < zero_demand_rate else rng.randint(1, max_demand)
            for r in catalogue
        }
        zone_list.append(
            {
                "id": f"zone-{index + 1:02d}",
                "name": f"Zone {index + 1}",
                "arrival_order": index + 1,
                "severity": rng.randint(0, 10),
                "vulnerability": rng.randint(0, 10),
                "time_criticality": rng.randint(0, 10),
                "demand": demand,
            }
        )

    low, high = STOCK_FACTOR[scarcity]
    stock = {}
    for r in catalogue:
        total = sum(z["demand"][r["id"]] for z in zone_list)
        stock[r["id"]] = int(total * rng.uniform(low, high))

    return parse_scenario(
        {
            "schema_version": "1.0",
            "scenario_id": f"gen-{scarcity}-{seed}",
            "title": f"Generated ({scarcity} scarcity, seed {seed})",
            "description": "Seeded synthetic scenario for tests and experiments.",
            "seed": seed,
            "synthetic": True,
            "resources": list(catalogue),
            "stock": stock,
            "zones": zone_list,
        }
    )
