import { ChevronDown } from 'lucide-react';
import { useId } from 'react';
import { useActiveScenarioId, useScenarioList } from '../state/scenario';

/** Switches the active scenario. Every page re-renders from the new backend snapshot. */
export function ScenarioSelector() {
  const id = useId();
  const [active, select] = useActiveScenarioId();
  const list = useScenarioList();
  const options = list.data ?? [];
  const known = options.some((o) => o.scenario_id === active);

  return (
    <div className="scenario-select">
      <label htmlFor={id} className="scenario-select__label">
        Scenario
      </label>
      <div className="scenario-select__control">
        <select
          id={id}
          value={active}
          disabled={list.status !== 'success'}
          onChange={(event) => select(event.target.value)}
        >
          {list.status === 'loading' && <option value={active}>Loading scenarios…</option>}
          {list.status === 'error' && <option value={active}>{active}</option>}
          {list.status === 'success' && !known && (
            <option value={active}>{active} (not found)</option>
          )}
          {options.map((o) => (
            <option key={o.scenario_id} value={o.scenario_id}>
              {o.title} · {o.scenario_id}
            </option>
          ))}
        </select>
        <ChevronDown size={16} aria-hidden="true" />
      </div>
    </div>
  );
}
