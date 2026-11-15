"""Evaluation API over a small real campaign written to a temporary results root."""

import dataclasses

import pytest
from fastapi.testclient import TestClient

from aidos.evaluation import campaign
from aidos.main import create_app

RUN = "custom-20260102T000000Z"


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    root = tmp_path_factory.mktemp("results")
    preset = dataclasses.replace(
        campaign.PRESETS["smoke"],
        families=("C",),
        dynamic_scripts=1,
        scaling_sizes=(5,),
        bootstrap_resamples=200,
    )
    campaign.run_campaign(preset, root, run_id=RUN, log=lambda _: None)
    (root / "not-a-run").mkdir()
    app = create_app()
    app.state.results_root = root
    return TestClient(app)


def test_list_runs(client):
    runs = client.get("/api/evaluation/runs").json()
    assert [r["run_id"] for r in runs] == [RUN]  # the stray folder is ignored
    assert runs[0]["status"] == "complete" and runs[0]["counts"]["static_scenarios"] == 1


def test_run_detail_has_manifest_config_and_summary(client):
    body = client.get(f"/api/evaluation/runs/{RUN}").json()
    assert body["manifest"]["run_id"] == RUN
    assert body["config"]["policies"] == ["fcfs", "greedy", "aidos", "aidos_balanced"]
    assert set(body["summary"]["static"]["overall"]) == {
        "fcfs",
        "greedy",
        "aidos",
        "aidos_balanced",
    }
    assert body["failures"] == []


def test_tables_with_filters(client):
    page = client.get(f"/api/evaluation/runs/{RUN}/tables/static?policy=aidos").json()
    assert page["total"] == 1 and page["rows"][0]["policy"] == "aidos"
    assert isinstance(page["rows"][0]["unit_coverage"], float)
    dispatch = client.get(f"/api/evaluation/runs/{RUN}/tables/dispatch").json()
    assert dispatch["total"] == 4


@pytest.mark.parametrize(
    ("path", "status", "code"),
    [
        ("/api/evaluation/runs/standard-20990101T000000Z", 404, "run_not_found"),
        ("/api/evaluation/runs/not-a-run", 422, "invalid_run_id"),
        ("/api/evaluation/runs/..%2F..%2Fdata", 404, None),
        (f"/api/evaluation/runs/{RUN}/tables/manifest", 422, "validation_error"),
    ],
)
def test_invalid_and_missing_runs(client, path, status, code):
    response = client.get(path)
    assert response.status_code == status
    if code:
        assert response.json()["error"]["code"] == code
