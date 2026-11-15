import { useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ErrorBar,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { Description, EvaluationSummary, MetricSpec } from '../../api/types';
import { POLICY_COLOUR, formatValue, policyLabel } from '../../lib/evaluation';
import { useReducedMotion } from '../../lib/useMediaQuery';
import { Panel } from '../ui/Panel';
import { StatusBadge } from '../ui/StatusBadge';

const AXIS = { stroke: '#2a3542' };
const TICK = { fill: '#a2b0c0', fontSize: 12 };
const PERCENT = new Set(['fraction', 'share']);

/** Values on the chart's own scale: fractions are drawn as percentages. */
const scaled = (value: number | null | undefined, unit: string) =>
  value === null || value === undefined ? null : PERCENT.has(unit) ? value * 100 : value;

const axisUnit = (unit: string) => (PERCENT.has(unit) ? '%' : unit === 'ms' ? 'ms' : unit);

/* The chart metric choices required by the brief, in display order. */
const CHART_METRICS = [
  'unit_coverage',
  'urgency_weighted_coverage',
  'starved_zones',
  'min_zone_coverage',
  'jain_fairness',
  'runtime_ms',
  'valid',
  'coverage_gap',
  'mean_resource_coverage',
  'critical_coverage',
];

function MetricSelect({
  metrics,
  value,
  onChange,
  label = 'Metric',
}: {
  metrics: MetricSpec[];
  value: string;
  onChange: (key: string) => void;
  label?: string;
}) {
  return (
    <label className="field">
      {label}
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {metrics.map((m) => (
          <option key={m.key} value={m.key}>
            {m.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function chartMetrics(summary: EvaluationSummary) {
  const byKey = new Map(summary.metrics.map((m) => [m.key, m]));
  return CHART_METRICS.map((k) => byKey.get(k)).filter((m): m is MetricSpec => Boolean(m));
}

/* ---------------------------------------------------------------- policies on one metric */

type Stat = 'mean' | 'median';

export function MetricChart({ summary }: { summary: EvaluationSummary }) {
  const reduced = useReducedMotion();
  const metrics = chartMetrics(summary);
  const [key, setKey] = useState(metrics[0]?.key ?? 'unit_coverage');
  const [stat, setStat] = useState<Stat>('mean');
  const spec = metrics.find((m) => m.key === key) ?? metrics[0];
  if (!spec) return null;
  const st = summary.static;
  const rows = st.policies.map((p) => {
    const d: Description | undefined = st.overall[p]?.[spec.key];
    const centre = stat === 'mean' ? d?.mean : d?.median;
    const value = scaled(centre, spec.unit);
    const p25 = scaled(d?.p25, spec.unit);
    const p75 = scaled(d?.p75, spec.unit);
    return {
      policy: policyLabel(p),
      id: p,
      value,
      // The interquartile range is drawn only around the median, where it always contains it.
      iqr:
        stat === 'median' && value !== null && p25 !== null && p75 !== null
          ? [value - p25, p75 - value]
          : undefined,
      d,
    };
  });
  const unit = axisUnit(spec.unit);
  return (
    <Panel
      title="Policies on one metric"
      description={
        stat === 'mean'
          ? `Bars: mean over ${st.scenarios} scenarios. ${spec.better === 'higher' ? 'Higher is better.' : spec.better === 'lower' ? 'Lower is better.' : ''}`
          : `Bars: median over ${st.scenarios} scenarios. Whiskers: 25th to 75th percentile. ${spec.better === 'higher' ? 'Higher is better.' : spec.better === 'lower' ? 'Lower is better.' : ''}`
      }
      actions={
        <div className="eval-controls">
          <MetricSelect metrics={metrics} value={spec.key} onChange={setKey} />
          <fieldset className="policy-tabs eval-stat">
            <legend className="visually-hidden">Statistic</legend>
            {(['mean', 'median'] as Stat[]).map((s) => (
              <label key={s} className="policy-tab">
                <input
                  type="radio"
                  name="eval-stat"
                  value={s}
                  checked={stat === s}
                  onChange={() => setStat(s)}
                  className="visually-hidden"
                />
                {s === 'mean' ? 'Mean' : 'Median + IQR'}
              </label>
            ))}
          </fieldset>
        </div>
      }
    >
      <p className="eval-chart-tags">
        {spec.aligned ? (
          <StatusBadge tone="warn">Objective-aligned</StatusBadge>
        ) : (
          <StatusBadge tone="neutral">External</StatusBadge>
        )}
        {spec.note && <span>{spec.note}</span>}
      </p>
      <div className="chart-frame" aria-hidden="true">
        <ResponsiveContainer width="100%" height={260} minWidth={0} debounce={50}>
          <BarChart data={rows} margin={{ top: 16, right: 8, bottom: 0, left: 4 }}>
            <CartesianGrid vertical={false} stroke="#1d2631" />
            <XAxis dataKey="policy" tickLine={false} axisLine={AXIS} tick={TICK} interval={0} />
            <YAxis
              tickLine={false}
              axisLine={false}
              tick={TICK}
              width={52}
              domain={PERCENT.has(spec.unit) ? [0, 100] : [0, 'auto']}
              unit={unit === '%' ? '%' : ''}
            />
            <Tooltip
              cursor={{ fill: 'rgba(255,255,255,0.03)' }}
              contentStyle={{ background: '#111821', border: '1px solid #2a3542', borderRadius: 8 }}
              formatter={(v) => [
                `${Number(v).toFixed(2)} ${unit}`,
                stat === 'mean' ? 'Mean' : 'Median',
              ]}
            />
            <Bar
              dataKey="value"
              isAnimationActive={!reduced}
              animationDuration={320}
              radius={[3, 3, 0, 0]}
            >
              {rows.map((r) => (
                <Cell key={r.id} fill={POLICY_COLOUR[r.id] ?? '#8a99ab'} />
              ))}
              {stat === 'median' && (
                <ErrorBar dataKey="iqr" width={6} stroke="#eaf0f4" strokeWidth={1.2} />
              )}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="visually-hidden">
        <table aria-label={`${spec.label} by policy`}>
          <thead>
            <tr>
              <th scope="col">Policy</th>
              <th scope="col">Mean</th>
              <th scope="col">Median</th>
              <th scope="col">25th percentile</th>
              <th scope="col">75th percentile</th>
              <th scope="col">n</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} data-policy={r.id}>
                <th scope="row">{r.policy}</th>
                <td>{formatValue(r.d?.mean, spec.unit)}</td>
                <td>{formatValue(r.d?.median, spec.unit)}</td>
                <td>{formatValue(r.d?.p25, spec.unit)}</td>
                <td>{formatValue(r.d?.p75, spec.unit)}</td>
                <td>{r.d?.n ?? 0}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

/* ---------------------------------------------------------------- scenario families */

export function FamilyChart({ summary }: { summary: EvaluationSummary }) {
  const reduced = useReducedMotion();
  const metrics = chartMetrics(summary);
  const st = summary.static;
  const [key, setKey] = useState('min_zone_coverage');
  const [shown, setShown] = useState<string[]>(st.families);
  const spec = metrics.find((m) => m.key === key) ?? metrics[0];
  if (!spec) return null;
  const families = st.families.filter((f) => shown.includes(f));
  const rows = families.map((f) => ({
    family: f,
    ...Object.fromEntries(
      st.policies.map((p) => [p, scaled(st.by_family[f]?.[p]?.[spec.key]?.mean, spec.unit)]),
    ),
  }));
  const toggle = (f: string) =>
    setShown((prev) => (prev.includes(f) ? prev.filter((x) => x !== f) : [...prev, f].sort()));

  return (
    <Panel
      title="By scenario family"
      description={`Mean of the metric within each family (${st.by_family[st.families[0]]?.[st.policies[0]]?.[spec.key]?.n ?? 0} scenarios per family in this run). Families change one condition at a time: scarcity, urgency spread, demand spread or which resources are short.`}
      actions={<MetricSelect metrics={metrics} value={spec.key} onChange={setKey} />}
    >
      <div className="eval-chips" role="group" aria-label="Families shown">
        {st.families.map((f) => (
          <button
            key={f}
            type="button"
            className="eval-chip"
            aria-pressed={shown.includes(f)}
            onClick={() => toggle(f)}
            title={summary.families[f]?.description}
          >
            {f} · {summary.families[f]?.name ?? f}
          </button>
        ))}
      </div>
      {families.length === 0 ? (
        <p className="explain__empty">Select at least one family.</p>
      ) : (
        <>
          <div className="chart-frame" aria-hidden="true">
            <ResponsiveContainer width="100%" height={280} minWidth={0} debounce={50}>
              <BarChart data={rows} margin={{ top: 16, right: 8, bottom: 0, left: 4 }} barGap={2}>
                <CartesianGrid vertical={false} stroke="#1d2631" />
                <XAxis dataKey="family" tickLine={false} axisLine={AXIS} tick={TICK} />
                <YAxis
                  tickLine={false}
                  axisLine={false}
                  tick={TICK}
                  width={52}
                  domain={PERCENT.has(spec.unit) ? [0, 100] : [0, 'auto']}
                  unit={PERCENT.has(spec.unit) ? '%' : ''}
                />
                <Tooltip
                  cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                  contentStyle={{
                    background: '#111821',
                    border: '1px solid #2a3542',
                    borderRadius: 8,
                  }}
                  formatter={(v, name) => [
                    `${Number(v).toFixed(2)} ${axisUnit(spec.unit)}`,
                    policyLabel(String(name)),
                  ]}
                />
                <Legend
                  formatter={(name: string) => policyLabel(name)}
                  wrapperStyle={{ fontSize: 12 }}
                />
                {st.policies.map((p) => (
                  <Bar
                    key={p}
                    dataKey={p}
                    fill={POLICY_COLOUR[p] ?? '#8a99ab'}
                    isAnimationActive={!reduced}
                    animationDuration={320}
                    radius={[2, 2, 0, 0]}
                  />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="table-scroll">
            <table
              className="data-table eval-table"
              aria-label={`${spec.label} by family and policy`}
            >
              <thead>
                <tr>
                  <th scope="col">Family</th>
                  {st.policies.map((p) => (
                    <th key={p} scope="col" className="is-num">
                      {policyLabel(p)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {families.map((f) => (
                  <tr key={f} data-family={f}>
                    <th scope="row">
                      {f} · {summary.families[f]?.name ?? f}
                    </th>
                    {st.policies.map((p) => (
                      <td key={p} className="is-num num" data-policy={p}>
                        {formatValue(st.by_family[f]?.[p]?.[spec.key]?.mean, spec.unit)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </Panel>
  );
}

/* ---------------------------------------------------------------- runtime scaling */

export function ScalingChart({ summary }: { summary: EvaluationSummary }) {
  const reduced = useReducedMotion();
  const points = summary.scaling.points;
  if (!points.length) {
    return (
      <Panel title="Runtime and problem size">
        <p className="explain__empty">This run has no scaling measurements.</p>
      </Panel>
    );
  }
  const policies = [...new Set(points.map((p) => p.policy))];
  const sizes = [...new Set(points.map((p) => p.zones))].sort((a, b) => a - b);
  const rows = sizes.map((zones) => ({
    zones,
    ...Object.fromEntries(
      policies.map((p) => [
        p,
        points.find((x) => x.zones === zones && x.policy === p)?.runtime_ms.median ?? null,
      ]),
    ),
  }));
  return (
    <Panel
      title="Runtime and problem size"
      description="Median wall-clock time of one policy call, by number of zones (4 resources, moderate scarcity). One machine, logarithmic axis; timings vary between runs and are never part of a reproducibility check."
    >
      <div className="chart-frame" aria-hidden="true">
        <ResponsiveContainer width="100%" height={260} minWidth={0} debounce={50}>
          <LineChart data={rows} margin={{ top: 16, right: 12, bottom: 4, left: 4 }}>
            <CartesianGrid stroke="#1d2631" />
            <XAxis
              dataKey="zones"
              tickLine={false}
              axisLine={AXIS}
              tick={TICK}
              label={{
                value: 'zones',
                position: 'insideBottomRight',
                offset: -2,
                fill: '#7d8a9b',
                fontSize: 12,
              }}
            />
            <YAxis
              scale="log"
              domain={['auto', 'auto']}
              allowDataOverflow
              tickLine={false}
              axisLine={false}
              tick={TICK}
              width={56}
              unit=" ms"
            />
            <Tooltip
              contentStyle={{ background: '#111821', border: '1px solid #2a3542', borderRadius: 8 }}
              formatter={(v, name) => [`${Number(v).toFixed(3)} ms`, policyLabel(String(name))]}
            />
            <Legend
              formatter={(name: string) => policyLabel(name)}
              wrapperStyle={{ fontSize: 12 }}
            />
            {policies.map((p) => (
              <Line
                key={p}
                type="monotone"
                dataKey={p}
                stroke={POLICY_COLOUR[p] ?? '#8a99ab'}
                strokeWidth={2}
                dot={{ r: 3 }}
                isAnimationActive={!reduced}
                animationDuration={320}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="table-scroll">
        <table className="data-table eval-table" aria-label="Median runtime by zones and policy">
          <thead>
            <tr>
              <th scope="col">Zones</th>
              {policies.map((p) => (
                <th key={p} scope="col" className="is-num">
                  {policyLabel(p)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sizes.map((zones) => (
              <tr key={zones} data-zones={zones}>
                <th scope="row" className="num">
                  {zones}
                </th>
                {policies.map((p) => {
                  const point = points.find((x) => x.zones === zones && x.policy === p);
                  return (
                    <td key={p} className="is-num num">
                      {formatValue(point?.runtime_ms.median, 'ms')}
                      {point && point.runs > 0 && p.startsWith('aidos') && (
                        <span className="eval-median">
                          optimal {point.optimal}/{point.runs}
                        </span>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
