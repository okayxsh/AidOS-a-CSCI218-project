import type { Limit, PolicyId, PolicyStatus, SupplyStatus, UrgencyCategory } from '../api/types';
import type { BadgeTone } from '../components/ui/StatusBadge';

/** How each backend allocation limit is labelled. The reason text itself comes from the engine. */
export const LIMIT_LABEL: Record<Limit, { label: string; tone: BadgeTone }> = {
  met: { label: 'Met in full', tone: 'ok' },
  no_demand: { label: 'No request', tone: 'neutral' },
  stock_exhausted: { label: 'Stock exhausted', tone: 'warn' },
  zero_stock: { label: 'Depot empty', tone: 'critical' },
  not_proven: { label: 'Not proven optimal', tone: 'warn' },
};

export const SUPPLY_STATUS: Record<
  SupplyStatus,
  { label: string; tone: 'default' | 'warn' | 'ok' | 'critical'; detail: string }
> = {
  shortage: { label: 'Shortage', tone: 'warn', detail: 'Requests exceed stock' },
  covered: { label: 'Covered', tone: 'ok', detail: 'Stock covers every request' },
  depot_empty: { label: 'Depot empty', tone: 'critical', detail: 'No stock of any resource' },
  no_demand: { label: 'No requests', tone: 'default', detail: 'No active zone is asking' },
};

export const POLICY_DESCRIPTION: Record<PolicyId, string> = {
  fcfs: 'Serves zones in arrival order and ignores urgency, by design. The reference baseline.',
  greedy:
    'Serves zones by fuzzy urgency, highest first, with no optimiser. Isolates what CP-SAT adds.',
  aidos:
    'Fuzzy urgency plus a CP-SAT model that maximises urgency-weighted allocation under the hard limits.',
  aidos_balanced:
    'Same model, but first guarantees every requesting zone a share of its request (up to 25%) when stock allows.',
};

/** Short policy names for dense tables; full labels come from the engine. */
export const POLICY_SHORT: Record<PolicyId, string> = {
  fcfs: 'FCFS',
  greedy: 'Urgency greedy',
  aidos: 'AidOS',
  aidos_balanced: 'AidOS balanced',
};

/** What the order of zones in a result means for each policy. */
export const ORDER_LABEL: Record<PolicyId, string> = {
  fcfs: 'Served in arrival order:',
  greedy: 'Served by urgency, highest first:',
  aidos: 'Ranked by urgency (CP-SAT allocates all zones at once):',
  aidos_balanced: 'Ranked by urgency (CP-SAT allocates all zones at once):',
};

export const STATUS_TONE: Record<PolicyStatus, BadgeTone> = {
  COMPLETE: 'ok',
  OPTIMAL: 'ok',
  FEASIBLE: 'warn',
  INFEASIBLE: 'critical',
  UNKNOWN: 'critical',
  MODEL_INVALID: 'critical',
};

/** Plain-language meaning of each status, for tooltips and notes. */
export const STATUS_MEANING: Record<PolicyStatus, string> = {
  COMPLETE: 'The deterministic baseline finished.',
  OPTIMAL: 'CP-SAT proved no better plan exists for the stated objective.',
  FEASIBLE: 'A valid plan, but CP-SAT did not prove it optimal within the time limit.',
  INFEASIBLE: 'CP-SAT found the model has no solution. No plan is shown.',
  UNKNOWN: 'CP-SAT found no plan before the time limit. No plan is shown.',
  MODEL_INVALID: 'CP-SAT rejected the model. No plan is shown.',
};

export const CATEGORY_TONE: Record<UrgencyCategory, BadgeTone> = {
  critical: 'critical',
  high: 'warn',
  moderate: 'neutral',
  low: 'neutral',
};

export const CHECK_LABEL: Record<string, string> = {
  integer: 'Whole units',
  non_negative: 'No negative allocation',
  within_demand: 'Never above a request',
  within_stock: 'Never above stock, per resource',
  complete: 'One cell per zone and resource',
  no_idle_stock: 'No idle stock while a zone is short',
};

export const INPUT_LABEL: Record<string, string> = {
  severity: 'Severity',
  time_criticality: 'Time-criticality',
  vulnerability: 'Vulnerability',
};

/** Zone segment shades for request bars: low-luminance slates, so stock and shortfall lead. */
export const SEGMENT_SHADES = ['#3d4e66', '#34445b', '#2c3a4f', '#46586f', '#394a61', '#303f55'];
