import { useState } from 'react';
import {
  DynamicResults,
  EvalOverview,
  Methodology,
  PairedComparisons,
  PolicyTable,
  RunMetadata,
} from '../components/eval/EvalPanels';
import { FamilyChart, MetricChart, ScalingChart } from '../components/eval/EvalCharts';
import { EmptyState, ErrorState, LoadingState } from '../components/ui/States';
import { StatusBadge } from '../components/ui/StatusBadge';
import { defaultRun } from '../lib/evaluation';
import { useEvaluationRun, useEvaluationRuns } from '../state/evaluation';

/**
 * Results of the offline evaluation campaigns (experiments/run_benchmarks.py). The page only
 * renders the engine's precomputed summary of a run; it never computes or estimates a number.
 */
export default function Evaluate() {
  const runs = useEvaluationRuns();
  const [picked, setPicked] = useState<string | null>(null);
  const runId = picked ?? (runs.data ? defaultRun(runs.data) : null);
  const run = useEvaluationRun(runId);
  const shown =
    run.data && run.data.manifest.run_id === runId ? run.data : run.stale ? run.data : undefined;

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1 className="page-head__title">Compare and evaluate</h1>
          <p className="page-head__desc">
            FCFS, urgency greedy, AidOS and AidOS balanced on the same synthetic scenarios, the same
            limits and the same event scripts, with paired statistics. Every number on this page was
            produced by an offline evaluation run.
          </p>
        </div>
        {runs.data && runs.data.length > 0 && (
          <label className="field eval-run-select">
            Evaluation run
            <select value={runId ?? ''} onChange={(e) => setPicked(e.target.value)}>
              {runs.data.map((r) => (
                <option key={r.run_id} value={r.run_id}>
                  {r.run_id} · {r.counts.static_scenarios ?? 0} scenarios · {r.status}
                </option>
              ))}
            </select>
          </label>
        )}
      </header>

      {runs.status === 'loading' && <LoadingState label="Loading evaluation runs" />}
      {runs.status === 'error' && <ErrorState error={runs.error} onRetry={runs.retry} />}
      {runs.data && runs.data.length === 0 && (
        <EmptyState title="No evaluation has been run yet">
          <p>
            Results appear here only after an offline run. From{' '}
            <span className="mono">apps/api/</span> run:
          </p>
          <pre className="eval-command">
            uv run python ../../experiments/run_benchmarks.py --preset standard
          </pre>
          <p>Nothing is estimated or filled in until that run exists.</p>
        </EmptyState>
      )}

      {runId && run.status === 'error' && <ErrorState error={run.error} onRetry={run.retry} />}
      {runId && run.status === 'loading' && !shown && <LoadingState label="Loading run results" />}

      {shown && (
        <div className={`eval-body${run.stale ? ' is-stale' : ''}`} aria-busy={run.stale}>
          {shown.manifest.status !== 'complete' && (
            <p className="eval-warning" role="status">
              <StatusBadge tone="warn" dot>
                {shown.manifest.status}
              </StatusBadge>{' '}
              This run did not finish cleanly. Failures are listed under &ldquo;Run and
              reproducibility&rdquo;; the statistics cover only what completed.
            </p>
          )}
          <EvalOverview run={shown} />
          {shown.summary ? (
            <>
              <PolicyTable summary={shown.summary} />
              <div className="eval-charts">
                <MetricChart summary={shown.summary} />
                <FamilyChart summary={shown.summary} />
              </div>
              <PairedComparisons summary={shown.summary} />
              <DynamicResults summary={shown.summary} />
              <ScalingChart summary={shown.summary} />
              <Methodology />
            </>
          ) : (
            <EmptyState title="This run has no summary">
              The run directory has no summary.json, so there is nothing to show.
            </EmptyState>
          )}
          <RunMetadata run={shown} />
        </div>
      )}
    </div>
  );
}
