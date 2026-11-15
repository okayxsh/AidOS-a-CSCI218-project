"""CP-SAT allocation model (spec Sections 5.2 and 11): constraints, objective, statuses."""

import itertools

import pytest
from ortools.sat.python import cp_model

from aidos.ai.baseline_greedy import allocate_greedy
from aidos.ai.constraints import (
    AidosConfig,
    AllocationConfigError,
    allocate_aidos,
    coefficients,
)
from aidos.ai.fuzzy import evaluate
from aidos.ai.policies import Limit, PolicyId, PolicyStatus
from aidos.domain.snapshots import load_builtin_scenario
from aidos.evaluation.invariants import validate_allocation


def scores_of(scenario):
    return {
        z.id: evaluate(
            {
                "severity": z.severity,
                "time_criticality": z.time_criticality,
                "vulnerability": z.vulnerability,
            }
        ).score
        for z in scenario.zones
    }


def grid(result):
    return {(c.zone_id, c.resource_id): c.allocated for c in result.cells}


def objective_of(scenario, urgency, allocation, config=None):
    coef = coefficients(scenario, urgency, config or AidosConfig())
    return sum(coef[z][r] * units for (z, r), units in allocation.items())


# ---------------------------------------------------------------- hand-solvable cases


def test_small_case_matches_the_hand_solution(make_scenario):
    """Stock 10, both zones ask for 8. Urgency 80 vs 40: the urgent zone gets 8, the other 2.

    Coefficients are (urgency + epsilon) * 10,000: 810,000 and 410,000.
    Objective = 8 * 810,000 + 2 * 410,000 = 7,300,000.
    """
    scenario = make_scenario(
        {"kits": 10}, [("a", 1, (5, 5, 5), {"kits": 8}), ("b", 2, (5, 5, 5), {"kits": 8})]
    )
    result = allocate_aidos(scenario, {"a": 80.0, "b": 40.0})
    assert result.status is PolicyStatus.OPTIMAL
    assert grid(result) == {("a", "kits"): 8, ("b", "kits"): 2}
    assert result.solver.objective_value == 7_300_000
    assert [p.status for p in result.solver.phases] == ["OPTIMAL", "OPTIMAL"]


def test_later_arrival_with_higher_urgency_is_served_first(make_scenario):
    scenario = make_scenario(
        {"kits": 10}, [("a", 1, (5, 5, 5), {"kits": 10}), ("b", 2, (5, 5, 5), {"kits": 10})]
    )
    result = allocate_aidos(scenario, {"a": 30.0, "b": 70.0})
    assert grid(result) == {("a", "kits"): 0, ("b", "kits"): 10}
    assert result.zone_order == ("b", "a")


def test_equal_priorities_break_ties_by_arrival_deterministically(make_scenario):
    scenario = make_scenario(
        {"kits": 5}, [("b", 2, (5, 5, 5), {"kits": 4}), ("a", 1, (5, 5, 5), {"kits": 4})]
    )
    results = [allocate_aidos(scenario, {"a": 50.0, "b": 50.0}) for _ in range(5)]
    assert all(grid(r) == {("a", "kits"): 4, ("b", "kits"): 1} for r in results)
    assert "tie-break favours earlier arrival" in next(
        c.reason for c in results[0].cells if c.zone_id == "b"
    )


def test_highly_unequal_priorities_can_starve_the_low_zone(make_scenario):
    """A documented property of the urgency-first objective (balanced mode addresses it)."""
    scenario = make_scenario(
        {"kits": 10}, [("a", 1, (5, 5, 5), {"kits": 10}), ("b", 2, (5, 5, 5), {"kits": 10})]
    )
    urgency_first = allocate_aidos(scenario, {"a": 87.5, "b": 12.5})
    assert grid(urgency_first)[("b", "kits")] == 0
    balanced = allocate_aidos(scenario, {"a": 87.5, "b": 12.5}, objective="balanced")
    assert grid(balanced)[("b", "kits")] >= 3  # ceil(0.25 * 10)


# ---------------------------------------------------------------- edge cases


def test_zero_stock_returns_zero_allocations_and_reports_optimal():
    scenario = load_builtin_scenario("zero-stock")
    result = allocate_aidos(scenario, scores_of(scenario))
    assert result.status is PolicyStatus.OPTIMAL
    assert all(c.allocated == 0 and c.limit is Limit.ZERO_STOCK for c in result.cells)
    assert result.solver.variables == 0


def test_zero_total_demand(make_scenario):
    scenario = make_scenario({"kits": 10}, [("a", 1, (5, 5, 5), {})])
    result = allocate_aidos(scenario, {"a": 50.0})
    assert result.status is PolicyStatus.OPTIMAL
    assert [(c.allocated, c.limit) for c in result.cells] == [(0, Limit.NO_DEMAND)]


def test_stock_exceeding_demand_meets_every_request():
    scenario = load_builtin_scenario("no-scarcity")
    result = allocate_aidos(scenario, scores_of(scenario))
    assert all(c.allocated == c.requested for c in result.cells)


def test_single_zone_single_resource(make_scenario):
    scenario = make_scenario({"kits": 7}, [("a", 1, (9, 9, 9), {"kits": 12})])
    result = allocate_aidos(scenario, {"a": 87.5})
    (cell,) = result.cells
    assert (cell.allocated, cell.unmet, cell.limit) == (7, 5, Limit.STOCK_EXHAUSTED)
    assert "highest urgency" in cell.reason


def test_resources_never_substitute(make_scenario):
    """Surplus water cannot cover missing medical kits."""
    scenario = make_scenario(
        {"medical": 5, "water": 500},
        [
            ("a", 1, (9, 9, 9), {"medical": 20, "water": 10}),
            ("b", 2, (2, 2, 2), {"medical": 20, "water": 10}),
        ],
    )
    result = allocate_aidos(scenario, {"a": 87.5, "b": 12.5})
    assert sum(c.allocated for c in result.cells if c.resource_id == "medical") == 5
    assert all(c.allocated == 10 for c in result.cells if c.resource_id == "water")


def test_all_zones_compete_for_one_scarce_resource():
    scenario = load_builtin_scenario("late-critical-arrival")
    result = allocate_aidos(scenario, scores_of(scenario))
    assert validate_allocation(scenario, result).valid
    medical = grid(result)
    assert medical[("zone-d", "medical_kits")] == 60  # the critical late arrival is met first


def test_large_demand_values_do_not_overflow(make_scenario):
    big = 1_000_000
    scenario = make_scenario(
        {"kits": big}, [("a", 1, (9, 9, 9), {"kits": big}), ("b", 2, (5, 5, 5), {"kits": big})]
    )
    result = allocate_aidos(
        scenario, {"a": 87.5, "b": 50.0}, AidosConfig(resource_weights={"kits": 100})
    )
    assert result.status is PolicyStatus.OPTIMAL
    assert grid(result) == {("a", "kits"): big, ("b", "kits"): 0}


def test_inactive_zones_receive_no_cells(make_scenario):
    scenario = make_scenario(
        {"kits": 10}, [("a", 1, (5, 5, 5), {"kits": 4}), ("b", 2, (9, 9, 9), {"kits": 4}, 1)]
    )
    result = allocate_aidos(scenario, {"a": 50.0, "b": 87.5})
    assert {c.zone_id for c in result.cells} == {"a"}


# ---------------------------------------------------------------- objective correctness


def brute_force_best(scenario, urgency):
    """Exhaustive optimum of the urgency objective over every feasible integer plan."""
    zones = [z for z in scenario.active_zones()]
    keys = [(z.id, r) for z in zones for r in scenario.resource_ids()]
    ranges = [range(scenario.demand_of(z, r) + 1) for z in zones for r in scenario.resource_ids()]
    best = 0
    for values in itertools.product(*ranges):
        plan = dict(zip(keys, values, strict=True))
        if all(
            sum(plan[(z.id, r)] for z in zones) <= scenario.stock[r]
            for r in scenario.resource_ids()
        ):
            best = max(best, objective_of(scenario, urgency, plan))
    return best


@pytest.mark.parametrize("seed", range(8))
def test_objective_equals_exhaustive_optimum_on_small_instances(make_scenario, seed):
    import random

    rng = random.Random(seed)
    zones = [
        (f"z{i}", i + 1, (5, 5, 5), {"r1": rng.randint(0, 4), "r2": rng.randint(0, 3)})
        for i in range(3)
    ]
    scenario = make_scenario({"r1": rng.randint(0, 6), "r2": rng.randint(0, 4)}, zones)
    urgency = {f"z{i}": rng.choice([12.5, 37.5, 50.0, 62.5, 87.5]) for i in range(3)}
    result = allocate_aidos(scenario, urgency)
    assert result.status is PolicyStatus.OPTIMAL
    assert objective_of(scenario, urgency, grid(result)) == brute_force_best(scenario, urgency)
    assert result.solver.objective_value == brute_force_best(scenario, urgency)


def test_scores_that_differ_in_the_fourth_decimal_get_different_coefficients(make_scenario):
    """The coefficient scale matches the score's resolution, so no real difference is lost."""
    scenario = make_scenario(
        {"kits": 5}, [("a", 1, (5, 5, 5), {"kits": 5}), ("b", 2, (5, 5, 5), {"kits": 5})]
    )
    result = allocate_aidos(scenario, {"a": 62.5, "b": 62.5001})
    assert grid(result) == {("a", "kits"): 0, ("b", "kits"): 5}


def test_explanation_names_only_zones_that_compete_for_the_resource(make_scenario):
    scenario = make_scenario(
        {"kits": 4, "water": 9},
        [
            ("a", 1, (5, 5, 5), {"kits": 4}),
            ("b", 2, (5, 5, 5), {"water": 9}),  # more urgent, but does not want kits
            ("c", 3, (5, 5, 5), {"kits": 4}),
        ],
    )
    result = allocate_aidos(scenario, {"a": 60.0, "b": 80.0, "c": 40.0})
    reason = next(c.reason for c in result.cells if (c.zone_id, c.resource_id) == ("c", "kits"))
    assert "(a) received 4 units" in reason and "b" not in reason.split("(")[2]


def test_urgency_first_matches_greedy_on_the_fixtures():
    """The spec's experimental control: with a linear objective the optimum is the greedy plan."""
    for sid in ("triage-demo-001", "late-critical-arrival", "coastal-storm-005"):
        scenario = load_builtin_scenario(sid)
        urgency = scores_of(scenario)
        assert grid(allocate_aidos(scenario, urgency)) == grid(allocate_greedy(scenario, urgency))


# ---------------------------------------------------------------- balanced mode


def test_balanced_floor_is_met_and_costs_some_urgency_objective():
    scenario = load_builtin_scenario("triage-demo-001")
    urgency = scores_of(scenario)
    first = allocate_aidos(scenario, urgency)
    balanced = allocate_aidos(scenario, urgency, objective="balanced")
    assert balanced.policy_id is PolicyId.AIDOS_BALANCED
    assert balanced.status is PolicyStatus.OPTIMAL
    assert dict(balanced.solver.coverage_floor) == {
        "medical_kits": 0.25,
        "water_packs": 0.25,
        "shelter_kits": 0.25,
    }
    for cell in balanced.cells:
        if cell.requested:
            assert cell.allocated * 4 >= cell.requested  # >= 25 % of each request
    assert balanced.solver.objective_value <= first.solver.objective_value
    assert [p.name for p in balanced.solver.phases] == ["coverage_floor", "urgency", "tie_break"]


def test_balanced_floor_shrinks_to_what_stock_allows(make_scenario):
    """Target 25 %, but 3 units across two requests of 10 only allow 10 % (1 unit each)."""
    scenario = make_scenario(
        {"kits": 3}, [("a", 1, (5, 5, 5), {"kits": 10}), ("b", 2, (5, 5, 5), {"kits": 10})]
    )
    result = allocate_aidos(scenario, {"a": 80.0, "b": 20.0}, objective="balanced")
    floor = result.solver.coverage_floor["kits"]
    assert 0.1 <= floor < 0.25
    assert grid(result)[("b", "kits")] >= 1
    assert validate_allocation(scenario, result).valid


# ---------------------------------------------------------------- statuses and failures


def _patch_status(monkeypatch, statuses):
    """Run the real solve, then report the given statuses in order (to exercise handling)."""
    original = cp_model.CpSolver.solve
    queue = list(statuses)

    def fake(self, model, *args, **kwargs):
        real = original(self, model, *args, **kwargs)
        return queue.pop(0) if queue else real

    monkeypatch.setattr(cp_model.CpSolver, "solve", fake)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (cp_model.UNKNOWN, PolicyStatus.UNKNOWN),
        (cp_model.INFEASIBLE, PolicyStatus.INFEASIBLE),
        (cp_model.MODEL_INVALID, PolicyStatus.MODEL_INVALID),
    ],
)
def test_failed_first_phase_returns_no_invented_plan(monkeypatch, raw, expected):
    _patch_status(monkeypatch, [raw])
    scenario = load_builtin_scenario("triage-demo-001")
    result = allocate_aidos(scenario, scores_of(scenario))
    assert result.status is expected
    assert not result.has_plan
    assert result.cells == ()
    assert "no allocation is shown" in result.message
    assert not validate_allocation(scenario, result).applicable


def test_a_later_phase_stopping_early_downgrades_to_feasible(monkeypatch):
    _patch_status(monkeypatch, [cp_model.OPTIMAL, cp_model.UNKNOWN])
    scenario = load_builtin_scenario("triage-demo-001")
    result = allocate_aidos(scenario, scores_of(scenario))
    assert result.status is PolicyStatus.FEASIBLE
    assert result.has_plan
    assert validate_allocation(scenario, result).valid
    assert "not proven optimal" in result.message


def test_solver_configuration_is_deterministic_and_bounded():
    scenario = load_builtin_scenario("coastal-storm-005")
    urgency = scores_of(scenario)
    runs = [allocate_aidos(scenario, urgency) for _ in range(3)]
    assert all(grid(r) == grid(runs[0]) for r in runs)
    params = runs[0].solver.parameters
    assert params["num_workers"] == 1 and params["max_time_in_seconds"] == 5.0


@pytest.mark.parametrize(
    "config",
    [
        AidosConfig(epsilon=0),
        AidosConfig(min_coverage=1.5),
        AidosConfig(time_limit_s=0),
        AidosConfig(resource_weights={"fuel": 2}),
        AidosConfig(resource_weights={"medical_kits": 0}),
        AidosConfig(resource_weights={"medical_kits": 1.5}),
    ],
)
def test_invalid_configuration_is_rejected(config):
    scenario = load_builtin_scenario("triage-demo-001")
    with pytest.raises(AllocationConfigError):
        allocate_aidos(scenario, scores_of(scenario), config)


def test_resource_weights_scale_coefficients_only_within_their_resource():
    scenario = load_builtin_scenario("triage-demo-001")
    coef = coefficients(
        scenario, scores_of(scenario), AidosConfig(resource_weights={"water_packs": 3})
    )
    assert coef["zone-a"]["water_packs"] == 3 * coef["zone-a"]["medical_kits"]
    assert coef["zone-a"]["medical_kits"] == 875_000 + 10_000
