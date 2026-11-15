"""End-to-end smoke test against a running AidOS engine (standard library only).

Start the engine first (from apps/api/):  uv run uvicorn aidos.main:app --port 8000
Then run (from the repository root):       python scripts/smoke_test.py [base_url]

For every built-in scenario it fetches the validated snapshot, scores it with the fuzzy
engine, runs all four policies (FCFS, urgency greedy, AidOS, AidOS balanced) through the API
and re-checks the hard invariants from the outside: integer allocations, 0 <= x <= d,
sum_z x <= S per resource, totals that reconcile, truthful solver statuses and an unchanged
snapshot hash. Exits non-zero on any failure.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")
POLICIES = ["fcfs", "greedy", "aidos", "aidos_balanced"]


def call(path: str, body: dict | None = None) -> tuple[int, dict]:
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(
        BASE + path, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as err:
        return err.code, json.load(err)


DEMO_EVENTS = [
    {"type": "urgency_changed", "zone_id": "zone-b", "severity": 9},
    {
        "type": "zone_added",
        "zone": {
            "id": "zone-d",
            "name": "Zone D · Riverside clinic",
            "severity": 8,
            "vulnerability": 9,
            "time_criticality": 9,
            "population": 2400,
            "demand": {"medical_kits": 40, "water_packs": 50, "shelter_kits": 10},
        },
    },
    {"type": "supply_lost", "resource_id": "medical_kits", "quantity": 30},
]


def simulation_demo(check) -> None:
    """The Stage 3 demo: load, run, escalate, add a zone, lose stock, reset, replay, compare."""
    sim = "/api/simulation/sessions"
    status, session = call(sim, {"scenario_id": "triage-demo-001"})
    check(status == 201, f"simulation: create returned HTTP {status}")
    sid = session["session_id"]
    status, session = call(f"{sim}/{sid}/start", {"expected_version": session["version"]})
    check(session.get("state") == "ACTIVE", "simulation: start did not activate the session")
    for event in DEMO_EVENTS:
        status, session = call(
            f"{sim}/{sid}/events", {"expected_version": session["version"], "event": event}
        )
        check(status == 200, f"simulation: {event['type']} returned HTTP {status}")
        for result in session["current"]["comparison"]["results"]:
            check(result["validation"]["valid"], f"simulation: {result['policy_id']} invalid")
        line = session["diff"]["explanation"]
        print(f"ok    simulation {event['type']:<16} {line[-3] if len(line) > 2 else line[0]}")
    final = [h["outcome_hash"] for h in session["history"]]
    status, stale = call(f"{sim}/{sid}/events", {"expected_version": 1, "event": DEMO_EVENTS[2]})
    check(status == 409, "simulation: a stale version was not rejected")
    status, session = call(f"{sim}/{sid}/reset", {"expected_version": session["version"]})
    check(session.get("event_count") == 0, "simulation: reset did not clear history")
    status, session = call(
        f"{sim}/{sid}/replay", {"expected_version": session["version"], "events": DEMO_EVENTS}
    )
    replayed = [h["outcome_hash"] for h in session.get("history", [])]
    check(replayed == final, "simulation: replay did not reproduce the original outcomes")
    status, exported = call(f"{sim}/{sid}/export")
    status, imported = call("/api/simulation/import", exported)
    check(status == 201 and imported["verification"]["matches"], "simulation: import mismatch")
    print(f"ok    simulation reset + replay reproduced {len(final)} steps; import verified")


def evaluation_api(check) -> None:
    """Stage 4: the precomputed runs are served read-only and reconcile with themselves."""
    status, runs = call("/api/evaluation/runs")
    check(status == 200, f"evaluation: list returned HTTP {status}")
    if not runs:
        print(
            "note  evaluation: no runs in experiments/results (run run_benchmarks.py --preset ...)"
        )
        return
    run_id = runs[0]["run_id"]
    status, detail = call(f"/api/evaluation/runs/{run_id}")
    check(status == 200 and detail.get("summary") is not None, "evaluation: run detail missing")
    static = detail["summary"]["static"]
    feasibility = static["feasibility"]
    check(all(v["valid"] == v["plans"] for v in feasibility.values()), "evaluation: invalid plans")
    status, page = call(f"/api/evaluation/runs/{run_id}/tables/static?policy=aidos&limit=5000")
    values = [r["urgency_weighted_coverage"] for r in page.get("rows", [])]
    mean = sum(values) / len(values) if values else None
    reported = static["overall"]["aidos"]["urgency_weighted_coverage"]["mean"]
    check(
        mean is not None and abs(mean - reported) < 1e-9, "evaluation: summary does not match rows"
    )
    status, _ = call("/api/evaluation/runs/not-a-run")
    check(status == 422, "evaluation: an invalid run id was not rejected")
    print(f"ok    evaluation {run_id}: {page.get('total')} AidOS rows reconcile with the summary")


def main() -> int:
    # Windows consoles and pipes default to cp1252, which cannot print the explanation arrows.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    failures: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    try:
        status, health = call("/api/health")
    except urllib.error.URLError as err:
        print(f"FAIL  cannot reach the engine at {BASE}: {err.reason}")
        return 1
    check(status == 200 and health.get("status") == "ok", "health endpoint is not ok")
    print(f"engine {health.get('version')} stage {health.get('engine_stage')}")

    _, manifests = call("/api/scenarios")
    for manifest in manifests:
        sid = manifest["scenario_id"]
        _, detail = call(f"/api/scenarios/{sid}")
        scenario, summary = detail["scenario"], detail["summary"]
        check(scenario["synthetic"] is True, f"{sid}: not marked synthetic")

        status, urgency = call("/api/urgency/evaluate", {"scenario": scenario})
        check(status == 200, f"{sid}: urgency returned HTTP {status}")
        for zone in urgency.get("zones", []):
            total = sum(a["contribution"] for a in zone["activations"])
            check(abs(total - zone["score"]) < 1e-4, f"{sid}: {zone['zone_id']} trace != score")

        status, compare = call(
            "/api/allocations/compare", {"scenario": scenario, "policies": POLICIES}
        )
        check(status == 200, f"{sid}: compare returned HTTP {status}")
        check(compare["snapshot_hash"] == detail["snapshot_hash"], f"{sid}: snapshot changed")
        line = []
        for result in compare["results"]:
            pid = result["policy_id"]
            check(result["has_plan"], f"{sid}/{pid}: no plan ({result['status']})")
            if pid.startswith("aidos"):
                check(result["status"] in ("OPTIMAL", "FEASIBLE"), f"{sid}/{pid}: status")
                phases = [p["status"] for p in result["solver"]["phases"]]
                proven = all(p == "OPTIMAL" for p in phases)
                check(proven == (result["status"] == "OPTIMAL"), f"{sid}/{pid}: status mismatch")
            used: dict[str, int] = {}
            for cell in result["cells"]:
                x, d = cell["allocated"], cell["requested"]
                check(isinstance(x, int), f"{sid}/{pid}: non-integer allocation {x}")
                check(0 <= x <= d, f"{sid}/{pid}: {cell['zone_id']}/{cell['resource_id']} {x}")
                used[cell["resource_id"]] = used.get(cell["resource_id"], 0) + x
            for rid, total in used.items():
                check(total <= scenario["stock"][rid], f"{sid}/{pid}: {rid} {total} > stock")
            metrics = result["metrics"]
            check(metrics["allocated_units"] == sum(used.values()), f"{sid}/{pid}: totals")
            check(metrics["feasibility_violations"] == 0, f"{sid}/{pid}: engine violations")
            check(result["validation"]["valid"], f"{sid}/{pid}: validator rejected the plan")
            line.append(f"{pid} {metrics['allocated_units']}")

        print(f"ok    {sid:<24} {summary['supply_status']:<12} {' | '.join(line)}")

    status, _ = call("/api/allocations/compare", {"scenario": scenario, "policies": ["magic"]})
    check(status == 422, "an unknown policy was not rejected with 422")
    bad = dict(scenario, stock={**scenario["stock"], next(iter(scenario["stock"])): -1})
    status, _ = call("/api/allocations/compare", {"scenario": bad, "policies": POLICIES})
    check(status == 422, "negative stock was not rejected with 422")

    simulation_demo(check)
    evaluation_api(check)

    for failure in failures:
        print(f"FAIL  {failure}")
    print("smoke test passed" if not failures else f"{len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
