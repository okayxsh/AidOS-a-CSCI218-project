"""AidOS allocation model: OR-Tools CP-SAT over fuzzy urgency (spec Section 5.2).

Decision variables: x[z, r] = whole units of resource r for active zone z.

Hard constraints (docs/algorithms/allocation-formulation.md):
  0 <= x[z, r] <= d[z, r]       encoded as each variable's domain
  sum_z x[z, r] <= S[r]         one linear constraint per resource
  x[z, r] integer               CP-SAT variables are integers
  no substitution               each variable belongs to one resource and only that
                                resource's stock constraint mentions it

Objectives, solved lexicographically (each later phase keeps the earlier optimum fixed):
  urgency_first (default):  1. maximize sum w_r * (U_z + E) * x[z, r]
                            2. tie-break: prefer earlier arrival among equal coefficients
  balanced:                 1. maximize the coverage floor f_r per resource (capped at a
                               target) such that every requesting zone gets x >= f_r * d
                            2. then the urgency objective   3. then the tie-break

U_z is the fuzzy score times 10,000 (87.5 -> 875000) and E the epsilon times 10,000. Scores
have 4 decimals, so every coefficient is an exact integer, as CP-SAT requires, and no two
different scores share a coefficient.

No plan is fabricated: if CP-SAT returns INFEASIBLE, UNKNOWN or MODEL_INVALID in the first
phase, the result carries that status and no cells. Statuses are reported as returned.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from time import perf_counter
from typing import Literal

from ortools.sat.python import cp_model

from aidos.ai.fuzzy import SCORE_DECIMALS
from aidos.ai.policies import (
    BASIC_REASON,
    AllocationResult,
    CellResult,
    Limit,
    PolicyId,
    PolicyStatus,
    SolverPhase,
    SolverReport,
    basic_limit,
    zero_stock_reason,
)
from aidos.domain.models import Scenario

Objective = Literal["urgency_first", "balanced"]

SCALE = 10**SCORE_DECIMALS  # urgency points -> integer coefficient units (exact for scores)
FLOOR_SCALE = 1000  # coverage floor in per-mille


class AllocationConfigError(ValueError):
    """An allocation setting is out of range or names an unknown resource."""


@dataclass(frozen=True)
class AidosConfig:
    """Documented, versioned knobs of the AidOS policy. Defaults are what the dashboard runs."""

    epsilon: float = 1.0  # urgency points added to every zone so low urgency still counts
    resource_weights: Mapping[str, int] = field(default_factory=dict)  # w_r; missing -> 1
    min_coverage: float = 0.25  # balanced only: target floor as a fraction of each request
    time_limit_s: float = 5.0  # total wall-clock budget across all phases
    random_seed: int = 0
    workers: int = 1  # one worker keeps the search deterministic

    def check(self, scenario: Scenario) -> None:
        problems = []
        if not 0 < self.epsilon <= 100:
            problems.append("epsilon must be in (0, 100]")
        if not 0 <= self.min_coverage <= 1:
            problems.append("min_coverage must be in [0, 1]")
        if not 0.01 <= self.time_limit_s <= 60:
            problems.append("time_limit_s must be in [0.01, 60]")
        known = set(scenario.resource_ids())
        for rid, weight in self.resource_weights.items():
            if rid not in known:
                problems.append(f"resource_weights: unknown resource '{rid}'")
            elif isinstance(weight, bool) or not isinstance(weight, int) or not 1 <= weight <= 100:
                problems.append(f"resource_weights.{rid} must be an integer in [1, 100]")
        if problems:
            raise AllocationConfigError("; ".join(problems))

    def weight(self, resource_id: str) -> int:
        return self.resource_weights.get(resource_id, 1)


_STATUS = {
    cp_model.OPTIMAL: PolicyStatus.OPTIMAL,
    cp_model.FEASIBLE: PolicyStatus.FEASIBLE,
    cp_model.INFEASIBLE: PolicyStatus.INFEASIBLE,
    cp_model.MODEL_INVALID: PolicyStatus.MODEL_INVALID,
    cp_model.UNKNOWN: PolicyStatus.UNKNOWN,
}


def coefficients(
    scenario: Scenario, urgency: Mapping[str, float], config: AidosConfig
) -> dict[str, dict[str, int]]:
    """Integer objective coefficient w_r * (U_z + E) for every active zone and resource."""
    bonus = round(config.epsilon * SCALE)
    return {
        z.id: {
            rid: config.weight(rid) * (round(urgency[z.id] * SCALE) + bonus)
            for rid in scenario.resource_ids()
        }
        for z in scenario.active_zones()
    }


def allocate_aidos(
    scenario: Scenario,
    urgency: Mapping[str, float],
    config: AidosConfig | None = None,
    objective: Objective = "urgency_first",
) -> AllocationResult:
    config = config or AidosConfig()
    config.check(scenario)
    policy_id = PolicyId.AIDOS if objective == "urgency_first" else PolicyId.AIDOS_BALANCED

    zones = sorted(scenario.active_zones(), key=lambda z: (z.arrival_order, z.id))
    coef = coefficients(scenario, urgency, config)
    model = cp_model.CpModel()

    # Variables only where a zone requests the resource and the depot holds some.
    x: dict[tuple[str, str], cp_model.IntVar] = {}
    for zone in zones:
        for rid in scenario.resource_ids():
            demand = scenario.demand_of(zone, rid)
            if demand > 0 and scenario.stock[rid] > 0:
                x[zone.id, rid] = model.new_int_var(0, demand, f"x[{zone.id},{rid}]")

    for rid in scenario.resource_ids():
        terms = [var for (_, r), var in x.items() if r == rid]
        if terms:
            model.add(sum(terms) <= scenario.stock[rid])

    keys = list(x)
    x_vars = [x[k] for k in keys]
    # Earlier arrival earns a larger tie-break weight; it never overrides urgency (phase order).
    rank = {zone.id: len(zones) - index for index, zone in enumerate(zones)}
    # Each phase: (name, variables, integer weights). Objective = sum(weight * variable).
    phases: list[tuple[str, list, list[int]]] = [
        ("urgency", x_vars, [coef[z][r] for z, r in keys]),
        ("tie_break", x_vars, [rank[z] for z, _ in keys]),
    ]

    floors: dict[str, cp_model.IntVar] = {}
    if objective == "balanced":
        target = round(config.min_coverage * FLOOR_SCALE)
        for rid in scenario.resource_ids():
            requesting = [(z, var) for (z, r), var in x.items() if r == rid]
            if not requesting:
                continue
            floors[rid] = model.new_int_var(0, target, f"floor[{rid}]")
            for z_id, var in requesting:
                demand = scenario.demand_of(next(z for z in zones if z.id == z_id), rid)
                # x / d >= floor / 1000, kept integral: 1000 * x >= floor * d
                model.add(FLOOR_SCALE * var >= demand * floors[rid])
        floor_vars = list(floors.values())
        phases.insert(0, ("coverage_floor", floor_vars, [1] * len(floor_vars)))

    parameters = {
        "max_time_in_seconds": config.time_limit_s,
        "num_workers": config.workers,
        "random_seed": config.random_seed,
    }
    reports: list[SolverPhase] = []
    values: dict[tuple[str, str], int] | None = None
    floor_values: dict[str, int] = {}
    statuses: list[PolicyStatus] = []
    urgency_value: int | None = None
    started = perf_counter()

    for name, variables, weights in phases:
        expr = cp_model.LinearExpr.weighted_sum(variables, weights)
        model.clear_objective()
        model.maximize(expr)
        if values is not None:
            model.clear_hints()
            for key, var in x.items():
                model.add_hint(var, values[key])
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = max(
            0.01, config.time_limit_s - (perf_counter() - started)
        )
        solver.parameters.num_workers = config.workers
        solver.parameters.random_seed = config.random_seed
        raw = solver.solve(model)
        status = _STATUS.get(raw, PolicyStatus.UNKNOWN)
        has_solution = status in (PolicyStatus.OPTIMAL, PolicyStatus.FEASIBLE)
        reports.append(
            SolverPhase(
                name=name,
                status=solver.status_name(raw),
                objective_value=solver.objective_value if has_solution else None,
                best_bound=solver.best_objective_bound if has_solution else None,
                wall_time_ms=solver.wall_time * 1000,
            )
        )
        statuses.append(status)
        if not has_solution:
            break
        values = {key: int(solver.value(var)) for key, var in x.items()}
        if name == "coverage_floor":
            floor_values = {rid: int(solver.value(var)) for rid, var in floors.items()}
        # Exact integer value of this phase's objective, recomputed from the solution (the
        # solver reports it as a float, which loses precision on very large instances).
        reached = sum(w * int(solver.value(v)) for v, w in zip(variables, weights, strict=True))
        if name == "urgency":
            urgency_value = reached
        # Freeze this phase's optimum (or the value reached) before optimising the next.
        model.add(expr >= reached)

    report_base = dict(
        objective=objective,
        objective_value=urgency_value,
        phases=tuple(reports),
        variables=len(model.proto.variables),
        constraints=len(model.proto.constraints),
        parameters=parameters,
        coefficients=coef,
        coverage_floor={rid: v / FLOOR_SCALE for rid, v in floor_values.items()},
    )

    if values is None:
        status = statuses[-1]
        message = (
            f"CP-SAT returned {status} before finding any plan; no allocation is shown "
            "rather than an invented one."
        )
        return AllocationResult(
            policy_id=policy_id,
            status=status,
            zone_order=(),
            cells=(),
            solver=SolverReport(status=status, message=message, **report_base),
            message=message,
        )

    complete = all(s is PolicyStatus.OPTIMAL for s in statuses) and len(statuses) == len(phases)
    status = PolicyStatus.OPTIMAL if complete else PolicyStatus.FEASIBLE
    message = (
        ""
        if complete
        else "At least one solve phase ended without a proof of optimality; the plan is valid "
        "but not proven optimal for the full lexicographic objective."
    )
    allocated = {key: values.get(key, 0) for key in x}
    cells = _explain_cells(scenario, zones, coef, allocated, floor_values, objective, status)
    order = tuple(
        z.id for z in sorted(zones, key=lambda z: (-urgency[z.id], z.arrival_order, z.id))
    )
    return AllocationResult(
        policy_id=policy_id,
        status=status,
        zone_order=order,
        cells=tuple(cells),
        solver=SolverReport(status=status, message=message, **report_base),
        message=message,
    )


def _floor_units(fraction: float, demand: int) -> int:
    """Smallest whole number of units meeting the floor: ceil(fraction * demand)."""
    return -(-round(fraction * FLOOR_SCALE) * demand // FLOOR_SCALE) if demand else 0


def _names(zones: list) -> str:
    """Short zone names ("Zone A" from "Zone A · Northern floodplain")."""
    return ", ".join(z.name.split("·")[0].strip() for z in zones)


def _explain_cells(
    scenario: Scenario,
    zones: list,
    coef: Mapping[str, Mapping[str, int]],
    allocated: Mapping[tuple[str, str], int],
    floors: Mapping[str, int],
    objective: Objective,
    status: PolicyStatus,
) -> list[CellResult]:
    """Explain every cell from quantities in the solved model; no counterfactual claims."""
    cells: list[CellResult] = []
    for zone in zones:
        for rid in scenario.resource_ids():
            stock = scenario.stock[rid]
            requested = scenario.demand_of(zone, rid)
            got = allocated.get((zone.id, rid), 0)
            limit = basic_limit(stock, requested, got)
            if limit in BASIC_REASON:
                cells.append(CellResult(zone.id, rid, requested, got, limit, BASIC_REASON[limit]))
                continue
            if limit is Limit.ZERO_STOCK:
                cells.append(
                    CellResult(zone.id, rid, requested, got, limit, zero_stock_reason(requested))
                )
                continue

            used = sum(v for (_, r), v in allocated.items() if r == rid)
            unmet = requested - got
            if used < stock:
                # Cannot happen at a proven optimum (an idle unit could raise the objective).
                cells.append(
                    CellResult(
                        zone.id,
                        rid,
                        requested,
                        got,
                        Limit.NOT_PROVEN,
                        f"{stock - used} of {stock} units were left unallocated in a plan "
                        f"CP-SAT reported as {status}, not proven optimal ({unmet} unmet).",
                    )
                )
                continue

            mine = coef[zone.id][rid]
            others = [z for z in zones if z.id != zone.id]
            # Only zones that actually compete for this resource are named.
            rivals = [z for z in others if scenario.demand_of(z, rid) > 0]
            higher = [z for z in rivals if coef[z.id][rid] > mine]
            equal = [z for z in rivals if coef[z.id][rid] == mine]
            parts = [f"All {stock} units are allocated ({unmet} unmet)."]
            if objective == "balanced" and rid in floors:
                fraction = floors[rid] / FLOOR_SCALE
                reserved = sum(_floor_units(fraction, scenario.demand_of(z, rid)) for z in others)
                parts.append(
                    f"Balanced mode first guaranteed every requesting zone {fraction:.1%} of its "
                    f"request (this zone: {_floor_units(fraction, requested)}; the others: "
                    f"{reserved}), then gave the remaining stock by urgency."
                )
            if higher:
                units = sum(allocated.get((z.id, rid), 0) for z in higher)
                parts.append(
                    f"Zones with higher urgency ({_names(higher)}) received {units} units."
                )
            if equal and status is PolicyStatus.OPTIMAL:
                parts.append(
                    f"It ties on urgency with {_names(equal)}; the tie-break favours earlier "
                    f"arrival."
                )
            if not higher and not equal and objective == "urgency_first" and requested > stock:
                parts.append(
                    "It has the highest urgency for this resource and asked for more "
                    "than the depot holds."
                )
            cells.append(
                CellResult(zone.id, rid, requested, got, Limit.STOCK_EXHAUSTED, " ".join(parts))
            )
    return cells
