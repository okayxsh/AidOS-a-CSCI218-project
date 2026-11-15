"""Simulation state machine (spec Section 5.3, docs/simulation/state-machine.md)."""

import itertools

import pytest

from aidos.simulation.fsm import (
    TRANSITIONS,
    Action,
    InvalidTransitionError,
    SimState,
    allowed_actions,
    transition,
)

VALID = [
    (SimState.READY, Action.START, SimState.ACTIVE),
    (SimState.ACTIVE, Action.PAUSE, SimState.PAUSED),
    (SimState.PAUSED, Action.RESUME, SimState.ACTIVE),
    (SimState.ACTIVE, Action.COMPLETE, SimState.COMPLETED),
    (SimState.ACTIVE, Action.APPLY_EVENT, SimState.ACTIVE),
    (SimState.ACTIVE, Action.FAIL, SimState.ERROR),
] + [(state, Action.RESET, SimState.READY) for state in SimState]


@pytest.mark.parametrize(("state", "action", "expected"), VALID)
def test_valid_transitions(state, action, expected):
    assert transition(state, action) is expected


def test_every_other_pair_is_rejected():
    valid = {(s, a) for s, a, _ in VALID}
    assert set(TRANSITIONS) == valid
    for state, action in itertools.product(SimState, Action):
        if (state, action) not in valid:
            with pytest.raises(InvalidTransitionError):
                transition(state, action)


@pytest.mark.parametrize(
    ("state", "action"),
    [
        (SimState.READY, Action.APPLY_EVENT),  # must start first
        (SimState.PAUSED, Action.APPLY_EVENT),  # paused sessions refuse changes
        (SimState.COMPLETED, Action.APPLY_EVENT),
        (SimState.ERROR, Action.APPLY_EVENT),
        (SimState.ACTIVE, Action.START),
        (SimState.READY, Action.PAUSE),
        (SimState.COMPLETED, Action.RESUME),
        (SimState.PAUSED, Action.COMPLETE),
    ],
)
def test_invalid_transitions_name_the_allowed_actions(state, action):
    with pytest.raises(InvalidTransitionError) as caught:
        transition(state, action)
    assert state.value in str(caught.value)
    assert "allowed:" in str(caught.value)


def test_allowed_actions_per_state():
    assert [a.value for a in allowed_actions(SimState.READY)] == ["start", "reset"]
    assert [a.value for a in allowed_actions(SimState.ACTIVE)] == [
        "pause",
        "complete",
        "reset",
        "apply_event",
    ]
    assert [a.value for a in allowed_actions(SimState.PAUSED)] == ["resume", "reset"]
    assert [a.value for a in allowed_actions(SimState.COMPLETED)] == ["reset"]
    assert [a.value for a in allowed_actions(SimState.ERROR)] == ["reset"]
    for state in SimState:  # FAIL is internal and never offered
        assert Action.FAIL not in allowed_actions(state)
