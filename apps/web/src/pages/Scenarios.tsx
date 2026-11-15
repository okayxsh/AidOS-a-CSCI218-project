import { ArrowRight, Check } from 'lucide-react';
import { Link } from 'react-router';
import { Panel } from '../components/ui/Panel';
import { ErrorState, LoadingState } from '../components/ui/States';
import { StatusBadge } from '../components/ui/StatusBadge';
import { useActiveScenarioId, useScenarioList } from '../state/scenario';

/** Built-in synthetic scenarios served by the engine. Choosing one updates every page. */
export default function Scenarios() {
  const list = useScenarioList();
  const [active, select] = useActiveScenarioId();

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1 className="page-head__title">Emergency scenarios</h1>
          <p className="page-head__desc">
            Built-in synthetic scenarios, each validated by the engine when it is loaded. Every one
            uses the same schema, so every policy sees exactly the same inputs.
          </p>
        </div>
      </header>

      {list.status === 'loading' && <LoadingState label="Loading scenarios" />}
      {list.status === 'error' && <ErrorState error={list.error} onRetry={list.retry} />}
      {list.data && (
        <Panel
          title={`${list.data.length} scenarios`}
          description="Select a scenario to make it the active snapshot for the whole dashboard."
        >
          <ul className="scenario-list">
            {list.data.map((s) => {
              const isActive = s.scenario_id === active;
              return (
                <li key={s.scenario_id} className={`scenario-item${isActive ? ' is-active' : ''}`}>
                  <div className="scenario-item__main">
                    <h3>
                      {s.title}
                      {isActive && (
                        <StatusBadge tone="built">
                          <Check size={12} aria-hidden="true" /> Active
                        </StatusBadge>
                      )}
                    </h3>
                    <p>{s.description}</p>
                    <ul className="scenario-item__facts">
                      <li className="mono">{s.scenario_id}</li>
                      <li>
                        {s.zone_count} zones · {s.resource_count} resources
                      </li>
                      <li>
                        Seed <span className="mono">{s.seed}</span>
                      </li>
                      {s.synthetic && <li>Synthetic</li>}
                    </ul>
                  </div>
                  <div className="scenario-item__actions">
                    {isActive ? (
                      <Link
                        to={`/dashboard?scenario=${encodeURIComponent(s.scenario_id)}`}
                        className="btn btn--quiet"
                      >
                        View overview
                        <ArrowRight size={15} aria-hidden="true" />
                      </Link>
                    ) : (
                      <button
                        type="button"
                        className="btn btn--quiet"
                        onClick={() => select(s.scenario_id)}
                        aria-label={`Make ${s.title} the active scenario`}
                      >
                        Use this scenario
                      </button>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        </Panel>
      )}
    </div>
  );
}
