import { ArrowRight, LoaderCircle, Play } from 'lucide-react';
import { Link } from 'react-router';
import type { ScenarioDetail } from '../api/types';
import { POLICY_DESCRIPTION, STATUS_TONE } from '../lib/display';
import { formatInt, formatRatio } from '../lib/format';
import { useAllocationRun, useHealth, useScenarioQuery } from '../state/scenario';
import { Panel } from './ui/Panel';
import { ErrorState } from './ui/States';
import { StatusBadge } from './ui/StatusBadge';

/** Overview entry point for allocation: every engine policy, run together on demand. */
export function AllocationPreview({ detail }: { detail: ScenarioDetail }) {
  const health = useHealth();
  const run = useAllocationRun(detail);
  const query = useScenarioQuery();
  const results = new Map(run.data?.results.map((r) => [r.policy_id, r]));

  return (
    <Panel
      title="Allocation"
      description="Policies run on a copy of this snapshot. Nothing is consumed unless a plan is dispatched in the simulator."
      actions={
        <>
          {run.status === 'idle' && (
            <button type="button" className="btn btn--accent" onClick={run.run}>
              <Play size={15} aria-hidden="true" />
              Run allocation
            </button>
          )}
          <Link className="btn btn--quiet" to={`/dashboard/allocate${query}`}>
            Open workspace
            <ArrowRight size={15} aria-hidden="true" />
          </Link>
        </>
      }
    >
      {health.status === 'error' && <ErrorState error={health.error} onRetry={health.retry} />}
      {health.status === 'loading' && (
        <p className="policy-list__loading">Checking which policies the engine offers…</p>
      )}
      {run.status === 'loading' && (
        <p className="policy-row__running" role="status">
          <LoaderCircle size={16} className="spin" aria-hidden="true" /> Running four policies on
          the engine…
        </p>
      )}
      {run.status === 'error' && <ErrorState error={run.error} onRetry={run.retry} />}
      {health.data && (
        <ul className="policy-list">
          {health.data.policies.map((policy) => {
            const result = results.get(policy.id);
            const m = result?.metrics;
            return (
              <li key={policy.id} className="policy-row">
                <div className="policy-row__name">
                  <h3>{policy.label}</h3>
                  <p>{POLICY_DESCRIPTION[policy.id]}</p>
                </div>
                <div className="policy-row__state">
                  {!result && run.status === 'idle' && (
                    <p className="policy-row__hint">Not run on this snapshot yet.</p>
                  )}
                  {result && (
                    <dl className="policy-row__result">
                      <div>
                        <dt>Allocated</dt>
                        <dd className="num">
                          {m ? formatInt(m.allocated_units) : '—'}
                          <span> / {formatInt(detail.summary.totals.requested)}</span>
                        </dd>
                      </div>
                      <div>
                        <dt>Urgency-weighted</dt>
                        <dd className="num">
                          {m ? formatRatio(m.urgency_weighted_coverage) : '—'}
                        </dd>
                      </div>
                      <div>
                        <dt>Lowest zone</dt>
                        <dd className="num">{m ? formatRatio(m.min_zone_coverage) : '—'}</dd>
                      </div>
                      <div>
                        <dt>Status</dt>
                        <dd>
                          <StatusBadge tone={STATUS_TONE[result.status]}>
                            {result.status}
                          </StatusBadge>
                        </dd>
                      </div>
                    </dl>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </Panel>
  );
}
