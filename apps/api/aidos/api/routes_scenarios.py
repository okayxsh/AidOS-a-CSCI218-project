"""Built-in scenario endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from aidos.api.schemas import ScenarioDetail, ScenarioManifest, SummaryOut
from aidos.domain.snapshots import list_builtin_scenarios, load_builtin_scenario, snapshot_hash
from aidos.evaluation.metrics import summarize_scenario

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioManifest])
def list_scenarios() -> list[ScenarioManifest]:
    return [
        ScenarioManifest(
            scenario_id=s.scenario_id,
            title=s.title,
            description=s.description,
            seed=s.seed,
            synthetic=s.synthetic,
            zone_count=len(s.zones),
            resource_count=len(s.resources),
        )
        for s in list_builtin_scenarios()
    ]


@router.get("/{scenario_id}", response_model=ScenarioDetail)
def get_scenario(scenario_id: str) -> ScenarioDetail:
    scenario = load_builtin_scenario(scenario_id)
    return ScenarioDetail(
        snapshot_hash=snapshot_hash(scenario),
        scenario=scenario,
        summary=SummaryOut.from_domain(summarize_scenario(scenario)),
    )
