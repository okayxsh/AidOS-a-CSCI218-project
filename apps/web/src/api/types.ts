/**
 * Types mirroring the backend schemas in apps/api/aidos/api/schemas.py.
 * The frontend never computes allocations or scores; it only renders these.
 */

export type PolicyId = 'fcfs' | 'greedy' | 'aidos' | 'aidos_balanced';

export interface PolicyInfo {
  id: PolicyId;
  label: string;
  available: boolean;
  planned_stage: number | null;
}

export interface Health {
  status: string;
  version: string;
  engine_stage: number;
  policies: PolicyInfo[];
}

export interface ResourceType {
  id: string;
  label: string;
  unit: string;
}

export interface CrisisZone {
  id: string;
  name: string;
  arrival_order: number;
  severity: number;
  vulnerability: number;
  time_criticality: number;
  activation_step: number;
  population: number | null;
  demand: Record<string, number>;
}

export interface Scenario {
  schema_version: '1.0';
  scenario_id: string;
  title: string;
  description: string;
  seed: number;
  synthetic: true;
  step: number;
  resources: ResourceType[];
  stock: Record<string, number>;
  zones: CrisisZone[];
}

export interface ScenarioManifest {
  scenario_id: string;
  title: string;
  description: string;
  seed: number;
  synthetic: boolean;
  zone_count: number;
  resource_count: number;
}

export interface ResourceSummary {
  resource_id: string;
  stock: number;
  requested: number;
  shortfall: number;
  surplus: number;
}

export interface ZoneSummary {
  zone_id: string;
  active: boolean;
  requested_units: number;
}

export interface ScenarioSummary {
  resources: ResourceSummary[];
  zones: ZoneSummary[];
  totals: {
    stock: number;
    requested: number;
    shortfall: number;
    zones: number;
    active_zones: number;
  };
  supply_status: SupplyStatus;
}

/** Backend judgement of stock against active requests, per resource. */
export type SupplyStatus = 'no_demand' | 'covered' | 'shortage' | 'depot_empty';

export interface ScenarioDetail {
  snapshot_hash: string;
  scenario: Scenario;
  summary: ScenarioSummary;
}

export type Limit = 'met' | 'no_demand' | 'stock_exhausted' | 'zero_stock' | 'not_proven';

/** COMPLETE comes from the deterministic baselines; the others are CP-SAT statuses, as returned. */
export type PolicyStatus =
  'COMPLETE' | 'OPTIMAL' | 'FEASIBLE' | 'INFEASIBLE' | 'UNKNOWN' | 'MODEL_INVALID';

export type UrgencyCategory = 'low' | 'moderate' | 'high' | 'critical';

export interface RuleActivation {
  rule_id: string;
  text: string;
  consequent: UrgencyCategory;
  strength: number;
  output: number;
  /** Points this rule adds to the score; the contributions sum to the score. */
  contribution: number;
}

export interface UrgencyAssessment {
  zone_id: string | null;
  active: boolean | null;
  score: number;
  category: UrgencyCategory;
  inputs: Record<string, number>;
  normalized: Record<string, number>;
  memberships: Record<string, Record<string, number>>;
  activations: RuleActivation[];
  term_support: Record<string, number>;
  explanation: string;
}

export interface UrgencyResponse {
  method: string;
  config_version: string;
  scenario_id: string | null;
  snapshot_hash: string | null;
  zones: UrgencyAssessment[];
}

export interface FuzzyConfig {
  method: string;
  version: string;
  inputs: Record<
    string,
    { label: string; range: number[]; terms: Record<string, { shape: string; points: number[] }> }
  >;
  output: Record<string, { value: number; band: number[] }>;
  rules: { id: string; antecedent: Record<string, string>; consequent: string; text: string }[];
}

export interface AllocationCell {
  zone_id: string;
  resource_id: string;
  requested: number;
  allocated: number;
  unmet: number;
  limit: Limit;
  reason: string;
}

export interface AllocationMetrics {
  unit_coverage: number | null;
  coverage_by_resource: Record<string, number | null>;
  coverage_by_zone: Record<string, number | null>;
  allocated_units: number;
  unmet_units: number;
  feasibility_violations: number;
  allocated_by_resource: Record<string, number>;
  remaining_by_resource: Record<string, number>;
  stock_utilization: number | null;
  urgency_weighted_coverage: number | null;
  min_zone_coverage: number | null;
  jain_fairness: number | null;
  unmet_high_urgency: number | null;
}

export interface ValidationCheck {
  name: string;
  passed: boolean;
  /** Hard checks are invariants; the others are quality checks that never invalidate a plan. */
  hard: boolean;
  detail: string;
}

export interface Validation {
  applicable: boolean;
  valid: boolean;
  checks: ValidationCheck[];
  violations: {
    kind: string;
    zone_id: string | null;
    resource_id: string | null;
    detail: string;
  }[];
}

export interface SolverPhase {
  name: string;
  status: string;
  objective_value: number | null;
  best_bound: number | null;
  wall_time_ms: number;
}

export interface SolverReport {
  engine: string;
  status: PolicyStatus;
  objective: string;
  objective_value: number | null;
  objective_scale: number;
  phases: SolverPhase[];
  variables: number;
  constraints: number;
  parameters: Record<string, number>;
  coefficients: Record<string, Record<string, number>>;
  coverage_floor: Record<string, number>;
  message: string;
}

export interface PolicyResult {
  policy_id: PolicyId;
  label: string;
  status: PolicyStatus;
  has_plan: boolean;
  message: string;
  zone_order: string[];
  cells: AllocationCell[];
  /** Null when the policy returned no plan: a solver failure is never filled in. */
  metrics: AllocationMetrics | null;
  validation: Validation;
  solver: SolverReport | null;
  runtime_ms: number;
}

export interface AidosConfig {
  epsilon: number;
  resource_weights: Record<string, number>;
  min_coverage: number;
  time_limit_s: number;
  random_seed: number;
  workers: number;
}

export interface CompareResponse {
  scenario_id: string;
  snapshot_hash: string;
  engine_version: string;
  fuzzy: { method: string; config_version: string };
  /** The fuzzy scores every policy in this response saw. */
  urgency: UrgencyAssessment[];
  urgency_ms: number;
  config: AidosConfig;
  results: PolicyResult[];
}

export interface ApiErrorBody {
  error: { code: string; message: string; details: { path: string; message: string }[] };
}

/* ---------------------------------------------------------------- simulation (Stage 3) */

/** Session lifecycle states (apps/api/aidos/simulation/fsm.py). */
export type SimState = 'READY' | 'ACTIVE' | 'PAUSED' | 'COMPLETED' | 'ERROR';

export type SimAction = 'start' | 'pause' | 'resume' | 'complete' | 'reset' | 'apply_event';

export type ControlAction = Exclude<SimAction, 'apply_event'>;

export interface NewZone {
  id: string;
  name: string;
  severity: number;
  vulnerability: number;
  time_criticality: number;
  population?: number | null;
  demand: Record<string, number>;
}

/** A crisis event. The engine validates every field and the result; values are absolute. */
export type SimEvent =
  | { type: 'zone_added'; zone: NewZone }
  | {
      type: 'urgency_changed';
      zone_id: string;
      severity?: number | null;
      vulnerability?: number | null;
      time_criticality?: number | null;
    }
  | { type: 'supply_arrived'; resource_id: string; quantity: number }
  | { type: 'supply_lost'; resource_id: string; quantity: number }
  | { type: 'request_updated'; zone_id: string; resource_id: string; quantity: number }
  | { type: 'zone_resolved'; zone_id: string }
  | { type: 'time_advanced' }
  | { type: 'plan_committed'; policy: PolicyId; expected_snapshot_hash: string };

export type SimEventType = SimEvent['type'];

export interface DispatchCell {
  zone_id: string;
  resource_id: string;
  units: number;
}

export interface SimStep {
  seq: number;
  event_id: string | null;
  event: SimEvent | null;
  /** The scenario clock; only time_advanced moves it. */
  sim_step: number;
  snapshot_hash: string;
  outcome_hash: string;
  changes: string[];
  dispatch: DispatchCell[];
  scenario: Scenario;
  summary: ScenarioSummary;
  comparison: CompareResponse;
}

export interface HistoryItem {
  seq: number;
  event_id: string | null;
  type: SimEventType | null;
  event: SimEvent | null;
  sim_step: number;
  summary: string;
  snapshot_hash: string;
  outcome_hash: string;
  allocated_units: number;
  unmet_units: number;
  urgency_weighted_coverage: number | null;
  changed_cells: number;
  dispatched_units: number;
}

export interface UrgencyDelta {
  zone_id: string;
  name: string;
  score_before: number | null;
  score_after: number | null;
  category_before: UrgencyCategory | null;
  category_after: UrgencyCategory | null;
  rank_before: number | null;
  rank_after: number | null;
}

export interface CellDelta {
  zone_id: string;
  resource_id: string;
  requested_before: number;
  requested_after: number;
  allocated_before: number;
  allocated_after: number;
}

export interface PolicyDelta {
  policy_id: PolicyId;
  status_before: string;
  status_after: string;
  changed_cells: number;
  cells: CellDelta[];
  allocated_before: number;
  allocated_after: number;
  unmet_before: number;
  unmet_after: number;
  uwc_before: number | null;
  uwc_after: number | null;
}

export interface ResourceDelta {
  resource_id: string;
  label: string;
  stock_before: number;
  stock_after: number;
  requested_before: number;
  requested_after: number;
  shortfall_before: number;
  shortfall_after: number;
}

export interface StepDiff {
  before_seq: number;
  after_seq: number;
  events: SimEventType[];
  input_changes: string[];
  urgency: UrgencyDelta[];
  order_before: string[];
  order_after: string[];
  resources: ResourceDelta[];
  /** The recommended policy first, then FCFS. */
  policies: PolicyDelta[];
  recommendation_changed: boolean;
  /** Sentences written by the engine from the two stored steps. */
  explanation: string[];
}

export interface LedgerEntry {
  seq: number;
  event_id: string;
  policy: PolicyId;
  snapshot_hash: string;
  total: number;
  cells: DispatchCell[];
}

export interface ResolvedZone {
  zone_id: string;
  name: string;
  resolved_at_step: number;
  remaining_demand: Record<string, number>;
}

export interface SimSession {
  session_id: string;
  scenario_id: string;
  state: SimState;
  /** Send as expected_version with the next change. */
  version: number;
  allowed_actions: SimAction[];
  policy: PolicyId;
  config: AidosConfig;
  event_count: number;
  max_events: number;
  error: string | null;
  current: SimStep;
  /** Previous step → current step; null at step 0. */
  diff: StepDiff | null;
  history: HistoryItem[];
  ledger: LedgerEntry[];
  dispatched_units: number;
  resolved_zones: ResolvedZone[];
}

export interface SimExport {
  format: 'aidos-simulation';
  format_version: '1.0';
  engine_version: string | null;
  fuzzy_version: string | null;
  scenario_id: string;
  initial_snapshot_hash: string;
  initial_scenario: Scenario;
  config: Record<string, unknown>;
  events: { seq: number; event_id: string | null; event: SimEvent }[];
  outcomes: { seq: number; snapshot_hash: string; outcome_hash: string }[];
}

export interface ReplayVerification {
  /** False when the document recorded no outcomes to compare against. */
  checked: boolean;
  matches: boolean;
  first_mismatch_seq: number | null;
  engine_version_recorded: string | null;
}

export interface ImportResult {
  session: SimSession;
  verification: ReplayVerification;
}

/* ---------------------------------------------------------------- evaluation (Stage 4) */

/** Summary statistics of one metric over a set of observations (None values excluded). */
export interface Description {
  n: number;
  mean: number | null;
  sd: number | null;
  median: number | null;
  min: number | null;
  max: number | null;
  p10: number | null;
  p25: number | null;
  p75: number | null;
  p90: number | null;
}

export interface MetricSpec {
  key: string;
  label: string;
  unit: string;
  better: 'higher' | 'lower' | 'n/a';
  /** True when the AidOS objective (or the urgency model it uses) favours it by design. */
  aligned: boolean;
  note: string;
}

export interface PairedComparison {
  scope?: string;
  a: string;
  b: string;
  metric: string;
  n: number;
  dropped: number;
  mean_diff: number | null;
  median_diff: number | null;
  sd_diff: number | null;
  ci_mean: [number, number] | null;
  ci_median: [number, number] | null;
  level: number;
  effect_dz: number | null;
  wins: number;
  ties: number;
  losses: number;
  sign_p: number | null;
}

export interface PrimaryTest {
  a: string;
  b: string;
  metric: string;
  sign_p: number | null;
  holm_p: number | null;
}

export type DescriptionTable = Record<string, Record<string, Description>>;

export interface StaticSummary {
  policies: string[];
  families: string[];
  scenarios: number;
  overall: DescriptionTable;
  by_family: Record<string, DescriptionTable>;
  comparisons: PairedComparison[];
  primary_tests: PrimaryTest[];
  statuses: Record<string, Record<string, number>>;
  feasibility: Record<
    string,
    { plans: number; valid: number; total: number; optimal_proven: number }
  >;
  identical_plans: Record<string, number>;
}

export interface DynamicSummary {
  scripts: number;
  steps: number;
  policies: string[];
  event_types: string[];
  overall: DescriptionTable;
  by_event: Record<string, DescriptionTable>;
  comparisons: PairedComparison[];
  valid_steps: Record<string, number>;
}

export interface DispatchSummary {
  scripts: number;
  policies: string[];
  overall: DescriptionTable;
  integrity: Record<
    string,
    {
      runs: number;
      inventory_conserved: number;
      ledger_consistent: number;
      double_dispatch_blocked: number;
      rejected_events: number;
    }
  >;
  comparisons: PairedComparison[];
}

export interface ScalingPoint {
  zones: number;
  policy: string;
  runtime_ms: Description;
  variables: Description;
  optimal: number;
  runs: number;
}

export interface EvaluationSummary {
  static: StaticSummary;
  dynamic_recommendation: Partial<DynamicSummary> & { steps: number };
  dynamic_dispatch: Partial<DispatchSummary> & { scripts: number };
  scaling: { points: ScalingPoint[] };
  metrics: MetricSpec[];
  families: Record<string, { name: string; description: string }>;
  bootstrap: { resamples: number; seed: number; level: number };
}

export interface RunCounts {
  static_scenarios?: number;
  static_records?: number;
  dynamic_scripts?: number;
  dynamic_steps?: number;
  dispatch_runs?: number;
  scaling_records?: number;
  failures?: number;
}

export interface EvaluationRunItem {
  run_id: string;
  preset: string;
  status: string;
  created_utc: string | null;
  duration_s: number | null;
  counts: RunCounts;
}

export interface EvaluationManifest {
  run_id: string;
  status: string;
  created_utc?: string;
  finished_utc?: string;
  duration_s?: number;
  preset?: string;
  counts?: RunCounts;
  versions?: Record<string, string>;
  environment?: Record<string, string>;
  source_revision?: string;
  files?: Record<string, string>;
}

export interface EvaluationConfig {
  run_id: string;
  preset: Record<string, unknown> & { name?: string };
  families: Record<string, Record<string, unknown>>;
  family_seeds: Record<string, [number, number]>;
  dynamic: Record<string, unknown>;
  policies: string[];
  aidos_config: Record<string, unknown>;
  fuzzy_config_version: string;
  fuzzy_method: string;
}

export interface EvaluationRun {
  manifest: EvaluationManifest;
  config: EvaluationConfig | null;
  summary: EvaluationSummary | null;
  failures: { stage: string; item: string; error: string }[] | null;
}
