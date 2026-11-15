"""Scenario summary and allocation metrics (spec Section 5.5)."""

from aidos.ai.baseline_fcfs import allocate_fcfs
from aidos.ai.policies import AllocationResult, CellResult, Limit, PolicyId, PolicyStatus
from aidos.domain.snapshots import load_builtin_scenario
from aidos.domain.validation import parse_scenario
from aidos.evaluation.metrics import compute_metrics, find_violations, summarize_scenario


def test_summary_of_triage_demo():
    summary = summarize_scenario(load_builtin_scenario("triage-demo-001"))
    by_id = {r.resource_id: r for r in summary.resources}
    assert (by_id["medical_kits"].stock, by_id["medical_kits"].requested) == (90, 150)
    assert by_id["medical_kits"].shortfall == 60
    assert summary.total_stock == 330
    assert summary.total_requested == 560
    assert summary.total_shortfall == 230
    assert summary.active_zone_count == 3


def test_shortfall_is_per_resource_not_netted():
    scenario = parse_scenario(
        {
            "schema_version": "1.0",
            "scenario_id": "netting",
            "title": "netting",
            "seed": 1,
            "synthetic": True,
            "resources": [
                {"id": "medical_kits", "label": "m", "unit": "kits"},
                {"id": "water_packs", "label": "w", "unit": "packs"},
            ],
            "stock": {"medical_kits": 0, "water_packs": 100},
            "zones": [
                {
                    "id": "zone-a",
                    "name": "a",
                    "arrival_order": 1,
                    "severity": 1,
                    "vulnerability": 1,
                    "time_criticality": 1,
                    "demand": {"medical_kits": 10, "water_packs": 10},
                }
            ],
        }
    )
    assert summarize_scenario(scenario).total_shortfall == 10


def test_inactive_zone_demand_is_not_counted():
    summary = summarize_scenario(load_builtin_scenario("coastal-storm-005"))
    assert summary.active_zone_count == 5
    medical = next(r for r in summary.resources if r.resource_id == "medical_kits")
    assert medical.requested == 170  # zone-f (25) is not active yet


def test_zero_demand_coverage_is_none_not_a_number():
    scenario = load_builtin_scenario("triage-demo-001")
    empty = AllocationResult(PolicyId.FCFS, PolicyStatus.COMPLETE, ("zone-a",), ())
    metrics = compute_metrics(scenario, empty)
    assert metrics.unit_coverage is None
    assert metrics.coverage_by_zone["zone-a"] is None


def test_fcfs_coverage_on_triage_demo():
    scenario = load_builtin_scenario("triage-demo-001")
    metrics = compute_metrics(scenario, allocate_fcfs(scenario))
    assert metrics.allocated_units == 330
    assert metrics.unmet_units == 230
    assert metrics.unit_coverage == 330 / 560
    assert metrics.coverage_by_resource["medical_kits"] == 90 / 150
    assert metrics.feasibility_violations == 0


def test_violations_are_detected_independently_of_the_policy():
    scenario = load_builtin_scenario("triage-demo-001")
    bad = AllocationResult(
        PolicyId.FCFS,
        PolicyStatus.COMPLETE,
        ("zone-a",),
        (
            CellResult("zone-a", "medical_kits", 75, 80, Limit.MET, ""),  # above demand
            CellResult("zone-a", "water_packs", 100, 200, Limit.MET, ""),  # above stock
        ),
    )
    kinds = sorted(v.kind for v in find_violations(scenario, bad) if v.kind != "incomplete")
    assert kinds == ["above_demand", "above_demand", "above_stock"]
    # Since Stage 2 the validator also notices the plan omits the other zone/resource cells.
    assert any(v.kind == "incomplete" for v in find_violations(scenario, bad))


def test_supply_status_reflects_stock_against_active_requests():
    status = {
        sid: summarize_scenario(load_builtin_scenario(sid)).supply_status
        for sid in ("triage-demo-001", "no-scarcity", "zero-stock")
    }
    assert status == {
        "triage-demo-001": "shortage",
        "no-scarcity": "covered",
        "zero-stock": "depot_empty",
    }


def test_supply_status_with_no_requests_is_no_demand():
    scenario = parse_scenario(
        {
            "schema_version": "1.0",
            "scenario_id": "quiet",
            "title": "quiet",
            "seed": 1,
            "synthetic": True,
            "resources": [{"id": "water_packs", "label": "w", "unit": "packs"}],
            "stock": {"water_packs": 0},
            "zones": [
                {
                    "id": "zone-a",
                    "name": "a",
                    "arrival_order": 1,
                    "severity": 1,
                    "vulnerability": 1,
                    "time_criticality": 1,
                    "demand": {},
                }
            ],
        }
    )
    assert summarize_scenario(scenario).supply_status == "no_demand"
