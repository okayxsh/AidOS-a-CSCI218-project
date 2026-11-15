"""End-to-end API flow over the real engine (spec Section 7, API contract)."""

import pytest
from fastapi.testclient import TestClient

from aidos import ENGINE_STAGE, __version__
from aidos.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health_reports_version_and_policy_availability(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["engine_stage"] == ENGINE_STAGE
    available = {p["id"]: p["available"] for p in body["policies"]}
    assert available == {"fcfs": True, "greedy": True, "aidos": True, "aidos_balanced": True}


def test_list_scenarios(client):
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    manifests = {m["scenario_id"]: m for m in response.json()}
    assert manifests["triage-demo-001"]["zone_count"] == 3
    assert all(m["synthetic"] for m in manifests.values())


def test_get_scenario_includes_backend_computed_summary(client):
    body = client.get("/api/scenarios/triage-demo-001").json()
    assert body["scenario"]["scenario_id"] == "triage-demo-001"
    assert len(body["snapshot_hash"]) == 64
    assert body["summary"]["totals"] == {
        "stock": 330,
        "requested": 560,
        "shortfall": 230,
        "zones": 3,
        "active_zones": 3,
    }
    assert body["summary"]["supply_status"] == "shortage"
    zero = client.get("/api/scenarios/zero-stock").json()
    assert zero["summary"]["supply_status"] == "depot_empty"


def test_unknown_scenario_is_a_404_with_a_stable_error_shape(client):
    response = client.get("/api/scenarios/nope")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "scenario_not_found"


def test_compare_runs_fcfs_on_the_submitted_snapshot(client):
    detail = client.get("/api/scenarios/triage-demo-001").json()
    response = client.post("/api/allocations/compare", json={"scenario": detail["scenario"]})
    assert response.status_code == 200
    body = response.json()
    assert body["snapshot_hash"] == detail["snapshot_hash"]
    (fcfs,) = body["results"]
    assert fcfs["policy_id"] == "fcfs"
    assert fcfs["metrics"]["feasibility_violations"] == 0
    cells = {(c["zone_id"], c["resource_id"]): c for c in fcfs["cells"]}
    assert cells[("zone-b", "medical_kits")]["allocated"] == 15
    assert cells[("zone-c", "medical_kits")]["limit"] == "stock_exhausted"


def test_aidos_runs_the_full_fuzzy_and_cp_sat_pipeline(client):
    detail = client.get("/api/scenarios/triage-demo-001").json()
    response = client.post(
        "/api/allocations/compare", json={"scenario": detail["scenario"], "policies": ["aidos"]}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["engine_version"] == __version__
    assert body["fuzzy"]["method"].startswith("sugeno")
    assert [u["zone_id"] for u in body["urgency"]] == ["zone-a", "zone-b", "zone-c"]
    (aidos,) = body["results"]
    assert aidos["status"] == "OPTIMAL" and aidos["has_plan"]
    assert aidos["validation"]["valid"] and aidos["validation"]["applicable"]
    assert {c["name"] for c in aidos["validation"]["checks"]} >= {
        "integer",
        "non_negative",
        "within_demand",
        "within_stock",
        "complete",
        "no_idle_stock",
    }
    solver = aidos["solver"]
    assert solver["engine"] == "OR-Tools CP-SAT" and solver["objective"] == "urgency_first"
    assert [p["status"] for p in solver["phases"]] == ["OPTIMAL", "OPTIMAL"]
    cells = {(c["zone_id"], c["resource_id"]): c for c in aidos["cells"]}
    assert cells[("zone-c", "medical_kits")]["allocated"] == 15
    assert cells[("zone-b", "medical_kits")]["allocated"] == 0


def test_compare_runs_all_policies_on_one_snapshot(client):
    detail = client.get("/api/scenarios/triage-demo-001").json()
    response = client.post(
        "/api/allocations/compare",
        json={
            "scenario": detail["scenario"],
            "policies": ["fcfs", "greedy", "aidos", "aidos_balanced"],
            "config": {"min_coverage": 0.2},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["snapshot_hash"] == detail["snapshot_hash"]
    assert body["config"]["min_coverage"] == 0.2
    results = {r["policy_id"]: r for r in body["results"]}
    assert list(results) == ["fcfs", "greedy", "aidos", "aidos_balanced"]
    assert {r["metrics"]["allocated_units"] for r in results.values()} == {330}
    assert results["fcfs"]["solver"] is None and results["fcfs"]["status"] == "COMPLETE"
    assert results["aidos_balanced"]["solver"]["coverage_floor"]["medical_kits"] == 0.2
    for r in results.values():
        m = r["metrics"]
        assert m["feasibility_violations"] == 0
        assert sum(m["allocated_by_resource"].values()) == m["allocated_units"]


def test_invalid_aidos_config_is_rejected(client):
    scenario = client.get("/api/scenarios/triage-demo-001").json()["scenario"]
    response = client.post(
        "/api/allocations/compare",
        json={
            "scenario": scenario,
            "policies": ["aidos"],
            "config": {"resource_weights": {"fuel": 2}},
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_config"
    response = client.post(
        "/api/allocations/compare",
        json={"scenario": scenario, "policies": ["aidos"], "config": {"epsilon": 0}},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_unknown_policy_is_a_validation_error(client):
    scenario = client.get("/api/scenarios/triage-demo-001").json()["scenario"]
    response = client.post(
        "/api/allocations/compare", json={"scenario": scenario, "policies": ["magic"]}
    )
    assert response.status_code == 422


def test_urgency_evaluate_scores_every_zone_with_a_trace(client):
    scenario = client.get("/api/scenarios/coastal-storm-005").json()["scenario"]
    body = client.post("/api/urgency/evaluate", json={"scenario": scenario}).json()
    assert body["config_version"] == "1.0" and len(body["zones"]) == 6
    zone_f = next(z for z in body["zones"] if z["zone_id"] == "zone-f")
    assert zone_f["active"] is False  # scored, but flagged as not yet active
    for zone in body["zones"]:
        assert 0 <= zone["score"] <= 100
        # Contributions sum to the score, which is rounded to 4 decimals.
        assert abs(sum(a["contribution"] for a in zone["activations"]) - zone["score"]) < 1e-4
        assert zone["score"] == round(zone["score"], 4)
        assert zone["explanation"].startswith("Urgency")


def test_urgency_evaluate_single_ratings_and_bad_requests(client):
    ok = client.post(
        "/api/urgency/evaluate",
        json={"ratings": {"severity": 7, "time_criticality": 7, "vulnerability": 5}},
    )
    assert ok.status_code == 200
    (zone,) = ok.json()["zones"]
    assert zone["zone_id"] is None and abs(zone["score"] - 70.8333) < 1e-4
    assert client.post("/api/urgency/evaluate", json={}).status_code == 422
    out_of_range = client.post(
        "/api/urgency/evaluate",
        json={"ratings": {"severity": 11, "time_criticality": 7, "vulnerability": 5}},
    )
    assert out_of_range.status_code == 422
    assert out_of_range.json()["error"]["code"] == "validation_error"


def test_fuzzy_config_is_published(client):
    body = client.get("/api/urgency/config").json()
    assert len(body["rules"]) == 27
    assert set(body["inputs"]) == {"severity", "time_criticality", "vulnerability"}
    assert body["output"]["critical"] == {"value": 87.5, "band": [75.0, 100.0]}


def test_invalid_scenario_is_rejected_not_masked(client):
    scenario = client.get("/api/scenarios/triage-demo-001").json()["scenario"]
    scenario["stock"]["medical_kits"] = -5
    response = client.post("/api/allocations/compare", json={"scenario": scenario})
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert any("medical_kits" in d["path"] for d in error["details"])


def test_unknown_resource_in_demand_is_rejected(client):
    scenario = client.get("/api/scenarios/triage-demo-001").json()["scenario"]
    scenario["zones"][0]["demand"]["fuel"] = 3
    response = client.post("/api/allocations/compare", json={"scenario": scenario})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_scenario"
