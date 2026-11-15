"""FCFS baseline behaviour (spec Sections 5.4 and 11, must-pass domain tests)."""

import copy

from aidos.ai.baseline_fcfs import allocate_fcfs
from aidos.ai.policies import Limit
from aidos.domain.snapshots import load_builtin_scenario
from aidos.domain.validation import parse_scenario
from aidos.evaluation.metrics import find_violations


def scenario_from(stock, zones, resources=("medical_kits", "water_packs")):
    return parse_scenario(
        {
            "schema_version": "1.0",
            "scenario_id": "fcfs-test",
            "title": "FCFS test",
            "seed": 7,
            "synthetic": True,
            "resources": [{"id": r, "label": r, "unit": "units"} for r in resources],
            "stock": stock,
            "zones": [
                {
                    "id": zid,
                    "name": zid,
                    "arrival_order": order,
                    "severity": 5,
                    "vulnerability": 5,
                    "time_criticality": 5,
                    "demand": demand,
                }
                for zid, order, demand in zones
            ],
        }
    )


def test_no_shortage_meets_every_request_exactly():
    scenario = load_builtin_scenario("no-scarcity")
    result = allocate_fcfs(scenario)
    assert all(cell.allocated == cell.requested for cell in result.cells)
    assert all(cell.limit in (Limit.MET, Limit.NO_DEMAND) for cell in result.cells)


def test_shortage_never_exceeds_stock_and_unmet_is_correct():
    scenario = load_builtin_scenario("triage-demo-001")
    result = allocate_fcfs(scenario)
    assert find_violations(scenario, result) == []
    for rid in scenario.resource_ids():
        cells = [c for c in result.cells if c.resource_id == rid]
        requested = sum(c.requested for c in cells)
        allocated = sum(c.allocated for c in cells)
        assert allocated == min(requested, scenario.stock[rid])
        assert sum(c.unmet for c in cells) == requested - allocated


def test_triage_demo_golden_case():
    # Zone A arrives first and takes 75 of 90 medical kits; B gets the remaining 15; C gets 0.
    result = allocate_fcfs(load_builtin_scenario("triage-demo-001"))
    assert result.zone_order == ("zone-a", "zone-b", "zone-c")
    assert result.allocated("zone-a", "medical_kits") == 75
    assert result.allocated("zone-b", "medical_kits") == 15
    assert result.allocated("zone-c", "medical_kits") == 0
    assert result.allocated("zone-a", "water_packs") == 100
    assert result.allocated("zone-b", "water_packs") == 80
    assert result.allocated("zone-c", "shelter_kits") == 0


def test_zero_stock_gives_zero_allocations_with_reasons():
    result = allocate_fcfs(load_builtin_scenario("zero-stock"))
    assert all(cell.allocated == 0 for cell in result.cells)
    assert all(cell.limit == Limit.ZERO_STOCK for cell in result.cells if cell.requested)
    assert all("no units" in cell.reason for cell in result.cells if cell.requested)


def test_zero_demand_allocates_nothing():
    scenario = scenario_from({"medical_kits": 5, "water_packs": 5}, [("zone-a", 1, {})])
    result = allocate_fcfs(scenario)
    assert all(c.allocated == 0 and c.limit == Limit.NO_DEMAND for c in result.cells)


def test_single_zone_is_fully_auditable():
    scenario = scenario_from(
        {"medical_kits": 3, "water_packs": 10},
        [("zone-a", 1, {"medical_kits": 5, "water_packs": 4})],
    )
    result = allocate_fcfs(scenario)
    assert result.allocated("zone-a", "medical_kits") == 3
    assert result.allocated("zone-a", "water_packs") == 4
    medical = next(c for c in result.cells if c.resource_id == "medical_kits")
    assert medical.limit == Limit.STOCK_EXHAUSTED
    assert "entire stock of 3" in medical.reason


def test_resources_never_substitute():
    # Plenty of water cannot cover missing medical kits.
    scenario = scenario_from(
        {"medical_kits": 0, "water_packs": 100},
        [("zone-a", 1, {"medical_kits": 10, "water_packs": 0})],
    )
    result = allocate_fcfs(scenario)
    assert result.allocated("zone-a", "medical_kits") == 0
    assert result.allocated("zone-a", "water_packs") == 0


def test_arrival_ties_break_by_zone_id_deterministically():
    zones = [("zone-b", 1, {"medical_kits": 5}), ("zone-a", 1, {"medical_kits": 5})]
    scenario = scenario_from({"medical_kits": 5, "water_packs": 0}, zones)
    first = allocate_fcfs(scenario)
    again = allocate_fcfs(scenario)
    assert first == again
    assert first.zone_order == ("zone-a", "zone-b")
    assert first.allocated("zone-a", "medical_kits") == 5
    assert first.allocated("zone-b", "medical_kits") == 0


def test_late_critical_zone_is_served_last_by_fcfs():
    result = allocate_fcfs(load_builtin_scenario("late-critical-arrival"))
    assert result.zone_order[-1] == "zone-d"
    assert result.allocated("zone-d", "medical_kits") == 10  # 100 stock - 90 used earlier


def test_inactive_zones_are_excluded():
    scenario = load_builtin_scenario("coastal-storm-005")
    result = allocate_fcfs(scenario)
    assert "zone-f" not in result.zone_order


def test_policy_does_not_mutate_the_snapshot():
    scenario = load_builtin_scenario("triage-demo-001")
    before = copy.deepcopy(scenario.model_dump())
    allocate_fcfs(scenario)
    assert scenario.model_dump() == before
