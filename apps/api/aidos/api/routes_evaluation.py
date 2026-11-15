"""Evaluation endpoints: read-only views of precomputed runs.

Experiments are never launched from HTTP (they take minutes); they are run offline with
`experiments/run_benchmarks.py` and served from experiments/results/. The results root is
`app.state.results_root`, so tests can point it at a temporary directory.
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

from aidos.evaluation import artifacts

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


class RunListItem(BaseModel):
    run_id: str
    preset: str
    status: str
    created_utc: str | None
    duration_s: float | None
    counts: dict[str, int]


class RunDetail(BaseModel):
    manifest: dict[str, Any]
    config: dict[str, Any] | None
    summary: dict[str, Any] | None
    failures: list[dict[str, Any]] | None


class TablePage(BaseModel):
    total: int
    offset: int
    rows: list[dict[str, Any]]


def _root(request: Request):
    return request.app.state.results_root


@router.get("/runs", response_model=list[RunListItem])
def list_runs(request: Request) -> list[dict[str, Any]]:
    return artifacts.list_runs(_root(request))


@router.get("/runs/{run_id}", response_model=RunDetail)
def get_run(run_id: str, request: Request) -> dict[str, Any]:
    return artifacts.load_run(run_id, _root(request))


@router.get("/runs/{run_id}/tables/{table}", response_model=TablePage)
def get_table(
    run_id: str,
    table: Literal[
        "static", "static_zones", "recommendation", "dispatch", "dispatch_zones", "scaling"
    ],
    request: Request,
    family: str | None = Query(default=None, max_length=1),
    policy: str | None = Query(default=None, max_length=32),
    scenario_id: str | None = Query(default=None, max_length=64),
    limit: int = Query(default=1000, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    filters = {"family": family, "policy": policy, "scenario_id": scenario_id}
    return artifacts.load_table(
        run_id,
        table,
        filters={k: v for k, v in filters.items() if v is not None},
        limit=limit,
        offset=offset,
        root=_root(request),
    )
