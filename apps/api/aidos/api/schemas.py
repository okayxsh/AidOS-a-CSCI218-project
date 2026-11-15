"""HTTP request/response schemas. These adapt domain objects; they hold no logic."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from aidos import __version__
from aidos.ai.constraints import SCALE, AidosConfig
from aidos.ai.fuzzy import UrgencyResult, default_config
from aidos.ai.policies import Limit, PolicyId, PolicyStatus, SolverReport
from aidos.domain.models import Identifier, Rating, Scenario
from aidos.evaluation.invariants import ValidationReport
from aidos.evaluation.metrics import AllocationMetrics, ScenarioSummary, SupplyStatus
from aidos.pipeline import Comparison, PolicyRun


class ErrorDetail(BaseModel):
    path: str
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] = []


class ErrorResponse(BaseModel):
    error: ErrorBody


class PolicyInfo(BaseModel):
    id: PolicyId
    label: str
    available: bool
    planned_stage: int | None = Field(description="Delivery stage when not yet available.")


class HealthResponse(BaseModel):
    status: str
    version: str
    engine_stage: int
    policies: list[PolicyInfo]


# ---------------------------------------------------------------- scenarios


class ScenarioManifest(BaseModel):
    scenario_id: str
    title: str
    description: str
    seed: int
    synthetic: bool
    zone_count: int
    resource_count: int


class ResourceSummaryOut(BaseModel):
    resource_id: str
    stock: int
    requested: int
    shortfall: int
    surplus: int


class ZoneSummaryOut(BaseModel):
    zone_id: str
    active: bool
    requested_units: int


class TotalsOut(BaseModel):
    stock: int
    requested: int
    shortfall: int
    zones: int
    active_zones: int


class SummaryOut(BaseModel):
    resources: list[ResourceSummaryOut]
    zones: list[ZoneSummaryOut]
    totals: TotalsOut
    supply_status: SupplyStatus = Field(
        description="Stock against active requests: no_demand, covered, shortage or depot_empty."
    )

    @classmethod
    def from_domain(cls, summary: ScenarioSummary) -> SummaryOut:
        return cls(
            supply_status=summary.supply_status,
            resources=[
                ResourceSummaryOut(
                    resource_id=r.resource_id,
                    stock=r.stock,
                    requested=r.requested,
                    shortfall=r.shortfall,
                    surplus=r.surplus,
                )
                for r in summary.resources
            ],
            zones=[
                ZoneSummaryOut(
                    zone_id=z.zone_id, active=z.active, requested_units=z.requested_units
                )
                for z in summary.zones
            ],
            totals=TotalsOut(
                stock=summary.total_stock,
                requested=summary.total_requested,
                shortfall=summary.total_shortfall,
                zones=len(summary.zones),
                active_zones=summary.active_zone_count,
            ),
        )


class ScenarioDetail(BaseModel):
    snapshot_hash: str
    scenario: Scenario
    summary: SummaryOut


# ---------------------------------------------------------------- fuzzy urgency


class UrgencyInputs(BaseModel):
    """One zone's simulated ratings, each 0-10."""

    severity: Rating
    time_criticality: Rating
    vulnerability: Rating


class UrgencyRequest(BaseModel):
    """Score every zone of a scenario, or one set of ratings. Send exactly one of the two."""

    scenario: Scenario | None = None
    ratings: UrgencyInputs | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> UrgencyRequest:
        if (self.scenario is None) == (self.ratings is None):
            raise ValueError("send exactly one of 'scenario' or 'ratings'")
        return self


class RuleActivationOut(BaseModel):
    rule_id: str
    text: str
    consequent: str
    strength: float = Field(description="Product of the antecedent degrees.")
    output: float = Field(description="The rule's constant output (its band centre).")
    contribution: float = Field(description="Points this rule adds; they sum to the score.")


class UrgencyOut(BaseModel):
    zone_id: str | None = Field(description="Null when scoring standalone ratings.")
    active: bool | None
    score: float
    category: str
    inputs: dict[str, float]
    normalized: dict[str, float]
    memberships: dict[str, dict[str, float]]
    activations: list[RuleActivationOut] = Field(description="Fired rules, strongest first.")
    term_support: dict[str, float] = Field(description="Share of rule strength per urgency term.")
    explanation: str

    @classmethod
    def from_domain(
        cls, result: UrgencyResult, explanation: str, zone_id: str | None, active: bool | None
    ) -> UrgencyOut:
        return cls(
            zone_id=zone_id,
            active=active,
            score=result.score,
            category=result.category,
            inputs=dict(result.inputs),
            normalized=dict(result.normalized),
            memberships={k: dict(v) for k, v in result.memberships.items()},
            activations=[
                RuleActivationOut(
                    rule_id=a.rule_id,
                    text=a.text,
                    consequent=a.consequent,
                    strength=a.strength,
                    output=a.output,
                    contribution=a.contribution,
                )
                for a in result.activations
            ],
            term_support=dict(result.term_support),
            explanation=explanation,
        )


class UrgencyResponse(BaseModel):
    method: str
    config_version: str
    scenario_id: str | None
    snapshot_hash: str | None
    zones: list[UrgencyOut]


class MembershipOut(BaseModel):
    shape: str
    points: list[float]


class InputSetOut(BaseModel):
    label: str
    range: list[float]
    terms: dict[str, MembershipOut]


class OutputTermOut(BaseModel):
    value: float
    band: list[float]


class RuleOut(BaseModel):
    id: str
    antecedent: dict[str, str]
    consequent: str
    text: str


class FuzzyConfigOut(BaseModel):
    method: str
    version: str
    inputs: dict[str, InputSetOut]
    output: dict[str, OutputTermOut]
    rules: list[RuleOut]


# ---------------------------------------------------------------- allocation


class AidosConfigIn(BaseModel):
    """Optional AidOS settings. Seed and worker count are fixed so runs stay deterministic."""

    epsilon: float = Field(default=1.0, gt=0, le=100, description="Urgency points added to all.")
    resource_weights: dict[Identifier, int] = Field(
        default={}, description="w_r per resource, integer 1-100; missing resources weigh 1."
    )
    min_coverage: float = Field(default=0.25, ge=0, le=1, description="Balanced-mode floor.")
    time_limit_s: float = Field(default=5.0, ge=0.01, le=10)

    def to_domain(self) -> AidosConfig:
        return AidosConfig(
            epsilon=self.epsilon,
            resource_weights=dict(self.resource_weights),
            min_coverage=self.min_coverage,
            time_limit_s=self.time_limit_s,
        )


class AidosConfigOut(BaseModel):
    epsilon: float
    resource_weights: dict[str, int]
    min_coverage: float
    time_limit_s: float
    random_seed: int
    workers: int

    @classmethod
    def from_domain(cls, c: AidosConfig) -> AidosConfigOut:
        return cls(
            epsilon=c.epsilon,
            resource_weights=dict(c.resource_weights),
            min_coverage=c.min_coverage,
            time_limit_s=c.time_limit_s,
            random_seed=c.random_seed,
            workers=c.workers,
        )


class CompareRequest(BaseModel):
    scenario: Scenario
    policies: list[PolicyId] = Field(default=[PolicyId.FCFS], min_length=1, max_length=4)
    config: AidosConfigIn | None = None


class CellOut(BaseModel):
    zone_id: str
    resource_id: str
    requested: int
    allocated: int
    unmet: int
    limit: Limit
    reason: str


class MetricsOut(BaseModel):
    unit_coverage: float | None
    coverage_by_resource: dict[str, float | None]
    coverage_by_zone: dict[str, float | None]
    allocated_units: int
    unmet_units: int
    feasibility_violations: int
    allocated_by_resource: dict[str, int]
    remaining_by_resource: dict[str, int]
    stock_utilization: float | None = Field(description="Σ allocated / Σ stock.")
    urgency_weighted_coverage: float | None = Field(description="Σ u·x / Σ u·d.")
    min_zone_coverage: float | None
    jain_fairness: float | None = Field(description="Jain's index over zone unit coverage.")
    unmet_high_urgency: int | None = Field(description="Unmet units in zones with urgency ≥ 50.")

    @classmethod
    def from_domain(cls, m: AllocationMetrics) -> MetricsOut:
        return cls(
            unit_coverage=m.unit_coverage,
            coverage_by_resource=m.coverage_by_resource,
            coverage_by_zone=m.coverage_by_zone,
            allocated_units=m.allocated_units,
            unmet_units=m.unmet_units,
            feasibility_violations=m.feasibility_violations,
            allocated_by_resource=m.allocated_by_resource,
            remaining_by_resource=m.remaining_by_resource,
            stock_utilization=m.stock_utilization,
            urgency_weighted_coverage=m.urgency_weighted_coverage,
            min_zone_coverage=m.min_zone_coverage,
            jain_fairness=m.jain_fairness,
            unmet_high_urgency=m.unmet_high_urgency,
        )


class CheckOut(BaseModel):
    name: str
    passed: bool
    hard: bool
    detail: str


class ViolationOut(BaseModel):
    kind: str
    zone_id: str | None
    resource_id: str | None
    detail: str


class ValidationOut(BaseModel):
    applicable: bool = Field(description="False when the policy returned no plan.")
    valid: bool
    checks: list[CheckOut]
    violations: list[ViolationOut]

    @classmethod
    def from_domain(cls, v: ValidationReport) -> ValidationOut:
        return cls(
            applicable=v.applicable,
            valid=v.valid,
            checks=[
                CheckOut(name=c.name, passed=c.passed, hard=c.hard, detail=c.detail)
                for c in v.checks
            ],
            violations=[
                ViolationOut(
                    kind=x.kind, zone_id=x.zone_id, resource_id=x.resource_id, detail=x.detail
                )
                for x in v.violations
            ],
        )


class SolverPhaseOut(BaseModel):
    name: str
    status: str
    objective_value: float | None
    best_bound: float | None
    wall_time_ms: float


class SolverOut(BaseModel):
    engine: str = "OR-Tools CP-SAT"
    status: PolicyStatus
    objective: str
    objective_value: int | None = Field(description="Primary (urgency) objective, integer form.")
    objective_scale: int = Field(description="Divide objective_value by this for urgency·units.")
    phases: list[SolverPhaseOut]
    variables: int
    constraints: int
    parameters: dict[str, float | int]
    coefficients: dict[str, dict[str, int]]
    coverage_floor: dict[str, float]
    message: str

    @classmethod
    def from_domain(cls, s: SolverReport) -> SolverOut:
        return cls(
            status=s.status,
            objective=s.objective,
            objective_value=s.objective_value,
            objective_scale=SCALE,
            phases=[
                SolverPhaseOut(
                    name=p.name,
                    status=p.status,
                    objective_value=p.objective_value,
                    best_bound=p.best_bound,
                    wall_time_ms=p.wall_time_ms,
                )
                for p in s.phases
            ],
            variables=s.variables,
            constraints=s.constraints,
            parameters=dict(s.parameters),
            coefficients={z: dict(r) for z, r in s.coefficients.items()},
            coverage_floor=dict(s.coverage_floor),
            message=s.message,
        )


class PolicyResultOut(BaseModel):
    policy_id: PolicyId
    label: str
    status: PolicyStatus
    has_plan: bool
    message: str
    zone_order: list[str]
    cells: list[CellOut]
    metrics: MetricsOut | None = Field(description="Null when the policy returned no plan.")
    validation: ValidationOut
    solver: SolverOut | None = Field(description="CP-SAT details for the AidOS policies.")
    runtime_ms: float = Field(description="Wall-clock time of the policy call only.")

    @classmethod
    def from_domain(cls, run: PolicyRun, label: str) -> PolicyResultOut:
        result = run.result
        return cls(
            policy_id=result.policy_id,
            label=label,
            status=result.status,
            has_plan=result.has_plan,
            message=result.message,
            zone_order=list(result.zone_order),
            cells=[
                CellOut(
                    zone_id=c.zone_id,
                    resource_id=c.resource_id,
                    requested=c.requested,
                    allocated=c.allocated,
                    unmet=c.unmet,
                    limit=c.limit,
                    reason=c.reason,
                )
                for c in result.cells
            ],
            metrics=MetricsOut.from_domain(run.metrics) if run.metrics else None,
            validation=ValidationOut.from_domain(run.validation),
            solver=SolverOut.from_domain(result.solver) if result.solver else None,
            runtime_ms=run.runtime_ms,
        )


class FuzzyInfoOut(BaseModel):
    method: str
    config_version: str


POLICY_LABELS: dict[PolicyId, str] = {
    PolicyId.FCFS: "First come, first served",
    PolicyId.GREEDY: "Urgency greedy",
    PolicyId.AIDOS: "AidOS (fuzzy + CP-SAT)",
    PolicyId.AIDOS_BALANCED: "AidOS balanced (coverage floor)",
}


class CompareResponse(BaseModel):
    scenario_id: str
    snapshot_hash: str
    engine_version: str
    fuzzy: FuzzyInfoOut
    urgency: list[UrgencyOut] = Field(description="The shared fuzzy scores every policy saw.")
    urgency_ms: float
    config: AidosConfigOut
    results: list[PolicyResultOut]

    @classmethod
    def from_domain(cls, comparison: Comparison) -> CompareResponse:
        fuzzy = default_config()
        return cls(
            scenario_id=comparison.scenario_id,
            snapshot_hash=comparison.snapshot_hash,
            engine_version=__version__,
            fuzzy=FuzzyInfoOut(method=fuzzy.method, config_version=fuzzy.version),
            urgency=[
                UrgencyOut.from_domain(u.result, u.explanation, u.zone_id, u.active)
                for u in comparison.urgency
            ],
            urgency_ms=comparison.urgency_ms,
            config=AidosConfigOut.from_domain(comparison.aidos_config),
            results=[
                PolicyResultOut.from_domain(run, POLICY_LABELS[run.result.policy_id])
                for run in comparison.runs
            ],
        )
