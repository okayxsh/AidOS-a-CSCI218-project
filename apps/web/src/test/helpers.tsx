import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { vi } from 'vitest';
import noScarcity from '../../../../data/scenarios/no-scarcity.json';
import triage from '../../../../data/scenarios/triage-demo-001.json';
import { AppRoutes } from '../app/Router';
import type {
  CompareResponse,
  Health,
  Scenario,
  ScenarioDetail,
  ScenarioManifest,
  EvaluationRun,
  EvaluationRunItem,
  SimSession,
  UrgencyResponse,
} from '../api/types';
import engineNoScarcity from './fixtures/engine-no-scarcity.json';
import engineTriage from './fixtures/engine-triage-demo-001.json';
import simTriage from './fixtures/sim-triage.json';

/**
 * Test doubles for the HTTP boundary only. The summary here is recomputed from the
 * fixture purely so the mocked API responses are self-consistent.
 */
function detailFor(raw: unknown, hash: string): ScenarioDetail {
  const scenario = { ...(raw as Scenario) };
  // Fill the defaults the backend adds when a fixture omits optional fields.
  scenario.zones = scenario.zones.map((z) => ({
    ...z,
    activation_step: z.activation_step ?? 0,
    population: z.population ?? null,
  }));
  const resources = scenario.resources.map((r) => {
    const requested = scenario.zones.reduce((s, z) => s + (z.demand[r.id] ?? 0), 0);
    const stock = scenario.stock[r.id];
    return {
      resource_id: r.id,
      stock,
      requested,
      shortfall: Math.max(0, requested - stock),
      surplus: Math.max(0, stock - requested),
    };
  });
  return {
    snapshot_hash: hash.padEnd(64, '0'),
    scenario,
    summary: {
      resources,
      zones: scenario.zones.map((z) => ({
        zone_id: z.id,
        active: true,
        requested_units: Object.values(z.demand).reduce((a, b) => a + b, 0),
      })),
      totals: {
        stock: resources.reduce((s, r) => s + r.stock, 0),
        requested: resources.reduce((s, r) => s + r.requested, 0),
        shortfall: resources.reduce((s, r) => s + r.shortfall, 0),
        zones: scenario.zones.length,
        active_zones: scenario.zones.length,
      },
      supply_status: resources.some((r) => r.shortfall > 0) ? 'shortage' : 'covered',
    },
  };
}

export const DETAILS: Record<string, ScenarioDetail> = {
  'triage-demo-001': detailFor(triage, 'aaaa'),
  'no-scarcity': detailFor(noScarcity, 'bbbb'),
};

const MANIFESTS: ScenarioManifest[] = Object.values(DETAILS).map(({ scenario }) => ({
  scenario_id: scenario.scenario_id,
  title: scenario.title,
  description: scenario.description,
  seed: scenario.seed,
  synthetic: true,
  zone_count: scenario.zones.length,
  resource_count: scenario.resources.length,
}));

const HEALTH: Health = {
  status: 'ok',
  version: '0.2.0',
  engine_stage: 2,
  policies: [
    { id: 'fcfs', label: 'First come, first served', available: true, planned_stage: null },
    { id: 'greedy', label: 'Urgency greedy', available: true, planned_stage: null },
    { id: 'aidos', label: 'AidOS (fuzzy + CP-SAT)', available: true, planned_stage: null },
    {
      id: 'aidos_balanced',
      label: 'AidOS balanced (coverage floor)',
      available: true,
      planned_stage: null,
    },
  ],
};

/**
 * Real engine responses captured from the running backend (scripts in the Stage 2 notes),
 * re-stamped with the mocked snapshot hash so they belong to the mocked scenario detail.
 */
const ENGINE = {
  'triage-demo-001': engineTriage,
  'no-scarcity': engineNoScarcity,
} as unknown as Record<string, { compare: CompareResponse; urgency: UrgencyResponse }>;

export function engineCompare(id: string): CompareResponse {
  return { ...ENGINE[id].compare, snapshot_hash: DETAILS[id].snapshot_hash };
}

export function engineUrgency(id: string): UrgencyResponse {
  return { ...ENGINE[id].urgency, snapshot_hash: DETAILS[id].snapshot_hash };
}

/**
 * Real simulation responses captured from the running engine (triage-demo-001: created,
 * started, Zone B severity 6 → 9, reset; plus a no-scarcity session and error bodies).
 */
export const SIM = simTriage as unknown as {
  created: SimSession;
  started: SimSession;
  escalated: SimSession;
  reset: SimSession;
  created_no_scarcity: SimSession;
  error_stock: unknown;
  error_conflict: unknown;
  not_found: unknown;
};

export interface EvalFixture {
  runs: EvaluationRunItem[];
  run: EvaluationRun;
}

export interface MockOptions {
  /** Evaluation results to serve (default: no runs), or an engine error. */
  evaluation?: EvalFixture | 'error';
  /** Make /api/allocations/compare fail with an engine error. */
  compareFails?: boolean;
  /** Hold /api/allocations/compare until `release()` is called. */
  holdCompare?: boolean;
  /** Make the next simulation event fail with the engine's insufficient-stock error. */
  simEventFails?: boolean;
  /** Pretend another client changed the session: events get 409, a reload gets step 1. */
  simConflict?: boolean;
}

const json = (body: unknown, status = 200) =>
  Promise.resolve(
    new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } }),
  );

/** A fetch double that answers like the AidOS API for the two fixtures above. */
export function mockApi(options: MockOptions = {}) {
  let release: () => void = () => {};
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  // One in-memory session per id, answering with the captured engine responses.
  const sessions = new Map<string, SimSession>();
  const simulation = (path: string, init: RequestInit | undefined, opts: MockOptions) => {
    const body = init?.body
      ? (JSON.parse(String(init.body)) as { scenario_id?: string; expected_version?: number })
      : {};
    if (path === '/api/simulation/sessions') {
      const created = body.scenario_id === 'no-scarcity' ? SIM.created_no_scarcity : SIM.created;
      sessions.set(created.session_id, created);
      return json(created, 201);
    }
    if (path === '/api/simulation/import') {
      sessions.set(SIM.escalated.session_id, SIM.escalated);
      return json(
        {
          session: SIM.escalated,
          verification: {
            checked: true,
            matches: true,
            first_mismatch_seq: null,
            engine_version_recorded: '0.3.0',
          },
        },
        201,
      );
    }
    const match = path.match(/^\/api\/simulation\/sessions\/([^/]+)(?:\/(\w+))?$/);
    const current = match ? sessions.get(decodeURIComponent(match[1])) : undefined;
    if (!match || !current) return json(SIM.not_found, 404);
    const action = match[2];
    if (!action) return json(opts.simConflict ? SIM.escalated : current);
    if (action === 'export')
      return json({ events: current.history.slice(1).map((h) => ({ event: h.event })) });
    if ((opts.simConflict && action === 'events') || body.expected_version !== current.version)
      return json(SIM.error_conflict, 409);
    const next: Record<string, SimSession | undefined> = {
      start: SIM.started,
      events: SIM.escalated,
      replay: SIM.escalated,
      reset: SIM.reset,
    };
    if (action === 'events' && opts.simEventFails) return json(SIM.error_stock, 422);
    const result = next[action];
    if (!result)
      return json(
        { error: { code: 'invalid_transition', message: `'${action}' not mocked`, details: [] } },
        409,
      );
    sessions.set(current.session_id, result);
    return json(result);
  };

  const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input));
    const body = init?.body ? (JSON.parse(String(init.body)) as { scenario?: Scenario }) : {};
    const posted = body.scenario?.scenario_id ?? '';
    if (url.pathname === '/api/health') return json(HEALTH);
    if (url.pathname === '/api/urgency/evaluate') return json(engineUrgency(posted));
    if (url.pathname === '/api/allocations/compare') {
      if (options.compareFails)
        return json(
          { error: { code: 'internal', message: 'The solver crashed.', details: [] } },
          500,
        );
      const response = engineCompare(posted);
      return options.holdCompare ? held.then(() => json(response)) : json(response);
    }
    if (url.pathname.startsWith('/api/simulation/')) return simulation(url.pathname, init, options);
    if (url.pathname === '/api/evaluation/runs') {
      if (options.evaluation === 'error')
        return json(
          { error: { code: 'internal', message: 'Results unreadable.', details: [] } },
          500,
        );
      return json(typeof options.evaluation === 'object' ? options.evaluation.runs : []);
    }
    const evalMatch = url.pathname.match(/^\/api\/evaluation\/runs\/([^/]+)$/);
    if (evalMatch) {
      const fixture = typeof options.evaluation === 'object' ? options.evaluation : undefined;
      return fixture && decodeURIComponent(evalMatch[1]) === fixture.run.manifest.run_id
        ? json(fixture.run)
        : json({ error: { code: 'run_not_found', message: 'No run', details: [] } }, 404);
    }
    if (url.pathname === '/api/scenarios') return json(MANIFESTS);
    const match = url.pathname.match(/^\/api\/scenarios\/(.+)$/);
    if (match) {
      const detail = DETAILS[decodeURIComponent(match[1])];
      return detail
        ? json(detail)
        : json({ error: { code: 'scenario_not_found', message: 'No scenario', details: [] } }, 404);
    }
    return json({ error: { code: 'not_found', message: 'Unknown route', details: [] } }, 404);
  });
  vi.stubGlobal('fetch', fetchMock);
  return Object.assign(fetchMock, { release: () => release() });
}

/** Simulates the engine not running at all. */
export function mockApiOffline() {
  vi.stubGlobal(
    'fetch',
    vi.fn(() => Promise.reject(new TypeError('Failed to fetch'))),
  );
}

export function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AppRoutes />
    </MemoryRouter>,
  );
}
