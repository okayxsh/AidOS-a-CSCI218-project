import type { ReactNode } from 'react';
import { Link } from 'react-router';
import { ApiError } from '../api/client';
import type { ScenarioDetail } from '../api/types';
import { shortHash } from '../lib/format';
import { DEFAULT_SCENARIO_ID } from '../state/scenario';
import type { RequestState } from '../state/useRequest';
import { ErrorState, LoadingState } from './ui/States';
import { StatusBadge } from './ui/StatusBadge';

interface ScenarioGateProps {
  detail: RequestState<ScenarioDetail>;
  children: (detail: ScenarioDetail) => ReactNode;
}

/** Renders loading and error states once, so every page handles them the same way. */
export function ScenarioGate({ detail, children }: ScenarioGateProps) {
  if (detail.status === 'error') {
    const notFound = detail.error instanceof ApiError && detail.error.status === 404;
    return (
      <>
        <ErrorState
          error={detail.error}
          onRetry={notFound ? undefined : detail.retry}
          title={notFound ? 'This scenario does not exist' : undefined}
        />
        {notFound && (
          <p className="state__after">
            <Link to={`/dashboard?scenario=${DEFAULT_SCENARIO_ID}`}>
              Open the default demo scenario
            </Link>
          </p>
        )}
      </>
    );
  }
  if (!detail.data) return <LoadingState label="Loading scenario" />;
  return (
    <div className={`gate${detail.stale ? ' is-stale' : ''}`} aria-busy={detail.stale}>
      {children(detail.data)}
    </div>
  );
}

/** Page heading for scenario-backed pages: what is loaded, and that it is synthetic. */
export function ScenarioHeader({
  detail,
  title,
  showFileStep = true,
}: {
  detail: ScenarioDetail;
  title?: string;
  /** The simulator keeps its own clock, so it hides the file's fixed step to avoid two "steps". */
  showFileStep?: boolean;
}) {
  const s = detail.scenario;
  return (
    <header className="page-head">
      <div>
        <h1 className="page-head__title">{title ?? s.title}</h1>
        {s.description && <p className="page-head__desc">{s.description}</p>}
      </div>
      <ul className="page-head__meta" aria-label="Snapshot details">
        <li>
          <StatusBadge tone="ok" dot>
            Validated by engine
          </StatusBadge>
        </li>
        <li className="mono">{s.scenario_id}</li>
        {showFileStep && (
          <li title="The step recorded in the scenario file. Simulation sessions keep their own clock.">
            Scenario file · step {s.step}
          </li>
        )}
        <li>
          Seed <span className="mono">{s.seed}</span>
        </li>
        <li className="mono" title={detail.snapshot_hash}>
          snapshot {shortHash(detail.snapshot_hash)}
        </li>
      </ul>
    </header>
  );
}
