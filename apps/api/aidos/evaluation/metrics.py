"""Scenario summaries, feasibility checks and coverage metrics (spec Section 5.5).

Ratios with a zero denominator are returned as None ("N/A"), never as 0 or 1.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

from aidos.ai.policies import AllocationResult
from aidos.domain.models import Scenario
from aidos.evaluation.invariants import Violation, validate_allocation

__all__ = ["Violation", "compute_metrics", "find_violations", "summarize_scenario"]

SupplyStatus = Literal["no_demand", "covered", "shortage", "depot_empty"]


def _ratio(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else numerator / denominator


# ---------------------------------------------------------------- scenario summary


@dataclass(frozen=True)
class ResourceSummary:
    resource_id: str
    stock: int
    requested: int

    @property
    def shortfall(self) -> int:
        return max(0, self.requested - self.stock)

    @property
    def surplus(self) -> int:
        return max(0, self.stock - self.requested)


@dataclass(frozen=True)
class ZoneSummary:
    zone_id: str
    active: bool
    requested_units: int


@dataclass(frozen=True)
class ScenarioSummary:
    resources: tuple[ResourceSummary, ...]
    zones: tuple[ZoneSummary, ...]

    @property
    def total_stock(self) -> int:
        return sum(r.stock for r in self.resources)

    @property
    def total_requested(self) -> int:
        return sum(r.requested for r in self.resources)

    @property
    def total_shortfall(self) -> int:
        # Summed per resource: surplus water never offsets missing medical kits.
        return sum(r.shortfall for r in self.resources)

    @property
    def active_zone_count(self) -> int:
        return sum(1 for z in self.zones if z.active)

    @property
    def supply_status(self) -> SupplyStatus:
        """Whether depot stock can cover the active requests, judged per resource."""
        if self.total_requested == 0:
            return "no_demand"
        if self.total_shortfall == 0:
            return "covered"
        if self.total_stock == 0:
            return "depot_empty"
        return "shortage"


def summarize_scenario(scenario: Scenario) -> ScenarioSummary:
    """Demand against stock for active zones. Inputs only; no allocation involved."""
    active = scenario.active_zones()
    active_ids = {z.id for z in active}
    resources = tuple(
        ResourceSummary(
            resource_id=rid,
            stock=scenario.stock[rid],
            requested=sum(scenario.demand_of(z, rid) for z in active),
        )
        for rid in scenario.resource_ids()
    )
    zones = tuple(
        ZoneSummary(
            zone_id=z.id,
            active=z.id in active_ids,
            requested_units=sum(z.demand.values()),
        )
        for z in scenario.zones
    )
    return ScenarioSummary(resources=resources, zones=zones)


# ---------------------------------------------------------------- allocation metrics

# Zones at or above this urgency (the lower edge of the "high" band) count as high urgency.
HIGH_URGENCY_THRESHOLD = 50.0
# Zones at or above this urgency (the lower edge of the "critical" band) count as critical.
CRITICAL_URGENCY_THRESHOLD = 75.0


def find_violations(scenario: Scenario, result: AllocationResult) -> list[Violation]:
    """Hard-invariant violations, from the independent validator."""
    return list(validate_allocation(scenario, result).violations)


@dataclass(frozen=True)
class AllocationMetrics:
    unit_coverage: float | None
    coverage_by_resource: dict[str, float | None]
    coverage_by_zone: dict[str, float | None]
    allocated_units: int
    unmet_units: int
    feasibility_violations: int
    allocated_by_resource: dict[str, int] = field(default_factory=dict)
    remaining_by_resource: dict[str, int] = field(default_factory=dict)
    stock_utilization: float | None = None
    urgency_weighted_coverage: float | None = None
    min_zone_coverage: float | None = None
    jain_fairness: float | None = None
    unmet_high_urgency: int | None = None
    # Stage 4 additions (docs/evaluation/metric-definitions.md)
    mean_resource_coverage: float | None = None  # unit-free: mean of per-resource coverage
    usable_stock_utilization: float | None = None  # allocated / sum_r min(stock_r, requested_r)
    zones_with_demand: int = 0
    starved_zones: int = 0  # zones with positive demand that receive nothing at all
    coverage_gap: float | None = None  # max minus min zone coverage
    critical_coverage: float | None = None  # unit coverage of zones with urgency >= 75


def compute_metrics(
    scenario: Scenario,
    result: AllocationResult,
    urgency: Mapping[str, float] | None = None,
) -> AllocationMetrics:
    """Metrics from a plan's cells. Urgency-based metrics need the shared fuzzy scores.

    urgency_weighted_coverage = sum(u_z * x) / sum(u_z * d)            (spec 5.5)
    stock_utilization         = sum(x) / sum(stock)
    jain_fairness             = (sum f_z)^2 / (n * sum f_z^2) over zones with demand,
                                where f_z is the zone's unit coverage; N/A if all f_z = 0
    unmet_high_urgency        = sum(d - x) over zones with u_z >= HIGH_URGENCY_THRESHOLD
    """
    allocated = sum(c.allocated for c in result.cells)
    requested = sum(c.requested for c in result.cells)

    by_resource: dict[str, float | None] = {}
    allocated_by_resource: dict[str, int] = {}
    for rid in scenario.resource_ids():
        cells = [c for c in result.cells if c.resource_id == rid]
        allocated_by_resource[rid] = sum(c.allocated for c in cells)
        by_resource[rid] = _ratio(allocated_by_resource[rid], sum(c.requested for c in cells))
    remaining = {rid: scenario.stock[rid] - allocated_by_resource[rid] for rid in by_resource}

    by_zone: dict[str, float | None] = {}
    for zone_id in result.zone_order:
        cells = [c for c in result.cells if c.zone_id == zone_id]
        by_zone[zone_id] = _ratio(sum(c.allocated for c in cells), sum(c.requested for c in cells))

    fractions = [f for f in by_zone.values() if f is not None]
    squares = sum(f * f for f in fractions)
    jain = (sum(fractions) ** 2) / (len(fractions) * squares) if fractions and squares else None

    zone_requested: dict[str, int] = {}
    zone_allocated: dict[str, int] = {}
    for c in result.cells:
        zone_requested[c.zone_id] = zone_requested.get(c.zone_id, 0) + c.requested
        zone_allocated[c.zone_id] = zone_allocated.get(c.zone_id, 0) + c.allocated
    demanding = [z for z, d in zone_requested.items() if d > 0]
    starved = sum(1 for z in demanding if zone_allocated[z] == 0)
    resource_fractions = [f for f in by_resource.values() if f is not None]
    usable = sum(
        min(scenario.stock[rid], sum(c.requested for c in result.cells if c.resource_id == rid))
        for rid in scenario.resource_ids()
    )

    weighted = high_unmet = critical = None
    if urgency is not None and result.has_plan:
        critical_zones = [z for z in demanding if urgency[z] >= CRITICAL_URGENCY_THRESHOLD]
        critical = _ratio(
            sum(zone_allocated[z] for z in critical_zones),
            sum(zone_requested[z] for z in critical_zones),
        )
        num = sum(urgency[c.zone_id] * c.allocated for c in result.cells)
        den = sum(urgency[c.zone_id] * c.requested for c in result.cells)
        weighted = None if den == 0 else num / den
        high_unmet = sum(
            c.unmet for c in result.cells if urgency[c.zone_id] >= HIGH_URGENCY_THRESHOLD
        )

    return AllocationMetrics(
        unit_coverage=_ratio(allocated, requested),
        coverage_by_resource=by_resource,
        coverage_by_zone=by_zone,
        allocated_units=allocated,
        unmet_units=requested - allocated,
        feasibility_violations=len(find_violations(scenario, result)),
        allocated_by_resource=allocated_by_resource,
        remaining_by_resource=remaining,
        stock_utilization=_ratio(allocated, sum(scenario.stock.values())),
        urgency_weighted_coverage=weighted,
        min_zone_coverage=min(fractions) if fractions else None,
        jain_fairness=jain,
        unmet_high_urgency=high_unmet,
        mean_resource_coverage=(
            sum(resource_fractions) / len(resource_fractions) if resource_fractions else None
        ),
        usable_stock_utilization=_ratio(allocated, usable),
        zones_with_demand=len(demanding),
        starved_zones=starved,
        coverage_gap=max(fractions) - min(fractions) if fractions else None,
        critical_coverage=critical,
    )
