"""Final hardening: stricter input checks, the error envelope, honest balanced-mode
explanations, and the dispatch guard (including the A -> B -> A case)."""

import pytest
from fastapi.testclient import TestClient

from aidos.main import create_app

BASE = "/api/simulation"


@pytest.fixture
def client():
    return TestClient(create_app())


def start_session(client):
    created = client.post(f"{BASE}/sessions", json={"scenario_id": "triage-demo-001"}).json()
    return client.post(
        f"{BASE}/sessions/{created['session_id']}/start",
        json={"expected_version": created["version"]},
    ).json()


def send(client, session, payload):
    return client.post(
        f"{BASE}/sessions/{session['session_id']}/events",
        json={"expected_version": session["version"], "event": payload},
    )


def commit_payload(session):
    return {"type": "plan_committed", "expected_snapshot_hash": session["current"]["snapshot_hash"]}


# --- Ratings are numbers, never booleans or strings -------------------------------------


@pytest.mark.parametrize("bad", [True, "7", None])
def test_urgency_ratings_reject_non_numbers(client, bad):
    ratings = {"severity": bad, "time_criticality": 7, "vulnerability": 5}
    response = client.post("/api/urgency/evaluate", json={"ratings": ratings})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_urgency_ratings_still_accept_integers_and_decimals(client):
    for value in (7, 7.0, 6.5):
        ratings = {"severity": value, "time_criticality": 7, "vulnerability": 5}
        assert client.post("/api/urgency/evaluate", json={"ratings": ratings}).status_code == 200


def test_escalation_event_rejects_a_boolean_rating(client):
    session = start_session(client)
    response = send(
        client, session, {"type": "urgency_changed", "zone_id": "zone-b", "severity": True}
    )
    assert response.status_code == 422
    after = client.get(f"{BASE}/sessions/{session['session_id']}").json()
    assert after["version"] == session["version"] and after["event_count"] == 0


# --- Every error uses the documented envelope ------------------------------------------


def test_unknown_route_and_wrong_method_use_the_error_envelope(client):
    missing = client.get("/api/does-not-exist")
    assert missing.status_code == 404 and missing.json()["error"]["code"] == "not_found"
    wrong_method = client.get("/api/allocations/compare")
    assert wrong_method.status_code == 405
    assert wrong_method.json()["error"]["code"] == "method_not_allowed"


# --- Imported sessions respect the API's solver limit ----------------------------------


def test_import_rejects_a_time_limit_above_the_api_cap(client):
    session = start_session(client)
    document = client.get(f"{BASE}/sessions/{session['session_id']}/export").json()
    document["config"]["time_limit_s"] = 60
    response = client.post(f"{BASE}/import", json=document)
    assert response.status_code == 422
    document["config"]["time_limit_s"] = 5
    assert client.post(f"{BASE}/import", json=document).status_code == 201


# --- Balanced-mode explanations never overstate the floor ------------------------------


def balanced_reasons(client, stock):
    scenario = client.get("/api/scenarios/triage-demo-001").json()["scenario"]
    scenario["stock"] = {**scenario["stock"], **stock}
    body = client.post(
        "/api/allocations/compare", json={"scenario": scenario, "policies": ["aidos_balanced"]}
    ).json()
    result = body["results"][0]
    return result, [c["reason"] for c in result["cells"] if c["resource_id"] == "medical_kits"]


def test_balanced_explanation_when_the_target_is_met(client):
    result, reasons = balanced_reasons(client, {})
    assert result["solver"]["coverage_floor"]["medical_kits"] == 0.25
    assert any("at least 25.0% of its request" in r for r in reasons)
    assert not any("guaranteed" in r for r in reasons)


def test_balanced_explanation_when_stock_is_too_low_for_any_floor(client):
    # 2 medical kits for three requesting zones: no common floor above 0 is possible.
    result, reasons = balanced_reasons(client, {"medical_kits": 2})
    assert result["solver"]["coverage_floor"]["medical_kits"] == 0.0
    assert all("guaranteed" not in r for r in reasons)
    assert any("too low for any common coverage floor" in r for r in reasons)


# --- Dispatch guard --------------------------------------------------------------------


def test_retrying_the_identical_commit_request_is_rejected(client):
    session = start_session(client)
    request = {"expected_version": session["version"], "event": commit_payload(session)}
    url = f"{BASE}/sessions/{session['session_id']}/events"
    first = client.post(url, json=request)
    assert first.status_code == 200 and len(first.json()["ledger"]) == 1
    retry = client.post(url, json=request)
    assert retry.status_code == 409 and retry.json()["error"]["code"] == "version_conflict"
    after = client.get(f"{BASE}/sessions/{session['session_id']}").json()
    assert (
        len(after["ledger"]) == 1 and after["dispatched_units"] == first.json()["dispatched_units"]
    )


def test_a_b_a_commit_is_a_new_dispatch_of_new_stock(client):
    """A -> B -> A: after a dispatch, new supply and restored requests can return the
    scenario to the snapshot it had before. Committing then dispatches the *current* plan
    for that state once more. That is a second dispatch of newly supplied units, not a
    repeat of the first: inventory stays conserved and the ledger records two commits."""
    session = start_session(client)
    initial = session["current"]["scenario"]
    initial_hash = session["current"]["snapshot_hash"]

    session = send(client, session, commit_payload(session)).json()
    first_units = session["dispatched_units"]
    assert len(session["ledger"]) == 1 and session["current"]["summary"]["totals"]["stock"] == 0

    # Replenish every resource and raise every request back to its original value.
    for rid, units in initial["stock"].items():
        session = send(
            client, session, {"type": "supply_arrived", "resource_id": rid, "quantity": units}
        ).json()
    for zone in initial["zones"]:
        now = next(z for z in session["current"]["scenario"]["zones"] if z["id"] == zone["id"])
        for rid, units in zone["demand"].items():
            if now["demand"].get(rid, 0) != units:
                payload = {
                    "type": "request_updated",
                    "zone_id": zone["id"],
                    "resource_id": rid,
                    "quantity": units,
                }
                session = send(client, session, payload).json()
    assert session["current"]["snapshot_hash"] == initial_hash  # back to state A

    second = send(
        client, session, {"type": "plan_committed", "expected_snapshot_hash": initial_hash}
    )
    assert second.status_code == 200
    body = second.json()
    assert len(body["ledger"]) == 2
    assert body["ledger"][0]["seq"] != body["ledger"][1]["seq"]
    assert body["dispatched_units"] == 2 * first_units
    supplied = sum(initial["stock"].values())
    # Conservation: initial stock + arrivals - dispatched = stock left (0 here).
    assert (
        supplied + supplied - body["dispatched_units"]
        == body["current"]["summary"]["totals"]["stock"]
    )

    # The old commit cannot be replayed once the state moves on again.
    again = send(client, body, {"type": "plan_committed", "expected_snapshot_hash": initial_hash})
    assert again.status_code == 409 and again.json()["error"]["code"] == "stale_plan"
