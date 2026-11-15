"""Simulation API over the real engine (docs/api-contract.md, Simulation)."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from aidos.main import create_app

DEMO = Path(__file__).resolve().parents[2] / "data" / "simulations" / "triage-demo-escalation.json"
BASE = "/api/simulation"


@pytest.fixture
def client():
    return TestClient(create_app())  # a fresh in-memory store per test


def create(client, scenario_id="triage-demo-001"):
    response = client.post(f"{BASE}/sessions", json={"scenario_id": scenario_id})
    assert response.status_code == 201
    return response.json()


def act(client, session, action):
    return client.post(
        f"{BASE}/sessions/{session['session_id']}/{action}",
        json={"expected_version": session["version"]},
    )


def event(client, session, payload, version=None):
    return client.post(
        f"{BASE}/sessions/{session['session_id']}/events",
        json={"expected_version": version or session["version"], "event": payload},
    )


ESCALATE = {"type": "urgency_changed", "zone_id": "zone-b", "severity": 9}


def test_create_start_apply_and_read_back(client):
    session = create(client)
    assert session["state"] == "READY" and session["allowed_actions"] == ["start", "reset"]
    assert session["diff"] is None and session["current"]["seq"] == 0
    assert len(session["current"]["comparison"]["results"]) == 4

    session = act(client, session, "start").json()
    assert session["state"] == "ACTIVE"
    response = event(client, session, ESCALATE)
    assert response.status_code == 200
    body = response.json()
    assert body["event_count"] == 1 and body["version"] == session["version"] + 1
    assert body["diff"]["recommendation_changed"] is True
    assert body["diff"]["explanation"][0] == "Zone B severity 6 → 9."
    assert [p["policy_id"] for p in body["diff"]["policies"]] == ["aidos", "fcfs"]
    assert body["history"][1]["type"] == "urgency_changed"
    assert body["history"][1]["changed_cells"] == 6

    read = client.get(f"{BASE}/sessions/{session['session_id']}").json()
    assert read["version"] == body["version"]
    assert read["current"]["outcome_hash"] == body["current"]["outcome_hash"]


def test_events_require_an_active_session(client):
    session = create(client)
    response = event(client, session, ESCALATE)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "invalid_transition"


def test_stale_version_is_a_conflict_and_changes_nothing(client):
    session = act(client, create(client), "start").json()
    assert event(client, session, ESCALATE).status_code == 200
    stale = event(
        client, session, {"type": "supply_lost", "resource_id": "medical_kits", "quantity": 5}
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "version_conflict"
    assert client.get(f"{BASE}/sessions/{session['session_id']}").json()["event_count"] == 1


@pytest.mark.parametrize(
    ("payload", "status", "code"),
    [
        (
            {"type": "supply_lost", "resource_id": "medical_kits", "quantity": 500},
            422,
            "insufficient_stock",
        ),
        ({"type": "supply_arrived", "resource_id": "fuel", "quantity": 5}, 422, "unknown_resource"),
        ({"type": "urgency_changed", "zone_id": "zone-z", "severity": 5}, 422, "unknown_zone"),
        ({"type": "urgency_changed", "zone_id": "zone-a", "severity": 9}, 422, "no_change"),
        (
            {"type": "supply_arrived", "resource_id": "medical_kits", "quantity": -3},
            422,
            "validation_error",
        ),
        ({"type": "urgency_changed", "zone_id": "zone-a", "severity": 11}, 422, "validation_error"),
        ({"type": "urgency_changed", "zone_id": "zone-a"}, 422, "validation_error"),
        ({"type": "meteor_strike"}, 422, "validation_error"),
        ({"type": "plan_committed", "expected_snapshot_hash": "0" * 64}, 409, "stale_plan"),
    ],
)
def test_invalid_events_are_rejected_without_corrupting_state(client, payload, status, code):
    session = act(client, create(client), "start").json()
    response = event(client, session, payload)
    assert response.status_code == status
    assert response.json()["error"]["code"] == code
    after = client.get(f"{BASE}/sessions/{session['session_id']}").json()
    assert after["version"] == session["version"] and after["event_count"] == 0


def test_commit_through_the_api_dispatches_once(client):
    session = act(client, create(client), "start").json()
    commit = {
        "type": "plan_committed",
        "expected_snapshot_hash": session["current"]["snapshot_hash"],
    }
    body = event(client, session, commit).json()
    assert body["dispatched_units"] == 330 and len(body["ledger"]) == 1
    assert body["current"]["summary"]["totals"]["stock"] == 0
    again = event(client, body, commit)
    assert again.status_code == 409 and again.json()["error"]["code"] == "stale_plan"


def test_pause_resume_complete_and_reset(client):
    session = act(client, create(client), "start").json()
    session = event(client, session, ESCALATE).json()
    paused = act(client, session, "pause").json()
    assert paused["state"] == "PAUSED" and paused["allowed_actions"] == ["resume", "reset"]
    assert event(client, paused, ESCALATE).json()["error"]["code"] == "invalid_transition"
    resumed = act(client, paused, "resume").json()
    done = act(client, resumed, "complete").json()
    assert done["state"] == "COMPLETED"
    reset = act(client, done, "reset").json()
    assert reset["state"] == "READY" and reset["event_count"] == 0
    assert reset["history"][0]["seq"] == 0 and len(reset["history"]) == 1
    assert reset["current"]["snapshot_hash"] == session["history"][0]["snapshot_hash"]
    assert act(client, reset, "pause").status_code == 409


def test_history_steps_diff_and_export(client):
    session = act(client, create(client), "start").json()
    session = event(client, session, ESCALATE).json()
    session = event(
        client, session, {"type": "supply_lost", "resource_id": "medical_kits", "quantity": 30}
    ).json()
    sid = session["session_id"]
    history = client.get(f"{BASE}/sessions/{sid}/history").json()
    assert [h["seq"] for h in history] == [0, 1, 2]
    assert client.get(f"{BASE}/sessions/{sid}/steps/1").json()["event"]["zone_id"] == "zone-b"
    assert client.get(f"{BASE}/sessions/{sid}/steps/7").status_code == 404
    whole = client.get(f"{BASE}/sessions/{sid}/diff?before=0&after=2").json()
    assert whole["events"] == ["urgency_changed", "supply_lost"]
    assert client.get(f"{BASE}/sessions/{sid}/diff?before=2&after=1").status_code == 422
    export = client.get(f"{BASE}/sessions/{sid}/export").json()
    assert export["format"] == "aidos-simulation" and len(export["outcomes"]) == 3


def test_replay_endpoint_reproduces_the_run(client):
    session = act(client, create(client), "start").json()
    events = [ESCALATE, {"type": "supply_lost", "resource_id": "medical_kits", "quantity": 30}]
    for payload in events:
        session = event(client, session, payload).json()
    hashes = [h["outcome_hash"] for h in session["history"]]
    replayed = client.post(
        f"{BASE}/sessions/{session['session_id']}/replay",
        json={"expected_version": session["version"], "events": events},
    ).json()
    assert [h["outcome_hash"] for h in replayed["history"]] == hashes
    bad = client.post(
        f"{BASE}/sessions/{session['session_id']}/replay",
        json={
            "expected_version": replayed["version"],
            "events": [{"type": "supply_lost", "resource_id": "medical_kits", "quantity": 999}],
        },
    )
    assert bad.status_code == 422 and bad.json()["error"]["details"][0]["path"] == "events.0"
    unchanged = client.get(f"{BASE}/sessions/{session['session_id']}").json()
    assert unchanged["version"] == replayed["version"]


def test_import_the_demo_script(client):
    document = json.loads(DEMO.read_text("utf-8"))
    response = client.post(f"{BASE}/import", json=document)
    assert response.status_code == 201
    body = response.json()
    assert body["verification"] == {
        "checked": True,
        "matches": True,
        "first_mismatch_seq": None,
        "engine_version_recorded": document["engine_version"],
    }
    assert body["session"]["event_count"] == 3 and body["session"]["state"] == "ACTIVE"
    assert client.post(f"{BASE}/import", json={"format": "x"}).status_code == 422


def test_missing_session_and_bad_create_requests(client):
    response = client.get(f"{BASE}/sessions/sim-missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "session_not_found"
    assert client.post(f"{BASE}/sessions", json={}).status_code == 422
    assert client.post(f"{BASE}/sessions", json={"scenario_id": "nope"}).status_code == 404
    assert (
        client.post(
            f"{BASE}/sessions", json={"scenario_id": "triage-demo-001", "policy": "fcfs"}
        ).status_code
        == 422
    )


def test_balanced_policy_session(client):
    body = client.post(
        f"{BASE}/sessions", json={"scenario_id": "triage-demo-001", "policy": "aidos_balanced"}
    ).json()
    assert body["policy"] == "aidos_balanced"
    session = act(client, body, "start").json()
    after = event(client, session, ESCALATE).json()
    assert after["diff"]["policies"][0]["policy_id"] == "aidos_balanced"
