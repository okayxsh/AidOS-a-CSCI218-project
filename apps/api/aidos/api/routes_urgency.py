"""Fuzzy urgency endpoints: score a scenario's zones (or one set of ratings) with full traces,
and publish the versioned membership functions and rule base."""

from __future__ import annotations

from fastapi import APIRouter

from aidos.ai.fuzzy import INPUT_TERMS, INPUTS, OUTPUT_TERMS, default_config, evaluate, explain
from aidos.api.schemas import (
    FuzzyConfigOut,
    InputSetOut,
    MembershipOut,
    OutputTermOut,
    RuleOut,
    UrgencyOut,
    UrgencyRequest,
    UrgencyResponse,
)
from aidos.domain.snapshots import snapshot_hash
from aidos.domain.validation import ScenarioValidationError, check_scenario_consistency
from aidos.pipeline import assess_urgency

router = APIRouter(prefix="/api/urgency", tags=["urgency"])


@router.post("/evaluate", response_model=UrgencyResponse)
def evaluate_urgency(request: UrgencyRequest) -> UrgencyResponse:
    config = default_config()
    if request.scenario is not None:
        scenario = request.scenario
        issues = check_scenario_consistency(scenario)
        if issues:
            raise ScenarioValidationError(issues)
        zones = [
            UrgencyOut.from_domain(u.result, u.explanation, u.zone_id, u.active)
            for u in assess_urgency(scenario, config)
        ]
        return UrgencyResponse(
            method=config.method,
            config_version=config.version,
            scenario_id=scenario.scenario_id,
            snapshot_hash=snapshot_hash(scenario),
            zones=zones,
        )

    result = evaluate(request.ratings.model_dump(), config)
    return UrgencyResponse(
        method=config.method,
        config_version=config.version,
        scenario_id=None,
        snapshot_hash=None,
        zones=[UrgencyOut.from_domain(result, explain(result, config), None, None)],
    )


@router.get("/config", response_model=FuzzyConfigOut)
def fuzzy_config() -> FuzzyConfigOut:
    config = default_config()
    return FuzzyConfigOut(
        method=config.method,
        version=config.version,
        inputs={
            name: InputSetOut(
                label=config.input_labels[name],
                range=list(config.input_range),
                terms={
                    t: MembershipOut(
                        shape=config.input_terms[name][t].shape,
                        points=list(config.input_terms[name][t].points),
                    )
                    for t in INPUT_TERMS
                },
            )
            for name in INPUTS
        },
        output={
            t: OutputTermOut(
                value=config.output_terms[t].value, band=list(config.output_terms[t].band)
            )
            for t in OUTPUT_TERMS
        },
        rules=[
            RuleOut(
                id=r.id,
                antecedent=dict(r.antecedent),
                consequent=r.consequent,
                text=r.text(config.input_labels),
            )
            for r in config.rules
        ],
    )
