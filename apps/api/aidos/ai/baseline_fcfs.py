"""First-come-first-served baseline (spec Section 5.4, policy 1).

Zones are served in `arrival_order`, ties broken by zone ID. For each resource, in the
catalogue's canonical order, a zone receives min(remaining stock, its request).
Urgency is deliberately ignored: that is what this baseline is for.
"""

from __future__ import annotations

from aidos.ai.policies import AllocationResult, CellResult, Limit, PolicyId, PolicyStatus
from aidos.domain.models import Scenario


def allocate_fcfs(scenario: Scenario) -> AllocationResult:
    zones = sorted(scenario.active_zones(), key=lambda z: (z.arrival_order, z.id))
    remaining = {rid: scenario.stock[rid] for rid in scenario.resource_ids()}
    cells: list[CellResult] = []

    for zone in zones:
        for rid in scenario.resource_ids():
            requested = scenario.demand_of(zone, rid)
            available = remaining[rid]
            allocated = min(available, requested)
            remaining[rid] -= allocated
            limit, reason = _explain(scenario.stock[rid], available, requested, allocated)
            cells.append(CellResult(zone.id, rid, requested, allocated, limit, reason))

    return AllocationResult(
        policy_id=PolicyId.FCFS,
        status=PolicyStatus.COMPLETE,
        zone_order=tuple(z.id for z in zones),
        cells=tuple(cells),
    )


def _explain(stock: int, available: int, requested: int, allocated: int) -> tuple[Limit, str]:
    """Explain one cell using only quantities the algorithm actually computed."""
    if requested == 0:
        return Limit.NO_DEMAND, "No units requested."
    if allocated == requested:
        return Limit.MET, "Request met in full."
    unmet = requested - allocated
    if stock == 0:
        return Limit.ZERO_STOCK, f"The depot holds no units of this resource ({unmet} unmet)."
    used_earlier = stock - available
    if used_earlier == 0:
        return (
            Limit.STOCK_EXHAUSTED,
            f"Request exceeds the depot's entire stock of {stock} ({unmet} unmet).",
        )
    return (
        Limit.STOCK_EXHAUSTED,
        f"Zones that arrived earlier used {used_earlier} of {stock} units; "
        f"{available} remained ({unmet} unmet).",
    )
