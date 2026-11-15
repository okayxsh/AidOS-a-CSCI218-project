import type { CompareResponse, PolicyResult, ScenarioDetail } from '../api/types';
import { POLICY_SHORT, STATUS_TONE } from '../lib/display';
import { formatInt, formatRatio, zoneShortName } from '../lib/format';
import { Panel } from './ui/Panel';
import { StatusBadge } from './ui/StatusBadge';

type Row = {
  label: string;
  formula?: string;
  value: (r: PolicyResult) => string;
};

const ratio = (pick: (r: PolicyResult) => number | null | undefined) => (r: PolicyResult) =>
  r.metrics ? formatRatio(pick(r)) : '—';
const units = (pick: (r: PolicyResult) => number | null | undefined) => (r: PolicyResult) => {
  if (!r.metrics) return '—';
  const v = pick(r);
  return v === null || v === undefined ? 'N/A' : formatInt(v);
};

const ROWS: Row[] = [
  { label: 'Units allocated', value: units((r) => r.metrics?.allocated_units) },
  { label: 'Unmet units', value: units((r) => r.metrics?.unmet_units) },
  {
    label: 'Urgency-weighted coverage',
    formula: 'Σ u·x / Σ u·d',
    value: ratio((r) => r.metrics?.urgency_weighted_coverage),
  },
  {
    label: 'Stock utilisation',
    formula: 'Σ x / Σ S',
    value: ratio((r) => r.metrics?.stock_utilization),
  },
  {
    label: 'Lowest zone coverage',
    formula: 'min over zones',
    value: ratio((r) => r.metrics?.min_zone_coverage),
  },
  {
    label: 'Fairness (Jain)',
    formula: '(Σf)² / n·Σf²',
    value: (r) =>
      !r.metrics
        ? '—'
        : r.metrics.jain_fairness === null
          ? 'N/A'
          : r.metrics.jain_fairness.toFixed(3),
  },
  {
    label: 'Unmet in high-urgency zones',
    formula: 'urgency ≥ 50',
    value: units((r) => r.metrics?.unmet_high_urgency),
  },
  {
    label: 'Constraint violations',
    value: (r) => (r.validation.applicable ? String(r.validation.violations.length) : '—'),
  },
];

/** True when two results allocate exactly the same units to every zone and resource. */
function samePlan(a: PolicyResult | undefined, b: PolicyResult | undefined): boolean {
  if (!a || !b || !a.has_plan || !b.has_plan) return false;
  const key = (r: PolicyResult) =>
    r.cells
      .map((c) => `${c.zone_id}|${c.resource_id}|${c.allocated}`)
      .sort()
      .join(',');
  return key(a) === key(b);
}

/**
 * Every policy on the same snapshot and the same fuzzy scores. Values are shown as the
 * engine returned them; nothing is ranked or highlighted, and equal values stay equal.
 */
export function RunComparison({ detail, data }: { detail: ScenarioDetail; data: CompareResponse }) {
  const results = data.results;
  const names = new Map(detail.scenario.zones.map((z) => [z.id, z.name]));
  const coverage = results.find((r) => r.metrics)?.metrics?.coverage_by_zone ?? {};
  const zoneIds = detail.scenario.zones.filter((z) => z.id in coverage).map((z) => z.id);
  const byId = new Map(results.map((r) => [r.policy_id, r]));
  const aidos = byId.get('aidos');
  const greedy = byId.get('greedy');
  const bothHavePlans = Boolean(aidos?.has_plan && greedy?.has_plan);
  const aidosMatchesGreedy = samePlan(aidos, greedy);

  return (
    <Panel
      title="Baseline comparison"
      description="Every policy ran on this same snapshot with the same fuzzy scores and the same hard limits."
    >
      <div className="table-scroll">
        <table className="data-table run-compare">
          <caption className="visually-hidden">
            Metrics of each allocation policy on snapshot {data.snapshot_hash.slice(0, 10)}
          </caption>
          <thead>
            <tr>
              <th scope="col">Metric</th>
              {results.map((r) => (
                <th key={r.policy_id} scope="col" className="is-num">
                  {POLICY_SHORT[r.policy_id]}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <th scope="row">Status</th>
              {results.map((r) => (
                <td key={r.policy_id} className="is-num">
                  <StatusBadge tone={STATUS_TONE[r.status]}>{r.status}</StatusBadge>
                </td>
              ))}
            </tr>
            {ROWS.map((row) => (
              <tr key={row.label}>
                <th scope="row">
                  {row.label}
                  {row.formula && <span className="run-compare__formula mono">{row.formula}</span>}
                </th>
                {results.map((r) => (
                  <td key={r.policy_id} className="is-num num">
                    {row.value(r)}
                  </td>
                ))}
              </tr>
            ))}
            <tr className="run-compare__group">
              <th scope="rowgroup" colSpan={results.length + 1}>
                Coverage by zone (Σ allocated / Σ requested)
              </th>
            </tr>
            {zoneIds.map((id) => (
              <tr key={id}>
                <th scope="row">{zoneShortName(names.get(id) ?? id)}</th>
                {results.map((r) => (
                  <td key={r.policy_id} className="is-num num">
                    {r.metrics ? formatRatio(r.metrics.coverage_by_zone[id]) : '—'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="run-compare__notes">
        <p>
          Stock is fixed, so when every policy uses all of it the totals match. What differs is
          which zones receive the units. No policy creates supply.
        </p>
        {bothHavePlans && aidosMatchesGreedy && (
          <p>
            AidOS (urgency-first) produced exactly the same allocation as urgency greedy. That is
            the expected control: with a linear urgency objective and no coupling constraints, the
            optimum serves zones in urgency order, so the solver adds a proof of optimality but not
            a different plan. The balanced mode adds a coverage floor, which is where the solver
            changes the outcome.
          </p>
        )}
        {bothHavePlans && !aidosMatchesGreedy && (
          <p>
            AidOS (urgency-first) and urgency greedy differ on this snapshot; compare the zone rows
            above to see where.
          </p>
        )}
        <p>
          A single scenario is not evidence that one policy is better. Paired results over many
          synthetic scenarios are on the Evaluation page.
        </p>
      </div>
    </Panel>
  );
}
