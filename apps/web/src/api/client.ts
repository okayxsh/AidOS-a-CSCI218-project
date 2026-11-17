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

/**
 * Trim a configured engine address so request paths, which all start with `/api/`, never
 * become `/api/api/...`: `https://host/api/` and `https://host` both give `https://host`.
 */
export function normaliseApiBase(base: string): string {
  return base
    .trim()
    .replace(/\/+$/, '')
    .replace(/\/api$/, '');
}

// The dev server talks to a local engine. A production build has no default host: it calls
// `/api/...` on its own origin, which the hosting platform forwards to the engine. The
// literal sits behind import.meta.env.DEV so it is removed from production bundles.
const DEV_ENGINE = import.meta.env.DEV ? 'http://localhost:8000' : '';

/** Engine base URL: VITE_API_BASE_URL when set, otherwise the default above ('' = same origin). */
export const API_BASE_URL: string = normaliseApiBase(
  import.meta.env.VITE_API_BASE_URL?.trim() || DEV_ENGINE,
);

/** Where the engine is expected, for messages. */
const ENGINE_LOCATION = API_BASE_URL || "this site's /api";

/** Replies that mean "no engine answered here" when they do not carry the engine's JSON. */
const UNAVAILABLE_STATUSES = new Set([404, 502, 503, 504]);

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
    throw new ApiError(`Cannot reach the AidOS engine at ${ENGINE_LOCATION}.`, 'network');
  }

  if (!response.ok) {
    let body: unknown;
    try {
      body = await response.json();
    } catch {
      // Not JSON: a hosting platform's own error page (no backend, backend asleep or down)
      // rather than the engine, which always answers errors in its JSON envelope.
      if (UNAVAILABLE_STATUSES.has(response.status)) {
        throw new ApiError(
          `No AidOS engine answered at ${ENGINE_LOCATION} (HTTP ${response.status}).`,
          'network',
          response.status,
        );
      }
    }
    const envelope = (body as Partial<ApiErrorBody> | undefined)?.error;
    throw new ApiError(
      envelope?.message ?? `The engine returned HTTP ${response.status}.`,
      'http',
      response.status,
      envelope?.code ?? null,
    );
  }

  try {
    return (await response.json()) as T;
  } catch {
    // A successful reply that is not JSON (an HTML page, for example) did not come from the
    // engine, so treat it as "engine not reachable" rather than as an engine error.
    throw new ApiError(
      `The server at ${ENGINE_LOCATION} sent a response that is not valid JSON, so no AidOS engine answered.`,
      'network',
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
