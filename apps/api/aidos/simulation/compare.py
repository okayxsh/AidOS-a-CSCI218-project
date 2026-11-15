"""Before/after comparison of two simulation steps, and the explanation built from it.

Every sentence is derived from the two stored steps: the inputs the events changed, the
fuzzy scores and urgency order, the per-resource stock and requests, and the plans of the
recommended policy and FCFS. When the recommended plan does not change, the explanation
says so instead of inventing a difference.
"""

from __future__ import annotations

from dataclasses import dataclass

from aidos.ai.policies import PolicyId
from aidos.domain.models import Scenario
from aidos.evaluation.metrics import summarize_scenario
from aidos.simulation.session import SessionState, StepRecord

RATING_EVENTS = {"urgency_changed"}


@dataclass(frozen=True)
class UrgencyDelta:
    zone_id: str
    name: str
    score_before: float | None  # None: the zone was not active at that step
    score_after: float | None
    category_before: str | None
    category_after: str | None
    rank_before: int | None  # 1 = most urgent active zone
    rank_after: int | None


@dataclass(frozen=True)
class CellDelta:
    zone_id: str
    resource_id: str
    requested_before: int
    requested_after: int
    allocated_before: int
    allocated_after: int


@dataclass(frozen=True)
class PolicyDelta:
    policy_id: PolicyId
    status_before: str
    status_after: str
    cells: tuple[CellDelta, ...]  # every (zone, resource) present at either step
    allocated_before: int
    allocated_after: int
    unmet_before: int
    unmet_after: int
    uwc_before: float | None
    uwc_after: float | None

    @property
    def changed(self) -> tuple[CellDelta, ...]:
        return tuple(c for c in self.cells if c.allocated_before != c.allocated_after)


@dataclass(frozen=True)
class ResourceDelta:
    resource_id: str
    label: str
    stock_before: int
    stock_after: int
    requested_before: int
    requested_after: int
    shortfall_before: int
    shortfall_after: int


@dataclass(frozen=True)
class StepDiff:
    before_seq: int
    after_seq: int
    events: tuple[str, ...]  # event types applied between the two steps
    input_changes: tuple[str, ...]
    urgency: tuple[UrgencyDelta, ...]
    order_before: tuple[str, ...]
    order_after: tuple[str, ...]
    resources: tuple[ResourceDelta, ...]
    policies: tuple[PolicyDelta, ...]  # the recommended policy first, then FCFS
    recommendation_changed: bool
    explanation: tuple[str, ...]


def _short(name: str) -> str:
    return name.split("·")[0].strip()


def _names(scenario: Scenario) -> dict[str, str]:
    return {z.id: _short(z.name) for z in scenario.zones}


def _order(scenario: Scenario, scores: dict[str, float]) -> tuple[str, ...]:
    """Active zones by urgency (highest first), ties by arrival order, then id."""
    active = scenario.active_zones()
    return tuple(z.id for z in sorted(active, key=lambda z: (-scores[z.id], z.arrival_order, z.id)))


def _policy_delta(policy: PolicyId, before: StepRecord, after: StepRecord) -> PolicyDelta:
    a, b = before.run(policy), after.run(policy)
    cells_a = {(c.zone_id, c.resource_id): c for c in a.result.cells}
    cells_b = {(c.zone_id, c.resource_id): c for c in b.result.cells}
    keys = list(cells_a) + [k for k in cells_b if k not in cells_a]
    cells = tuple(
        CellDelta(
            zone_id=z,
            resource_id=r,
            requested_before=cells_a[z, r].requested if (z, r) in cells_a else 0,
            requested_after=cells_b[z, r].requested if (z, r) in cells_b else 0,
            allocated_before=cells_a[z, r].allocated if (z, r) in cells_a else 0,
            allocated_after=cells_b[z, r].allocated if (z, r) in cells_b else 0,
        )
        for z, r in keys
    )
    ma, mb = a.metrics, b.metrics
    return PolicyDelta(
        policy_id=policy,
        status_before=str(a.result.status),
        status_after=str(b.result.status),
        cells=cells,
        allocated_before=ma.allocated_units if ma else 0,
        allocated_after=mb.allocated_units if mb else 0,
        unmet_before=ma.unmet_units if ma else 0,
        unmet_after=mb.unmet_units if mb else 0,
        uwc_before=ma.urgency_weighted_coverage if ma else None,
        uwc_after=mb.urgency_weighted_coverage if mb else None,
    )


def _pct(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.1%}"


def diff_steps(session: SessionState, before_seq: int, after_seq: int) -> StepDiff:
    """Compare two recorded steps of one session (before_seq < after_seq)."""
    if not 0 <= before_seq < after_seq <= session.current.seq:
        raise ValueError(f"need 0 <= before < after <= {session.current.seq}")
    before, after = session.steps[before_seq], session.steps[after_seq]
    between = session.steps[before_seq + 1 : after_seq + 1]
    policy = session.config.policy

    names = {**_names(before.scenario), **_names(after.scenario)}
    resource_label = {r.id: r.label for r in after.scenario.resources}

    # ---- urgency and order
    scores_a = {u.zone_id: u.result for u in before.comparison.urgency if u.active}
    scores_b = {u.zone_id: u.result for u in after.comparison.urgency if u.active}
    order_a = _order(before.scenario, {k: v.score for k, v in scores_a.items()})
    order_b = _order(after.scenario, {k: v.score for k, v in scores_b.items()})
    urgency = tuple(
        UrgencyDelta(
            zone_id=z,
            name=names.get(z, z),
            score_before=scores_a[z].score if z in scores_a else None,
            score_after=scores_b[z].score if z in scores_b else None,
            category_before=scores_a[z].category if z in scores_a else None,
            category_after=scores_b[z].category if z in scores_b else None,
            rank_before=order_a.index(z) + 1 if z in order_a else None,
            rank_after=order_b.index(z) + 1 if z in order_b else None,
        )
        for z in dict.fromkeys([*order_a, *order_b])
    )

    # ---- resources
    sum_a = {r.resource_id: r for r in summarize_scenario(before.scenario).resources}
    sum_b = {r.resource_id: r for r in summarize_scenario(after.scenario).resources}
    resources = tuple(
        ResourceDelta(
            resource_id=rid,
            label=resource_label[rid],
            stock_before=sum_a[rid].stock,
            stock_after=sum_b[rid].stock,
            requested_before=sum_a[rid].requested,
            requested_after=sum_b[rid].requested,
            shortfall_before=sum_a[rid].shortfall,
            shortfall_after=sum_b[rid].shortfall,
        )
        for rid in after.scenario.resource_ids()
    )

    policies = tuple(
        _policy_delta(p, before, after) for p in dict.fromkeys([policy, PolicyId.FCFS])
    )
    recommended = policies[0]
    fcfs = policies[-1]
    events = tuple(s.event.type for s in between)
    input_changes = tuple(change for s in between for change in s.changes)

    # ---- explanation, built only from the values above
    lines: list[str] = list(input_changes)
    for d in urgency:
        if d.score_before is None:
            lines.append(
                f"{d.name} is now in the problem with urgency {d.score_after:.1f} "
                f"({d.category_after})."
            )
        elif d.score_after is None:
            lines.append(f"{d.name} is no longer in the problem.")
        elif d.score_before != d.score_after:
            lines.append(
                f"{d.name} urgency {d.score_before:.1f} → {d.score_after:.1f} "
                f"({d.category_before} → {d.category_after})."
            )
    rated = [s.event.zone_id for s in between if s.event.type in RATING_EVENTS]
    for zone_id in dict.fromkeys(rated):
        d = next((u for u in urgency if u.zone_id == zone_id), None)
        if d and d.score_before is not None and d.score_before == d.score_after:
            lines.append(
                f"{d.name}'s ratings changed but its urgency stayed {d.score_after:.1f}: the "
                "rule base gives the same score for the new ratings."
            )
    label = lambda order: ", ".join(names.get(z, z) for z in order) or "none"  # noqa: E731
    if order_a != order_b:
        lines.append(f"Urgency order {label(order_a)} → {label(order_b)}.")
    else:
        lines.append(f"Urgency order unchanged: {label(order_b)}.")

    for r in resources:
        if (r.stock_before, r.requested_before) == (r.stock_after, r.requested_after):
            continue
        if r.shortfall_after == 0 and r.requested_after > 0:
            lines.append(
                f"{r.label}: stock {r.stock_after} now covers all {r.requested_after} requested."
            )
        elif r.shortfall_after:
            lines.append(
                f"{r.label}: shortfall {r.shortfall_before} → {r.shortfall_after} "
                f"(stock {r.stock_after}, requested {r.requested_after})."
            )

    policy_name = "AidOS" if policy is PolicyId.AIDOS else "AidOS balanced"
    changed = recommended.changed
    if changed:
        moves = "; ".join(
            f"{names.get(c.zone_id, c.zone_id)} {resource_label[c.resource_id].lower()} "
            f"{c.allocated_before} → {c.allocated_after}"
            for c in changed
        )
        lines.append(f"Recommended plan ({policy_name}) changed: {moves}.")
    else:
        stock_or_requests_same = all(
            (r.stock_before, r.requested_before) == (r.stock_after, r.requested_after)
            for r in resources
        )
        if order_a == order_b and stock_or_requests_same:
            reason = "the urgency order, the stock and the requests that determine it are unchanged"
        elif all(r.shortfall_after == 0 for r in resources) and all(
            r.shortfall_before == 0 for r in resources
        ):
            reason = "stock covers every request before and after, so every zone is met in full"
        else:
            reason = "the changed inputs do not alter which zones the stock reaches"
        lines.append(f"Recommended plan ({policy_name}) did not change: {reason}.")
    lines.append(
        f"Allocated {recommended.allocated_before} → {recommended.allocated_after} units; unmet "
        f"{recommended.unmet_before} → {recommended.unmet_after}; urgency-weighted coverage "
        f"{_pct(recommended.uwc_before)} → {_pct(recommended.uwc_after)}."
    )
    if fcfs is not recommended:
        if fcfs.changed:
            lines.append(f"FCFS on the same state changed {len(fcfs.changed)} allocation(s).")
        elif events and set(events) <= RATING_EVENTS:
            lines.append("FCFS on the same state did not change: it ignores urgency.")
        else:
            lines.append("FCFS on the same state did not change.")
    dispatched = sum(c.units for s in between for c in s.dispatch)
    if dispatched:
        lines.append(
            f"{dispatched} units were dispatched and recorded in the ledger; the new "
            "recommendation only covers what is still open."
        )

    return StepDiff(
        before_seq=before_seq,
        after_seq=after_seq,
        events=events,
        input_changes=input_changes,
        urgency=urgency,
        order_before=order_a,
        order_after=order_b,
        resources=resources,
        policies=policies,
        recommendation_changed=bool(changed),
        explanation=tuple(lines),
    )
