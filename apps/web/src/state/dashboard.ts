import { useOutletContext } from 'react-router';
import type { ScenarioDetail } from '../api/types';
import type { RequestState } from './useRequest';

/** What the dashboard layout hands to every page through the router outlet. */
export interface DashboardContext {
  scenarioId: string;
  detail: RequestState<ScenarioDetail>;
}

export const useDashboard = () => useOutletContext<DashboardContext>();
