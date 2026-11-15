import { CircleCheck, CircleX, Info } from 'lucide-react';
import type { PolicyResult, ScenarioDetail } from '../api/types';
import { CHECK_LABEL, STATUS_MEANING, STATUS_TONE } from '../lib/display';
import { formatInt, formatRatio, resourceById } from '../lib/format';
import { Panel } from './ui/Panel';
import { StatusBadge } from './ui/StatusBadge';

/** Stock, allocated and remaining per resource for one plan. Every number is from the engine. */
export function RemainingInventory({
  detail,
  result,
}: {
  detail: ScenarioDetail;
  result: PolicyResult;
}) {
  const resources = resourceById(detail.scenario);
  const metrics = result.metrics;
  return (
    <Panel
      title="Inventory after this plan"
      description="Nothing is consumed here: a plan only uses stock once it is dispatched in the simulator."
    >
      {!metrics ? (
        <p className="explain__empty">No plan, so no inventory change to show.</p>
      ) : (
        <div className="table-scroll">
          <table className="data-table inventory-table">
            <thead>
              <tr>
                <th scope="col">Resource</th>
                <th scope="col" className="is-num">
                  In stock
                </th>
                <th scope="col" className="is-num">
                  Allocated
                </th>
                <th scope="col" className="is-num">
                  Remaining
                </th>
              </tr>
            </thead>
            <tbody>
              {detail.scenario.resources.map((r) => (
                <tr key={r.id}>
                  <th scope="row">
                    <span className="resource-name">{resources.get(r.id)?.label ?? r.id}</span>
                  </th>
                  <td className="is-num num" data-label="In stock">
                    {formatInt(detail.scenario.stock[r.id])}
                  </td>
                  <td className="is-num num" data-label="Allocated">
                    {formatInt(metrics.allocated_by_resource[r.id] ?? 0)}
                  </td>
                  <td className="is-num num" data-label="Remaining">
                    {formatInt(metrics.remaining_by_resource[r.id] ?? 0)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
}

/** The engine's independent checks of this plan against the scenario. */
export function ValidationChecklist({ result }: { result: PolicyResult }) {
  const v = result.validation;
  return (
    <Panel
      title="Constraint validation"
      description="Checked by a separate validator against the scenario, not taken from the policy's own status."
    >
      {!v.applicable ? (
        <p className="explain__empty">No plan was returned, so there is nothing to validate.</p>
      ) : (
        <>
          <p className="checks__verdict">
            <StatusBadge tone={v.valid ? 'ok' : 'critical'} dot>
              {v.valid ? 'All hard constraints hold' : `${v.violations.length} violation(s)`}
            </StatusBadge>
          </p>
          <ul className="checks" aria-label="Validation checks">
            {v.checks.map((c) => {
              const Icon = c.passed ? CircleCheck : c.hard ? CircleX : Info;
              return (
                <li
                  key={c.name}
                  className={`check${c.passed ? ' is-pass' : c.hard ? ' is-fail' : ' is-note'}`}
                >
                  <Icon size={16} aria-hidden="true" />
                  <span className="check__name">
                    {CHECK_LABEL[c.name] ?? c.name}
                    <span className="check__kind">{c.hard ? 'hard' : 'quality'}</span>
                  </span>
                  <span className="check__state">{c.passed ? 'Pass' : 'Fail'}</span>
                  <span className="check__detail">{c.detail}</span>
                </li>
              );
            })}
          </ul>
        </>
      )}
    </Panel>
  );
}

const PHASE_LABEL: Record<string, string> = {
  coverage_floor: 'Coverage floor',
  urgency: 'Urgency objective',
  tie_break: 'Tie-break (earlier arrival)',
};

/** CP-SAT run details for the AidOS policies, reported exactly as the solver returned them. */
export function SolverDiagnostics({
  detail,
  result,
}: {
  detail: ScenarioDetail;
  result: PolicyResult;
}) {
  const s = result.solver;
  if (!s) return null;
  const resources = resourceById(detail.scenario);
  const floors = Object.entries(s.coverage_floor);
  return (
    <Panel
      title="Solver diagnostics"
      description={`${s.engine}. Phases run in order; each keeps the previous optimum fixed.`}
    >
      <dl className="solver-facts">
        <div>
          <dt>Status</dt>
          <dd>
            <StatusBadge tone={STATUS_TONE[s.status]} title={STATUS_MEANING[s.status]}>
              {s.status}
            </StatusBadge>
          </dd>
        </div>
        <div>
          <dt>Objective</dt>
          <dd className="mono">{s.objective}</dd>
        </div>
        <div>
          <dt>Objective value</dt>
          <dd className="num">
            {s.objective_value === null ? 'N/A' : formatInt(s.objective_value)}
            <span className="solver-facts__unit"> ÷ {s.objective_scale}</span>
          </dd>
        </div>
        <div>
          <dt>Model size</dt>
          <dd className="num">
            {s.variables} variables · {s.constraints} constraints
          </dd>
        </div>
      </dl>
      <p className="solver-note">{STATUS_MEANING[s.status]}</p>
      {s.message && <p className="solver-note">{s.message}</p>}
      <div className="table-scroll">
        <table className="data-table solver-phases">
          <thead>
            <tr>
              <th scope="col">Phase</th>
              <th scope="col">Status</th>
              <th scope="col" className="is-num">
                Value
              </th>
              <th scope="col" className="is-num">
                Bound
              </th>
              <th scope="col" className="is-num">
                Time
              </th>
            </tr>
          </thead>
          <tbody>
            {s.phases.map((p) => (
              <tr key={p.name}>
                <th scope="row">{PHASE_LABEL[p.name] ?? p.name}</th>
                <td className="mono">{p.status}</td>
                <td className="is-num num">
                  {p.objective_value === null ? '—' : formatInt(p.objective_value)}
                </td>
                <td className="is-num num">
                  {p.best_bound === null ? '—' : formatInt(p.best_bound)}
                </td>
                <td className="is-num num">{p.wall_time_ms.toFixed(1)} ms</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {floors.length > 0 && (
        <p className="solver-note">
          Coverage floor reached:{' '}
          {floors
            .map(([rid, f]) => `${resources.get(rid)?.label ?? rid} ${formatRatio(f)}`)
            .join(' · ')}
          . Every requesting zone received at least this share of its request.
        </p>
      )}
    </Panel>
  );
}
