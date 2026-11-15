import type {
  AidosConfig,
  ApiErrorBody,
  CompareResponse,
  EvaluationRun,
  EvaluationRunItem,
  FuzzyConfig,
  Health,
  ControlAction,
  ImportResult,
  PolicyId,
  Scenario,
  ScenarioDetail,
  ScenarioManifest,
  SimEvent,
  SimExport,
  SimSession,
  UrgencyResponse,
} from './types';

/** Every policy, in the order the dashboard compares them. */
export const ALL_POLICIES: PolicyId[] = ['fcfs', 'greedy', 'aidos', 'aidos_balanced'];

/** The AidOS settings a request may override; seed and workers stay fixed on the engine. */
export type AidosConfigInput = Partial<
  Pick<AidosConfig, 'epsilon' | 'resource_weights' | 'min_coverage' | 'time_limit_s'>
>;

export const API_BASE_URL: string = (
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
).replace(/\/$/, '');

/** A failed API call. `kind` separates "engine not running" from "engine said no". */
export class ApiError extends Error {
  readonly kind: 'network' | 'http';
  readonly status: number | null;
  readonly code: string | null;

  constructor(
    message: string,
    kind: 'network' | 'http',
    status: number | null = null,
    code: string | null = null,
  ) {
    super(message);
    this.name = 'ApiError';
    this.kind = kind;
    this.status = status;
    this.code = code;
  }
}

/** Most calls finish in milliseconds; a hung engine must not leave a spinner forever. */
const DEFAULT_TIMEOUT_MS = 60_000;
/** Replay and import recompute every event (up to 200), so they get longer. */
const LONG_TIMEOUT_MS = 300_000;

async function request<T>(
  path: string,
  init?: RequestInit,
  timeoutMs: number = DEFAULT_TIMEOUT_MS,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      signal: AbortSignal.timeout(timeoutMs),
      headers: {
        Accept: 'application/json',
        ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      },
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'TimeoutError') {
      throw new ApiError(
        `The AidOS engine did not answer within ${Math.round(timeoutMs / 1000)} s.`,
        'network',
      );
    }
    throw new ApiError(`Cannot reach the AidOS engine at ${API_BASE_URL}.`, 'network');
  }

  if (!response.ok) {
    let message = `The engine returned HTTP ${response.status}.`;
    let code: string | null = null;
    try {
      const body = (await response.json()) as ApiErrorBody;
      message = body.error.message;
      code = body.error.code;
    } catch {
      // Keep the generic message when the body is not the standard error shape.
    }
    throw new ApiError(message, 'http', response.status, code);
  }

  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError(
      'The engine sent a response that is not valid JSON.',
      'http',
      response.status,
    );
  }
}

export const api = {
  health: () => request<Health>('/api/health'),
  listScenarios: () => request<ScenarioManifest[]>('/api/scenarios'),
  getScenario: (id: string) => request<ScenarioDetail>(`/api/scenarios/${encodeURIComponent(id)}`),
  compare: (scenario: Scenario, policies: PolicyId[] = ALL_POLICIES, config?: AidosConfigInput) =>
    request<CompareResponse>('/api/allocations/compare', {
      method: 'POST',
      body: JSON.stringify(config ? { scenario, policies, config } : { scenario, policies }),
    }),
  urgency: (scenario: Scenario) =>
    request<UrgencyResponse>('/api/urgency/evaluate', {
      method: 'POST',
      body: JSON.stringify({ scenario }),
    }),
  fuzzyConfig: () => request<FuzzyConfig>('/api/urgency/config'),
};

const session = (id: string) => `/api/simulation/sessions/${encodeURIComponent(id)}`;
const post = (body: unknown): RequestInit => ({ method: 'POST', body: JSON.stringify(body) });

/** Simulation sessions (Stage 3). Every change names the version it expects. */
export const simApi = {
  create: (scenarioId: string, policy: 'aidos' | 'aidos_balanced' = 'aidos') =>
    request<SimSession>('/api/simulation/sessions', post({ scenario_id: scenarioId, policy })),
  get: (id: string) => request<SimSession>(session(id)),
  control: (id: string, action: ControlAction, version: number) =>
    request<SimSession>(`${session(id)}/${action}`, post({ expected_version: version })),
  apply: (id: string, version: number, event: SimEvent) =>
    request<SimSession>(`${session(id)}/events`, post({ expected_version: version, event })),
  replay: (id: string, version: number, events: SimEvent[]) =>
    request<SimSession>(
      `${session(id)}/replay`,
      post({ expected_version: version, events }),
      LONG_TIMEOUT_MS,
    ),
  exportSession: (id: string) => request<SimExport>(`${session(id)}/export`),
  importSession: (document: unknown) =>
    request<ImportResult>('/api/simulation/import', post(document), LONG_TIMEOUT_MS),
};

/** Precomputed evaluation runs (Stage 4). Read-only: experiments run offline. */
export const evalApi = {
  runs: () => request<EvaluationRunItem[]>('/api/evaluation/runs'),
  run: (id: string) => request<EvaluationRun>(`/api/evaluation/runs/${encodeURIComponent(id)}`),
};
