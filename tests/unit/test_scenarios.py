"""Scenario schema and fixture validation (spec Section 4)."""

import copy

import pytest

from aidos.domain.snapshots import (
    ScenarioNotFoundError,
    list_builtin_scenarios,
    load_builtin_scenario,
    snapshot_hash,
)
from aidos.domain.validation import ScenarioValidationError, parse_scenario

BASE = {
    "schema_version": "1.0",
    "scenario_id": "unit-test",
    "title": "Unit test",
    "seed": 1,
    "synthetic": True,
    "step": 0,
    "resources": [
        {"id": "medical_kits", "label": "Medical kits", "unit": "kits"},
        {"id": "water_packs", "label": "Water packs", "unit": "packs"},
    ],
    "stock": {"medical_kits": 10, "water_packs": 5},
    "zones": [
        {
            "id": "zone-a",
            "name": "Zone A",
            "arrival_order": 1,
            "severity": 5,
            "vulnerability": 5,
            "time_criticality": 5,
            "demand": {"medical_kits": 4, "water_packs": 2},
        }
    ],
}


def mutated(**changes):
    data = copy.deepcopy(BASE)
    for path, value in changes.items():
        target = data
        *parents, leaf = path.split("__")
        for key in parents:
            target = target[int(key)] if key.isdigit() else target[key]
        target[int(leaf) if leaf.isdigit() else leaf] = value
    return data


def test_every_builtin_fixture_is_valid_and_synthetic():
    scenarios = list_builtin_scenarios()
    assert len(scenarios) >= 4
    assert all(s.synthetic is True for s in scenarios)
    ids = [s.scenario_id for s in scenarios]
    assert len(ids) == len(set(ids))
    for required in ("triage-demo-001", "no-scarcity", "late-critical-arrival", "zero-stock"):
        assert required in ids


def test_base_payload_parses():
    scenario = parse_scenario(BASE)
    assert scenario.resource_ids() == ("medical_kits", "water_packs")


@pytest.mark.parametrize(
    "changes, expected_path",
    [
        ({"stock__medical_kits": -1}, "stock.medical_kits"),
        ({"zones__0__demand": {"medical_kits": -3}}, "zones.0.demand.medical_kits"),
        ({"zones__0__severity": 11}, "zones.0.severity"),
        ({"synthetic": False}, "synthetic"),
        ({"stock": {"medical_kits": 10}}, "stock.water_packs"),
        ({"stock": {"medical_kits": 1, "water_packs": 1, "fuel": 3}}, "stock.fuel"),
        ({"zones__0__demand": {"fuel": 3}}, "zones.0.demand.fuel"),
        ({"stock__medical_kits": 2.5}, "stock.medical_kits"),
    ],
)
def test_invalid_payloads_are_rejected_with_a_located_message(changes, expected_path):
    with pytest.raises(ScenarioValidationError) as info:
        parse_scenario(mutated(**changes))
    assert any(issue.path == expected_path for issue in info.value.issues), info.value.issues


def test_duplicate_zone_ids_are_rejected():
    data = copy.deepcopy(BASE)
    data["zones"].append(copy.deepcopy(data["zones"][0]))
    with pytest.raises(ScenarioValidationError) as info:
        parse_scenario(data)
    assert "duplicate zone id" in str(info.value)


def test_pathological_zone_count_is_rejected():
    data = copy.deepcopy(BASE)
    zone = data["zones"][0]
    data["zones"] = [dict(zone, id=f"zone-{i}") for i in range(51)]
    with pytest.raises(ScenarioValidationError):
        parse_scenario(data)


def test_snapshot_hash_is_stable_and_content_sensitive():
    a = parse_scenario(BASE)
    b = parse_scenario(copy.deepcopy(BASE))
    c = parse_scenario(mutated(stock__water_packs=6))
    assert snapshot_hash(a) == snapshot_hash(b)
    assert snapshot_hash(a) != snapshot_hash(c)


def test_unknown_builtin_scenario_raises():
    with pytest.raises(ScenarioNotFoundError):
        load_builtin_scenario("does-not-exist")
