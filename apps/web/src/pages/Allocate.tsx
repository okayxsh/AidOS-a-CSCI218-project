import { ChevronRight, LoaderCircle, Play, RotateCcw } from 'lucide-react';
import { useState } from 'react';
import { AllocationMatrix, type CellKey } from '../components/AllocationMatrix';
import { ExplainabilityPanel } from '../components/ExplainabilityPanel';
import {
  RemainingInventory,
  SolverDiagnostics,
  ValidationChecklist,
} from '../components/PlanDetails';
import { RunComparison } from '../components/RunComparison';
import { ScenarioGate, ScenarioHeader } from '../components/ScenarioGate';
import { UrgencyPanel } from '../components/UrgencyPanel';
import { Metric } from '../components/ui/Metric';
import { Panel } from '../components/ui/Panel';
import { EmptyState, ErrorState } from '../components/ui/States';
import { StatusBadge } from '../components/ui/StatusBadge';
import type { PolicyId, PolicyResult, ScenarioDetail } from '../api/types';
import { ORDER_LABEL, STATUS_MEANING, STATUS_TONE } from '../lib/display';
import { formatInt, formatRatio, zoneShortName } from '../lib/format';
import { useDashboard } from '../state/dashboard';
import { useAllocationRun, useHealth, useUrgency } from '../state/scenario';

const DEFAULT_POLICY: PolicyId = 'aidos';

/** Which result the matrix and explanations show. Lists the engine's policies. */
function PolicyPicker({ value, onChange }: { value: PolicyId; onChange: (id: PolicyId) => void }) {
  const health = useHealth();
  if (health.status === 'error') {
    return <p className="policy-row__hint">Policy list unavailable: the engine did not respond.</p>;
  }
  if (!health.data) return <p className="policy-row__hint">Loading policies…</p>;
  return (
    <fieldset className="policy-tabs">
      <legend className="visually-hidden">Allocation policy</legend>
      {health.data.policies.map((p) => (
        <label key={p.id} className={`policy-tab${p.available ? '' : ' is-disabled'}`}>
          <input
            type="radio"
            name="policy"
            value={p.id}
            checked={value === p.id}
            disabled={!p.available}
            onChange={() => onChange(p.id)}
            className="visually-hidden"
          />
          {p.label}
          {!p.available && p.planned_stage && (
            <span className="policy-tab__stage">Stage {p.planned_stage}</span>
          )}
        </label>
      ))}
    </fieldset>
  );
}

function ZoneOrder({ detail, result }: { detail: ScenarioDetail; result: PolicyResult }) {
  const zones = new Map(detail.scenario.zones.map((z) => [z.id, z]));
  return (
    <span className="serve-order">
      <span className="serve-order__label">{ORDER_LABEL[result.policy_id]}</span>
      {result.zone_order.map((id, i) => (
        <span key={id} className="serve-order__step">
          {i > 0 && <ChevronRight size={14} aria-hidden="true" />}
          <span className="serve-order__zone">{zoneShortName(zones.get(id)?.name ?? id)}</span>
        </span>
      ))}
    </span>
  );
}

function ResultSummary({ detail, result }: { detail: ScenarioDetail; result: PolicyResult }) {
  const m = result.metrics;
  const checks = result.validation.checks.filter((c) => c.hard);
  const passed = checks.filter((c) => c.passed).length;
  return (
    <dl className="metrics metrics--six" aria-label={`${result.label} result summary`}>
      <Metric
        label="Units allocated"
        value={m ? formatInt(m.allocated_units) : '—'}
        detail={`of ${formatInt(detail.summary.totals.requested)} requested`}
      />
      <Metric
        label="Unmet units"
        value={m ? formatInt(m.unmet_units) : '—'}
        tone={m && m.unmet_units > 0 ? 'warn' : 'default'}
      />
      <Metric
        label="Urgency-weighted coverage"
        value={m ? formatRatio(m.urgency_weighted_coverage) : '—'}
        detail="Σ u·x / Σ u·d"
      />
      <Metric
        label="Stock utilisation"
        value={m ? formatRatio(m.stock_utilization) : '—'}
        detail="Σ allocated / Σ stock"
      />
      <Metric
        label="Constraint checks"
        value={result.validation.applicable ? `${passed}/${checks.length}` : 'N/A'}
        tone={
          !result.validation.applicable ? 'default' : result.validation.valid ? 'ok' : 'critical'
        }
        detail="Independent validator"
      />
      <Metric
        label="Status"
        value={result.status}
        tone={
          STATUS_TONE[result.status] === 'critical'
            ? 'critical'
            : STATUS_TONE[result.status] === 'warn'
              ? 'warn'
              : 'default'
        }
        detail={`${result.runtime_ms.toFixed(1)} ms on the engine`}
      />
    </dl>
  );
}

function Workspace({ detail }: { detail: ScenarioDetail }) {
  const run = useAllocationRun(detail);
  const urgency = useUrgency(detail);
  const [policy, setPolicy] = useState<PolicyId>(DEFAULT_POLICY);
  const [picked, setPicked] = useState<CellKey | null>(null);
  const data = run.data;
  const result = data?.results.find((r) => r.policy_id === policy);

  // Scores shown are the ones the policies saw once a run exists; before that, the same
  // engine's scores for this snapshot.
  const scores = data?.urgency ?? urgency.data?.zones;
  const zoneScore = (id: string) => scores?.find((u) => u.zone_id === id);

  // Until the user picks a cell, explain the first one that left demand unmet.
  const fallback = result?.cells.find((c) => c.unmet > 0) ?? result?.cells[0];
  const selected: CellKey | null =
    picked ?? (fallback ? { zoneId: fallback.zone_id, resourceId: fallback.resource_id } : null);
  const selectedCell = result?.cells.find(
    (c) => c.zone_id === selected?.zoneId && c.resource_id === selected?.resourceId,
  );

  return (
    <div className="page">
      <ScenarioHeader detail={detail} title="Allocation results" />

      <div className="workspace-bar">
        <PolicyPicker value={policy} onChange={setPolicy} />
        <StatusBadge
          tone="partial"
          title="Plans are computed on a copy of the snapshot. Stock is dispatched only from the Simulation page."
        >
          Candidate plan · not committed
        </StatusBadge>
      </div>

      {run.status === 'idle' && (
        <EmptyState
          title="No plan computed for this snapshot yet"
          action={
            <button type="button" className="btn btn--accent" onClick={run.run}>
              <Play size={15} aria-hidden="true" />
              Run allocation
            </button>
          }
        >
          Runs first come first served, urgency greedy, AidOS and AidOS balanced on this snapshot in
          one request, with the same fuzzy scores and the same hard limits.
        </EmptyState>
      )}
      {run.status === 'loading' && (
        <p className="policy-row__running" role="status">
          <LoaderCircle size={16} className="spin" aria-hidden="true" /> Running four policies on
          the engine…
        </p>
      )}
      {run.status === 'error' && <ErrorState error={run.error} onRetry={run.retry} />}

      {data && result && (
        <>
          <ResultSummary detail={detail} result={result} />

          {!result.has_plan ? (
            <Panel title="No plan" description={STATUS_MEANING[result.status]}>
              <p className="explain__reason">{result.message}</p>
            </Panel>
          ) : (
            <div className="grid-allocate">
              <Panel
                title="Allocation matrix"
                description={<ZoneOrder detail={detail} result={result} />}
                actions={
                  <button type="button" className="btn btn--quiet" onClick={run.retry}>
                    <RotateCcw size={15} aria-hidden="true" />
                    Re-run
                  </button>
                }
              >
                <AllocationMatrix
                  detail={detail}
                  result={result}
                  selected={selected}
                  onSelect={setPicked}
                />
              </Panel>
              <ExplainabilityPanel
                detail={detail}
                cell={selectedCell}
                result={result}
                urgency={selectedCell ? zoneScore(selectedCell.zone_id) : undefined}
              />
            </div>
          )}
        </>
      )}

      <UrgencyPanel
        detail={detail}
        zones={scores}
        status={data ? 'success' : urgency.status}
        method={data ? `${data.fuzzy.method} · rules v${data.fuzzy.config_version}` : undefined}
      />

      {data && result && (
        <>
          <div className="grid-2 grid-2--even">
            <ValidationChecklist result={result} />
            <RemainingInventory detail={detail} result={result} />
          </div>
          <SolverDiagnostics detail={detail} result={result} />
          <RunComparison detail={detail} data={data} />
        </>
      )}
    </div>
  );
}

export default function Allocate() {
  const { detail } = useDashboard();
  return (
    <ScenarioGate detail={detail}>
      {(d) => <Workspace key={d.snapshot_hash} detail={d} />}
    </ScenarioGate>
  );
}
