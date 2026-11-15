import { useState } from 'react';
import type { EvaluationRun, EvaluationSummary, MetricSpec } from '../../api/types';
import {
  EVENT_LABEL,
  PAIRS,
  formatDiff,
  formatP,
  formatValue,
  policyLabel,
  readPaired,
} from '../../lib/evaluation';
import { formatInt } from '../../lib/format';
import { Metric } from '../ui/Metric';
import { Panel } from '../ui/Panel';
import { StatusBadge } from '../ui/StatusBadge';

/* ---------------------------------------------------------------- shared bits */

function AlignmentBadge({ spec }: { spec: MetricSpec }) {
  return spec.aligned ? (
    <StatusBadge
      tone="warn"
      title="The AidOS objective, or the urgency model it uses, favours this metric by design. A win here shows optimisation success, not independent evidence."
    >
      Objective-aligned
    </StatusBadge>
  ) : (
    <StatusBadge tone="neutral" title="Not targeted by any policy's objective.">
      External
    </StatusBadge>
  );
}

const direction = (spec: MetricSpec) =>
  spec.better === 'higher' ? 'Higher is better' : spec.better === 'lower' ? 'Lower is better' : '';

/* ---------------------------------------------------------------- metadata */

export function RunMetadata({ run }: { run: EvaluationRun }) {
  const { manifest, config, summary } = run;
  const counts = manifest.counts ?? {};
  const versions = manifest.versions ?? {};
  const failures = run.failures ?? [];
  return (
    <Panel
      title="Run and reproducibility"
      description="Everything needed to regenerate these numbers. The same seeds and configuration give the same allocations; only timings vary."
    >
      <dl className="eval-facts">
        <div>
          <dt>Run id</dt>
          <dd className="mono">{manifest.run_id}</dd>
        </div>
        <div>
          <dt>Preset</dt>
          <dd>{manifest.preset ?? config?.preset?.name ?? 'unknown'}</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>
            <StatusBadge tone={manifest.status === 'complete' ? 'ok' : 'warn'} dot>
              {manifest.status}
            </StatusBadge>
          </dd>
        </div>
        <div>
          <dt>Created (UTC)</dt>
          <dd className="num">{manifest.created_utc ?? 'N/A'}</dd>
        </div>
        <div>
          <dt>Duration</dt>
          <dd className="num">
            {manifest.duration_s !== undefined ? `${manifest.duration_s} s` : 'N/A'}
          </dd>
        </div>
        <div>
          <dt>Failures</dt>
          <dd className="num">{counts.failures ?? failures.length}</dd>
        </div>
        <div>
          <dt>Engine</dt>
          <dd className="num">{versions.engine ?? 'N/A'}</dd>
        </div>
        <div>
          <dt>Fuzzy rules</dt>
          <dd className="num">
            v{versions.fuzzy_config ?? config?.fuzzy_config_version ?? '?'}
            {config?.fuzzy_method && (
              <span className="eval-facts__sub"> {config.fuzzy_method}</span>
            )}
          </dd>
        </div>
        <div>
          <dt>OR-Tools</dt>
          <dd className="num">{versions.ortools ?? 'N/A'}</dd>
        </div>
        <div>
          <dt>Python / NumPy</dt>
          <dd className="num">
            {versions.python ?? 'N/A'} / {versions.numpy ?? 'N/A'}
          </dd>
        </div>
        <div>
          <dt>Bootstrap</dt>
          <dd className="num">
            {summary
              ? `${formatInt(summary.bootstrap.resamples)} resamples · seed ${summary.bootstrap.seed} · ${Math.round(summary.bootstrap.level * 100)}%`
              : 'N/A'}
          </dd>
        </div>
        <div className="eval-facts__wide">
          <dt>Source revision</dt>
          <dd>{manifest.source_revision ?? 'not recorded'}</dd>
        </div>
      </dl>

      {config && (
        <div className="eval-config">
          <div>
            <h3 className="eval-sub">AidOS configuration (frozen)</h3>
            <ul className="eval-kv">
              {Object.entries(config.aidos_config).map(([k, v]) => (
                <li key={k}>
                  <span className="mono">{k}</span>
                  <span className="num">{JSON.stringify(v)}</span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="eval-sub">Scenario seeds by family</h3>
            <ul className="eval-kv">
              {Object.entries(config.family_seeds).map(([family, [from, to]]) => (
                <li key={family}>
                  <span>
                    {family} · {summary?.families[family]?.name ?? ''}
                  </span>
                  <span className="num">
                    {from}–{to}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {failures.length > 0 && (
        <div className="eval-failures" role="status">
          <h3 className="eval-sub">Failures recorded in this run</h3>
          <ul>
            {failures.map((f) => (
              <li key={`${f.stage}-${f.item}`}>
                <span className="mono">
                  {f.stage} · {f.item}
                </span>{' '}
                {f.error}
              </li>
            ))}
          </ul>
        </div>
      )}
    </Panel>
  );
}

/* ---------------------------------------------------------------- overview */

export function EvalOverview({ run }: { run: EvaluationRun }) {
  const counts = run.manifest.counts ?? {};
  const summary = run.summary;
  return (
    <section className="eval-overview" aria-label="What this run compares">
      <p className="eval-lede">
        Four allocation policies ran on <b>the same synthetic scenarios</b>, with the same stock,
        requests, ratings and hard limits: <b>FCFS</b> (arrival order, ignores urgency),{' '}
        <b>urgency greedy</b> (urgency order, no optimiser), <b>AidOS</b> (fuzzy urgency + CP-SAT,
        urgency-first) and <b>AidOS balanced</b> (a coverage floor first). Because every policy sees
        every scenario, differences are compared <b>scenario by scenario</b> (paired), not as
        unrelated averages.
      </p>
      <dl className="metrics" aria-label="Run size">
        <Metric
          label="Static scenarios"
          value={formatInt(counts.static_scenarios ?? 0)}
          detail={`${summary?.static.families.length ?? 0} families (A–G)`}
        />
        <Metric
          label="Policy runs"
          value={formatInt(counts.static_records ?? 0)}
          detail="scenario × policy"
        />
        <Metric
          label="Event scripts"
          value={formatInt(counts.dynamic_scripts ?? 0)}
          detail={`${formatInt(counts.dynamic_steps ?? 0)} shared-state steps`}
        />
        <Metric
          label="Dispatch trajectories"
          value={formatInt(counts.dispatch_runs ?? 0)}
          detail="script × policy"
        />
        <Metric
          label="Failures"
          value={formatInt(counts.failures ?? 0)}
          tone={(counts.failures ?? 0) > 0 ? 'warn' : 'ok'}
          detail="recorded, never dropped"
        />
      </dl>
    </section>
  );
}

/* ---------------------------------------------------------------- policy table */

export function PolicyTable({ summary }: { summary: EvaluationSummary }) {
  const st = summary.static;
  const policies = st.policies;
  return (
    <Panel
      title="Policy comparison"
      description={`Mean over ${formatInt(st.scenarios)} scenarios (median and n below). Objective-aligned metrics are ones the AidOS objective or its urgency model favour by design; read them as optimisation success, not independent evidence.`}
    >
      <div className="table-scroll">
        <table className="data-table eval-table">
          <caption className="visually-hidden">Policy means for each metric</caption>
          <thead>
            <tr>
              <th scope="col">Metric</th>
              {policies.map((p) => (
                <th key={p} scope="col" className="is-num">
                  {policyLabel(p)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {summary.metrics.map((spec) => {
              const values = policies.map((p) => st.overall[p]?.[spec.key]);
              const means = values.map((d) => d?.mean);
              const allEqual = means.every(
                (m) => m !== null && m !== undefined && Math.abs(m - (means[0] ?? 0)) < 1e-12,
              );
              return (
                <tr key={spec.key} data-metric={spec.key}>
                  <th scope="row">
                    <span className="eval-metric">{spec.label}</span>
                    <span className="eval-metric__meta">
                      <AlignmentBadge spec={spec} />
                      <span>{direction(spec)}</span>
                    </span>
                    {spec.note && <span className="eval-metric__note">{spec.note}</span>}
                    {allEqual && (
                      <span className="eval-metric__note">Same mean for every policy.</span>
                    )}
                  </th>
                  {values.map((d, i) => (
                    <td key={policies[i]} className="is-num num" data-policy={policies[i]}>
                      <span className="eval-mean">{formatValue(d?.mean, spec.unit)}</span>
                      <span className="eval-median">
                        median {formatValue(d?.median, spec.unit)} · n {d?.n ?? 0}
                      </span>
                    </td>
                  ))}
                </tr>
              );
            })}
            <tr>
              <th scope="row">
                <span className="eval-metric">Valid plans / optimal proven</span>
                <span className="eval-metric__note">
                  Checked by the independent validator. FCFS and greedy are heuristics: they report
                  COMPLETE, never OPTIMAL.
                </span>
              </th>
              {policies.map((p) => {
                const f = st.feasibility[p];
                return (
                  <td key={p} className="is-num num" data-policy={p}>
                    <span className="eval-mean">
                      {f.valid}/{f.total}
                    </span>
                    <span className="eval-median">optimal proven {f.optimal_proven}</span>
                  </td>
                );
              })}
            </tr>
            <tr>
              <th scope="row">
                <span className="eval-metric">Solver statuses</span>
              </th>
              {policies.map((p) => (
                <td key={p} className="is-num">
                  {Object.entries(st.statuses[p] ?? {}).map(([status, n]) => (
                    <span key={status} className="eval-median mono">
                      {status} {n}
                    </span>
                  ))}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
      <ul className="eval-identical" aria-label="Identical plans">
        {Object.entries(st.identical_plans).map(([pair, n]) => {
          const [a, b] = pair.split('|');
          return (
            <li key={pair}>
              {policyLabel(a)} and {policyLabel(b)} produced the identical allocation in{' '}
              <b className="num">
                {n} of {st.scenarios}
              </b>{' '}
              scenarios.
            </li>
          );
        })}
      </ul>
    </Panel>
  );
}

/* ---------------------------------------------------------------- paired comparisons */

export function PairedComparisons({ summary }: { summary: EvaluationSummary }) {
  const st = summary.static;
  const [pair, setPair] = useState(0);
  const [scope, setScope] = useState('all');
  const [a, b] = PAIRS[pair];
  const specs = new Map(summary.metrics.map((m) => [m.key, m]));
  const rows = st.comparisons.filter((c) => c.scope === scope && c.a === a && c.b === b);
  const level = Math.round(summary.bootstrap.level * 100);

  return (
    <Panel
      title="Paired comparisons"
      description={`Difference A − B per scenario, then summarised. ${level}% percentile-bootstrap intervals (${formatInt(summary.bootstrap.resamples)} resamples). W/T/L counts scenarios where A was higher / equal / lower. d_z is the mean difference divided by its standard deviation.`}
      actions={
        <div className="eval-controls">
          <label className="field">
            Pair (A vs B)
            <select value={pair} onChange={(e) => setPair(Number(e.target.value))}>
              {PAIRS.map(([x, y], i) => (
                <option key={`${x}-${y}`} value={i}>
                  {policyLabel(x)} vs {policyLabel(y)}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            Scenarios
            <select value={scope} onChange={(e) => setScope(e.target.value)}>
              <option value="all">All families</option>
              {st.families.map((f) => (
                <option key={f} value={f}>
                  Family {f} · {summary.families[f]?.name ?? ''}
                </option>
              ))}
            </select>
          </label>
        </div>
      }
    >
      {rows.length === 0 ? (
        <p className="explain__empty">
          This run did not record a comparison for {policyLabel(a)} vs {policyLabel(b)} in this
          scope.
        </p>
      ) : (
        <div className="table-scroll">
          <table className="data-table eval-table eval-paired">
            <caption className="visually-hidden">
              Paired differences, {policyLabel(a)} minus {policyLabel(b)}
            </caption>
            <thead>
              <tr>
                <th scope="col">Metric</th>
                <th scope="col" className="is-num">
                  Mean A − B [{level}% CI]
                </th>
                <th scope="col" className="is-num">
                  Median
                </th>
                <th scope="col" className="is-num">
                  W / T / L
                </th>
                <th scope="col" className="is-num">
                  d_z
                </th>
                <th scope="col">Reading</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((c) => {
                const spec = specs.get(c.metric);
                const unit = spec?.unit ?? '';
                return (
                  <tr key={c.metric} data-metric={c.metric}>
                    <th scope="row">
                      <span className="eval-metric">{spec?.label ?? c.metric}</span>
                      {spec && (
                        <span className="eval-metric__meta">
                          <AlignmentBadge spec={spec} />
                          <span>{direction(spec)}</span>
                        </span>
                      )}
                    </th>
                    <td className="is-num num">
                      {formatDiff(c.mean_diff, unit)}
                      <span className="eval-median">
                        {c.ci_mean
                          ? `[${formatDiff(c.ci_mean[0], unit)}, ${formatDiff(c.ci_mean[1], unit)}]`
                          : 'no interval'}{' '}
                        · n {c.n}
                        {c.dropped ? ` (${c.dropped} N/A)` : ''}
                      </span>
                    </td>
                    <td className="is-num num">{formatDiff(c.median_diff, unit)}</td>
                    <td className="is-num num">
                      {c.wins} / {c.ties} / {c.losses}
                    </td>
                    <td className="is-num num">
                      {c.effect_dz === null ? 'N/A' : c.effect_dz.toFixed(2)}
                    </td>
                    <td>{readPaired(c, spec)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <h3 className="eval-sub">Pre-declared tests (all scenarios)</h3>
      <p className="eval-note">
        Exact two-sided sign tests on the scenarios where A and B differ, Holm-adjusted across these
        {` ${st.primary_tests.length}`} tests only. Read the effect sizes and intervals above first;
        a small p-value says the difference is consistent, not that it matters.
      </p>
      <div className="table-scroll">
        <table className="data-table eval-table">
          <thead>
            <tr>
              <th scope="col">Comparison</th>
              <th scope="col">Metric</th>
              <th scope="col" className="is-num">
                Sign test p
              </th>
              <th scope="col" className="is-num">
                Holm p
              </th>
            </tr>
          </thead>
          <tbody>
            {st.primary_tests.map((t) => (
              <tr key={`${t.a}-${t.b}-${t.metric}`} data-test={t.metric}>
                <td>
                  {policyLabel(t.a)} vs {policyLabel(t.b)}
                </td>
                <td>{specs.get(t.metric)?.label ?? t.metric}</td>
                <td className="is-num num">{formatP(t.sign_p)}</td>
                <td className="is-num num">{formatP(t.holm_p)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

/* ---------------------------------------------------------------- dynamic */

const DISPATCH_ROWS: { key: string; label: string; unit: string; better: string }[] = [
  {
    key: 'dispatched_units',
    label: 'Units dispatched',
    unit: 'units',
    better: 'Equal stock: should match',
  },
  {
    key: 'fulfilment',
    label: 'Fulfilment (dispatched / total need)',
    unit: 'fraction',
    better: 'Higher is better',
  },
  {
    key: 'urgency_weighted_fulfilment',
    label: 'Urgency-weighted fulfilment',
    unit: 'fraction',
    better: 'Objective-aligned',
  },
  {
    key: 'min_zone_fulfilment',
    label: 'Lowest zone fulfilment',
    unit: 'fraction',
    better: 'Higher is better',
  },
  {
    key: 'zones_never_served',
    label: 'Zones never served',
    unit: 'zones',
    better: 'Lower is better',
  },
];

export function DynamicResults({ summary }: { summary: EvaluationSummary }) {
  const rec = summary.dynamic_recommendation;
  const dsp = summary.dynamic_dispatch;
  const recPolicies = rec.policies ?? [];
  const dspPolicies = dsp.policies ?? [];
  return (
    <div className="eval-dynamic">
      <Panel
        title="Dynamic events · recommendation mode"
        description={`Shared state: ${formatInt(rec.scripts ?? 0)} event scripts, ${formatInt(rec.steps)} steps. After each event every policy re-plans on the same snapshot; nothing is dispatched. Reallocation is the number of units whose recipient changed versus the previous step. A large reallocation is not automatically better: it can mean responsiveness or instability.`}
      >
        {rec.by_event && rec.event_types ? (
          <div className="table-scroll">
            <table className="data-table eval-table">
              <caption className="visually-hidden">Reallocation by event type and policy</caption>
              <thead>
                <tr>
                  <th scope="col">Event</th>
                  {recPolicies.map((p) => (
                    <th key={p} scope="col" className="is-num">
                      {policyLabel(p)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rec.event_types.map((event) => (
                  <tr key={event} data-event={event}>
                    <th scope="row">{EVENT_LABEL[event] ?? event}</th>
                    {recPolicies.map((p) => {
                      const d = rec.by_event?.[event]?.[p];
                      return (
                        <td key={p} className="is-num num">
                          <span className="eval-mean">
                            {formatValue(d?.reallocated_units?.mean, 'units')} units
                          </span>
                          <span className="eval-median">
                            plan changed {formatValue(d?.plan_changed?.mean, 'share')} · Δunmet{' '}
                            {formatValue(d?.unmet_change?.mean, 'units')}
                          </span>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="explain__empty">This run has no recommendation-mode results.</p>
        )}
      </Panel>

      <Panel
        title="Dynamic events · dispatch mode"
        description={`Policy-specific trajectories: ${formatInt(dsp.scripts)} scripts × ${dspPolicies.length} policies. Supplies arrive in waves while the crisis changes, and each policy dispatches its own plan after each wave, so later states differ between policies. Compared per script (paired), never mixed with the recommendation-mode rows above. Caution: every script adds a high-urgency zone that arrives last, which FCFS can never serve; the gaps in zones never served and lowest-zone fulfilment come from that zone, not from better equity in general (docs/evaluation/results.md, section 3).`}
      >
        {dsp.overall ? (
          <>
            <div className="table-scroll">
              <table className="data-table eval-table">
                <caption className="visually-hidden">Dispatch-mode outcomes by policy</caption>
                <thead>
                  <tr>
                    <th scope="col">Outcome (mean over scripts)</th>
                    {dspPolicies.map((p) => (
                      <th key={p} scope="col" className="is-num">
                        {policyLabel(p)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {DISPATCH_ROWS.map((row) => (
                    <tr key={row.key} data-metric={row.key}>
                      <th scope="row">
                        <span className="eval-metric">{row.label}</span>
                        <span className="eval-metric__note">{row.better}</span>
                      </th>
                      {dspPolicies.map((p) => (
                        <td key={p} className="is-num num">
                          {formatValue(dsp.overall?.[p]?.[row.key]?.mean, row.unit)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <h3 className="eval-sub">Dispatch integrity</h3>
            <div className="table-scroll">
              <table className="data-table eval-table">
                <thead>
                  <tr>
                    <th scope="col">Policy</th>
                    <th scope="col" className="is-num">
                      Inventory conserved
                    </th>
                    <th scope="col" className="is-num">
                      Ledger consistent
                    </th>
                    <th scope="col" className="is-num">
                      Double dispatch blocked
                    </th>
                    <th scope="col" className="is-num">
                      Rejected events
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {dspPolicies.map((p) => {
                    const i = dsp.integrity?.[p];
                    if (!i) return null;
                    return (
                      <tr key={p} data-policy={p}>
                        <th scope="row">{policyLabel(p)}</th>
                        <td className="is-num num">
                          {i.inventory_conserved}/{i.runs}
                        </td>
                        <td className="is-num num">
                          {i.ledger_consistent}/{i.runs}
                        </td>
                        <td className="is-num num">
                          {i.double_dispatch_blocked}/{i.runs}
                        </td>
                        <td className="is-num num">{i.rejected_events}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <p className="explain__empty">This run has no dispatch-mode results.</p>
        )}
      </Panel>
    </div>
  );
}

/* ---------------------------------------------------------------- methodology */

export function Methodology() {
  return (
    <Panel
      title="What these results do and do not show"
      description="Full definitions: docs/evaluation/metric-definitions.md and docs/evaluation/experimental-protocol.md."
    >
      <ul className="eval-limits">
        <li>
          <b>Synthetic only.</b> Every scenario comes from a seeded generator with chosen ranges.
          Intervals and tests describe variation within that synthetic distribution, not real
          disasters or humanitarian operations.
        </li>
        <li>
          <b>Objective-aligned metrics are circular.</b> AidOS maximises urgency-weighted
          allocation, and critical-zone coverage uses the same fuzzy scores. Winning there shows the
          optimiser does what it was told, not that the outcome is better for people.
        </li>
        <li>
          <b>Same supply, different recipients.</b> Every policy hands out all usable stock, so
          total coverage is identical by construction; policies differ only in who receives it.
        </li>
        <li>
          <b>Equality is not fairness.</b> Jain&apos;s index and the coverage gap measure how evenly
          coverage is spread, not whether the spread is just.
        </li>
        <li>
          <b>Runtime is one machine&apos;s wall clock.</b> It varies between runs and is never part
          of a reproducibility check.
        </li>
        <li>
          <b>No humanitarian effectiveness is established.</b> The evaluation tests the algorithms
          inside a simulation; it says nothing about lives or outcomes.
        </li>
      </ul>
    </Panel>
  );
}
