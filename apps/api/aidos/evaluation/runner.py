"""Experiment runner (spec Section 5.5): the same engine as the API, run offline.

`run_experiment` runs every policy on every scenario through `pipeline.compare`, so each
policy sees identical inputs and identical fuzzy scores, and records enough to reproduce
the run: snapshot hash, seed, policy, configuration and software versions. Timing varies
between runs; allocations and scores do not.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Any

from ortools import __version__ as ORTOOLS_VERSION

from aidos import __version__ as ENGINE_VERSION
from aidos.ai.constraints import AidosConfig
from aidos.ai.policies import PolicyId
from aidos.domain.models import Scenario
from aidos.pipeline import POLICY_ORDER, compare


@dataclass(frozen=True)
class ExperimentRecord:
    scenario_id: str
    snapshot_hash: str
    seed: int
    policy_id: str
    status: str
    has_plan: bool
    valid: bool  # passed every hard check of the independent validator
    violations: int
    runtime_ms: float
    metrics: dict[str, Any] | None
    config: dict[str, Any]
    engine_version: str
    fuzzy_version: str
    ortools_version: str


def run_experiment(
    scenarios: Iterable[Scenario],
    policies: Iterable[PolicyId] = POLICY_ORDER,
    config: AidosConfig | None = None,
) -> list[ExperimentRecord]:
    config = config or AidosConfig()
    policies = tuple(policies)
    records: list[ExperimentRecord] = []
    for scenario in scenarios:
        comparison = compare(scenario, policies, config)
        for run in comparison.runs:
            records.append(
                ExperimentRecord(
                    scenario_id=scenario.scenario_id,
                    snapshot_hash=comparison.snapshot_hash,
                    seed=scenario.seed,
                    policy_id=str(run.result.policy_id),
                    status=str(run.result.status),
                    has_plan=run.result.has_plan,
                    valid=run.validation.valid,
                    violations=len(run.validation.violations),
                    runtime_ms=run.runtime_ms,
                    metrics=asdict(run.metrics) if run.metrics else None,
                    config={
                        "epsilon": config.epsilon,
                        "resource_weights": dict(config.resource_weights),
                        "min_coverage": config.min_coverage,
                        "time_limit_s": config.time_limit_s,
                        "random_seed": config.random_seed,
                        "workers": config.workers,
                    },
                    engine_version=ENGINE_VERSION,
                    fuzzy_version=comparison.fuzzy_version,
                    ortools_version=ORTOOLS_VERSION,
                )
            )
    return records
