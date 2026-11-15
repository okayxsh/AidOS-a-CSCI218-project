import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { clearRequestCache } from '../state/useRequest';
import { DETAILS, engineUrgency, mockApi, mockApiOffline, renderAt } from './helpers';

const summaryValue = (label: string) => {
  const summary = screen.getByLabelText('Scenario summary');
  const term = within(summary).getByText(label);
  return term.parentElement?.querySelector('.metric__value')?.textContent ?? '';
};

describe('dashboard', () => {
  beforeEach(() => clearRequestCache());

  it('deep-links to /dashboard and shows the backend summary for the default scenario', async () => {
    mockApi();
    renderAt('/dashboard');
    // Whichever test runs first pays for lazy-loading the dashboard chunk, so allow it longer.
    expect(
      await screen.findByRole(
        'heading',
        { level: 1, name: 'Three-zone shortage' },
        { timeout: 8000 },
      ),
    ).toBeTruthy();
    const totals = DETAILS['triage-demo-001'].summary.totals;
    expect(summaryValue('Units requested')).toBe(String(totals.requested));
    expect(summaryValue('Units in stock')).toBe(String(totals.stock));
    expect(summaryValue('Shortfall')).toBe(String(totals.shortfall));
    expect(summaryValue('Supply status')).toBe('Shortage');
    // The fixture's own step is labelled as the file's, distinct from any simulation clock.
    expect(screen.getByText('Scenario file · step 0')).toBeTruthy();
  });

  it('updates every panel when another scenario is selected', async () => {
    mockApi();
    renderAt('/dashboard?scenario=triage-demo-001');
    await screen.findByRole('heading', { level: 1, name: 'Three-zone shortage' });
    const select = await screen.findByLabelText('Scenario');
    await waitFor(() => expect((select as HTMLSelectElement).disabled).toBe(false));

    fireEvent.change(select, { target: { value: 'no-scarcity' } });

    expect(await screen.findByRole('heading', { level: 1, name: 'Sufficient stock' })).toBeTruthy();
    const totals = DETAILS['no-scarcity'].summary.totals;
    expect(summaryValue('Units requested')).toBe(String(totals.requested));
    expect(summaryValue('Shortfall')).toBe('None');
    expect(summaryValue('Supply status')).toBe('Covered');
    // The zone table follows the same snapshot.
    const zoneTable = screen
      .getByRole('heading', { name: 'Emergency zones' })
      .closest('section') as HTMLElement;
    expect(within(zoneTable).getByText('Zone A')).toBeTruthy();
    expect(within(zoneTable).getAllByRole('row')).toHaveLength(
      DETAILS['no-scarcity'].scenario.zones.length + 1,
    );
  });

  it('shows a clear error, not placeholder numbers, when the engine is offline', async () => {
    mockApiOffline();
    renderAt('/dashboard');
    expect(await screen.findByText('The AidOS engine is not running')).toBeTruthy();
    expect(screen.queryByLabelText('Scenario summary')).toBeNull();
    const main = screen.getByRole('main');
    expect(within(main).getByRole('button', { name: 'Retry' })).toBeTruthy();
    // The sidebar reports the same outage.
    expect(screen.getByText('Engine offline')).toBeTruthy();
  });

  it('lists every page, including evaluation, as built in the navigation', async () => {
    mockApi();
    renderAt('/dashboard/simulate');
    const nav = await screen.findByRole('navigation', { name: 'Dashboard' });
    expect(within(nav).getByRole('link', { name: /simulation/i }).textContent).not.toMatch(
      /Stage \d/,
    );
    expect(within(nav).getByRole('link', { name: /evaluation/i }).textContent).not.toMatch(
      /Stage \d/,
    );
    expect(within(nav).queryByText('Later stages')).toBeNull();
    expect(await screen.findByText('No simulation session for this scenario')).toBeTruthy();
  });

  it('keeps the active scenario when moving between dashboard pages', async () => {
    mockApi();
    renderAt('/dashboard?scenario=no-scarcity');
    const nav = await screen.findByRole('navigation', { name: 'Dashboard' });
    const inventory = within(nav).getByRole('link', { name: /resource inventory/i });
    expect(inventory.getAttribute('href')).toBe('/dashboard/inventory?scenario=no-scarcity');
  });

  it('reports an unknown scenario instead of rendering an empty dashboard', async () => {
    mockApi();
    renderAt('/dashboard?scenario=missing');
    expect(await screen.findByText('This scenario does not exist')).toBeTruthy();
  });

  it('offers every policy the engine reports as built', async () => {
    mockApi();
    renderAt('/dashboard/allocate');
    const picker = await screen.findByRole('group', { name: 'Allocation policy' });
    const radios = (await within(picker).findAllByRole('radio')) as HTMLInputElement[];
    expect(radios.map((r) => r.disabled)).toEqual([false, false, false, false]);
    expect(radios.map((r) => r.value)).toEqual(['fcfs', 'greedy', 'aidos', 'aidos_balanced']);
    expect(await screen.findByRole('button', { name: 'Run allocation' })).toBeTruthy();
  });

  it('shows the fuzzy urgency score of every zone in the zone table', async () => {
    mockApi();
    renderAt('/dashboard?scenario=triage-demo-001');
    const zoneTable = (await screen.findByRole('heading', { name: 'Emergency zones' })).closest(
      'section',
    ) as HTMLElement;
    for (const zone of engineUrgency('triage-demo-001').zones) {
      expect(await within(zoneTable).findByText(zone.score.toFixed(1))).toBeTruthy();
    }
  });
});
