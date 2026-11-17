import { screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError, api, normaliseApiBase } from '../api/client';
import { clearRequestCache } from '../state/useRequest';
import { renderAt } from './helpers';

/** Answer every request with one fixed reply. */
function replyWith(body: string, status: number, contentType = 'text/html') {
  const fetchMock = vi.fn(() =>
    Promise.resolve(new Response(body, { status, headers: { 'Content-Type': contentType } })),
  );
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

async function failureOf(call: Promise<unknown>): Promise<ApiError> {
  const failure = await call.catch((error: unknown) => error);
  expect(failure).toBeInstanceOf(ApiError);
  return failure as ApiError;
}

describe('deployment: engine address and missing-engine replies', () => {
  beforeEach(() => clearRequestCache());
  afterEach(() => vi.unstubAllGlobals());

  it('never doubles the /api prefix, whatever form the configured base takes', () => {
    expect(normaliseApiBase('https://engine.example')).toBe('https://engine.example');
    expect(normaliseApiBase('https://engine.example/')).toBe('https://engine.example');
    expect(normaliseApiBase('https://engine.example/api')).toBe('https://engine.example');
    expect(normaliseApiBase('https://engine.example/api/')).toBe('https://engine.example');
    expect(normaliseApiBase(' http://localhost:8000 ')).toBe('http://localhost:8000');
    expect(normaliseApiBase('')).toBe('');
  });

  it('requests each endpoint once under /api', async () => {
    const fetchMock = replyWith('{"status":"ok"}', 200, 'application/json');
    await api.health();
    const url = String((fetchMock.mock.calls[0] as unknown[])[0]);
    expect(url.endsWith('/api/health')).toBe(true);
    expect(url).not.toContain('/api/api/');
  });

  it.each([404, 502, 503, 504])(
    'treats a non-JSON HTTP %i page from the host as "engine not reachable"',
    async (status) => {
      replyWith('<html>The page could not be found</html>', status);
      const failure = await failureOf(api.health());
      expect(failure.kind).toBe('network');
      expect(failure.status).toBe(status);
      expect(failure.message).toMatch(/No AidOS engine answered/);
    },
  );

  it('treats an HTML page served with 200 as "engine not reachable", not as data', async () => {
    replyWith('<!doctype html><html><body>app shell</body></html>', 200);
    const failure = await failureOf(api.listScenarios());
    expect(failure.kind).toBe('network');
    expect(failure.message).toMatch(/not valid JSON/);
  });

  it("keeps the engine's own JSON errors as engine errors, with their code", async () => {
    replyWith(
      '{"error":{"code":"not_found","message":"Scenario x was not found."}}',
      404,
      'application/json',
    );
    const failure = await failureOf(api.getScenario('x'));
    expect(failure.kind).toBe('http');
    expect(failure.code).toBe('not_found');
    expect(failure.message).toBe('Scenario x was not found.');
  });

  it('reports a non-JSON server error as an error, not as a missing engine', async () => {
    replyWith('Internal Server Error', 500, 'text/plain');
    const failure = await failureOf(api.health());
    expect(failure.kind).toBe('http');
    expect(failure.message).toBe('The engine returned HTTP 500.');
  });

  it('shows "engine not running", not "scenario does not exist", when the host has no backend', async () => {
    replyWith('<html>404: NOT_FOUND</html>', 404);
    renderAt('/dashboard/allocate?scenario=triage-demo-001');
    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toContain('The AidOS engine is not running');
    expect(alert.textContent).not.toContain('This scenario does not exist');
    // The error panel offers Retry, as does the engine-status pill in the header.
    expect(screen.getAllByRole('button', { name: 'Retry' })).toHaveLength(2);
  });
});
