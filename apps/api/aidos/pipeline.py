"""The Stage 2 decision pipeline, as separate steps over one immutable snapshot.

    scenario -> assess_urgency (fuzzy)  -> run_policy (FCFS / greedy / CP-SAT)
             -> validate_allocation (independent) -> compute_metrics -> Comparison

Every policy in a comparison sees the same scenario object and the same urgency scores,
so results differ only by policy. Nothing here touches FastAPI, the network or global
state; the API and the experiment runner both call `compare`.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from time import perf_counter

from aidos.ai.baseline_fcfs import allocate_fcfs
from aidos.ai.baseline_greedy import allocate_greedy
from aidos.ai.constraints import AidosConfig, allocate_aidos
from aidos.ai.fuzzy import FuzzyConfig, UrgencyResult, default_config, evaluate, explain
from aidos.ai.policies import AllocationResult, PolicyId
from aidos.domain.models import Scenario
from aidos.domain.snapshots import snapshot_hash
from aidos.domain.validation import ScenarioValidationError, check_scenario_consistency
from aidos.evaluation.invariants import ValidationReport, validate_allocation
from aidos.evaluation.metrics import AllocationMetrics, compute_metrics

POLICY_ORDER = (PolicyId.FCFS, PolicyId.GREEDY, PolicyId.AIDOS, PolicyId.AIDOS_BALANCED)


@dataclass(frozen=True)
class ZoneUrgency:
    zone_id: str
    active: bool
    result: UrgencyResult
    explanation: str


@dataclass(frozen=True)
class PolicyRun:
    result: AllocationResult
    validation: ValidationReport
    metrics: AllocationMetrics | None  # None when the policy returned no plan
    runtime_ms: float  # wall-clock time of the policy call only


@dataclass(frozen=True)
class Comparison:
    scenario_id: str
    snapshot_hash: str
    urgency: tuple[ZoneUrgency, ...]
    urgency_ms: float
    runs: tuple[PolicyRun, ...]
    aidos_config: AidosConfig
    fuzzy_version: str


def assess_urgency(
    scenario: Scenario, config: FuzzyConfig | None = None
) -> tuple[ZoneUrgency, ...]:
    """Fuzzy urgency for every zone in the scenario (inactive zones are scored and flagged)."""
    config = config or default_config()
    active = {z.id for z in scenario.active_zones()}
    assessments = []
    for zone in scenario.zones:
        ratings = {
            "severity": zone.severity,
            "time_criticality": zone.time_criticality,
            "vulnerability": zone.vulnerability,
        }
        result = evaluate(ratings, config)
        assessments.append(ZoneUrgency(zone.id, zone.id in active, result, explain(result, config)))
    return tuple(assessments)


def run_policy(
    policy_id: PolicyId,
    scenario: Scenario,
    scores: Mapping[str, float],
    config: AidosConfig,
) -> PolicyRun:
    started = perf_counter()
    if policy_id is PolicyId.FCFS:
        result = allocate_fcfs(scenario)
    elif policy_id is PolicyId.GREEDY:
        result = allocate_greedy(scenario, scores)
    elif policy_id is PolicyId.AIDOS:
        result = allocate_aidos(scenario, scores, config, objective="urgency_first")
    else:
        result = allocate_aidos(scenario, scores, config, objective="balanced")
    runtime_ms = (perf_counter() - started) * 1000

    validation = validate_allocation(scenario, result)
    metrics = compute_metrics(scenario, result, scores) if result.has_plan else None
    return PolicyRun(result, validation, metrics, runtime_ms)


def compare(
    scenario: Scenario,
    policies: Iterable[PolicyId] = POLICY_ORDER,
    config: AidosConfig | None = None,
) -> Comparison:
    """Run each policy once on the same snapshot and the same urgency scores."""
    issues = check_scenario_consistency(scenario)
    if issues:
        raise ScenarioValidationError(issues)
    config = config or AidosConfig()
    config.check(scenario)

    started = perf_counter()
    urgency = assess_urgency(scenario)
    urgency_ms = (perf_counter() - started) * 1000
    scores = {u.zone_id: u.result.score for u in urgency}

    runs = tuple(
        run_policy(policy_id, scenario, scores, config)
        for policy_id in dict.fromkeys(policies)  # de-duplicate, keep order
    )
    return Comparison(
        scenario_id=scenario.scenario_id,
        snapshot_hash=snapshot_hash(scenario),
        urgency=urgency,
        urgency_ms=urgency_ms,
        runs=runs,
        aidos_config=config,
        fuzzy_version=default_config().version,
    )
