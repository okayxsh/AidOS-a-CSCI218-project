"""Simulation engine: events, inventory semantics, atomicity, replay (spec Section 5.3)."""

import copy
import dataclasses
import json
import random
import threading
from pathlib import Path

import pytest
from ortools.sat.python import cp_model

import aidos.pipeline as pipeline
from aidos.ai.policies import PolicyId
from aidos.domain.snapshots import load_builtin_scenario, snapshot_hash
from aidos.evaluation.invariants import ValidationReport, Violation
from aidos.simulation import session as S
from aidos.simulation.compare import diff_steps
from aidos.simulation.events import (
    NewZone,
    PlanCommitted,
    RequestUpdated,
    SupplyArrived,
    SupplyLost,
    TimeAdvanced,
    UrgencyChanged,
    ZoneAdded,
    ZoneResolved,
)
from aidos.simulation.fsm import Action, InvalidTransitionError, SimState
from aidos.simulation.reducer import EventRejectedError
from aidos.simulation.store import SessionNotFoundError, SessionStore, VersionConflictError

DEMO_SCRIPT = Path(__file__).resolve().parents[2] / "data" / "simulations"


def started(scenario_id="triage-demo-001", **config):
    session = S.create_session(load_builtin_scenario(scenario_id), "sim-test", **config)
    return S.control(session, Action.START)


def plan(step, policy=PolicyId.AIDOS):
    return {(c.zone_id, c.resource_id): c.allocated for c in step.run(policy).result.cells}


def score(step, zone_id):
    return next(u.result.score for u in step.comparison.urgency if u.zone_id == zone_id)


ZONE_D = NewZone(
    id="zone-d",
    name="Zone D · Riverside clinic",
    severity=8,
    vulnerability=9,
    time_criticality=9,
    demand={"medical_kits": 40, "water_packs": 50, "shelter_kits": 10},
)
DEMO_EVENTS = [
    UrgencyChanged(zone_id="zone-b", severity=9),
    ZoneAdded(zone=ZONE_D),
    SupplyLost(resource_id="medical_kits", quantity=30),
]


# ---------------------------------------------------------------- lifecycle


def test_new_session_is_ready_with_a_scored_and_allocated_step_zero():
    session = S.create_session(load_builtin_scenario("triage-demo-001"), "s1")
    assert session.state is SimState.READY and session.version == 1
    assert session.event_count == 0
    assert session.current.run(PolicyId.AIDOS).result.status == "OPTIMAL"
    with pytest.raises(InvalidTransitionError):
        S.apply(session, SupplyArrived(resource_id="medical_kits", quantity=1))


def test_pause_blocks_events_and_resume_allows_them():
    paused = S.control(started(), Action.PAUSE)
    with pytest.raises(InvalidTransitionError):
        S.apply(paused, SupplyArrived(resource_id="medical_kits", quantity=1))
    resumed = S.control(paused, Action.RESUME)
    assert S.apply(resumed, SupplyArrived(resource_id="medical_kits", quantity=1)).event_count == 1


def test_complete_is_read_only_until_reset():
    done = S.control(S.apply(started(), DEMO_EVENTS[0]), Action.COMPLETE)
    assert done.state is SimState.COMPLETED
    with pytest.raises(InvalidTransitionError):
        S.apply(done, DEMO_EVENTS[1])
    reset = S.control(done, Action.RESET)
    assert reset.state is SimState.READY and reset.event_count == 0


def test_reset_restores_the_initial_snapshot_and_clears_everything():
    session = started()
    initial = session.current
    session = S.apply(session, DEMO_EVENTS[0])
    session = S.apply(session, PlanCommitted(expected_snapshot_hash=session.current.snapshot_hash))
    assert session.ledger
    reset = S.control(session, Action.RESET)
    assert reset.steps == (initial,)
    assert reset.ledger == () and reset.retired == () and reset.error is None
    assert reset.current.snapshot_hash == initial.snapshot_hash
    assert plan(reset.current) == plan(initial)


def test_versions_increase_on_every_change():
    session = started()
    versions = [session.version]
    for event in DEMO_EVENTS:
        session = S.apply(session, event)
        versions.append(session.version)
    assert versions == sorted(set(versions))


# ---------------------------------------------------------------- events


def test_severity_escalation_rescores_and_reallocates():
    session = S.apply(started(), UrgencyChanged(zone_id="zone-b", severity=9))
    before, after = session.steps
    assert score(before, "zone-b") == 62.5
    assert score(after, "zone-b") > score(after, "zone-c")  # B now outranks C
    assert plan(before)[("zone-b", "medical_kits")] == 0
    assert plan(after)[("zone-b", "medical_kits")] == 15
    assert plan(after)[("zone-c", "medical_kits")] == 0
    assert plan(before, PolicyId.FCFS) == plan(after, PolicyId.FCFS)  # FCFS ignores urgency
    diff = diff_steps(session, 0, 1)
    assert diff.recommendation_changed
    assert any(
        "FCFS on the same state did not change: it ignores urgency" in s for s in diff.explanation
    )


def test_new_zone_arrives_last_and_is_active_now():
    session = S.apply(started(), ZoneAdded(zone=ZONE_D))
    zone = next(z for z in session.current.scenario.zones if z.id == "zone-d")
    assert zone.arrival_order == 4 and zone.activation_step == 0
    assert zone in session.current.scenario.active_zones()
    assert plan(session.current)[("zone-d", "medical_kits")] == 15  # critical: served after A
    with pytest.raises(EventRejectedError, match="already in use"):
        S.apply(session, ZoneAdded(zone=ZONE_D))


def test_new_zone_with_an_unknown_resource_is_rejected():
    bad = ZONE_D.model_copy(update={"demand": {"fuel": 3}})
    with pytest.raises(EventRejectedError) as caught:
        S.apply(started(), ZoneAdded(zone=bad))
    assert caught.value.code == "unknown_resource"


def test_supply_arrival_raises_stock_and_reduces_unmet():
    session = S.apply(started(), SupplyArrived(resource_id="medical_kits", quantity=60))
    before, after = session.steps
    assert after.scenario.stock["medical_kits"] == 150
    assert after.run(PolicyId.AIDOS).metrics.unmet_units == (
        before.run(PolicyId.AIDOS).metrics.unmet_units - 60
    )


def test_supply_loss_cannot_make_stock_negative():
    session = started()
    with pytest.raises(EventRejectedError) as caught:
        S.apply(session, SupplyLost(resource_id="medical_kits", quantity=91))
    assert caught.value.code == "insufficient_stock"
    emptied = S.apply(session, SupplyLost(resource_id="medical_kits", quantity=90))
    assert emptied.current.scenario.stock["medical_kits"] == 0
    assert all(v == 0 for (z, r), v in plan(emptied.current).items() if r == "medical_kits")


def test_request_update_changes_demand_and_rejects_no_ops():
    session = S.apply(
        started(), RequestUpdated(zone_id="zone-c", resource_id="water_packs", quantity=90)
    )
    zone_c = next(z for z in session.current.scenario.zones if z.id == "zone-c")
    assert zone_c.demand["water_packs"] == 90
    with pytest.raises(EventRejectedError) as caught:
        S.apply(session, RequestUpdated(zone_id="zone-c", resource_id="water_packs", quantity=90))
    assert caught.value.code == "no_change"


def test_zone_resolution_drops_open_demand_without_returning_dispatched_stock():
    session = started()
    session = S.apply(session, PlanCommitted(expected_snapshot_hash=session.current.snapshot_hash))
    stock_after_dispatch = dict(session.current.scenario.stock)
    session = S.apply(session, ZoneResolved(zone_id="zone-b"))
    assert "zone-b" not in {z.id for z in session.current.scenario.zones}
    assert dict(session.current.scenario.stock) == stock_after_dispatch  # nothing returned
    assert session.retired[0].zone_id == "zone-b"
    with pytest.raises(EventRejectedError, match="already in use"):  # ids are never reused
        S.apply(session, ZoneAdded(zone=ZONE_D.model_copy(update={"id": "zone-b"})))


def test_the_last_zone_cannot_be_resolved():
    session = started()
    session = S.apply(session, ZoneResolved(zone_id="zone-a"))
    session = S.apply(session, ZoneResolved(zone_id="zone-b"))
    with pytest.raises(EventRejectedError) as caught:
        S.apply(session, ZoneResolved(zone_id="zone-c"))
    assert caught.value.code == "last_zone"


def test_unknown_zone_and_resource_are_rejected():
    session = started()
    with pytest.raises(EventRejectedError) as caught:
        S.apply(session, UrgencyChanged(zone_id="zone-z", severity=5))
    assert caught.value.code == "unknown_zone"
    with pytest.raises(EventRejectedError) as caught:
        S.apply(session, SupplyArrived(resource_id="fuel", quantity=5))
    assert caught.value.code == "unknown_resource"


def test_rating_no_op_is_rejected():
    with pytest.raises(EventRejectedError) as caught:
        S.apply(started(), UrgencyChanged(zone_id="zone-a", severity=9))  # already 9
    assert caught.value.code == "no_change"


def test_time_advance_activates_scheduled_zones():
    session = started("competing-emergency-009")
    assert "zone-d" not in {z.id for z in session.current.scenario.active_zones()}
    session = S.apply(session, TimeAdvanced())
    assert session.current.scenario.step == 1
    assert "zone-d" in {z.id for z in session.current.scenario.active_zones()}
    assert any("became active (scheduled for step 1)" in c for c in session.current.changes)
    assert plan(session.current)[("zone-d", "medical_kits")] == 45
    # FCFS serves by arrival: the critical newcomer gets only what is left (nothing).
    assert plan(session.current, PolicyId.FCFS)[("zone-d", "medical_kits")] == 0


def test_other_events_do_not_move_the_clock():
    session = S.apply(
        started("competing-emergency-009"), SupplyArrived(resource_id="water_packs", quantity=5)
    )
    assert session.current.scenario.step == 0
    assert "zone-d" not in {z.id for z in session.current.scenario.active_zones()}


def test_repeated_events_accumulate_exactly():
    session = started()
    for _ in range(3):
        session = S.apply(session, SupplyArrived(resource_id="shelter_kits", quantity=10))
    assert session.current.scenario.stock["shelter_kits"] == 90
    assert session.event_count == 3


# ---------------------------------------------------------------- inventory semantics


def test_recommendations_never_consume_inventory():
    session = started()
    stock = dict(session.current.scenario.stock)
    demand = {z.id: dict(z.demand) for z in session.current.scenario.zones}
    for _ in range(3):  # re-evaluating the same state never changes it
        again = S.evaluate_step(0, session.current.scenario, session.config)
        assert plan(again) == plan(session.current)
        assert again.outcome_hash == session.current.outcome_hash
    assert dict(session.current.scenario.stock) == stock
    assert {z.id: dict(z.demand) for z in session.current.scenario.zones} == demand


def test_commit_dispatches_exactly_once():
    session = started()
    before = session.current
    committed = S.apply(session, PlanCommitted(expected_snapshot_hash=before.snapshot_hash))
    dispatched = plan(before)
    assert committed.dispatched_units == sum(dispatched.values()) == 330
    for rid, stock in before.scenario.stock.items():
        used = sum(v for (z, r), v in dispatched.items() if r == rid)
        assert committed.current.scenario.stock[rid] == stock - used
    for zone in committed.current.scenario.zones:
        old = next(z for z in before.scenario.zones if z.id == zone.id)
        for rid, units in old.demand.items():
            assert zone.demand[rid] == units - dispatched[(zone.id, rid)]
    # The same commit again is stale: the snapshot changed when stock left the depot.
    with pytest.raises(EventRejectedError) as caught:
        S.apply(committed, PlanCommitted(expected_snapshot_hash=before.snapshot_hash))
    assert caught.value.code == "stale_plan"
    assert committed.ledger[0].snapshot_hash == before.snapshot_hash


def test_commit_of_an_empty_plan_is_rejected():
    session = started("zero-stock")
    with pytest.raises(EventRejectedError) as caught:
        S.apply(session, PlanCommitted(expected_snapshot_hash=session.current.snapshot_hash))
    assert caught.value.code == "no_change"


def _random_event(kind, rng, session, zones, resources, n):
    if kind == "arrive":
        return SupplyArrived(resource_id=rng.choice(resources), quantity=rng.randint(1, 40))
    if kind == "lose":
        return SupplyLost(resource_id=rng.choice(resources), quantity=rng.randint(1, 40))
    if kind == "request":
        return RequestUpdated(
            zone_id=rng.choice(zones),
            resource_id=rng.choice(resources),
            quantity=rng.randint(0, 80),
        )
    if kind == "rate":
        return UrgencyChanged(zone_id=rng.choice(zones), severity=rng.randint(0, 10))
    if kind == "add":
        return ZoneAdded(zone=ZONE_D.model_copy(update={"id": f"zone-x{n}"}))
    if kind == "commit":
        return PlanCommitted(expected_snapshot_hash=session.current.snapshot_hash)
    return TimeAdvanced()


@pytest.mark.parametrize("seed", range(8))
def test_hard_constraints_hold_after_every_random_event(seed):
    rng = random.Random(seed)
    session = started("severe-shortage-008")
    resources = session.current.scenario.resource_ids()
    applied = 0
    while applied < 12:
        zones = [z.id for z in session.current.scenario.zones]
        kind = rng.choice(["arrive", "lose", "request", "rate", "add", "commit", "tick"])
        event = _random_event(kind, rng, session, zones, resources, applied)
        try:
            session = S.apply(session, event)
        except EventRejectedError:
            continue  # rejected events must leave the session as it was (checked below)
        applied += 1
        step = session.current
        for run in step.comparison.runs:
            assert run.validation.valid, (seed, kind, run.result.policy_id)
            for cell in run.result.cells:
                assert isinstance(cell.allocated, int) and 0 <= cell.allocated <= cell.requested
        assert all(v >= 0 for v in step.scenario.stock.values())


# ---------------------------------------------------------------- atomicity and failures


def test_rejected_event_leaves_the_session_identical():
    session = S.apply(started(), DEMO_EVENTS[0])
    snapshot = copy.deepcopy(session)
    with pytest.raises(EventRejectedError):
        S.apply(session, SupplyLost(resource_id="medical_kits", quantity=10_000))
    assert session == snapshot


def test_solver_failure_rejects_the_event_and_keeps_the_session(monkeypatch):
    session = started()
    original = cp_model.CpSolver.solve

    def unknown(self, model, *args, **kwargs):
        original(self, model, *args, **kwargs)
        return cp_model.UNKNOWN

    monkeypatch.setattr(cp_model.CpSolver, "solve", unknown)
    with pytest.raises(S.SolverFailedError):
        S.apply(session, DEMO_EVENTS[0])
    monkeypatch.undo()
    assert session.event_count == 0 and session.state is SimState.ACTIVE


def test_invariant_breach_moves_to_error_without_applying_the_event(monkeypatch):
    session = started()
    broken = ValidationReport(True, (), (Violation("above_stock", None, "medical_kits", "forced"),))
    monkeypatch.setattr(pipeline, "validate_allocation", lambda scenario, result: broken)
    with pytest.raises(S.InvariantBreachError) as caught:
        S.apply(session, DEMO_EVENTS[0])
    failed = caught.value.session
    assert failed.state is SimState.ERROR and failed.event_count == 0
    assert "forced" in failed.error
    with pytest.raises(InvalidTransitionError):
        S.apply(failed, DEMO_EVENTS[0])
    monkeypatch.undo()
    assert S.control(failed, Action.RESET).state is SimState.READY


# ---------------------------------------------------------------- replay and export


def test_replay_reproduces_every_logical_outcome():
    original = started()
    for event in DEMO_EVENTS:
        original = S.apply(original, event)
    replayed = S.replay(original, DEMO_EVENTS)
    assert [s.outcome_hash for s in replayed.steps] == [s.outcome_hash for s in original.steps]
    assert [s.event_id for s in replayed.steps] == [s.event_id for s in original.steps]
    assert replayed.state is SimState.ACTIVE


def test_replay_is_all_or_nothing_and_keeps_order():
    session = S.apply(started(), DEMO_EVENTS[0])
    bad = [DEMO_EVENTS[1], SupplyLost(resource_id="medical_kits", quantity=10_000)]
    with pytest.raises(S.ReplayError) as caught:
        S.replay(session, bad)
    assert caught.value.index == 1
    assert session.event_count == 1  # untouched
    swapped = S.replay(session, [DEMO_EVENTS[2], DEMO_EVENTS[0]])
    straight = S.replay(session, [DEMO_EVENTS[0], DEMO_EVENTS[2]])
    assert [s.event.type for s in swapped.steps[1:]] == ["supply_lost", "urgency_changed"]
    assert swapped.steps[1].outcome_hash != straight.steps[1].outcome_hash


def test_replay_does_not_duplicate_inventory_changes():
    session = S.apply(started(), SupplyArrived(resource_id="water_packs", quantity=20))
    twice = S.replay(
        S.replay(session, [SupplyArrived(resource_id="water_packs", quantity=20)]),
        [SupplyArrived(resource_id="water_packs", quantity=20)],
    )
    assert twice.current.scenario.stock["water_packs"] == 200


def test_export_import_round_trip_verifies_outcomes():
    session = started()
    for event in DEMO_EVENTS:
        session = S.apply(session, event)
    document = json.loads(json.dumps(S.export_session(session)))
    rebuilt, verification = S.import_session(document, "sim-copy")
    assert verification.checked and verification.matches
    assert rebuilt.current.outcome_hash == session.current.outcome_hash


def test_import_detects_a_tampered_outcome_and_rejects_malformed_documents():
    session = S.apply(started(), DEMO_EVENTS[0])
    document = S.export_session(session)
    document["outcomes"][1]["outcome_hash"] = "0" * 64
    _, verification = S.import_session(document, "x")
    assert verification.checked and not verification.matches
    assert verification.first_mismatch_seq == 1

    for mutate in (
        lambda d: d.update(format="other"),
        lambda d: d["initial_scenario"]["stock"].update(medical_kits=1),  # hash mismatch
        lambda d: d["events"][0]["event"].update(type="meteor_strike"),
        lambda d: d["events"][0].update(seq=5),
        lambda d: d.update(events="nope"),
    ):
        bad = copy.deepcopy(S.export_session(session))
        mutate(bad)
        with pytest.raises(S.ReplayError):
            S.import_session(bad, "x")


def test_the_recorded_demo_script_still_reproduces():
    document = json.loads((DEMO_SCRIPT / "triage-demo-escalation.json").read_text("utf-8"))
    session, verification = S.import_session(document, "demo")
    assert verification.matches, verification
    assert session.event_count == 3
    assert document["initial_snapshot_hash"] == snapshot_hash(
        load_builtin_scenario("triage-demo-001")
    )


# ---------------------------------------------------------------- store


def test_store_enforces_versions_and_expiry():
    now = [0.0]
    store = SessionStore(ttl_seconds=10, clock=lambda: now[0])
    session = store.add(S.create_session(load_builtin_scenario("triage-demo-001"), "s1"))
    store.mutate("s1", 1, lambda s: S.control(s, Action.START))
    with pytest.raises(VersionConflictError):
        store.mutate("s1", 1, lambda s: S.control(s, Action.PAUSE))
    assert store.get("s1").state is SimState.ACTIVE
    now[0] = 11
    with pytest.raises(SessionNotFoundError):
        store.get(session.session_id)


def test_store_evicts_the_oldest_idle_session_and_never_stores_into_a_dropped_one():
    now = [0.0]
    store = SessionStore(max_sessions=2, clock=lambda: now[0])
    base = S.create_session(load_builtin_scenario("triage-demo-001"), "a")
    for sid in ("a", "b"):
        now[0] += 1
        store.add(dataclasses.replace(base, session_id=sid))
    now[0] += 1
    store.add(dataclasses.replace(base, session_id="c"))  # evicts "a", the oldest idle
    with pytest.raises(SessionNotFoundError):
        store.get("a")

    def evict_then_change(session):
        store.add(dataclasses.replace(base, session_id="d"))  # evicts "b" mid-change
        return S.control(session, Action.START)

    with pytest.raises(SessionNotFoundError):
        store.mutate("b", 1, evict_then_change)


def test_event_limit(monkeypatch):
    monkeypatch.setattr(S, "MAX_EVENTS", 2)
    session = started()
    session = S.apply(session, SupplyArrived(resource_id="water_packs", quantity=1))
    session = S.apply(session, SupplyArrived(resource_id="water_packs", quantity=1))
    with pytest.raises(EventRejectedError) as caught:
        S.apply(session, SupplyArrived(resource_id="water_packs", quantity=1))
    assert caught.value.code == "too_many_events"


def test_concurrent_changes_with_the_same_version_cannot_both_win():
    store = SessionStore()
    store.add(
        S.control(S.create_session(load_builtin_scenario("triage-demo-001"), "s1"), Action.START)
    )
    results: list[str] = []
    barrier = threading.Barrier(4)

    def worker(quantity):
        barrier.wait()
        try:
            store.mutate(
                "s1",
                2,
                lambda s: S.apply(s, SupplyArrived(resource_id="water_packs", quantity=quantity)),
            )
            results.append("ok")
        except VersionConflictError:
            results.append("conflict")

    threads = [threading.Thread(target=worker, args=(q,)) for q in (1, 2, 3, 4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == ["conflict", "conflict", "conflict", "ok"]
    final = store.get("s1")
    assert final.event_count == 1 and final.version == 3
