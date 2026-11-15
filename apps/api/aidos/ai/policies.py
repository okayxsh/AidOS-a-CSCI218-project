"""Common interface and result types for allocation policies (spec Section 5.4).

Every policy reads the same immutable Scenario and returns an AllocationResult with one
cell per (active zone, resource). Policies never mutate the scenario; stock is only
consumed by an explicit commit (Stage 3).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class PolicyId(StrEnum):
    FCFS = "fcfs"
    GREEDY = "greedy"
    AIDOS = "aidos"  # fuzzy urgency + CP-SAT, urgency-first objective
    AIDOS_BALANCED = "aidos_balanced"  # fuzzy urgency + CP-SAT, coverage floor first


class PolicyStatus(StrEnum):
    """COMPLETE: a deterministic heuristic finished. The rest are CP-SAT statuses, as returned."""

    COMPLETE = "COMPLETE"
    OPTIMAL = "OPTIMAL"  # the solver proved no better plan exists for the stated objective
    FEASIBLE = "FEASIBLE"  # a valid plan, but optimality was not proven (e.g. time limit)
    INFEASIBLE = "INFEASIBLE"  # the model has no solution; no plan is returned
    UNKNOWN = "UNKNOWN"  # no solution found before the limit; no plan is returned
    MODEL_INVALID = "MODEL_INVALID"  # the model was rejected; no plan is returned

    @property
    def has_plan(self) -> bool:
        return self in (PolicyStatus.COMPLETE, PolicyStatus.OPTIMAL, PolicyStatus.FEASIBLE)


class Limit(StrEnum):
    """Why a zone received what it did for one resource."""

    MET = "met"  # received everything requested
    NO_DEMAND = "no_demand"  # requested nothing
    STOCK_EXHAUSTED = "stock_exhausted"  # the resource's stock was fully allocated
    ZERO_STOCK = "zero_stock"  # the depot held none of this resource
    NOT_PROVEN = "not_proven"  # stock left over in a plan the solver did not prove optimal


@dataclass(frozen=True)
class CellResult:
    zone_id: str
    resource_id: str
    requested: int
    allocated: int
    limit: Limit
    reason: str

    @property
    def unmet(self) -> int:
        return self.requested - self.allocated


@dataclass(frozen=True)
class SolverPhase:
    """One lexicographic solve: its objective, the status CP-SAT returned, and the values."""

    name: str
    status: str
    objective_value: float | None
    best_bound: float | None
    wall_time_ms: float


@dataclass(frozen=True)
class SolverReport:
    status: PolicyStatus
    objective: str  # named objective, e.g. "urgency_first"
    objective_value: int | None  # primary objective in its integer (scaled) form
    phases: tuple[SolverPhase, ...]
    variables: int
    constraints: int
    parameters: Mapping[str, Any]
    coefficients: Mapping[str, Mapping[str, int]]  # zone -> resource -> objective coefficient
    coverage_floor: Mapping[str, float] = field(default_factory=dict)  # balanced only
    message: str = ""


@dataclass(frozen=True)
class AllocationResult:
    policy_id: PolicyId
    status: PolicyStatus
    zone_order: tuple[str, ...]  # order in which zones were served or ranked
    cells: tuple[CellResult, ...]
    solver: SolverReport | None = None
    message: str = ""  # set when no plan is returned

    @property
    def has_plan(self) -> bool:
        return self.status.has_plan

    def allocated(self, zone_id: str, resource_id: str) -> int:
        for cell in self.cells:
            if cell.zone_id == zone_id and cell.resource_id == resource_id:
                return cell.allocated
        return 0


def basic_limit(stock: int, requested: int, allocated: int) -> Limit | None:
    """The limit for cells every policy explains the same way; None when policy-specific."""
    if requested == 0:
        return Limit.NO_DEMAND
    if allocated == requested:
        return Limit.MET
    if stock == 0:
        return Limit.ZERO_STOCK
    return None


BASIC_REASON = {
    Limit.NO_DEMAND: "No units requested.",
    Limit.MET: "Request met in full.",
}


def zero_stock_reason(unmet: int) -> str:
    return f"The depot holds no units of this resource ({unmet} unmet)."
