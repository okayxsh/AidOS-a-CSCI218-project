"""Greedy baseline, independent validator, pipeline, randomized invariants and the runner."""

import csv
import json

import pytest

from aidos.ai.baseline_fcfs import allocate_fcfs
from aidos.ai.baseline_greedy import allocate_greedy, urgency_rank
from aidos.ai.policies import AllocationResult, CellResult, Limit, PolicyId, PolicyStatus
from aidos.domain.snapshots import load_builtin_scenario, snapshot_hash
from aidos.evaluation.exports import to_rows, write_csv, write_json
from aidos.evaluation.generator import generate_scenario
from aidos.evaluation.invariants import validate_allocation
from aidos.evaluation.runner import run_experiment
from aidos.pipeline import POLICY_ORDER, compare

# ---------------------------------------------------------------- urgency greedy


def test_greedy_ranks_by_urgency_then_arrival_then_id(make_scenario):
    scenario = make_scenario(
        {"kits": 1},
        [("c", 3, (5, 5, 5), {}), ("b", 2, (5, 5, 5), {}), ("a", 1, (5, 5, 5), {})],
    )
    assert urgency_rank(scenario, {"a": 40.0, "b": 70.0, "c": 70.0}) == ("b", "c", "a")


def test_greedy_serves_urgent_zones_first(make_scenario):
    scenario = make_scenario(
        {"kits": 10}, [("a", 1, (5, 5, 5), {"kits": 8}), ("b", 2, (5, 5, 5), {"kits": 8})]
    )
    result = allocate_greedy(scenario, {"a": 20.0, "b": 80.0})
    cells = {c.zone_id: c for c in result.cells}
    assert (cells["b"].allocated, cells["a"].allocated) == (8, 2)
    assert "ranked above it by urgency used 8 of 10" in cells["a"].reason


# ---------------------------------------------------------------- independent validator


def test_validator_accepts_every_policy_on_every_fixture():
    for sid in (
        "triage-demo-001",
        "no-scarcity",
        "late-critical-arrival",
        "zero-stock",
        "coastal-storm-005",
    ):
        scenario = load_builtin_scenario(sid)
        for run in compare(scenario, POLICY_ORDER).runs:
            report = run.validation
            assert report.valid, (sid, run.result.policy_id, report.violations)
            assert all(c.passed for c in report.checks if c.hard)


def _result(cells):
    return AllocationResult(PolicyId.AIDOS, PolicyStatus.OPTIMAL, ("zone-a",), tuple(cells))


def test_validator_checks_the_scenario_not_the_policys_claims():
    scenario = load_builtin_scenario("triage-demo-001")
    fcfs = allocate_fcfs(scenario)
    # A policy that under-reports the request to make an over-allocation look legal.
    forged = [
        CellResult(c.zone_id, c.resource_id, 999, 999, Limit.MET, "")
        if (c.zone_id, c.resource_id) == ("zone-c", "medical_kits")
        else c
        for c in fcfs.cells
    ]
    report = validate_allocation(scenario, _result(forged))
    kinds = {v.kind for v in report.violations}
    assert {"above_demand", "above_stock", "incomplete"} <= kinds
    assert not report.valid


def test_validator_flags_non_integers_negatives_and_missing_cells():
    scenario = load_builtin_scenario("triage-demo-001")
    cells = list(allocate_fcfs(scenario).cells)
    cells[0] = CellResult(
        cells[0].zone_id, cells[0].resource_id, cells[0].requested, 2.5, Limit.MET, ""
    )
    cells[1] = CellResult(
        cells[1].zone_id, cells[1].resource_id, cells[1].requested, -1, Limit.MET, ""
    )
    del cells[2]
    kinds = {v.kind for v in validate_allocation(scenario, _result(cells)).violations}
    assert {"not_integer", "negative", "incomplete"} <= kinds


def test_validator_reports_idle_stock_as_quality_not_violation():
    scenario = load_builtin_scenario("triage-demo-001")
    idle = [
        CellResult(c.zone_id, c.resource_id, c.requested, 0, Limit.MET, "")
        for c in allocate_fcfs(scenario).cells
    ]
    report = validate_allocation(scenario, _result(idle))
    assert report.valid
    quality = next(c for c in report.checks if c.name == "no_idle_stock")
    assert not quality.passed and not quality.hard


def test_validator_is_not_applicable_without_a_plan():
    scenario = load_builtin_scenario("triage-demo-001")
    empty = AllocationResult(PolicyId.AIDOS, PolicyStatus.UNKNOWN, (), ())
    report = validate_allocation(scenario, empty)
    assert not report.applicable and not report.valid


# ---------------------------------------------------------------- pipeline


def test_every_policy_sees_the_same_snapshot_and_scores():
    scenario = load_builtin_scenario("triage-demo-001")
    before = snapshot_hash(scenario)
    comparison = compare(scenario, POLICY_ORDER)
    assert snapshot_hash(scenario) == before  # comparing never mutates the snapshot
    assert comparison.snapshot_hash == before
    assert [r.result.policy_id for r in comparison.runs] == list(POLICY_ORDER)
    scores = {u.zone_id: u.result.score for u in comparison.urgency}
    assert scores == pytest.approx({"zone-a": 87.5, "zone-b": 62.5, "zone-c": 70.8333}, abs=1e-4)


def test_constrained_stock_gives_equal_totals_but_different_recipients():
    """Total units can tie across policies; what differs is which zones receive them."""
    comparison = compare(load_builtin_scenario("triage-demo-001"), POLICY_ORDER)
    totals = {r.result.policy_id: r.metrics.allocated_units for r in comparison.runs}
    assert set(totals.values()) == {330}
    fcfs, _, aidos, _ = comparison.runs
    assert fcfs.result.allocated("zone-c", "medical_kits") == 0
    assert aidos.result.allocated("zone-c", "medical_kits") == 15
    assert aidos.metrics.urgency_weighted_coverage > fcfs.metrics.urgency_weighted_coverage


def test_metrics_reconcile_with_cells():
    for run in compare(load_builtin_scenario("coastal-storm-005"), POLICY_ORDER).runs:
        m, cells = run.metrics, run.result.cells
        assert m.allocated_units == sum(c.allocated for c in cells)
        assert m.unmet_units == sum(c.unmet for c in cells)
        for rid, used in m.allocated_by_resource.items():
            assert used == sum(c.allocated for c in cells if c.resource_id == rid)
            assert m.remaining_by_resource[rid] >= 0


def test_zero_demand_metrics_are_none_not_numbers(make_scenario):
    scenario = make_scenario({"kits": 0}, [("a", 1, (5, 5, 5), {})])
    for run in compare(scenario, POLICY_ORDER).runs:
        m = run.metrics
        assert m.unit_coverage is None
        assert m.urgency_weighted_coverage is None
        assert m.stock_utilization is None
        assert m.jain_fairness is None


def test_comparison_is_reproducible():
    scenario = generate_scenario(5, "severe")
    a, b = compare(scenario, POLICY_ORDER), compare(scenario, POLICY_ORDER)
    for x, y in zip(a.runs, b.runs, strict=True):
        assert x.result.cells == y.result.cells
        assert x.result.status == y.result.status


# ---------------------------------------------------------------- randomized invariants


@pytest.mark.parametrize("scarcity", ["none", "mild", "severe", "zero"])
@pytest.mark.parametrize("seed", range(6))
def test_no_policy_ever_violates_a_hard_constraint(seed, scarcity):
    scenario = generate_scenario(1000 + seed, scarcity)
    comparison = compare(scenario, POLICY_ORDER)
    for run in comparison.runs:
        assert run.result.has_plan
        assert run.validation.valid, (seed, scarcity, run.result.policy_id)
        for cell in run.result.cells:
            assert isinstance(cell.allocated, int) and 0 <= cell.allocated <= cell.requested
        if run.result.policy_id is PolicyId.AIDOS:
            # Linear objective + shared tie-break: the optimum is the urgency-greedy plan.
            greedy = next(r for r in comparison.runs if r.result.policy_id is PolicyId.GREEDY)
            assert {(c.zone_id, c.resource_id): c.allocated for c in run.result.cells} == {
                (c.zone_id, c.resource_id): c.allocated for c in greedy.result.cells
            }
        if run.result.policy_id in (PolicyId.AIDOS, PolicyId.AIDOS_BALANCED):
            assert run.result.status is PolicyStatus.OPTIMAL
            idle = next(c for c in run.validation.checks if c.name == "no_idle_stock")
            assert idle.passed


def test_generator_is_seeded():
    assert generate_scenario(3, "mild") == generate_scenario(3, "mild")
    assert generate_scenario(3, "mild") != generate_scenario(4, "mild")
    assert all(v == 0 for v in generate_scenario(3, "zero").stock.values())


# ---------------------------------------------------------------- experiment interface


def test_runner_records_config_versions_and_metrics(tmp_path):
    scenarios = [load_builtin_scenario("triage-demo-001"), generate_scenario(9, "severe")]
    records = run_experiment(scenarios)
    assert len(records) == 2 * len(POLICY_ORDER)
    first = records[0]
    assert first.engine_version and first.fuzzy_version == "1.0" and first.ortools_version
    assert first.config["workers"] == 1
    assert all(r.valid for r in records)

    write_json(records, tmp_path / "r.json", {"run": "test"})
    payload = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert payload["manifest"] == {"run": "test"} and len(payload["records"]) == 8

    write_csv(records, tmp_path / "r.csv")
    rows = list(csv.DictReader((tmp_path / "r.csv").open(encoding="utf-8")))
    assert len(rows) == 8 and rows[0]["policy_id"] == "fcfs"
    assert to_rows(records)[0]["allocated_units"] == 330
