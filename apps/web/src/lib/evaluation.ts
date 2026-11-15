import type { Description, EvaluationRunItem, MetricSpec, PairedComparison } from '../api/types';

/**
 * Formatting and wording for evaluation results. Nothing here computes a statistic: every
 * value passed in comes from the engine's summary.json.
 */

export const POLICY_LABEL: Record<string, string> = {
  fcfs: 'FCFS',
  greedy: 'Urgency greedy',
  aidos: 'AidOS',
  aidos_balanced: 'AidOS balanced',
};

export const policyLabel = (id: string) => POLICY_LABEL[id] ?? id;

/** Restrained, distinguishable series colours on the dark dashboard ground. */
export const POLICY_COLOUR: Record<string, string> = {
  fcfs: '#8a99ab',
  greedy: '#b49be6',
  aidos: '#43c9c1',
  aidos_balanced: '#6aa8ea',
};

export const PAIRS: [string, string][] = [
  ['aidos', 'fcfs'],
  ['aidos', 'greedy'],
  ['aidos_balanced', 'aidos'],
  ['aidos_balanced', 'fcfs'],
  ['greedy', 'fcfs'],
];

const PERCENT_UNITS = new Set(['fraction', 'share']);

/** A metric value in its own unit. Fractions are shown as percentages. */
export function formatValue(value: number | null | undefined, unit: string): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return 'N/A';
  if (PERCENT_UNITS.has(unit)) return `${(value * 100).toFixed(1)}%`;
  if (unit === 'ms') return `${value < 1 ? value.toFixed(3) : value.toFixed(1)} ms`;
  if (unit === 'index') return value.toFixed(3);
  if (unit === 'zones') return value.toFixed(2);
  if (unit === 'units') return value.toFixed(1);
  return value.toFixed(2);
}

/** A difference in the metric's unit. Fractions become percentage points. */
export function formatDiff(value: number | null | undefined, unit: string): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return 'N/A';
  const sign = value > 0 ? '+' : value < 0 ? '−' : '±';
  const abs = Math.abs(value);
  if (PERCENT_UNITS.has(unit)) return `${sign}${(abs * 100).toFixed(1)} pp`;
  if (unit === 'ms') return `${sign}${abs.toFixed(2)} ms`;
  if (unit === 'index') return `${sign}${abs.toFixed(3)}`;
  return `${sign}${abs.toFixed(2)}`;
}

export function formatP(p: number | null | undefined): string {
  if (p === null || p === undefined) return 'N/A';
  if (p < 0.0001) return '< 0.0001';
  return p.toFixed(4);
}

/** Plain reading of a paired result, derived only from its CI and tie counts. */
export function readPaired(c: PairedComparison, spec: MetricSpec | undefined): string {
  if (c.n === 0) return 'No paired observations';
  if (c.ties === c.n) return `Identical in all ${c.n} scenarios`;
  if (!c.ci_mean) return 'Too few pairs for an interval';
  const [low, high] = c.ci_mean;
  if (low <= 0 && high >= 0) return 'No clear difference (CI includes 0)';
  const aHigher = low > 0;
  if (!spec || spec.better === 'n/a') return aHigher ? 'A higher' : 'A lower';
  const better = spec.better === 'higher' ? aHigher : !aHigher;
  return `${better ? 'A better' : 'A worse'} on this metric (CI excludes 0)`;
}

export const median = (d: Description | undefined) => d?.median ?? null;
export const mean = (d: Description | undefined) => d?.mean ?? null;

/** The run shown by default: the newest complete extended run, else standard, else newest. */
export function defaultRun(runs: EvaluationRunItem[]): string | null {
  const complete = runs.filter((r) => r.status.startsWith('complete'));
  return (
    complete.find((r) => r.preset === 'extended')?.run_id ??
    complete.find((r) => r.preset === 'standard')?.run_id ??
    runs[0]?.run_id ??
    null
  );
}

export const EVENT_LABEL: Record<string, string> = {
  urgency_changed: 'Urgency escalation',
  zone_added: 'New emergency zone',
  supply_lost: 'Supply loss',
  supply_arrived: 'Supply arrival',
  request_updated: 'Demand increase',
  time_advanced: 'Time advance',
  zone_resolved: 'Zone resolved',
};
