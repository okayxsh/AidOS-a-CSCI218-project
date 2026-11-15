import { useState } from 'react';
import { useSearchParams } from 'react-router';
import { ALL_POLICIES, api } from '../api/client';
import type { ScenarioDetail } from '../api/types';
import { hasCachedRequest, useRequest } from './useRequest';

/** The scenario the dashboard opens with: the spec's default demo fixture. */
export const DEFAULT_SCENARIO_ID = 'triage-demo-001';

export const useHealth = () => useRequest('health', api.health);

export const useScenarioList = () => useRequest('scenarios', api.listScenarios);

/** Switching scenarios keeps the previous snapshot on screen (dimmed) until the next arrives. */
export const useScenarioDetail = (id: string | null) =>
  useRequest(id ? `scenario:${id}` : null, () => api.getScenario(id as string), {
    keepPrevious: true,
  });

/**
 * The active scenario lives in the URL (?scenario=...), so it survives refresh,
 * deep links and back/forward, and every dashboard page reads the same value.
 */
export function useActiveScenarioId(): [string, (id: string) => void] {
  const [params, setParams] = useSearchParams();
  const id = params.get('scenario') || DEFAULT_SCENARIO_ID;
  const select = (next: string) => {
    const copy = new URLSearchParams(params);
    copy.set('scenario', next);
    setParams(copy);
  };
  return [id, select];
}

/** Query string that keeps the active scenario when moving between dashboard pages. */
export function useScenarioQuery(): string {
  const [params] = useSearchParams();
  const id = params.get('scenario');
  return id ? `?scenario=${encodeURIComponent(id)}` : '';
}

/** Fuzzy urgency for the snapshot's zones. Scoring is not an allocation, so it loads unasked. */
export function useUrgency(detail: ScenarioDetail | undefined) {
  const hash = detail?.snapshot_hash;
  const request = useRequest(hash ? `urgency:${hash}` : null, () =>
    api.urgency((detail as ScenarioDetail).scenario),
  );
  // Never show scores computed for another snapshot.
  const data = request.data?.snapshot_hash === hash ? request.data : undefined;
  return { ...request, data };
}

/**
 * Runs every policy on the backend in one request, only when the user asks. The cache key
 * is the snapshot hash, so a plan is never shown against a different scenario; a plan
 * already cached for this snapshot (from another page) is shown without asking again.
 */
export function useAllocationRun(detail: ScenarioDetail | undefined) {
  const [askedKey, setAskedKey] = useState<string | null>(null);
  const hash = detail?.snapshot_hash;
  const key = hash ? `compare:all:${hash}` : null;
  const requested = key !== null && (askedKey === key || hasCachedRequest(key));
  const request = useRequest(requested ? key : null, () =>
    api.compare((detail as ScenarioDetail).scenario, ALL_POLICIES),
  );
  // Defensive: a response for another snapshot is never returned.
  const data = request.data?.snapshot_hash === hash ? request.data : undefined;
  return {
    ...request,
    data,
    run: () => setAskedKey(key),
    // Re-running must keep the request "asked for", even when the plan on screen came from
    // the cache of another page; otherwise the page would fall back to its empty state.
    retry: () => {
      setAskedKey(key);
      request.retry();
    },
  };
}
