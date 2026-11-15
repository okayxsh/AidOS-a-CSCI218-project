import { Circle, CircleDot, PackageCheck } from 'lucide-react';
import type { CellDelta, PolicyResult, SimSession } from '../../api/types';
import { formatInt, formatRatio, resourceById, shortHash, zoneShortName } from '../../lib/format';
import { EVENT_LABEL, fmtScore, POLICY_NAME, STATE_INFO } from '../../lib/simulation';
import { Metric } from '../ui/Metric';
import { Panel } from '../ui/Panel';
import { StatusBadge } from '../ui/StatusBadge';

const zoneNames = (session: SimSession) => {
  const names = new Map<string, string>();
  for (const r of session.resolved_zones) names.set(r.zone_id, zoneShortName(r.name));
  for (const z of session.current.scenario.zones) names.set(z.id, zoneShortName(z.name));
  return names;
};

const recommendedOf = (session: SimSession): PolicyResult | undefined =>
  session.current.comparison.results.find((r) => r.policy_id === session.policy);

/* ---------------------------------------------------------------- summary */

export function SimSummary({ session }: { session: SimSession }) {
  const { summary, scenario } = session.current;
  const active = scenario.zones.filter((z) => z.activation_step <= scenario.step).length;
  const scheduled = scenario.zones.length - active;
  const plan = recommendedOf(session);
  const resources = resourceById(scenario);
  return (
    <>
      <dl className="metrics metrics--six" aria-label="Simulation state">
        <Metric
          label="Session state"
          value={session.state}
          tone={
            session.state === 'ERROR' ? 'critical' : session.state === 'PAUSED' ? 'warn' : 'default'
          }
          detail={STATE_INFO[session.state].meaning}
        />
        <Metric
          label="Events applied"
          value={formatInt(session.event_count)}
          detail={`of ${session.max_events} · clock step ${session.current.sim_step}`}
        />
        <Metric
          label="Active zones"
          value={formatInt(active)}
          detail={scheduled ? `${scheduled} scheduled later` : 'none scheduled'}
        />
        <Metric
          label="Requested"
          value={formatInt(summary.totals.requested)}
          detail={`against ${formatInt(summary.totals.stock)} in stock`}
        />
        <Metric
          label="Shortfall"
          value={formatInt(summary.totals.shortfall)}
          tone={summary.totals.shortfall > 0 ? 'warn' : 'ok'}
          detail="Σ per resource"
        />
        <Metric
          label="Dispatched"
          value={formatInt(session.dispatched_units)}
          detail={session.ledger.length ? `${session.ledger.length} dispatch(es)` : 'nothing yet'}
        />
      </dl>
      <Panel
        title="Inventory at this step"
        description={`Stock and active requests now, and what the ${POLICY_NAME[session.policy]} candidate plan would use. Running a plan never consumes stock.`}
      >
        <div className="table-scroll">
          <table className="data-table inventory-table">
            <thead>
              <tr>
                <th scope="col">Resource</th>
                <th scope="col" className="is-num">
                  In stock
                </th>
                <th scope="col" className="is-num">
                  Requested
                </th>
                <th scope="col" className="is-num">
                  Shortfall
                </th>
                <th scope="col" className="is-num">
                  Plan allocates
                </th>
                <th scope="col" className="is-num">
                  Left after plan
                </th>
              </tr>
            </thead>
            <tbody>
              {summary.resources.map((r) => (
                <tr key={r.resource_id}>
                  <th scope="row">{resources.get(r.resource_id)?.label ?? r.resource_id}</th>
                  <td className="is-num num" data-label="In stock">
                    {formatInt(r.stock)}
                  </td>
                  <td className="is-num num" data-label="Requested">
                    {formatInt(r.requested)}
                  </td>
                  <td
                    className={`is-num num${r.shortfall ? ' is-short' : ''}`}
                    data-label="Shortfall"
                  >
                    {formatInt(r.shortfall)}
                  </td>
                  <td className="is-num num" data-label="Plan allocates">
                    {plan?.metrics
                      ? formatInt(plan.metrics.allocated_by_resource[r.resource_id] ?? 0)
                      : '—'}
                  </td>
                  <td className="is-num num" data-label="Left after plan">
                    {plan?.metrics
                      ? formatInt(plan.metrics.remaining_by_resource[r.resource_id] ?? 0)
                      : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </>
  );
}

/* ---------------------------------------------------------------- allocation bars */

/**
 * The recommended plan per zone and resource. Bars keep their DOM node between steps, so a
 * change animates from the previous width to the new one; values that changed are marked.
 */
export function SimAllocation({ session }: { session: SimSession }) {
  const plan = recommendedOf(session);
  const { scenario } = session.current;
  const names = zoneNames(session);
  const previous = new Map<string, CellDelta>(
    (session.diff?.policies[0]?.cells ?? []).map((c) => [`${c.zone_id}|${c.resource_id}`, c]),
  );
  const cells = new Map((plan?.cells ?? []).map((c) => [`${c.zone_id}|${c.resource_id}`, c]));
  const seq = session.current.seq;

  return (
    <Panel
      title={`Recommended plan · ${POLICY_NAME[session.policy]}`}
      description="Candidate plan, not dispatched. Zones in urgency order; the faint mark shows the previous step's allocation."
    >
      {!plan?.has_plan ? (
        <p className="explain__empty">No plan for this step.</p>
      ) : (
        <ul className="sim-alloc" aria-label="Allocation by zone">
          {plan.zone_order.map((zoneId) => (
            <li key={zoneId} className="sim-alloc__zone">
              <p className="sim-alloc__name">{names.get(zoneId) ?? zoneId}</p>
              <div className="sim-alloc__rows">
                {scenario.resources.map((res) => {
                  const key = `${zoneId}|${res.id}`;
                  const cell = cells.get(key);
                  if (!cell || cell.requested === 0)
                    return (
                      <div key={res.id} className="sim-alloc__row is-none">
                        <span className="sim-alloc__res">{res.label}</span>
                        <span className="sim-alloc__value">no request</span>
                      </div>
                    );
                  const before = previous.get(key);
                  const changed =
                    before !== undefined && before.allocated_before !== cell.allocated;
                  const width = (cell.allocated / cell.requested) * 100;
                  const ghost =
                    before && before.requested_before
                      ? Math.min(100, (before.allocated_before / cell.requested) * 100)
                      : null;
                  return (
                    <div key={res.id} className={`sim-alloc__row${changed ? ' is-changed' : ''}`}>
                      <span className="sim-alloc__res">{res.label}</span>
                      <span className="sim-alloc__track" aria-hidden="true">
                        {changed && ghost !== null && (
                          <span className="sim-alloc__ghost" style={{ left: `${ghost}%` }} />
                        )}
                        <span
                          className={`sim-alloc__fill${cell.unmet ? ' is-short' : ''}`}
                          style={{ width: `${width}%` }}
                        />
                      </span>
                      <span className="sim-alloc__value num" key={`${seq}-${cell.allocated}`}>
                        <b>{formatInt(cell.allocated)}</b> / {formatInt(cell.requested)}
                        {changed && (
                          <span className="sim-alloc__was">
                            {' '}
                            was {formatInt(before.allocated_before)}
                          </span>
                        )}
                      </span>
                    </div>
                  );
                })}
              </div>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

/* ---------------------------------------------------------------- before / after */

export function StepComparison({ session }: { session: SimSession }) {
  const diff = session.diff;
  const names = zoneNames(session);
  const resources = resourceById(session.current.scenario);
  if (!diff) {
    return (
      <Panel
        title="Before and after"
        description="The latest event compared with the step before it."
      >
        <p className="explain__empty">No event yet. Apply one to see what it changed.</p>
      </Panel>
    );
  }
  const [recommended, fcfs] = diff.policies;
  const totals: [string, (p: typeof recommended) => [string, string]][] = [
    ['Units allocated', (p) => [formatInt(p.allocated_before), formatInt(p.allocated_after)]],
    ['Unmet units', (p) => [formatInt(p.unmet_before), formatInt(p.unmet_after)]],
    ['Urgency-weighted coverage', (p) => [formatRatio(p.uwc_before), formatRatio(p.uwc_after)]],
  ];
  const changedList = (p: typeof recommended) =>
    p.cells.filter((c) => c.allocated_before !== c.allocated_after);

  return (
    <Panel
      title="Before and after"
      description={`Step ${diff.before_seq} → step ${diff.after_seq}, both computed by the engine on the same rules and limits.`}
    >
      <div className="sim-compare">
        <div className="table-scroll">
          <table className="data-table sim-compare__table sim-compare__table--urgency">
            <caption className="sim-compare__caption">Fuzzy urgency</caption>
            <thead>
              <tr>
                <th scope="col">Zone</th>
                <th scope="col" className="is-num">
                  Before
                </th>
                <th scope="col" className="is-num">
                  After
                </th>
                <th scope="col">Category</th>
                <th scope="col" className="is-num">
                  Rank
                </th>
              </tr>
            </thead>
            <tbody>
              {diff.urgency.map((u) => {
                const moved = u.score_before !== u.score_after || u.rank_before !== u.rank_after;
                return (
                  <tr key={u.zone_id} className={moved ? 'is-changed' : undefined}>
                    <th scope="row">{u.name}</th>
                    <td className="is-num num">{fmtScore(u.score_before)}</td>
                    <td className="is-num num">{fmtScore(u.score_after)}</td>
                    <td>
                      {u.category_before === u.category_after
                        ? (u.category_after ?? '—')
                        : `${u.category_before ?? 'not active'} → ${u.category_after ?? 'not active'}`}
                    </td>
                    <td className="is-num num">
                      {u.rank_before === u.rank_after
                        ? (u.rank_after ?? '—')
                        : `${u.rank_before ?? '—'} → ${u.rank_after ?? '—'}`}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="table-scroll">
          <table className="data-table sim-compare__table">
            <caption className="sim-compare__caption">
              {POLICY_NAME[recommended.policy_id]} next to FCFS on the same state
            </caption>
            <thead>
              <tr>
                <th scope="col">Metric</th>
                <th scope="col" className="is-num">
                  {POLICY_NAME[recommended.policy_id]}
                </th>
                {fcfs && fcfs !== recommended && (
                  <th scope="col" className="is-num">
                    FCFS
                  </th>
                )}
              </tr>
            </thead>
            <tbody>
              {totals.map(([label, pick]) => (
                <tr key={label}>
                  <th scope="row">{label}</th>
                  {[recommended, fcfs].filter(Boolean).map((p) => {
                    const [a, b] = pick(p);
                    return (
                      <td key={p.policy_id} className="is-num num">
                        {a === b ? b : `${a} → ${b}`}
                      </td>
                    );
                  })}
                </tr>
              ))}
              <tr>
                <th scope="row">Allocations changed</th>
                {[recommended, fcfs].filter(Boolean).map((p) => (
                  <td key={p.policy_id} className="is-num num">
                    {p.changed_cells}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>

        <div className="table-scroll">
          <table className="data-table sim-compare__table">
            <caption className="sim-compare__caption">Stock and shortfall</caption>
            <thead>
              <tr>
                <th scope="col">Resource</th>
                <th scope="col" className="is-num">
                  Stock
                </th>
                <th scope="col" className="is-num">
                  Requested
                </th>
                <th scope="col" className="is-num">
                  Shortfall
                </th>
              </tr>
            </thead>
            <tbody>
              {diff.resources.map((r) => {
                const pair = (a: number, b: number) =>
                  a === b ? formatInt(b) : `${formatInt(a)} → ${formatInt(b)}`;
                return (
                  <tr key={r.resource_id}>
                    <th scope="row">{r.label}</th>
                    <td className="is-num num">{pair(r.stock_before, r.stock_after)}</td>
                    <td className="is-num num">{pair(r.requested_before, r.requested_after)}</td>
                    <td className={`is-num num${r.shortfall_after ? ' is-short' : ''}`}>
                      {pair(r.shortfall_before, r.shortfall_after)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {[recommended, fcfs].filter(Boolean).map((p) => {
          const changed = changedList(p);
          return (
            <div key={p.policy_id} className="sim-compare__changes">
              <h3 className="sim-compare__caption">
                {POLICY_NAME[p.policy_id]}:{' '}
                {changed.length ? 'allocations that changed' : 'no allocation changed'}
              </h3>
              {changed.length > 0 && (
                <ul>
                  {changed.map((c) => (
                    <li key={`${c.zone_id}|${c.resource_id}`} className="num">
                      {names.get(c.zone_id) ?? c.zone_id} ·{' '}
                      {resources.get(c.resource_id)?.label ?? c.resource_id}:{' '}
                      {formatInt(c.allocated_before)} → <b>{formatInt(c.allocated_after)}</b>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          );
        })}
      </div>
    </Panel>
  );
}

export function SimExplanation({ session }: { session: SimSession }) {
  const diff = session.diff;
  return (
    <Panel
      title="Why the plan changed"
      description="Written by the engine from the two stored steps: changed inputs, scores, limits and plans."
      actions={
        diff ? (
          <StatusBadge tone={diff.recommendation_changed ? 'warn' : 'neutral'}>
            {diff.recommendation_changed ? 'Plan changed' : 'Plan unchanged'}
          </StatusBadge>
        ) : undefined
      }
    >
      {diff ? (
        <ul className="sim-explain" aria-label="Engine explanation">
          {diff.explanation.map((line, i) => (
            <li key={`${session.current.seq}-${i}`}>{line}</li>
          ))}
        </ul>
      ) : (
        <p className="explain__empty">
          Initial snapshot: the engine scored every zone and computed a candidate plan. No event has
          been applied yet.
        </p>
      )}
    </Panel>
  );
}

/* ---------------------------------------------------------------- timeline and ledger */

export function SimTimeline({ session }: { session: SimSession }) {
  const items = [...session.history].reverse();
  return (
    <Panel
      title="Event timeline"
      description="Every step the engine recorded, newest first. Each has its own snapshot and outcome hash."
    >
      <ol className="timeline sim-timeline" aria-label="Event history">
        {items.map((item) => {
          const current = item.seq === session.current.seq;
          const Icon = current ? CircleDot : Circle;
          return (
            <li
              key={`${item.seq}-${item.outcome_hash}`}
              className={`timeline__item${current ? ' is-current' : ''}`}
            >
              <Icon size={18} aria-hidden="true" />
              <div>
                <p className="timeline__title">
                  <span className="sim-timeline__seq num">{item.seq}</span>
                  {item.type ? EVENT_LABEL[item.type] : 'Initial snapshot'}
                </p>
                <p className="sim-timeline__summary">{item.summary}</p>
                <p className="timeline__meta">
                  <span className="num">
                    Allocated {formatInt(item.allocated_units)} · unmet{' '}
                    {formatInt(item.unmet_units)}
                  </span>
                  {item.seq > 0 && (
                    <>
                      {' · '}
                      {item.changed_cells
                        ? `${item.changed_cells} allocation${item.changed_cells === 1 ? '' : 's'} changed`
                        : 'plan unchanged'}
                    </>
                  )}
                  {item.dispatched_units > 0 && ` · ${formatInt(item.dispatched_units)} dispatched`}
                  {' · clock '}
                  {item.sim_step}
                  {' · '}
                  <span className="mono">{shortHash(item.snapshot_hash)}</span>
                </p>
              </div>
            </li>
          );
        })}
      </ol>
    </Panel>
  );
}

export function SimLedger({ session }: { session: SimSession }) {
  const names = zoneNames(session);
  const resources = resourceById(session.current.scenario);
  return (
    <Panel
      title="Dispatch ledger"
      description="Units that left the depot, recorded once. Nothing returns to stock; only resetting the whole session clears the ledger."
    >
      {session.ledger.length === 0 && session.resolved_zones.length === 0 ? (
        <p className="explain__empty">
          Nothing dispatched. Every plan shown is a candidate until you dispatch it.
        </p>
      ) : (
        <ul className="sim-ledger">
          {session.ledger.map((entry) => {
            const byResource = new Map<string, number>();
            for (const c of entry.cells)
              byResource.set(c.resource_id, (byResource.get(c.resource_id) ?? 0) + c.units);
            return (
              <li key={entry.event_id}>
                <PackageCheck size={16} aria-hidden="true" />
                <div>
                  <p>
                    <b className="num">{formatInt(entry.total)}</b> units dispatched at step{' '}
                    {entry.seq} ({POLICY_NAME[entry.policy]} plan)
                  </p>
                  <p className="timeline__meta num">
                    {[...byResource]
                      .map(
                        ([rid, units]) => `${resources.get(rid)?.label ?? rid} ${formatInt(units)}`,
                      )
                      .join(' · ')}{' '}
                    · to{' '}
                    {[...new Set(entry.cells.map((c) => names.get(c.zone_id) ?? c.zone_id))].join(
                      ', ',
                    )}
                  </p>
                </div>
              </li>
            );
          })}
          {session.resolved_zones.map((r) => (
            <li key={r.zone_id}>
              <CircleDot size={16} aria-hidden="true" />
              <div>
                <p>
                  {zoneShortName(r.name)} resolved at clock step {r.resolved_at_step}
                </p>
                <p className="timeline__meta num">
                  {Object.values(r.remaining_demand).reduce((a, b) => a + b, 0)} open requested
                  units left the problem
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}
