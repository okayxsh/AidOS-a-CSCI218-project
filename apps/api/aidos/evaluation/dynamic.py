"""Dynamic (event-driven) experiments on the Stage 3 simulator (family H).

Two modes, never mixed in aggregation:

Recommendation mode (shared state). One session per script. Every step stores all four
policies' plans on the same post-event snapshot, so per-step comparisons are paired. Nothing
is dispatched; stock changes only through supply events.

Dispatch mode (policy-specific trajectories). One session per (script, policy). The same
script is applied to each, and after each event the policy's own plan is committed, so later
states differ between policies. Comparisons are paired by script, not by state.

Scripts are generated from the base scenario and a seed, and contain only events that are
valid whatever was dispatched before them (losses happen before the first dispatch, request
updates only raise requests), so every policy experiences the same script.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from aidos.ai.policies import PolicyId
from aidos.domain.models import Scenario
from aidos.domain.validation import parse_scenario
from aidos.evaluation.families import generate
from aidos.pipeline import POLICY_ORDER
from aidos.simulation import session as S
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
from aidos.simulation.fsm import Action
from aidos.simulation.reducer import EventRejectedError

DYNAMIC_SEED_BASE = 800_000
COMMIT = "commit"


def base_scenario(index: int) -> Scenario:
    """Dynamic scripts start from moderate-scarcity (family B) scenarios with their own seeds."""
    return generate("B", DYNAMIC_SEED_BASE - 200_000 + index)  # seeds 800000+ via family B


def _escalation(scenario: Scenario, rng: random.Random) -> UrgencyChanged:
    candidates = [z for z in scenario.active_zones() if min(z.severity, z.time_criticality) < 10]
    zone = rng.choice(candidates or list(scenario.active_zones()))
    if zone.severity < 10:
        return UrgencyChanged(zone_id=zone.id, severity=10)
    if zone.time_criticality < 10:
        return UrgencyChanged(zone_id=zone.id, time_criticality=10)
    return UrgencyChanged(zone_id=zone.id, vulnerability=max(0.0, zone.vulnerability - 5))


def _new_zone(scenario: Scenario, rng: random.Random, tag: str) -> ZoneAdded:
    return ZoneAdded(
        zone=NewZone(
            id=f"zone-new-{tag}",
            name=f"New zone {tag}",
            severity=rng.randint(6, 10),
            vulnerability=rng.randint(4, 10),
            time_criticality=rng.randint(6, 10),
            demand={rid: rng.randint(10, 60) for rid in scenario.resource_ids()},
        )
    )


# ---------------------------------------------------------------- recommendation mode


def recommendation_run(index: int) -> tuple[Scenario, S.SessionState]:
    """Generate and apply a 7-event script on shared state; return the finished session."""
    scenario = base_scenario(index)
    rng = random.Random(DYNAMIC_SEED_BASE + index)
    session = S.control(S.create_session(scenario, f"rec-{index}"), Action.START)

    def current() -> Scenario:
        return session.current.scenario

    builders = [
        lambda: _escalation(current(), rng),
        lambda: _new_zone(current(), rng, str(index)),
        lambda: _loss(current(), rng),
        lambda: SupplyArrived(
            resource_id=rng.choice(current().resource_ids()), quantity=rng.randint(20, 80)
        ),
        lambda: _increase(current(), rng),
        lambda: TimeAdvanced(),
        lambda: _resolve(current(), rng),
    ]
    for build in builders:
        event = build()
        if event is not None:
            session = S.apply(session, event)
    return scenario, session


def _loss(scenario: Scenario, rng: random.Random) -> SupplyLost | None:
    stocked = [r for r in scenario.resource_ids() if scenario.stock[r] > 0]
    if not stocked:
        return None
    rid = rng.choice(stocked)
    return SupplyLost(resource_id=rid, quantity=max(1, int(scenario.stock[rid] * 0.3)))


def _increase(scenario: Scenario, rng: random.Random) -> RequestUpdated:
    zone = rng.choice(list(scenario.active_zones()))
    rid = rng.choice(scenario.resource_ids())
    return RequestUpdated(
        zone_id=zone.id, resource_id=rid, quantity=zone.demand.get(rid, 0) + rng.randint(10, 40)
    )


def _resolve(scenario: Scenario, rng: random.Random) -> ZoneResolved | None:
    original = [z for z in scenario.zones if not z.id.startswith("zone-new")]
    if len(scenario.zones) < 3 or not original:
        return None
    return ZoneResolved(zone_id=rng.choice(original).id)


def _cells(step: S.StepRecord, policy: PolicyId) -> dict[tuple[str, str], int]:
    return {(c.zone_id, c.resource_id): c.allocated for c in step.run(policy).result.cells}


def recommendation_rows(index: int) -> list[dict[str, Any]]:
    """One row per (step >= 1, policy): plan metrics plus change versus the previous step."""
    scenario, session = recommendation_run(index)
    rows = []
    for prev, step in zip(session.steps, session.steps[1:], strict=False):
        scores_prev = {u.zone_id: u.result.score for u in prev.comparison.urgency if u.active}
        scores_now = {u.zone_id: u.result.score for u in step.comparison.urgency if u.active}
        common = scores_prev.keys() & scores_now.keys()
        max_urgency_change = max((abs(scores_now[z] - scores_prev[z]) for z in common), default=0.0)
        for policy in POLICY_ORDER:
            before, after = _cells(prev, policy), _cells(step, policy)
            moved = sum(
                abs(after.get(k, 0) - before.get(k, 0)) for k in before.keys() | after.keys()
            )
            m_prev, m_now = prev.run(policy).metrics, step.run(policy).metrics
            zone_prev, zone_now = m_prev.coverage_by_zone, m_now.coverage_by_zone
            shared = [
                z
                for z in zone_prev
                if z in zone_now and zone_prev[z] is not None and zone_now[z] is not None
            ]
            alloc_total = m_prev.allocated_units + m_now.allocated_units
            rows.append(
                {
                    "script_id": f"dyn-{index}",
                    "base_scenario_id": scenario.scenario_id,
                    "seed": DYNAMIC_SEED_BASE + index,
                    "step": step.seq,
                    "event_type": step.event.type,
                    "policy": policy.value,
                    "status": str(step.run(policy).result.status),
                    "valid": int(step.run(policy).validation.valid),
                    "reallocated_units": moved,
                    "reallocated_share": moved / alloc_total if alloc_total else None,
                    "plan_changed": int(moved > 0),
                    "unmet_before": m_prev.unmet_units,
                    "unmet_after": m_now.unmet_units,
                    "unmet_change": m_now.unmet_units - m_prev.unmet_units,
                    "uwc_after": m_now.urgency_weighted_coverage,
                    "min_zone_coverage_after": m_now.min_zone_coverage,
                    "starved_zones_after": m_now.starved_zones,
                    "mean_abs_zone_coverage_change": (
                        sum(abs(zone_now[z] - zone_prev[z]) for z in shared) / len(shared)
                        if shared
                        else None
                    ),
                    "max_urgency_change": max_urgency_change,
                    "runtime_ms": step.run(policy).runtime_ms,
                    "outcome_hash": step.outcome_hash,
                }
            )
    return rows


# ---------------------------------------------------------------- dispatch mode


INITIAL_SHARE = 0.30  # dispatch mode: the depot starts with 30% of each resource's requests
WAVE_SHARE = 0.15  # each of three later shipments brings 15% of the initial requests


def dispatch_base(index: int) -> Scenario:
    """The family-B base scenario with stock reset to INITIAL_SHARE of requests."""
    scenario = base_scenario(index)
    raw = scenario.model_dump(mode="json")
    for rid in scenario.resource_ids():
        requested = sum(z.demand.get(rid, 0) for z in scenario.active_zones())
        raw["stock"][rid] = int(requested * INITIAL_SHARE)
    raw["scenario_id"] = f"dsp-{scenario.scenario_id}"
    return parse_scenario(raw)


def dispatch_script(index: int) -> tuple[Scenario, list[Any]]:
    """Supplies arrive in waves while the crisis changes; each policy dispatches after each wave.

    [loss, commit, escalation, wave 1, commit, new zone, wave 2, commit, request increase,
     wave 3, commit]. Every event is valid whatever was dispatched before it: the loss comes
    before the first dispatch, and the request update raises the zone's original request.
    """
    scenario = dispatch_base(index)
    rng = random.Random(DYNAMIC_SEED_BASE + 50_000 + index)
    requested = {
        rid: sum(z.demand.get(rid, 0) for z in scenario.active_zones())
        for rid in scenario.resource_ids()
    }

    def wave() -> list[SupplyArrived]:
        return [
            SupplyArrived(resource_id=rid, quantity=max(1, int(units * WAVE_SHARE)))
            for rid, units in requested.items()
            if units > 0
        ]

    actions: list[Any] = []
    stocked = [r for r in scenario.resource_ids() if scenario.stock[r] > 0]
    if stocked:
        rid = rng.choice(stocked)
        actions.append(SupplyLost(resource_id=rid, quantity=max(1, int(scenario.stock[rid] * 0.2))))
    actions += [COMMIT, _escalation(scenario, rng), *wave(), COMMIT]
    actions += [_new_zone(scenario, rng, f"d{index}"), *wave(), COMMIT]
    zone = rng.choice(list(scenario.active_zones()))
    rid = rng.choice(scenario.resource_ids())
    increase = RequestUpdated(
        zone_id=zone.id, resource_id=rid, quantity=zone.demand.get(rid, 0) + rng.randint(10, 40)
    )
    actions += [increase, *wave(), COMMIT]
    return scenario, actions


@dataclass(frozen=True)
class DispatchOutcome:
    row: dict[str, Any]
    zone_rows: list[dict[str, Any]]


def dispatch_run(index: int, policy: PolicyId) -> DispatchOutcome:
    scenario, actions = dispatch_script(index)
    session = S.control(S.create_session(scenario, f"dsp-{index}-{policy.value}"), Action.START)
    commits = empty_commits = rejected_events = blocked_repeats = repeat_attempts = 0
    arrived = dict.fromkeys(scenario.resource_ids(), 0)
    lost = dict.fromkeys(scenario.resource_ids(), 0)
    for action in actions:
        if action == COMMIT:
            stale_hash = session.current.snapshot_hash
            try:
                session = S.apply(
                    session, PlanCommitted(policy=policy, expected_snapshot_hash=stale_hash)
                )
            except EventRejectedError as err:
                if err.code != "no_change":
                    raise
                empty_commits += 1  # nothing left to dispatch: a legitimate outcome
                continue
            commits += 1
            repeat_attempts += 1
            try:  # the identical commit again must be refused: no double dispatch
                S.apply(session, PlanCommitted(policy=policy, expected_snapshot_hash=stale_hash))
            except EventRejectedError as err:
                blocked_repeats += int(err.code == "stale_plan")
            continue
        try:
            session = S.apply(session, action)
        except EventRejectedError:
            rejected_events += 1  # by construction this should stay 0; it is reported
            continue
        if isinstance(action, SupplyArrived):
            arrived[action.resource_id] += action.quantity
        if isinstance(action, SupplyLost):
            lost[action.resource_id] += action.quantity

    final = session.current
    dispatched_by_zone: dict[str, int] = {}
    dispatched_by_resource = dict.fromkeys(scenario.resource_ids(), 0)
    for entry in session.ledger:
        for cell in entry.cells:
            dispatched_by_zone[cell.zone_id] = dispatched_by_zone.get(cell.zone_id, 0) + cell.units
            dispatched_by_resource[cell.resource_id] += cell.units
    conserved = all(
        scenario.stock[r] + arrived[r] - lost[r] - dispatched_by_resource[r]
        == final.scenario.stock[r]
        for r in scenario.resource_ids()
    )
    scores = {u.zone_id: u.result.score for u in final.comparison.urgency}
    zone_rows = []
    fulfilment = []
    for zone in final.scenario.active_zones():
        open_units = sum(zone.demand.values())
        got = dispatched_by_zone.get(zone.id, 0)
        need = got + open_units
        fulfilment.append((zone.id, got, need))
        zone_rows.append(
            {
                "script_id": f"dyn-{index}",
                "policy": policy.value,
                "zone_id": zone.id,
                "urgency": scores[zone.id],
                "dispatched": got,
                "total_need": need,
                "fulfilment": got / need if need else None,
            }
        )
    dispatched = sum(got for _, got, _ in fulfilment)
    need_total = sum(need for _, _, need in fulfilment)
    weighted_need = sum(scores[z] * need for z, _, need in fulfilment)
    with_need = [(z, got, need) for z, got, need in fulfilment if need > 0]
    ledger_total = sum(entry.total for entry in session.ledger)
    return DispatchOutcome(
        row={
            "script_id": f"dyn-{index}",
            "base_scenario_id": scenario.scenario_id,
            "seed": DYNAMIC_SEED_BASE + 50_000 + index,
            "policy": policy.value,
            "commits": commits,
            "empty_commits": empty_commits,
            "rejected_events": rejected_events,
            "dispatched_units": dispatched,
            "fulfilment": dispatched / need_total if need_total else None,
            "urgency_weighted_fulfilment": (
                sum(scores[z] * got for z, got, _ in fulfilment) / weighted_need
                if weighted_need
                else None
            ),
            "min_zone_fulfilment": min((got / need for _, got, need in with_need), default=None),
            "zones_never_served": sum(1 for _, got, _ in with_need if got == 0),
            "zones_with_need": len(with_need),
            "inventory_conserved": int(conserved),
            "ledger_consistent": int(ledger_total == dispatched and len(session.ledger) == commits),
            "double_dispatch_blocked": int(blocked_repeats == repeat_attempts),
            "final_outcome_hash": final.outcome_hash,
        },
        zone_rows=zone_rows,
    )
