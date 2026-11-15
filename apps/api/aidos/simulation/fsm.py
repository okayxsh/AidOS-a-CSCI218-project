"""Simulation session state machine (docs/simulation/state-machine.md).

    READY --start--> ACTIVE --pause--> PAUSED --resume--> ACTIVE
                     ACTIVE --complete--> COMPLETED
                     ACTIVE --fail--> ERROR          (an engine invariant broke; event not applied)
    any state --reset--> READY                       (back to the initial snapshot, history cleared)

Events (crisis changes and plan commits) are accepted only in ACTIVE. Reading a session,
its history and its export is allowed in every state. The table below is the only place
transitions are defined; anything not listed is rejected with InvalidTransitionError.
"""

from __future__ import annotations

from enum import StrEnum


class SimState(StrEnum):
    READY = "READY"  # scenario loaded and scored; no event applied yet
    ACTIVE = "ACTIVE"  # accepts events
    PAUSED = "PAUSED"  # frozen: events are refused until resumed (there is no running clock)
    COMPLETED = "COMPLETED"  # the user ended the run; read-only until reset
    ERROR = "ERROR"  # an engine invariant failed; read-only until reset


class Action(StrEnum):
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    COMPLETE = "complete"
    RESET = "reset"
    APPLY_EVENT = "apply_event"
    FAIL = "fail"  # internal: entered only when the independent validator rejects a plan


TRANSITIONS: dict[tuple[SimState, Action], SimState] = {
    (SimState.READY, Action.START): SimState.ACTIVE,
    (SimState.ACTIVE, Action.PAUSE): SimState.PAUSED,
    (SimState.PAUSED, Action.RESUME): SimState.ACTIVE,
    (SimState.ACTIVE, Action.COMPLETE): SimState.COMPLETED,
    (SimState.ACTIVE, Action.APPLY_EVENT): SimState.ACTIVE,
    (SimState.ACTIVE, Action.FAIL): SimState.ERROR,
    **{(state, Action.RESET): SimState.READY for state in SimState},
}

# Actions a user can request directly (FAIL is internal, APPLY_EVENT has its own endpoint).
USER_ACTIONS = (Action.START, Action.PAUSE, Action.RESUME, Action.COMPLETE, Action.RESET)


class InvalidTransitionError(Exception):
    def __init__(self, state: SimState, action: Action):
        self.state, self.action = state, action
        allowed = ", ".join(a.value for a in allowed_actions(state)) or "none"
        super().__init__(
            f"'{action.value}' is not allowed while the session is {state.value} "
            f"(allowed: {allowed})."
        )


def transition(state: SimState, action: Action) -> SimState:
    try:
        return TRANSITIONS[state, action]
    except KeyError:
        raise InvalidTransitionError(state, action) from None


def allowed_actions(state: SimState) -> tuple[Action, ...]:
    """User-facing actions permitted in a state, in a stable order."""
    order = (*USER_ACTIONS, Action.APPLY_EVENT)
    return tuple(a for a in order if (state, a) in TRANSITIONS)
