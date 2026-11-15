import { act, fireEvent, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { formatInt, formatRatio } from '../lib/format';
import { clearRequestCache } from '../state/useRequest';
import { engineCompare, engineUrgency, mockApi, renderAt } from './helpers';

const triage = engineCompare('triage-demo-001');
const resultOf = (id: string) => {
  const result = triage.results.find((r) => r.policy_id === id);
  if (!result) throw new Error(`fixture has no ${id} result`);
  return result;
};

/** The value shown in a metric tile of the given summary. */
const tile = (summaryLabel: RegExp, label: string) => {
  const summary = screen.getByLabelText(summaryLabel);
  const term = within(summary).getByText(label);
  return term.parentElement?.querySelector('.metric__value')?.textContent ?? '';
};

const openAllocate = async (scenario = 'triage-demo-001') => {
  renderAt(`/dashboard/allocate?scenario=${scenario}`);
  return screen.findByRole('button', { name: 'Run allocation' }, { timeout: 8000 });
};

describe('allocation workspace', () => {
  beforeEach(() => clearRequestCache());

  it('shows the engine urgency scores before any plan is computed', async () => {
    mockApi();
    await openAllocate();
    const panel = screen.getByRole('heading', { name: 'Fuzzy urgency' }).closest('section');
    const expected = engineUrgency('triage-demo-001').zones;
    for (const zone of expected) {
      expect(await within(panel as HTMLElement).findByText(zone.score.toFixed(1))).toBeTruthy();
    }
    expect(screen.getByText('No plan computed for this snapshot yet')).toBeTruthy();
    expect(screen.queryByLabelText(/result summary/)).toBeNull();
  });

  it('runs every policy on request, shows a loading state, then the engine values', async () => {
    const api = mockApi({ holdCompare: true });
    fireEvent.click(await openAllocate());
    expect(await screen.findByRole('status')).toBeTruthy();
    expect(screen.getByText(/Running four policies on the engine/)).toBeTruthy();

    await act(async () => api.release());
    const aidos = resultOf('aidos');
    await screen.findByLabelText(/AidOS \(fuzzy \+ CP-SAT\) result summary/);
    const label = /AidOS \(fuzzy \+ CP-SAT\) result summary/;
    expect(tile(label, 'Units allocated')).toBe(formatInt(aidos.metrics!.allocated_units));
    expect(tile(label, 'Urgency-weighted coverage')).toBe(
      formatRatio(aidos.metrics!.urgency_weighted_coverage),
    );
    expect(tile(label, 'Stock utilisation')).toBe(formatRatio(aidos.metrics!.stock_utilization));
    expect(tile(label, 'Status')).toBe('OPTIMAL');
    expect(tile(label, 'Constraint checks')).toBe('5/5');

    // One request carried all four policies for this snapshot.
    const compareCalls = api.mock.calls.filter(([url]) =>
      String(url).endsWith('/api/allocations/compare'),
    );
    expect(compareCalls).toHaveLength(1);
    const sent = JSON.parse(String(compareCalls[0][1]?.body));
    expect(sent.policies).toEqual(['fcfs', 'greedy', 'aidos', 'aidos_balanced']);
  });

  it('switches the matrix and summary between policies without re-running', async () => {
    const api = mockApi();
    fireEvent.click(await openAllocate());
    await screen.findByLabelText(/AidOS \(fuzzy \+ CP-SAT\) result summary/);

    fireEvent.click(screen.getByRole('radio', { name: 'First come, first served' }));
    const label = /First come, first served result summary/;
    await screen.findByLabelText(label);
    expect(tile(label, 'Status')).toBe('COMPLETE');

    const fcfs = resultOf('fcfs');
    const cell = fcfs.cells.find((c) => c.zone_id === 'zone-b' && c.resource_id === 'medical_kits');
    expect(
      screen.getByRole('button', {
        name: new RegExp(
          `Zone B, Medical kits: ${cell!.allocated} of ${cell!.requested} allocated`,
        ),
      }),
    ).toBeTruthy();
    expect(screen.getByText(/Served in arrival order/)).toBeTruthy();
    expect(
      api.mock.calls.filter(([url]) => String(url).endsWith('/api/allocations/compare')),
    ).toHaveLength(1);
  });

  it('explains a cell with the engine reason, separating constraints from fuzzy rules', async () => {
    mockApi();
    fireEvent.click(await openAllocate());
    await screen.findByLabelText(/AidOS \(fuzzy \+ CP-SAT\) result summary/);
    const aidos = resultOf('aidos');
    const first = aidos.cells.find((c) => c.unmet > 0)!;
    expect(screen.getByText(first.reason)).toBeTruthy();
    expect(screen.getByRole('heading', { name: 'From the allocation constraints' })).toBeTruthy();
    expect(screen.getByRole('heading', { name: 'From the fuzzy rules' })).toBeTruthy();
  });

  it('shows the independent validation and the baseline comparison as returned', async () => {
    mockApi();
    fireEvent.click(await openAllocate());
    await screen.findByLabelText(/AidOS \(fuzzy \+ CP-SAT\) result summary/);

    expect(screen.getByText('All hard constraints hold')).toBeTruthy();
    const checks = screen.getByRole('list', { name: 'Validation checks' });
    expect(within(checks).getAllByRole('listitem')).toHaveLength(
      resultOf('aidos').validation.checks.length,
    );
    expect(within(checks).getByText('Never above stock, per resource')).toBeTruthy();

    const table = screen.getByRole('heading', { name: 'Baseline comparison' }).closest('section');
    const row = within(table as HTMLElement)
      .getByRole('rowheader', { name: /Urgency-weighted coverage/ })
      .closest('tr') as HTMLElement;
    const cells = within(row)
      .getAllByRole('cell')
      .map((c) => c.textContent);
    expect(cells).toEqual(
      triage.results.map((r) => formatRatio(r.metrics!.urgency_weighted_coverage)),
    );
    // On this fixture AidOS urgency-first equals greedy, and the page says so.
    expect(screen.getByText(/produced exactly the same allocation as urgency greedy/)).toBeTruthy();
  });

  it('reports an engine error instead of a plan', async () => {
    mockApi({ compareFails: true });
    fireEvent.click(await openAllocate());
    expect(await screen.findByText('The solver crashed.')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Retry' })).toBeTruthy();
    expect(screen.queryByLabelText(/result summary/)).toBeNull();
  });

  it(
    'never shows a plan against another scenario after switching',
    { timeout: 15000 },
    async () => {
      mockApi();
      fireEvent.click(await openAllocate());
      await screen.findByLabelText(/AidOS \(fuzzy \+ CP-SAT\) result summary/);

      const select = (await screen.findByLabelText('Scenario')) as HTMLSelectElement;
      await waitFor(() => expect(select.disabled).toBe(false));
      fireEvent.change(select, { target: { value: 'no-scarcity' } });

      // The header re-mounts with the new snapshot, so query it afresh each time.
      await waitFor(
        () =>
          expect(screen.getByRole('list', { name: 'Snapshot details' }).textContent).toContain(
            'no-scarcity',
          ),
        { timeout: 4000 },
      );
      expect(await screen.findByRole('button', { name: 'Run allocation' })).toBeTruthy();
      expect(screen.queryByLabelText(/result summary/)).toBeNull();

      fireEvent.click(screen.getByRole('button', { name: 'Run allocation' }));
      const label = /AidOS \(fuzzy \+ CP-SAT\) result summary/;
      await screen.findByLabelText(label);
      const expected = engineCompare('no-scarcity').results.find((r) => r.policy_id === 'aidos');
      expect(tile(label, 'Units allocated')).toBe(formatInt(expected!.metrics!.allocated_units));
    },
  );
});
