"""Stage 5: edge cases found in the audit, greedy/CP-SAT equivalence, supplementary tooling."""

import math
import random
from datetime import UTC, datetime

import pytest

from aidos.ai.baseline_greedy import allocate_greedy
from aidos.ai.constraints import AidosConfig, allocate_aidos
from aidos.ai.policies import PolicyId
from aidos.domain.snapshots import load_builtin_scenario
from aidos.domain.validation import ScenarioValidationError, parse_scenario
from aidos.evaluation import dynamic_controlled as dc
from aidos.evaluation import supplementary as sup
from aidos.evaluation.families import generate
from aidos.pipeline import POLICY_ORDER, assess_urgency, compare
from aidos.simulation import session as S
from aidos.simulation.events import SupplyArrived
from aidos.simulation.fsm import Action
from aidos.simulation.reducer import EventRejectedError


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_non_finite_ratings_are_rejected(bad):
    raw = load_builtin_scenario("triage-demo-001").model_dump(mode="json")
    raw["zones"][0]["severity"] = bad
    with pytest.raises(ScenarioValidationError):
        parse_scenario(raw)


def test_stock_cannot_exceed_the_unit_limit_through_arrivals():
    session = S.control(
        S.create_session(load_builtin_scenario("triage-demo-001"), "s"), Action.START
    )
    with pytest.raises(EventRejectedError) as caught:
        S.apply(session, SupplyArrived(resource_id="medical_kits", quantity=1_000_000))
    assert caught.value.code == "invalid_result"
    assert any("stock.medical_kits" in d["path"] for d in caught.value.details)
    assert session.event_count == 0


def test_largest_accepted_input_is_solved_validly_within_the_limit():
    """50 zones x 10 resources at the 1,000,000-unit cap: the worst case the API accepts."""
    big = parse_scenario(
        {
            "schema_version": "1.0",
            "scenario_id": "big",
            "title": "big",
            "seed": 1,
            "synthetic": True,
            "resources": [{"id": f"r{i}", "label": "r", "unit": "u"} for i in range(10)],
            "stock": {f"r{i}": 1_000_000 for i in range(10)},
            "zones": [
                {
                    "id": f"z{j}",
                    "name": "z",
                    "arrival_order": j + 1,
                    "severity": j % 11,
                    "vulnerability": 5,
                    "time_criticality": 7,
                    "demand": {f"r{i}": 1_000_000 for i in range(10)},
                }
                for j in range(50)
            ],
        }
    )
    for run in compare(big, POLICY_ORDER).runs:
        assert run.validation.valid
        assert run.result.status.value in ("COMPLETE", "OPTIMAL", "FEASIBLE")


@pytest.mark.parametrize("seed", range(6))
def test_cp_sat_equals_greedy_for_any_positive_weights_and_epsilon(seed):
    """The equivalence holds for every per-resource weight and epsilon (it only needs the
    coefficient order within each resource, which those cannot change)."""
    rng = random.Random(seed)
    scenario = generate("C", 4000 + seed)
    urgency = {u.zone_id: u.result.score for u in assess_urgency(scenario)}
    config = AidosConfig(
        epsilon=rng.choice([0.01, 1.0, 50.0]),
        resource_weights={r: rng.randint(1, 100) for r in scenario.resource_ids()},
    )
    a = {
        (c.zone_id, c.resource_id): c.allocated
        for c in allocate_aidos(scenario, urgency, config).cells
    }
    g = {(c.zone_id, c.resource_id): c.allocated for c in allocate_greedy(scenario, urgency).cells}
    assert a == g


def test_any_order_preserving_change_of_scores_leaves_aidos_unchanged():
    scenario = generate("B", 4100)
    urgency = {u.zone_id: u.result.score for u in assess_urgency(scenario)}
    stretched = {z: round(10 + 0.5 * s, 4) for z, s in urgency.items()}  # strictly increasing map

    def plan(scores):
        return {
            (c.zone_id, c.resource_id): c.allocated for c in allocate_aidos(scenario, scores).cells
        }

    assert plan(urgency) == plan(stretched)


def test_supplementary_runs_never_overwrite(tmp_path):
    stamp = datetime(2026, 1, 1, tzinfo=UTC)
    sup.new_run_dir(tmp_path, "x", stamp)
    with pytest.raises(FileExistsError):
        sup.new_run_dir(tmp_path, "x", stamp)


@pytest.mark.parametrize("level", list(dc.LEVELS))
def test_controlled_new_zone_ratings_follow_the_level(level):
    _, actions = dc.dispatch_script(level, 5, 0)
    added = next(a for a in actions if getattr(a, "type", None) == "zone_added")
    low, high = dc.LEVELS[level]
    for value in (added.zone.severity, added.zone.vulnerability, added.zone.time_criticality):
        assert low <= value <= high


def test_controlled_dispatch_is_identical_input_and_conserves_inventory():
    rows = [dc.dispatch("random", 3, 1, policy) for policy in PolicyId]
    assert len({r["exogenous_script_hash"] for r in rows}) == 1
    assert all(r["inventory_conserved"] == 1 and r["double_dispatch_blocked"] == 1 for r in rows)
    assert all(r["rejected_events"] == 0 for r in rows)


def test_controlled_recommendation_is_deterministic_and_valid():
    def strip(rows):
        return [dict(r) for r in rows]

    first, second = dc.recommendation("moderate", 5, 2), dc.recommendation("moderate", 5, 2)
    assert strip(first) == strip(second)
    assert all(r["valid"] == 1 for r in first)
