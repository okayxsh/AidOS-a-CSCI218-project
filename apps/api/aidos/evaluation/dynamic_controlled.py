"""Controlled dynamic experiments (Stage 5), correcting the Stage 4 script bias.

Stage 4's scripts always added a late zone with HIGH ratings, which FCFS can never serve. Here
the new zone's urgency level is an experimental factor, crossed with the initial zone count:

    level            new-zone ratings (each of severity, vulnerability, time criticality)
    low              0-3
    moderate         4-6
    high             7-10
    random           0-10 (independent of arrival order)
    initial zones    3, 5, 8

Recommendation mode (shared state) and dispatch mode (policy-specific trajectories) are kept
apart, exactly as in Stage 4. The original functions in dynamic.py are untouched so the frozen
Stage 4 run stays reproducible.
"""

from __future__ import annotations

import hashlib
import json
import random
from typing import Any

from aidos.ai.policies import PolicyId
from aidos.domain.models import Scenario
from aidos.domain.validation import parse_scenario
from aidos.evaluation.generator import CATALOGUE
from aidos.pipeline import POLICY_ORDER
from aidos.simulation import session as S
from aidos.simulation.events import (
    NewZone,
    PlanCommitted,
    RequestUpdated,
    SupplyArrived,
    SupplyLost,
    UrgencyChanged,
    ZoneAdded,
)
from aidos.simulation.fsm import Action
from aidos.simulation.reducer import EventRejectedError

LEVELS = {"low": (0, 3), "moderate": (4, 6), "high": (7, 10), "random": (0, 10)}
ZONE_COUNTS = (3, 5, 8)
SEED_BASE = 1_100_000
NEW_ZONE = "zone-new"


def script_seed(level: str, zones: int, index: int) -> int:
    return SEED_BASE + list(LEVELS).index(level) * 10_000 + zones * 100 + index


def base(zones: int, seed: int, stock_share: tuple[float, float] = (0.60, 0.85)) -> Scenario:
    rng = random.Random(seed)
    catalogue = list(CATALOGUE[:3])
    zone_list = [
        {
            "id": f"zone-{i + 1:02d}",
            "name": f"Zone {i + 1}",
            "arrival_order": i + 1,
            "severity": rng.randint(0, 10),
            "vulnerability": rng.randint(0, 10),
            "time_criticality": rng.randint(0, 10),
            "demand": {r["id"]: rng.randint(10, 80) for r in catalogue},
        }
        for i in range(zones)
    ]
    stock = {
        r["id"]: int(sum(z["demand"][r["id"]] for z in zone_list) * rng.uniform(*stock_share))
        for r in catalogue
    }
    return parse_scenario(
        {
            "schema_version": "1.0",
            "scenario_id": f"ctl-{seed}",
            "title": f"Controlled base {seed}",
            "seed": seed,
            "synthetic": True,
            "resources": catalogue,
            "stock": stock,
            "zones": zone_list,
        }
    )


def new_zone(level: str, rng: random.Random, resources: tuple[str, ...]) -> ZoneAdded:
    low, high = LEVELS[level]
    return ZoneAdded(
        zone=NewZone(
            id=NEW_ZONE,
            name="New zone",
            severity=rng.randint(low, high),
            vulnerability=rng.randint(low, high),
            time_criticality=rng.randint(low, high),
            demand={r: rng.randint(10, 60) for r in resources},
        )
    )


def escalation(scenario: Scenario, rng: random.Random) -> UrgencyChanged:
    zone = rng.choice([z for z in scenario.zones if z.id != NEW_ZONE])
    if zone.severity < 10:
        return UrgencyChanged(zone_id=zone.id, severity=10)
    return UrgencyChanged(zone_id=zone.id, time_criticality=10 if zone.time_criticality < 10 else 0)


def _coverage(cells: dict[tuple[str, str], tuple[int, int]], zone_id: str) -> float | None:
    got = sum(a for (z, _), (a, _) in cells.items() if z == zone_id)
    asked = sum(d for (z, _), (_, d) in cells.items() if z == zone_id)
    return got / asked if asked else None


def _zone_stats(cells, zone_ids):
    cov = [c for c in (_coverage(cells, z) for z in zone_ids) if c is not None]
    return (
        min(cov) if cov else None,
        sum(cov) / len(cov) if cov else None,
        sum(1 for c in cov if c == 0),
    )


# ---------------------------------------------------------------- recommendation mode


def recommendation(level: str, zones: int, index: int) -> list[dict[str, Any]]:
    seed = script_seed(level, zones, index)
    scenario = base(zones, seed)
    rng = random.Random(seed + 1)
    resources = scenario.resource_ids()
    session = S.control(S.create_session(scenario, f"ctl-rec-{seed}"), Action.START)
    events = [
        lambda sc: escalation(sc, rng),
        lambda sc: new_zone(level, rng, resources),
        lambda sc: SupplyLost(
            resource_id=(r := rng.choice(resources)), quantity=max(1, sc.stock[r] // 4)
        ),
        lambda sc: SupplyArrived(
            resource_id=rng.choice(resources),
            quantity=max(1, sum(z.demand.get(resources[0], 0) for z in sc.zones) // 7),
        ),
        lambda sc: RequestUpdated(
            zone_id=(z := rng.choice([z for z in sc.zones if z.id != NEW_ZONE])).id,
            resource_id=(r := rng.choice(resources)),
            quantity=z.demand.get(r, 0) + rng.randint(10, 40),
        ),
    ]
    for build in events:
        try:
            session = S.apply(session, build(session.current.scenario))
        except EventRejectedError:
            continue  # e.g. a loss when that stock is already 0: recorded by the missing step
    original = [z.id for z in scenario.zones]
    rows = []
    for prev, step in zip(session.steps, session.steps[1:], strict=False):
        for policy in POLICY_ORDER:
            before = {
                (c.zone_id, c.resource_id): c.allocated for c in prev.run(policy).result.cells
            }
            cells = {
                (c.zone_id, c.resource_id): (c.allocated, c.requested)
                for c in step.run(policy).result.cells
            }
            moved = sum(
                abs(cells.get(k, (0, 0))[0] - before.get(k, 0))
                for k in before.keys() | cells.keys()
            )
            orig_min, orig_mean, orig_starved = _zone_stats(cells, original)
            new_present = any(z == NEW_ZONE for z, _ in cells)
            rows.append(
                {
                    "script_id": f"ctl-{seed}",
                    "level": level,
                    "initial_zones": zones,
                    "seed": seed,
                    "step": step.seq,
                    "event_type": step.event.type,
                    "policy": policy.value,
                    "valid": int(step.run(policy).validation.valid),
                    "reallocated_units": moved,
                    "plan_changed": int(moved > 0),
                    "new_zone_coverage": _coverage(cells, NEW_ZONE) if new_present else None,
                    "original_min_coverage": orig_min,
                    "original_mean_coverage": orig_mean,
                    "original_starved": orig_starved,
                    "uwc": step.run(policy).metrics.urgency_weighted_coverage,
                    "new_zone_urgency": next(
                        (u.result.score for u in step.comparison.urgency if u.zone_id == NEW_ZONE),
                        None,
                    ),
                    "outcome_hash": step.outcome_hash,
                }
            )
    return rows


# ---------------------------------------------------------------- dispatch mode


def dispatch_script(level: str, zones: int, index: int) -> tuple[Scenario, list[Any]]:
    """Stock starts at 30% of requests; three 15% waves; one dispatch per wave."""
    seed = script_seed(level, zones, index)
    full = base(zones, seed)
    raw = full.model_dump(mode="json")
    requested = {r: sum(z.demand.get(r, 0) for z in full.zones) for r in full.resource_ids()}
    raw["stock"] = {r: int(units * 0.30) for r, units in requested.items()}
    raw["scenario_id"] = f"ctl-dsp-{seed}"
    scenario = parse_scenario(raw)
    rng = random.Random(seed + 2)
    resources = scenario.resource_ids()

    def wave():
        return [
            SupplyArrived(resource_id=r, quantity=max(1, int(u * 0.15)))
            for r, u in requested.items()
            if u
        ]

    stocked = [r for r in resources if scenario.stock[r] > 0]
    actions: list[Any] = []
    if stocked:
        r = rng.choice(stocked)
        actions.append(SupplyLost(resource_id=r, quantity=max(1, scenario.stock[r] // 5)))
    actions += ["commit", escalation(scenario, rng), *wave(), "commit"]
    actions += [new_zone(level, rng, resources), *wave(), "commit"]
    z = rng.choice(list(scenario.zones))
    r = rng.choice(resources)
    actions += [
        RequestUpdated(
            zone_id=z.id, resource_id=r, quantity=z.demand.get(r, 0) + rng.randint(10, 40)
        ),
        *wave(),
        "commit",
    ]
    return scenario, actions


def script_hash(actions: list[Any]) -> str:
    payload = [a if isinstance(a, str) else a.model_dump(mode="json") for a in actions]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def dispatch(level: str, zones: int, index: int, policy: PolicyId) -> dict[str, Any]:
    scenario, actions = dispatch_script(level, zones, index)
    session = S.control(S.create_session(scenario, "ctl-dsp"), Action.START)
    arrived = dict.fromkeys(scenario.resource_ids(), 0)
    lost = dict.fromkeys(scenario.resource_ids(), 0)
    commits = empty = rejected = blocked = 0
    per_round = []
    for action in actions:
        if action == "commit":
            stale = session.current.snapshot_hash
            try:
                session = S.apply(
                    session, PlanCommitted(policy=policy, expected_snapshot_hash=stale)
                )
            except EventRejectedError as err:
                if err.code != "no_change":
                    raise
                empty += 1
                per_round.append(0)
                continue
            commits += 1
            per_round.append(session.ledger[-1].total)
            try:
                S.apply(session, PlanCommitted(policy=policy, expected_snapshot_hash=stale))
            except EventRejectedError as err:
                blocked += int(err.code == "stale_plan")
            continue
        try:
            session = S.apply(session, action)
        except EventRejectedError:
            rejected += 1
            continue
        if isinstance(action, SupplyArrived):
            arrived[action.resource_id] += action.quantity
        if isinstance(action, SupplyLost):
            lost[action.resource_id] += action.quantity

    final = session.current.scenario
    got: dict[str, int] = {}
    dispatched_r = dict.fromkeys(scenario.resource_ids(), 0)
    for entry in session.ledger:
        for c in entry.cells:
            got[c.zone_id] = got.get(c.zone_id, 0) + c.units
            dispatched_r[c.resource_id] += c.units
    fulfil = {
        z.id: (got.get(z.id, 0), got.get(z.id, 0) + sum(z.demand.values()))
        for z in final.active_zones()
    }
    original = [z for z in fulfil if z != NEW_ZONE]
    orig_f = [g / n for z, (g, n) in fulfil.items() if z in original and n]
    new_g, new_n = fulfil.get(NEW_ZONE, (0, 0))
    return {
        "script_id": f"ctl-{script_seed(level, zones, index)}",
        "level": level,
        "initial_zones": zones,
        "policy": policy.value,
        "exogenous_script_hash": script_hash(actions),
        "commits": commits,
        "empty_commits": empty,
        "rejected_events": rejected,
        "dispatched_per_round": "|".join(map(str, per_round)),
        "dispatched_units": sum(got.values()),
        "new_zone_fulfilment": new_g / new_n if new_n else None,
        "new_zone_never_served": int(new_n > 0 and new_g == 0),
        "original_min_fulfilment": min(orig_f) if orig_f else None,
        "original_mean_fulfilment": sum(orig_f) / len(orig_f) if orig_f else None,
        "original_never_served": sum(1 for z in original if fulfil[z][1] and fulfil[z][0] == 0),
        "final_stock": "|".join(f"{r}:{final.stock[r]}" for r in final.resource_ids()),
        "inventory_conserved": int(
            all(
                scenario.stock[r] + arrived[r] - lost[r] - dispatched_r[r] == final.stock[r]
                for r in scenario.resource_ids()
            )
        ),
        "double_dispatch_blocked": int(blocked == commits),
    }
