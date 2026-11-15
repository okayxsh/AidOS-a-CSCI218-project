import { fireEvent, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { clearRequestCache } from '../state/useRequest';
import { mockApi, mockApiOffline, renderAt } from './helpers';

describe('landing page', () => {
  beforeEach(() => clearRequestCache());

  it('explains AidOS on the default route, without the backend', () => {
    mockApiOffline();
    renderAt('/');
    expect(screen.getByRole('heading', { level: 1 }).textContent).toContain(
      'When every resource matters',
    );
    expect(screen.getAllByText(/synthetic/i).length).toBeGreaterThan(0);
    expect(screen.getByRole('heading', { name: /A CSCI218 student project/i })).toBeTruthy();
  });

  it('points every Launch Dashboard button at /dashboard, in the header and the hero', () => {
    renderAt('/');
    const header = document.querySelector('header.site-header') as HTMLElement;
    const main = screen.getByRole('main');
    const inHeader = within(header).getAllByRole('link', { name: /launch dashboard/i });
    const inMain = within(main).getAllByRole('link', { name: /launch dashboard/i });
    expect(inHeader.length).toBeGreaterThanOrEqual(1);
    expect(inMain.length).toBeGreaterThanOrEqual(1);
    for (const link of [...inHeader, ...inMain])
      expect(link.getAttribute('href')).toBe('/dashboard');
  });

  it('links the section navigation to real sections', () => {
    renderAt('/');
    const nav = screen.getByRole('navigation', { name: 'Primary' });
    for (const link of within(nav).getAllByRole('link')) {
      const target = link.getAttribute('href') ?? '';
      expect(target.startsWith('#')).toBe(true);
      expect(document.getElementById(target.slice(1))).not.toBeNull();
    }
  });

  it('labels each workflow step with a truthful build status', () => {
    renderAt('/');
    const steps = within(document.getElementById('how-it-works') as HTMLElement).getAllByRole(
      'listitem',
    );
    expect(steps).toHaveLength(5);
    expect(steps[0].textContent).toContain('Built');
    expect(steps[1].textContent).toContain('Built'); // fuzzy urgency (Stage 2)
    expect(steps[2].textContent).toContain('Built'); // CP-SAT allocation (Stage 2)
    expect(steps[4].textContent).toContain('Built'); // crisis simulation (Stage 3)
    expect(steps[4].textContent).toContain('Stage 3');
    expect(steps[4].textContent).not.toContain('Planned');
  });

  it('opens the dashboard when Launch Dashboard is activated', async () => {
    mockApi();
    renderAt('/');
    fireEvent.click(
      within(screen.getByRole('main')).getAllByRole('link', { name: /launch dashboard/i })[0],
    );
    expect(
      await screen.findByRole('navigation', { name: 'Dashboard' }, { timeout: 8000 }),
    ).toBeTruthy();
    expect(await screen.findByRole('link', { name: /about aidos/i })).toBeTruthy();
  });

  it('switches feature panels from the keyboard', () => {
    renderAt('/');
    const tabs = screen.getAllByRole('tab');
    expect(tabs[0].getAttribute('aria-selected')).toBe('true');
    fireEvent.keyDown(tabs[0], { key: 'ArrowDown' });
    expect(screen.getAllByRole('tab')[1].getAttribute('aria-selected')).toBe('true');
    expect(screen.getByRole('tabpanel').textContent).toContain('Constraint-aware allocation');
  });
});
