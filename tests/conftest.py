"""Shared test helpers."""

import pytest

from aidos.domain.validation import parse_scenario


def build_scenario(stock, zones, resources=None, scenario_id="test", step=0):
    """zones: (id, arrival_order, (severity, vulnerability, time_criticality), demand[, step])."""
    resources = resources or tuple(stock)
    return parse_scenario(
        {
            "schema_version": "1.0",
            "scenario_id": scenario_id,
            "title": scenario_id,
            "seed": 7,
            "synthetic": True,
            "step": step,
            "resources": [{"id": r, "label": r, "unit": "units"} for r in resources],
            "stock": stock,
            "zones": [
                {
                    "id": z[0],
                    "name": f"{z[0]} · test",
                    "arrival_order": z[1],
                    "severity": z[2][0],
                    "vulnerability": z[2][1],
                    "time_criticality": z[2][2],
                    "demand": z[3],
                    "activation_step": z[4] if len(z) > 4 else 0,
                }
                for z in zones
            ],
        }
    )


@pytest.fixture
def make_scenario():
    return build_scenario
