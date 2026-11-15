import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError, api } from '../api/client';
import { RouteErrorBoundary } from '../components/ui/RouteErrorBoundary';
import { formatValue } from '../lib/evaluation';
import { clearRequestCache } from '../state/useRequest';
import { mockApi, renderAt } from './helpers';

function Broken(): never {
  throw new Error('render failed');
}

describe('final hardening', () => {
  beforeEach(() => clearRequestCache());
  afterEach(() => vi.restoreAllMocks());

  it('shows a readable error instead of a blank page when a page fails to render', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
    render(
      <RouteErrorBoundary>
        <Broken />
      </RouteErrorBoundary>,
    );
    expect(screen.getByRole('alert').textContent).toContain('This page could not be displayed');
    expect(screen.getByRole('button', { name: 'Retry' })).toBeTruthy();
  });

  it('turns an engine that never answers into a clear timeout error', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.reject(new DOMException('The operation timed out.', 'TimeoutError'))),
    );
    const failure = await api.health().catch((error: unknown) => error);
    expect(failure).toBeInstanceOf(ApiError);
    expect((failure as ApiError).kind).toBe('network');
    expect((failure as ApiError).message).toMatch(/did not answer within 60 s/);
  });

  it('turns a non-JSON reply into an ApiError rather than a raw SyntaxError', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve(new Response('<html>proxy page</html>', { status: 200 }))),
    );
    const failure = await api.health().catch((error: unknown) => error);
    expect(failure).toBeInstanceOf(ApiError);
    expect((failure as ApiError).message).toMatch(/not valid JSON/);
  });

  it('shows sub-millisecond runtimes instead of rounding them to 0.0 ms', () => {
    expect(formatValue(0.0488, 'ms')).toBe('0.049 ms');
    expect(formatValue(12.42, 'ms')).toBe('12.4 ms');
  });

  it('moves focus to the results after Run allocation', async () => {
    mockApi();
    renderAt('/dashboard/allocate?scenario=triage-demo-001');
    const button = await screen.findByRole('button', { name: 'Run allocation' }, { timeout: 8000 });
    button.focus();
    fireEvent.click(button);
    const summary = await screen.findByLabelText(/result summary/);
    await waitFor(() => expect(document.activeElement).toBe(summary.parentElement));
  });

  it('moves focus into the phone menu and back to the menu button on close', async () => {
    mockApi();
    renderAt('/dashboard?scenario=triage-demo-001');
    const open = await screen.findByRole('button', { name: 'Open menu' }, { timeout: 8000 });
    fireEvent.click(open);
    const close = screen.getByRole('button', { name: 'Close menu' });
    await waitFor(() => expect(document.activeElement).toBe(close));
    fireEvent.click(close);
    await waitFor(() => expect(document.activeElement).toBe(open));
  });
});
