"""Independent allocation validator (spec Sections 2 and 7, data invariants).

Checks a returned plan against the *scenario*, never against the policy's own claims: a
solver status of OPTIMAL is not accepted as proof that the plan is valid. Every policy,
heuristic or solver, goes through the same checks.

Hard checks (any failure is a violation):
  integer            every allocation is a whole number
  non_negative       x >= 0
  within_demand      x <= the scenario's demand for that zone and resource
  within_stock       sum over zones <= the scenario's stock, per resource (no netting
                     between resources, so no substitution can hide here)
  complete           exactly one cell per (active zone, resource); no unknown or inactive
                     zone, no unknown resource, and each cell's `requested` equals the demand

Quality check (reported, never a violation):
  no_idle_stock      no resource keeps unused stock while an active zone still lacks it
"""

from __future__ import annotations

from dataclasses import dataclass

from aidos.ai.policies import AllocationResult
from aidos.domain.models import Scenario


@dataclass(frozen=True)
class Violation:
    kind: str  # "not_integer", "negative", "above_demand", "above_stock", "incomplete"
    zone_id: str | None
    resource_id: str | None
    detail: str


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str
    hard: bool = True


@dataclass(frozen=True)
class ValidationReport:
    applicable: bool  # False when the policy returned no plan (nothing to validate)
    checks: tuple[Check, ...]
    violations: tuple[Violation, ...]

    @property
    def valid(self) -> bool:
        return self.applicable and not self.violations


HARD_CHECKS = ("integer", "non_negative", "within_demand", "within_stock", "complete")


def validate_allocation(scenario: Scenario, result: AllocationResult) -> ValidationReport:
    if not result.has_plan:
        return ValidationReport(applicable=False, checks=(), violations=())

    violations: list[Violation] = []
    active = {z.id: z for z in scenario.active_zones()}
    resource_ids = scenario.resource_ids()
    used = dict.fromkeys(resource_ids, 0)
    seen: dict[tuple[str, str], int] = {}

    for cell in result.cells:
        key = (cell.zone_id, cell.resource_id)
        seen[key] = seen.get(key, 0) + 1
        value = cell.allocated
        if isinstance(value, bool) or not isinstance(value, int):
            violations.append(Violation("not_integer", *key, f"{value!r} is not a whole number"))
            continue
        if value < 0:
            violations.append(Violation("negative", *key, f"{value} units"))
        zone = active.get(cell.zone_id)
        if zone is None or cell.resource_id not in used:
            what = "zone is not active" if zone is None else "resource is unknown"
            violations.append(Violation("incomplete", *key, f"cell for a {what}"))
            continue
        demand = scenario.demand_of(zone, cell.resource_id)
        if value > demand:
            violations.append(
                Violation("above_demand", *key, f"{value} allocated > {demand} requested")
            )
        if cell.requested != demand:
            violations.append(
                Violation("incomplete", *key, f"says {cell.requested} requested; scenario {demand}")
            )
        used[cell.resource_id] += value

    for zone_id in active:
        for rid in resource_ids:
            count = seen.get((zone_id, rid), 0)
            if count != 1:
                violations.append(
                    Violation("incomplete", zone_id, rid, f"{count} cells (expected exactly 1)")
                )

    for rid, total in used.items():
        if total > scenario.stock[rid]:
            violations.append(
                Violation("above_stock", None, rid, f"{total} used > {scenario.stock[rid]} stock")
            )

    by_kind = {
        "integer": "not_integer",
        "non_negative": "negative",
        "within_demand": "above_demand",
        "within_stock": "above_stock",
        "complete": "incomplete",
    }
    describe = {
        "integer": "Every allocation is a whole number of units.",
        "non_negative": "No allocation is negative.",
        "within_demand": "No zone receives more than it requested.",
        "within_stock": "No resource is allocated beyond the depot's stock.",
        "complete": "One cell per active zone and resource, matching the scenario's requests.",
    }
    checks = []
    for name in HARD_CHECKS:
        failed = [v for v in violations if v.kind == by_kind[name]]
        detail = describe[name] if not failed else f"{len(failed)} failure(s): {failed[0].detail}"
        checks.append(Check(name, not failed, detail))

    idle = [
        rid
        for rid in resource_ids
        if used[rid] < scenario.stock[rid]
        and any(result.allocated(z.id, rid) < scenario.demand_of(z, rid) for z in active.values())
    ]
    checks.append(
        Check(
            "no_idle_stock",
            not idle,
            "No stock is left unused while a zone still needs it."
            if not idle
            else f"Unused stock with unmet demand for: {', '.join(idle)}.",
            hard=False,
        )
    )
    return ValidationReport(applicable=True, checks=tuple(checks), violations=tuple(violations))
