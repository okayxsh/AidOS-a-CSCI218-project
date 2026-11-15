"""Simulation sessions: pure functions from one immutable session state to the next.

    create_session -> READY, step 0 scored and allocated
    control(start | pause | resume | complete | reset)
    apply(event):  check state -> reducer (copy + validate) -> fuzzy urgency -> every policy
                   (CP-SAT included) -> independent validation -> outcome hash -> new state
    replay(events): reset, start, then apply each event in order; all or nothing

Nothing here mutates a session: every function returns a new SessionState, so a failure at
any point leaves the caller's state exactly as it was (atomic events). Storage, locking and
versions-on-the-wire live in store.py; HTTP lives in api/routes_simulation.py.

Determinism: the same initial scenario, events and configuration give the same snapshot
hashes, scores, allocations and outcome hashes. Only wall-clock timings differ.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field, replace
from typing import Any

from pydantic import TypeAdapter, ValidationError

from aidos import __version__ as ENGINE_VERSION
from aidos.ai.constraints import AidosConfig
from aidos.ai.fuzzy import default_config
from aidos.ai.policies import PolicyId
from aidos.domain.models import Scenario
from aidos.domain.snapshots import snapshot_hash
from aidos.domain.validation import ScenarioValidationError, parse_scenario
from aidos.pipeline import POLICY_ORDER, Comparison, PolicyRun, compare
from aidos.simulation.events import Event
from aidos.simulation.fsm import Action, SimState, transition
from aidos.simulation.reducer import DispatchCell, EventRejectedError, ResolvedZone, apply_event

MAX_EVENTS = 200
RECOMMENDABLE = (PolicyId.AIDOS, PolicyId.AIDOS_BALANCED)
EXPORT_FORMAT = "aidos-simulation"
EXPORT_VERSION = "1.0"

EVENT_ADAPTER: TypeAdapter[Any] = TypeAdapter(Event)


class SolverFailedError(Exception):
    """The recommended policy returned no plan for the new state; the event was not applied."""


class InvariantBreachError(Exception):
    """A computed plan failed the independent validator. Carries the ERROR-state session."""

    def __init__(self, message: str, session: SessionState):
        self.session = session
        super().__init__(message)


class _PlanInvalidError(Exception):
    """Internal: a plan failed validation (an engine defect, never a user error)."""


class ReplayError(Exception):
    def __init__(self, index: int, cause: Exception):
        self.index, self.cause = index, cause
        super().__init__(f"Event {index + 1} could not be replayed: {cause}")


@dataclass(frozen=True)
class SimulationConfig:
    policy: PolicyId = PolicyId.AIDOS  # the recommendation; the other policies are compared
    aidos: AidosConfig = field(default_factory=AidosConfig)


@dataclass(frozen=True)
class LedgerEntry:
    """Units that left the depot. Append-only: nothing is ever returned to stock."""

    seq: int
    event_id: str
    policy: PolicyId
    snapshot_hash: str  # the snapshot whose plan was dispatched
    cells: tuple[DispatchCell, ...]

    @property
    def total(self) -> int:
        return sum(c.units for c in self.cells)


@dataclass(frozen=True)
class StepRecord:
    seq: int  # 0 = initial snapshot; n = after the n-th event
    event: Any | None  # the validated event, or None for step 0
    event_id: str | None
    scenario: Scenario
    snapshot_hash: str
    comparison: Comparison  # every policy on this snapshot, with the shared fuzzy scores
    outcome_hash: str  # hash of the logical outcome (no timings)
    changes: tuple[str, ...] = ()
    dispatch: tuple[DispatchCell, ...] = ()
    resolved: ResolvedZone | None = None

    def run(self, policy: PolicyId) -> PolicyRun:
        return next(r for r in self.comparison.runs if r.result.policy_id is policy)


@dataclass(frozen=True)
class SessionState:
    session_id: str
    scenario_id: str
    config: SimulationConfig
    state: SimState
    version: int
    steps: tuple[StepRecord, ...]  # steps[0] is the initial snapshot
    ledger: tuple[LedgerEntry, ...] = ()
    retired: tuple[ResolvedZone, ...] = ()
    error: str | None = None

    @property
    def initial(self) -> StepRecord:
        return self.steps[0]

    @property
    def current(self) -> StepRecord:
        return self.steps[-1]

    @property
    def event_count(self) -> int:
        return len(self.steps) - 1

    @property
    def dispatched_units(self) -> int:
        return sum(entry.total for entry in self.ledger)


# ---------------------------------------------------------------- hashing


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def event_payload(event: Any) -> dict[str, Any]:
    return event.model_dump(mode="json")


def outcome_hash(comparison: Comparison, dispatch: Sequence[DispatchCell]) -> str:
    """SHA-256 of everything a replay must reproduce: snapshot, scores, plans, dispatch."""
    payload = {
        "snapshot": comparison.snapshot_hash,
        "urgency": {u.zone_id: u.result.score for u in comparison.urgency},
        "runs": [
            {
                "policy": str(r.result.policy_id),
                "status": str(r.result.status),
                "cells": sorted((c.zone_id, c.resource_id, c.allocated) for c in r.result.cells),
            }
            for r in comparison.runs
        ],
        "dispatch": sorted((c.zone_id, c.resource_id, c.units) for c in dispatch),
    }
    return hashlib.sha256(_canonical(payload).encode()).hexdigest()


def event_id(seq: int, event: Any, previous_hash: str) -> str:
    """Content-addressed id: the same event on the same snapshot gets the same id on replay."""
    digest = hashlib.sha256((_canonical(event_payload(event)) + previous_hash).encode())
    return f"e{seq:03d}-{digest.hexdigest()[:8]}"


# ---------------------------------------------------------------- steps


def evaluate_step(
    seq: int,
    scenario: Scenario,
    config: SimulationConfig,
    *,
    event: Any | None = None,
    event_id_: str | None = None,
    changes: tuple[str, ...] = (),
    dispatch: tuple[DispatchCell, ...] = (),
    resolved: ResolvedZone | None = None,
) -> StepRecord:
    """Score and allocate one snapshot with every policy, then check every plan independently."""
    comparison = compare(scenario, POLICY_ORDER, config.aidos)
    recommended = next(r for r in comparison.runs if r.result.policy_id is config.policy)
    if not recommended.result.has_plan:
        raise SolverFailedError(
            f"{config.policy} returned {recommended.result.status} for the new state, so no "
            "recommendation exists; the event was not applied."
        )
    for run in comparison.runs:
        if run.result.has_plan and not run.validation.valid:
            first = run.validation.violations[0]
            raise _PlanInvalidError(
                f"{run.result.policy_id} broke a hard constraint: {first.detail}"
            )
    return StepRecord(
        seq=seq,
        event=event,
        event_id=event_id_,
        scenario=scenario,
        snapshot_hash=comparison.snapshot_hash,
        comparison=comparison,
        outcome_hash=outcome_hash(comparison, dispatch),
        changes=changes,
        dispatch=dispatch,
        resolved=resolved,
    )


def create_session(
    scenario: Scenario, session_id: str, config: SimulationConfig | None = None
) -> SessionState:
    config = config or SimulationConfig()
    if config.policy not in RECOMMENDABLE:
        raise ValueError(f"policy must be one of {[p.value for p in RECOMMENDABLE]}")
    config.aidos.check(scenario)
    try:
        initial = evaluate_step(0, scenario, config)
    except _PlanInvalidError as breach:  # a defect, not a user error
        raise SolverFailedError(str(breach)) from None
    return SessionState(
        session_id=session_id,
        scenario_id=scenario.scenario_id,
        config=config,
        state=SimState.READY,
        version=1,
        steps=(initial,),
    )


def control(session: SessionState, action: Action) -> SessionState:
    """start / pause / resume / complete / reset. Reset restores step 0 and clears everything."""
    state = transition(session.state, action)
    if action is Action.RESET:
        return replace(
            session,
            state=state,
            version=session.version + 1,
            steps=(session.initial,),
            ledger=(),
            retired=(),
            error=None,
        )
    return replace(session, state=state, version=session.version + 1)


def apply(session: SessionState, event: Any) -> SessionState:
    """Apply one event atomically. Raises; on any error the given session is unchanged."""
    transition(session.state, Action.APPLY_EVENT)
    if session.event_count >= MAX_EVENTS:
        raise EventRejectedError(
            f"A session holds at most {MAX_EVENTS} events; reset or complete it.", "too_many_events"
        )
    current = session.current
    plans = {r.result.policy_id: r.result for r in current.comparison.runs}
    applied = apply_event(
        current.scenario,
        event,
        snapshot_hash=current.snapshot_hash,
        plans=plans,
        retired=session.retired,
    )
    seq = current.seq + 1
    eid = event_id(seq, event, current.snapshot_hash)
    try:
        step = evaluate_step(
            seq,
            applied.scenario,
            session.config,
            event=event,
            event_id_=eid,
            changes=applied.changes,
            dispatch=applied.dispatch,
            resolved=applied.resolved,
        )
    except _PlanInvalidError as breach:
        failed = replace(
            session,
            state=transition(session.state, Action.FAIL),
            version=session.version + 1,
            error=f"Event {seq} was not applied: {breach}",
        )
        raise InvariantBreachError(str(breach), failed) from None

    ledger = session.ledger
    if applied.dispatch:
        policy = event.policy
        ledger = (*ledger, LedgerEntry(seq, eid, policy, current.snapshot_hash, applied.dispatch))
    retired = (*session.retired, applied.resolved) if applied.resolved else session.retired
    return replace(
        session,
        version=session.version + 1,
        steps=(*session.steps, step),
        ledger=ledger,
        retired=retired,
    )


def parse_events(raw_events: Iterable[Any]) -> list[Any]:
    """Validate raw event dicts (e.g. from an export). Raises ReplayError at the first bad one."""
    events = []
    for index, raw in enumerate(raw_events):
        try:
            events.append(raw if not isinstance(raw, dict) else EVENT_ADAPTER.validate_python(raw))
        except ValidationError as err:
            raise ReplayError(index, EventRejectedError(str(err).splitlines()[0])) from None
    return events


def replay(session: SessionState, events: Sequence[Any]) -> SessionState:
    """Reset, start and apply `events` in order. All or nothing: any failure raises."""
    state = control(session, Action.RESET) if session.state is not SimState.READY else session
    state = control(state, Action.START)
    for index, event in enumerate(events):
        try:
            state = apply(state, event)
        except (EventRejectedError, SolverFailedError, InvariantBreachError) as err:
            raise ReplayError(index, err) from None
    return state


# ---------------------------------------------------------------- export / import


def export_session(session: SessionState) -> dict[str, Any]:
    """A self-contained replay file: the initial scenario, configuration and ordered events."""
    aidos = session.config.aidos
    return {
        "format": EXPORT_FORMAT,
        "format_version": EXPORT_VERSION,
        "engine_version": ENGINE_VERSION,
        "fuzzy_version": default_config().version,
        "scenario_id": session.scenario_id,
        "initial_snapshot_hash": session.initial.snapshot_hash,
        "initial_scenario": session.initial.scenario.model_dump(mode="json"),
        "config": {
            "policy": session.config.policy.value,
            "epsilon": aidos.epsilon,
            "resource_weights": dict(aidos.resource_weights),
            "min_coverage": aidos.min_coverage,
            "time_limit_s": aidos.time_limit_s,
        },
        "events": [
            {"seq": s.seq, "event_id": s.event_id, "event": event_payload(s.event)}
            for s in session.steps[1:]
        ],
        "outcomes": [
            {"seq": s.seq, "snapshot_hash": s.snapshot_hash, "outcome_hash": s.outcome_hash}
            for s in session.steps
        ],
    }


@dataclass(frozen=True)
class Verification:
    checked: bool  # False when the document recorded no outcomes
    matches: bool
    first_mismatch_seq: int | None
    engine_version_recorded: str | None


def import_session(document: dict[str, Any], session_id: str) -> tuple[SessionState, Verification]:
    """Rebuild a session from an export and check it reproduces the recorded outcomes."""
    if document.get("format") != EXPORT_FORMAT or document.get("format_version") != EXPORT_VERSION:
        raise ReplayError(-1, EventRejectedError("Not an aidos-simulation 1.0 document."))
    try:
        scenario = parse_scenario(document["initial_scenario"])
    except (KeyError, TypeError):
        raise ReplayError(-1, EventRejectedError("The document has no initial_scenario.")) from None
    except ScenarioValidationError as err:
        raise ReplayError(-1, EventRejectedError(f"initial_scenario is invalid: {err}")) from None
    recorded_hash = document.get("initial_snapshot_hash")
    if recorded_hash is not None and recorded_hash != snapshot_hash(scenario):
        raise ReplayError(
            -1, EventRejectedError("initial_scenario does not match initial_snapshot_hash.")
        )
    raw_config = document.get("config") or {}
    try:
        config = SimulationConfig(
            policy=PolicyId(raw_config.get("policy", "aidos")),
            aidos=AidosConfig(
                epsilon=float(raw_config.get("epsilon", 1.0)),
                resource_weights=dict(raw_config.get("resource_weights", {})),
                min_coverage=float(raw_config.get("min_coverage", 0.25)),
                time_limit_s=float(raw_config.get("time_limit_s", 5.0)),
            ),
        )
    except (ValueError, TypeError) as err:
        raise ReplayError(-1, EventRejectedError(f"config is invalid: {err}")) from None

    raw_events = document.get("events")
    if not isinstance(raw_events, list):
        raise ReplayError(-1, EventRejectedError("events must be a list."))
    ordered = []
    for index, item in enumerate(raw_events):
        if not isinstance(item, dict) or "event" not in item:
            raise ReplayError(index, EventRejectedError("each entry needs an 'event' object"))
        if item.get("seq", index + 1) != index + 1:
            raise ReplayError(index, EventRejectedError("events are out of order"))
        ordered.append(item["event"])
    events = parse_events(ordered)

    session = replay(create_session(scenario, session_id, config), events)

    outcomes = document.get("outcomes")
    if not outcomes:
        return session, Verification(False, True, None, document.get("engine_version"))
    mismatch = None
    for step, recorded in zip(session.steps, outcomes, strict=False):
        if (step.snapshot_hash, step.outcome_hash) != (
            recorded.get("snapshot_hash"),
            recorded.get("outcome_hash"),
        ):
            mismatch = step.seq
            break
    if mismatch is None and len(outcomes) != len(session.steps):
        mismatch = min(len(outcomes), len(session.steps))
    return session, Verification(True, mismatch is None, mismatch, document.get("engine_version"))
