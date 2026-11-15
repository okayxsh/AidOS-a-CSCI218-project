"""Allocation endpoints. Policies run on the submitted snapshot and never mutate it.

One endpoint serves both "run the AI allocation" (policies: ["aidos"]) and "compare with
the baselines" (several policies), so every result in a response shares one snapshot and
one set of fuzzy scores.
"""

from __future__ import annotations

from fastapi import APIRouter

from aidos.ai.policies import PolicyId
from aidos.api.schemas import POLICY_LABELS, CompareRequest, CompareResponse, PolicyInfo
from aidos.pipeline import compare as run_comparison

router = APIRouter(prefix="/api/allocations", tags=["allocations"])

POLICY_CATALOGUE: tuple[PolicyInfo, ...] = tuple(
    PolicyInfo(id=policy, label=POLICY_LABELS[policy], available=True, planned_stage=None)
    for policy in (PolicyId.FCFS, PolicyId.GREEDY, PolicyId.AIDOS, PolicyId.AIDOS_BALANCED)
)


@router.post("/compare", response_model=CompareResponse)
def compare(request: CompareRequest) -> CompareResponse:
    config = request.config.to_domain() if request.config else None
    return CompareResponse.from_domain(run_comparison(request.scenario, request.policies, config))
