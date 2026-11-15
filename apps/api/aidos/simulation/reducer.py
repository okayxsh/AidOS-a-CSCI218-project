"""Apply one event to a scenario: a pure function, scenario in, new scenario out.

The input scenario is never modified. The event is applied to a plain copy, the copy is
re-validated with the same `parse_scenario` used for fixtures, and only then returned. Any
problem raises EventRejectedError and nothing changes.

Inventory semantics (docs/simulation/events.md): running a policy never changes stock or
requests. Stock changes only through supply_arrived / supply_lost, and through
plan_committed, which dispatches a plan's units: stock and the matching requests both
drop by exactly the dispatched units, recorded once in the session's ledger.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from typing import Any

from aidos.ai.policies import AllocationResult, PolicyId
from aidos.domain.models import Scenario
from aidos.domain.validation import ScenarioValidationError, parse_scenario
from aidos.simulation.events import (
    PlanCommitted,
    RequestUpdated,
    SupplyArrived,
    SupplyLost,
    TimeAdvanced,
    UrgencyChanged,
    ZoneAdded,
    ZoneResolved,
)

RATINGS = ("severity", "vulnerability", "time_criticality")
RATING_LABEL = {
    "severity": "severity",
    "vulnerability": "vulnerability",
    "time_criticality": "time criticality",
}


class EventRejectedError(ValueError):
    """The event cannot be applied to the current scenario. Nothing was changed."""

    def __init__(self, message: str, code: str = "invalid_event", details: list | None = None):
        self.code, self.details = code, details or []
        super().__init__(message)


@dataclass(frozen=True)
class DispatchCell:
    zone_id: str
    resource_id: str
    units: int


@dataclass(frozen=True)
class ResolvedZone:
    zone_id: str
    name: str
    arrival_order: int
    resolved_at_step: int
    remaining_demand: dict[str, int]  # requests that were still open; they are dropped


@dataclass(frozen=True)
class Applied:
    scenario: Scenario
    changes: tuple[str, ...]  # readable list of every input that changed
    dispatch: tuple[DispatchCell, ...] = ()
    resolved: ResolvedZone | None = None


def _short(name: str) -> str:
    return name.split("·")[0].strip()


def _fmt(value: float) -> str:
    return f"{value:g}"


def _zone(raw: dict[str, Any], zone_id: str) -> dict[str, Any]:
    for zone in raw["zones"]:
        if zone["id"] == zone_id:
            return zone
    raise EventRejectedError(f"Unknown zone '{zone_id}'.", "unknown_zone")


def _resource(scenario: Scenario, resource_id: str) -> str:
    for resource in scenario.resources:
        if resource.id == resource_id:
            return resource.label
    raise EventRejectedError(f"Unknown resource '{resource_id}'.", "unknown_resource")


def apply_event(
    scenario: Scenario,
    event: Any,
    *,
    snapshot_hash: str,
    plans: dict[PolicyId, AllocationResult],
    retired: Collection[ResolvedZone] = (),
) -> Applied:
    """Return the scenario after `event`. Raises EventRejectedError; never mutates input."""
    raw = scenario.model_dump(mode="json")
    changes: list[str] = []
    dispatch: tuple[DispatchCell, ...] = ()
    resolved: ResolvedZone | None = None

    if isinstance(event, ZoneAdded):
        new = event.zone
        taken = {z["id"] for z in raw["zones"]} | {r.zone_id for r in retired}
        if new.id in taken:
            raise EventRejectedError(f"Zone id '{new.id}' is already in use.", "duplicate_zone")
        for rid in new.demand:
            _resource(scenario, rid)
        orders = [z["arrival_order"] for z in raw["zones"]] + [r.arrival_order for r in retired]
        raw["zones"].append(
            {
                "id": new.id,
                "name": new.name,
                "arrival_order": max(orders, default=0) + 1,
                "severity": new.severity,
                "vulnerability": new.vulnerability,
                "time_criticality": new.time_criticality,
                "activation_step": raw["step"],
                "population": new.population,
                "demand": dict(new.demand),
            }
        )
        total = sum(new.demand.values())
        changes.append(
            f"{_short(new.name)} reported (severity {_fmt(new.severity)}, vulnerability "
            f"{_fmt(new.vulnerability)}, time criticality {_fmt(new.time_criticality)}) "
            f"requesting {total} units; it arrives after every existing zone."
        )

    elif isinstance(event, UrgencyChanged):
        zone = _zone(raw, event.zone_id)
        for field in RATINGS:
            value = getattr(event, field)
            if value is not None and value != zone[field]:
                changes.append(
                    f"{_short(zone['name'])} {RATING_LABEL[field]} "
                    f"{_fmt(zone[field])} → {_fmt(value)}."
                )
                zone[field] = value
        if not changes:
            raise EventRejectedError(
                f"{_short(zone['name'])} already has those ratings; nothing would change.",
                "no_change",
            )

    elif isinstance(event, SupplyArrived | SupplyLost):
        label = _resource(scenario, event.resource_id)
        before = raw["stock"][event.resource_id]
        delta = event.quantity if isinstance(event, SupplyArrived) else -event.quantity
        if before + delta < 0:
            raise EventRejectedError(
                f"Cannot lose {event.quantity} {label.lower()}: only {before} in stock. "
                "Stock never goes negative.",
                "insufficient_stock",
            )
        raw["stock"][event.resource_id] = before + delta
        verb = "arrived" if delta > 0 else "lost"
        changes.append(f"{label} stock {before} → {before + delta} ({abs(delta)} {verb}).")

    elif isinstance(event, RequestUpdated):
        zone = _zone(raw, event.zone_id)
        label = _resource(scenario, event.resource_id)
        before = zone["demand"].get(event.resource_id, 0)
        if before == event.quantity:
            raise EventRejectedError(
                f"{_short(zone['name'])} already requests {before} {label.lower()}.", "no_change"
            )
        zone["demand"][event.resource_id] = event.quantity
        changes.append(
            f"{_short(zone['name'])} request for {label.lower()} {before} → {event.quantity}."
        )

    elif isinstance(event, ZoneResolved):
        zone = _zone(raw, event.zone_id)
        if len(raw["zones"]) == 1:
            raise EventRejectedError(
                "The last zone cannot be resolved: a scenario needs at least one zone.",
                "last_zone",
            )
        raw["zones"].remove(zone)
        open_demand = {rid: units for rid, units in zone["demand"].items() if units > 0}
        resolved = ResolvedZone(
            zone_id=zone["id"],
            name=zone["name"],
            arrival_order=zone["arrival_order"],
            resolved_at_step=raw["step"],
            remaining_demand=open_demand,
        )
        changes.append(
            f"{_short(zone['name'])} resolved: its {sum(open_demand.values())} open requested "
            "units leave the problem. Units already dispatched to it stay dispatched."
        )

    elif isinstance(event, TimeAdvanced):
        raw["step"] += 1
        changes.append(f"Simulation clock {raw['step'] - 1} → {raw['step']}.")
        for zone in raw["zones"]:
            if zone["activation_step"] == raw["step"]:
                changes.append(
                    f"{_short(zone['name'])} became active (scheduled for step {raw['step']}), "
                    f"requesting {sum(zone['demand'].values())} units."
                )

    elif isinstance(event, PlanCommitted):
        if event.expected_snapshot_hash != snapshot_hash:
            raise EventRejectedError(
                "The plan was computed for a different snapshot (stale or already committed); "
                "nothing was dispatched.",
                "stale_plan",
            )
        plan = plans.get(event.policy)
        if plan is None or not plan.has_plan:
            raise EventRejectedError(
                f"There is no {event.policy} plan for this snapshot to commit.", "no_plan"
            )
        cells = tuple(
            DispatchCell(c.zone_id, c.resource_id, c.allocated) for c in plan.cells if c.allocated
        )
        if not cells:
            raise EventRejectedError("The plan dispatches no units.", "no_change")
        for cell in cells:
            zone = _zone(raw, cell.zone_id)
            open_request = zone["demand"].get(cell.resource_id, 0)
            if cell.units > open_request or cell.units > raw["stock"][cell.resource_id]:
                raise EventRejectedError(
                    "The plan exceeds a request or the stock; it was not dispatched.",
                    "invalid_plan",
                )
            zone["demand"][cell.resource_id] = open_request - cell.units
            raw["stock"][cell.resource_id] -= cell.units
        dispatch = cells
        by_resource: dict[str, int] = {}
        for cell in cells:
            by_resource[cell.resource_id] = by_resource.get(cell.resource_id, 0) + cell.units
        for rid, units in by_resource.items():
            changes.append(
                f"{_resource(scenario, rid)}: {units} units dispatched; stock and the "
                "receiving zones' open requests drop by the same amount."
            )

    else:  # pragma: no cover - the schema admits no other type
        raise EventRejectedError(f"Unsupported event {type(event).__name__}.")

    try:
        new = parse_scenario(raw)
    except ScenarioValidationError as err:
        details = [{"path": i.path, "message": i.message} for i in err.issues]
        raise EventRejectedError(
            "The scenario after this event would be invalid.", "invalid_result", details
        ) from None
    return Applied(new, tuple(changes), dispatch, resolved)
