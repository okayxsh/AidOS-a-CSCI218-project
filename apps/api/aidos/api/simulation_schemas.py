"""HTTP schemas for the simulation API. Adapters only: every value comes from the engine."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from aidos.ai.policies import PolicyId
from aidos.api.schemas import AidosConfigIn, AidosConfigOut, CompareResponse, SummaryOut
from aidos.domain.models import Scenario
from aidos.evaluation.metrics import summarize_scenario
from aidos.simulation.compare import StepDiff
from aidos.simulation.events import Event
from aidos.simulation.fsm import allowed_actions
from aidos.simulation.session import MAX_EVENTS, SessionState, StepRecord, Verification

# ---------------------------------------------------------------- requests


class CreateSessionRequest(BaseModel):
    """Start from a built-in scenario (`scenario_id`) or a full scenario. Send exactly one."""

    scenario_id: str | None = None
    scenario: Scenario | None = None
    policy: Literal["aidos", "aidos_balanced"] = "aidos"
    config: AidosConfigIn | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> CreateSessionRequest:
        if (self.scenario_id is None) == (self.scenario is None):
            raise ValueError("send exactly one of 'scenario_id' or 'scenario'")
        return self


class VersionedRequest(BaseModel):
    expected_version: int = Field(ge=1, description="The session version you last saw.")


class EventRequest(VersionedRequest):
    event: Event


class ReplayRequest(VersionedRequest):
    events: list[Event] = Field(max_length=MAX_EVENTS)


class ExportConfig(BaseModel):
    # Same bounds as AidosConfigIn, so an imported session cannot exceed the API's limits.
    policy: Literal["aidos", "aidos_balanced"] = "aidos"
    epsilon: float = Field(default=1.0, gt=0, le=100)
    resource_weights: dict[str, int] = {}
    min_coverage: float = Field(default=0.25, ge=0, le=1)
    time_limit_s: float = Field(default=5.0, ge=0.01, le=10)


class ExportedEvent(BaseModel):
    seq: int = Field(ge=1)
    event_id: str | None = None
    event: dict[str, Any]


class ExportedOutcome(BaseModel):
    seq: int = Field(ge=0)
    snapshot_hash: str
    outcome_hash: str


class SimulationExport(BaseModel):
    """A self-contained, replayable record of a session."""

    format: Literal["aidos-simulation"]
    format_version: Literal["1.0"]
    engine_version: str | None = None
    fuzzy_version: str | None = None
    scenario_id: str
    initial_snapshot_hash: str
    initial_scenario: dict[str, Any]
    config: ExportConfig
    events: list[ExportedEvent] = Field(max_length=MAX_EVENTS)
    outcomes: list[ExportedOutcome] = []


# ---------------------------------------------------------------- responses


class DispatchCellOut(BaseModel):
    zone_id: str
    resource_id: str
    units: int


class LedgerEntryOut(BaseModel):
    seq: int
    event_id: str
    policy: PolicyId
    snapshot_hash: str
    total: int
    cells: list[DispatchCellOut]


class ResolvedZoneOut(BaseModel):
    zone_id: str
    name: str
    resolved_at_step: int
    remaining_demand: dict[str, int]


class StepOut(BaseModel):
    seq: int = Field(description="0 is the initial snapshot; n is the state after event n.")
    event_id: str | None
    event: dict[str, Any] | None
    sim_step: int = Field(description="The scenario clock (advanced only by time_advanced).")
    snapshot_hash: str
    outcome_hash: str = Field(description="Hash of the logical outcome; timings excluded.")
    changes: list[str]
    dispatch: list[DispatchCellOut]
    scenario: Scenario
    summary: SummaryOut
    comparison: CompareResponse

    @classmethod
    def from_domain(cls, step: StepRecord) -> StepOut:
        return cls(
            seq=step.seq,
            event_id=step.event_id,
            event=step.event.model_dump(mode="json") if step.event else None,
            sim_step=step.scenario.step,
            snapshot_hash=step.snapshot_hash,
            outcome_hash=step.outcome_hash,
            changes=list(step.changes),
            dispatch=[DispatchCellOut(**vars(c)) for c in step.dispatch],
            scenario=step.scenario,
            summary=SummaryOut.from_domain(summarize_scenario(step.scenario)),
            comparison=CompareResponse.from_domain(step.comparison),
        )


class HistoryItemOut(BaseModel):
    seq: int
    event_id: str | None
    type: str | None
    event: dict[str, Any] | None
    sim_step: int
    summary: str
    snapshot_hash: str
    outcome_hash: str
    allocated_units: int
    unmet_units: int
    urgency_weighted_coverage: float | None
    changed_cells: int = Field(description="Recommended-plan cells that differ from step seq-1.")
    dispatched_units: int


class UrgencyDeltaOut(BaseModel):
    zone_id: str
    name: str
    score_before: float | None
    score_after: float | None
    category_before: str | None
    category_after: str | None
    rank_before: int | None
    rank_after: int | None


class CellDeltaOut(BaseModel):
    zone_id: str
    resource_id: str
    requested_before: int
    requested_after: int
    allocated_before: int
    allocated_after: int


class PolicyDeltaOut(BaseModel):
    policy_id: PolicyId
    status_before: str
    status_after: str
    changed_cells: int
    cells: list[CellDeltaOut]
    allocated_before: int
    allocated_after: int
    unmet_before: int
    unmet_after: int
    uwc_before: float | None
    uwc_after: float | None


class ResourceDeltaOut(BaseModel):
    resource_id: str
    label: str
    stock_before: int
    stock_after: int
    requested_before: int
    requested_after: int
    shortfall_before: int
    shortfall_after: int


class StepDiffOut(BaseModel):
    before_seq: int
    after_seq: int
    events: list[str]
    input_changes: list[str]
    urgency: list[UrgencyDeltaOut]
    order_before: list[str]
    order_after: list[str]
    resources: list[ResourceDeltaOut]
    policies: list[PolicyDeltaOut] = Field(description="Recommended policy first, then FCFS.")
    recommendation_changed: bool
    explanation: list[str]

    @classmethod
    def from_domain(cls, d: StepDiff) -> StepDiffOut:
        return cls(
            before_seq=d.before_seq,
            after_seq=d.after_seq,
            events=list(d.events),
            input_changes=list(d.input_changes),
            urgency=[UrgencyDeltaOut(**vars(u)) for u in d.urgency],
            order_before=list(d.order_before),
            order_after=list(d.order_after),
            resources=[ResourceDeltaOut(**vars(r)) for r in d.resources],
            policies=[
                PolicyDeltaOut(
                    policy_id=p.policy_id,
                    status_before=p.status_before,
                    status_after=p.status_after,
                    changed_cells=len(p.changed),
                    cells=[CellDeltaOut(**vars(c)) for c in p.cells],
                    allocated_before=p.allocated_before,
                    allocated_after=p.allocated_after,
                    unmet_before=p.unmet_before,
                    unmet_after=p.unmet_after,
                    uwc_before=p.uwc_before,
                    uwc_after=p.uwc_after,
                )
                for p in d.policies
            ],
            recommendation_changed=d.recommendation_changed,
            explanation=list(d.explanation),
        )


class SessionOut(BaseModel):
    session_id: str
    scenario_id: str
    state: str
    version: int = Field(description="Send this as expected_version with the next change.")
    allowed_actions: list[str]
    policy: PolicyId = Field(description="The policy whose plan is the recommendation.")
    config: AidosConfigOut
    event_count: int
    max_events: int
    error: str | None
    current: StepOut
    diff: StepDiffOut | None = Field(description="Previous step → current step; null at step 0.")
    history: list[HistoryItemOut]
    ledger: list[LedgerEntryOut]
    dispatched_units: int
    resolved_zones: list[ResolvedZoneOut]


class VerificationOut(BaseModel):
    checked: bool = Field(description="False when the document recorded no outcomes.")
    matches: bool
    first_mismatch_seq: int | None
    engine_version_recorded: str | None

    @classmethod
    def from_domain(cls, v: Verification) -> VerificationOut:
        return cls(**vars(v))


class ImportResponse(BaseModel):
    session: SessionOut
    verification: VerificationOut


# ---------------------------------------------------------------- builders


def history_items(session: SessionState) -> list[HistoryItemOut]:
    items = []
    previous: StepRecord | None = None
    for step in session.steps:
        run = step.run(session.config.policy)
        metrics = run.metrics
        if previous is None:
            changed = 0
        else:
            before = {
                (c.zone_id, c.resource_id): c.allocated
                for c in previous.run(session.config.policy).result.cells
            }
            after = {(c.zone_id, c.resource_id): c.allocated for c in run.result.cells}
            changed = sum(
                1 for k in before.keys() | after.keys() if before.get(k, 0) != after.get(k, 0)
            )
        items.append(
            HistoryItemOut(
                seq=step.seq,
                event_id=step.event_id,
                type=step.event.type if step.event else None,
                event=step.event.model_dump(mode="json") if step.event else None,
                sim_step=step.scenario.step,
                summary=" ".join(step.changes) if step.changes else "Initial snapshot loaded.",
                snapshot_hash=step.snapshot_hash,
                outcome_hash=step.outcome_hash,
                allocated_units=metrics.allocated_units if metrics else 0,
                unmet_units=metrics.unmet_units if metrics else 0,
                urgency_weighted_coverage=metrics.urgency_weighted_coverage if metrics else None,
                changed_cells=changed,
                dispatched_units=sum(c.units for c in step.dispatch),
            )
        )
        previous = step
    return items


def session_out(session: SessionState, diff: StepDiff | None) -> SessionOut:
    return SessionOut(
        session_id=session.session_id,
        scenario_id=session.scenario_id,
        state=session.state.value,
        version=session.version,
        allowed_actions=[a.value for a in allowed_actions(session.state)],
        policy=session.config.policy,
        config=AidosConfigOut.from_domain(session.config.aidos),
        event_count=session.event_count,
        max_events=MAX_EVENTS,
        error=session.error,
        current=StepOut.from_domain(session.current),
        diff=StepDiffOut.from_domain(diff) if diff else None,
        history=history_items(session),
        ledger=[
            LedgerEntryOut(
                seq=e.seq,
                event_id=e.event_id,
                policy=e.policy,
                snapshot_hash=e.snapshot_hash,
                total=e.total,
                cells=[DispatchCellOut(**vars(c)) for c in e.cells],
            )
            for e in session.ledger
        ],
        dispatched_units=session.dispatched_units,
        resolved_zones=[
            ResolvedZoneOut(
                zone_id=r.zone_id,
                name=r.name,
                resolved_at_step=r.resolved_at_step,
                remaining_demand=dict(r.remaining_demand),
            )
            for r in session.retired
        ],
    )
