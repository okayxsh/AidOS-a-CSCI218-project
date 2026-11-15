import { evalApi } from '../api/client';
import { useRequest } from './useRequest';

/** Completed evaluation runs, newest first (from experiments/results via the engine). */
export const useEvaluationRuns = () => useRequest('evaluation:runs', evalApi.runs);

/** One run's manifest, frozen configuration and statistics. */
export const useEvaluationRun = (id: string | null) =>
  useRequest(id ? `evaluation:run:${id}` : null, () => evalApi.run(id as string), {
    keepPrevious: true,
  });
