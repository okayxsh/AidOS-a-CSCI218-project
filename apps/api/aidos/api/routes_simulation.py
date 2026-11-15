"""Simulation endpoints: thin adapters over aidos.simulation (sessions, events, replay).

The session store lives on `app.state.sessions` (one process, in memory). Every change
names the version it expects; the engine computes the next state with pure functions and
the store swaps it in only on success.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, HTTPException, Query, Request, status

from aidos.ai.policies import PolicyId
from aidos.api.simulation_schemas import (
    CreateSessionRequest,
    EventRequest,
    HistoryItemOut,
    ImportResponse,
    ReplayRequest,
    SessionOut,
    SimulationExport,
    StepDiffOut,
    StepOut,
    VerificationOut,
    VersionedRequest,
    history_items,
    session_out,
)
from aidos.domain.snapshots import load_builtin_scenario
from aidos.simulation import session as engine
from aidos.simulation.compare import diff_steps
from aidos.simulation.fsm import Action
from aidos.simulation.session import SessionState, SimulationConfig
from aidos.simulation.store import SessionStore

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


def _store(request: Request) -> SessionStore:
    return request.app.state.sessions


def _out(session: SessionState) -> SessionOut:
    seq = session.current.seq
    return session_out(session, diff_steps(session, seq - 1, seq) if seq else None)


@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create_session(body: CreateSessionRequest, request: Request) -> SessionOut:
    scenario = body.scenario or load_builtin_scenario(body.scenario_id or "")
    store = _store(request)
    config = SimulationConfig(
        policy=PolicyId(body.policy),
        aidos=body.config.to_domain() if body.config else SimulationConfig().aidos,
    )
    return _out(store.add(engine.create_session(scenario, store.new_id(), config)))


@router.get("/sessions/{session_id}", response_model=SessionOut)
def get_session(session_id: str, request: Request) -> SessionOut:
    return _out(_store(request).get(session_id))


def _control(action: Action) -> Callable[[str, VersionedRequest, Request], SessionOut]:
    def handler(session_id: str, body: VersionedRequest, request: Request) -> SessionOut:
        updated = _store(request).mutate(
            session_id, body.expected_version, lambda s: engine.control(s, action)
        )
        return _out(updated)

    handler.__name__ = f"{action.value}_session"
    handler.__doc__ = f"{action.value.capitalize()} the session (see the state machine)."
    return handler


for _action in (Action.START, Action.PAUSE, Action.RESUME, Action.COMPLETE, Action.RESET):
    router.add_api_route(
        f"/sessions/{{session_id}}/{_action.value}",
        _control(_action),
        methods=["POST"],
        response_model=SessionOut,
    )


@router.post("/sessions/{session_id}/events", response_model=SessionOut)
def apply_event(session_id: str, body: EventRequest, request: Request) -> SessionOut:
    updated = _store(request).mutate(
        session_id, body.expected_version, lambda s: engine.apply(s, body.event)
    )
    return _out(updated)


@router.post("/sessions/{session_id}/replay", response_model=SessionOut)
def replay_session(session_id: str, body: ReplayRequest, request: Request) -> SessionOut:
    updated = _store(request).mutate(
        session_id, body.expected_version, lambda s: engine.replay(s, body.events)
    )
    return _out(updated)


@router.get("/sessions/{session_id}/history", response_model=list[HistoryItemOut])
def history(session_id: str, request: Request) -> list[HistoryItemOut]:
    return history_items(_store(request).get(session_id))


@router.get("/sessions/{session_id}/steps/{seq}", response_model=StepOut)
def step(session_id: str, seq: int, request: Request) -> StepOut:
    session = _store(request).get(session_id)
    if not 0 <= seq <= session.current.seq:
        raise HTTPException(404, f"Step {seq} does not exist (0-{session.current.seq}).")
    return StepOut.from_domain(session.steps[seq])


@router.get("/sessions/{session_id}/diff", response_model=StepDiffOut)
def diff(
    session_id: str,
    request: Request,
    before: int | None = Query(default=None, ge=0),
    after: int | None = Query(default=None, ge=0),
) -> StepDiffOut:
    """Compare two steps (default: the previous step and the current one)."""
    session = _store(request).get(session_id)
    after_seq = session.current.seq if after is None else after
    before_seq = after_seq - 1 if before is None else before
    if not 0 <= before_seq < after_seq <= session.current.seq:
        raise HTTPException(
            422,
            f"Need 0 <= before < after <= {session.current.seq}; got {before_seq}, {after_seq}.",
        )
    return StepDiffOut.from_domain(diff_steps(session, before_seq, after_seq))


@router.get("/sessions/{session_id}/export", response_model=SimulationExport)
def export(session_id: str, request: Request) -> SimulationExport:
    return SimulationExport.model_validate(engine.export_session(_store(request).get(session_id)))


@router.post("/import", response_model=ImportResponse, status_code=status.HTTP_201_CREATED)
def import_session(body: SimulationExport, request: Request) -> ImportResponse:
    store = _store(request)
    session, verification = engine.import_session(body.model_dump(mode="json"), store.new_id())
    store.add(session)
    return ImportResponse(
        session=_out(session), verification=VerificationOut.from_domain(verification)
    )
