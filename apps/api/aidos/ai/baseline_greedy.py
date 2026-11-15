"""Urgency-greedy baseline (spec Section 5.4, policy 2).

Zones are ranked by fuzzy urgency (highest first), ties broken by arrival order and then
zone ID. For each resource, in catalogue order, a zone receives min(remaining stock, its
request). It uses the same urgency scores as AidOS but no optimiser, so comparing the two
isolates what the optimisation adds. Under a purely linear objective the two can coincide:
that is a planned experimental control, not a defect.
"""

from __future__ import annotations

from collections.abc import Mapping

from aidos.ai.policies import (
    BASIC_REASON,
    AllocationResult,
    CellResult,
    Limit,
    PolicyId,
    PolicyStatus,
    basic_limit,
    zero_stock_reason,
)
from aidos.domain.models import Scenario


def urgency_rank(scenario: Scenario, urgency: Mapping[str, float]) -> tuple[str, ...]:
    """Active zones by urgency (descending), then arrival order, then zone ID."""
    zones = sorted(scenario.active_zones(), key=lambda z: (-urgency[z.id], z.arrival_order, z.id))
    return tuple(z.id for z in zones)


def allocate_greedy(scenario: Scenario, urgency: Mapping[str, float]) -> AllocationResult:
    order = urgency_rank(scenario, urgency)
    zones = {z.id: z for z in scenario.zones}
    remaining = {rid: scenario.stock[rid] for rid in scenario.resource_ids()}
    cells: list[CellResult] = []

    for zone_id in order:
        for rid in scenario.resource_ids():
            stock = scenario.stock[rid]
            requested = scenario.demand_of(zones[zone_id], rid)
            available = remaining[rid]
            allocated = min(available, requested)
            remaining[rid] -= allocated
            limit = basic_limit(stock, requested, allocated)
            if limit in BASIC_REASON:
                reason = BASIC_REASON[limit]
            elif limit is Limit.ZERO_STOCK:
                reason = zero_stock_reason(requested - allocated)
            else:
                limit, reason = (
                    Limit.STOCK_EXHAUSTED,
                    _shortfall_reason(stock, available, requested - allocated),
                )
            cells.append(CellResult(zone_id, rid, requested, allocated, limit, reason))

    return AllocationResult(
        policy_id=PolicyId.GREEDY,
        status=PolicyStatus.COMPLETE,
        zone_order=order,
        cells=tuple(cells),
    )


def _shortfall_reason(stock: int, available: int, unmet: int) -> str:
    used_earlier = stock - available
    if used_earlier == 0:
        return f"Request exceeds the depot's entire stock of {stock} ({unmet} unmet)."
    return (
        f"Zones ranked above it by urgency used {used_earlier} of {stock} units; "
        f"{available} remained ({unmet} unmet)."
    )
