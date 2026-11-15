import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { clearRequestCache } from '../state/useRequest';
import { formatDiff, formatValue } from '../lib/evaluation';
import evalStandard from './fixtures/eval-standard.json';
import { type EvalFixture, mockApi, renderAt } from './helpers';

/** A real standard evaluation run captured from the engine (comparisons trimmed). */
const EVAL = evalStandard as unknown as EvalFixture;

const summary = EVAL.run.summary!;
const st = summary.static;
const spec = (key: string) => summary.metrics.find((m) => m.key === key)!;

afterEach(() => {
  clearRequestCache();
  vi.unstubAllGlobals();
});

async function openEvaluate() {
  mockApi({ evaluation: EVAL });
  renderAt('/dashboard/evaluate');
  // The page is lazy-loaded and the first render parses the whole summary.
  return screen.findByRole('heading', { name: 'Policy comparison' }, { timeout: 8000 });
}

const row = (container: HTMLElement, attr: string, value: string) =>
  container.querySelector(`[${attr}="${value}"]`) as HTMLElement;

describe('evaluation page', () => {
  it('shows the run metadata, including the missing source revision', async () => {
    await openEvaluate();
    const meta = screen
      .getByRole('heading', { name: 'Run and reproducibility' })
      .closest('section')!;
    const m = EVAL.run.manifest;
    expect(within(meta).getByText(m.run_id)).toBeTruthy();
    expect(within(meta).getByText(m.versions!.engine)).toBeTruthy();
    expect(within(meta).getByText(m.versions!.ortools)).toBeTruthy();
    expect(within(meta).getByText(/not a git repository/)).toBeTruthy();
    const [from, to] = EVAL.run.config!.family_seeds.C;
    expect(within(meta).getByText(`${from}–${to}`)).toBeTruthy();
    expect(within(meta).getByText('min_coverage')).toBeTruthy();
  });

  it('renders policy means exactly as the summary reports them', async () => {
    await openEvaluate();
    const table = screen.getByRole('table', { name: 'Policy means for each metric' });
    for (const key of [
      'urgency_weighted_coverage',
      'min_zone_coverage',
      'starved_zones',
      'runtime_ms',
    ]) {
      const r = row(table, 'data-metric', key);
      for (const policy of st.policies) {
        const cell = row(r, 'data-policy', policy);
        expect(cell.textContent).toContain(
          formatValue(st.overall[policy][key].mean, spec(key).unit),
        );
      }
    }
    const f = st.feasibility.aidos;
    expect(within(table).getAllByText(`${f.valid}/${f.total}`).length).toBeGreaterThan(0);
  });

  it('labels objective-aligned and external metrics', async () => {
    await openEvaluate();
    const table = screen.getByRole('table', { name: 'Policy means for each metric' });
    expect(row(table, 'data-metric', 'urgency_weighted_coverage').textContent).toContain(
      'Objective-aligned',
    );
    expect(row(table, 'data-metric', 'critical_coverage').textContent).toContain(
      'Objective-aligned',
    );
    expect(row(table, 'data-metric', 'min_zone_coverage').textContent).toContain('External');
    expect(row(table, 'data-metric', 'jain_fairness').textContent).toContain('External');
  });

  it('reports identical plans from the run', async () => {
    await openEvaluate();
    const list = screen.getByRole('list', { name: 'Identical plans' });
    const n = st.identical_plans['aidos|greedy'];
    expect(list.textContent).toContain(
      `AidOS and Urgency greedy produced the identical allocation in ${n} of ${st.scenarios}`,
    );
  });

  it('switches the paired comparison by pair and by scope', async () => {
    await openEvaluate();
    const panel = screen.getByRole('heading', { name: 'Paired comparisons' }).closest('section')!;
    const table = () => within(panel).getAllByRole('table')[0];
    const pick = (a: string, b: string, scope: string, metric: string) =>
      st.comparisons.find(
        (c) => c.a === a && c.b === b && c.scope === scope && c.metric === metric,
      )!;

    const uwc = pick('aidos', 'fcfs', 'all', 'urgency_weighted_coverage');
    expect(row(table(), 'data-metric', 'urgency_weighted_coverage').textContent).toContain(
      formatDiff(uwc.mean_diff, 'fraction'),
    );
    expect(row(table(), 'data-metric', 'urgency_weighted_coverage').textContent).toContain(
      `${uwc.wins} / ${uwc.ties} / ${uwc.losses}`,
    );

    fireEvent.change(within(panel).getByLabelText('Pair (A vs B)'), { target: { value: '1' } });
    expect(row(table(), 'data-metric', 'urgency_weighted_coverage').textContent).toContain(
      `Identical in all ${st.scenarios} scenarios`,
    );

    fireEvent.change(within(panel).getByLabelText('Pair (A vs B)'), { target: { value: '0' } });
    fireEvent.change(within(panel).getByLabelText('Scenarios'), { target: { value: 'C' } });
    const familyC = pick('aidos', 'fcfs', 'C', 'min_zone_coverage');
    expect(row(table(), 'data-metric', 'min_zone_coverage').textContent).toContain(
      `${familyC.wins} / ${familyC.ties} / ${familyC.losses}`,
    );
    expect(row(table(), 'data-metric', 'min_zone_coverage').textContent).toContain(
      `n ${familyC.n}`,
    );

    const tests = within(panel).getAllByRole('table')[1];
    expect(within(tests).getAllByRole('row')).toHaveLength(st.primary_tests.length + 1);
  });

  it('filters the family comparison', async () => {
    await openEvaluate();
    const table = screen.getByRole('table', { name: /by family and policy/ });
    expect(within(table).getAllByRole('row')).toHaveLength(st.families.length + 1);
    const c = row(table, 'data-family', 'C');
    expect(row(c, 'data-policy', 'aidos_balanced').textContent).toBe(
      formatValue(st.by_family.C.aidos_balanced.min_zone_coverage.mean, 'fraction'),
    );
    fireEvent.click(screen.getByRole('button', { name: /^A · / }));
    await waitFor(() =>
      expect(
        within(screen.getByRole('table', { name: /by family and policy/ })).getAllByRole('row'),
      ).toHaveLength(st.families.length),
    );
    expect(
      row(screen.getByRole('table', { name: /by family and policy/ }), 'data-family', 'A'),
    ).toBeNull();
  });

  it('charts the chosen metric from the summary values', async () => {
    await openEvaluate();
    const chartPanel = screen
      .getByRole('heading', { name: 'Policies on one metric' })
      .closest('section')!;
    fireEvent.change(within(chartPanel).getByLabelText('Metric'), {
      target: { value: 'starved_zones' },
    });
    const data = within(chartPanel).getByRole('table', { name: 'Starved zones by policy' });
    for (const policy of st.policies) {
      const d = st.overall[policy].starved_zones;
      expect(row(data, 'data-policy', policy).textContent).toContain(formatValue(d.mean, 'zones'));
      expect(row(data, 'data-policy', policy).textContent).toContain(formatValue(d.p75, 'zones'));
    }
  });

  it('keeps dispatch integrity and recommendation results apart', async () => {
    await openEvaluate();
    const rec = screen.getByRole('heading', { name: /recommendation mode/ }).closest('section')!;
    const dsp = screen.getByRole('heading', { name: /dispatch mode/ }).closest('section')!;
    expect(within(rec).queryByText('Inventory conserved')).toBeNull();
    const integrity = summary.dynamic_dispatch.integrity!.aidos;
    const r = row(dsp, 'data-policy', 'aidos');
    expect(r.textContent).toContain(`${integrity.inventory_conserved}/${integrity.runs}`);
  });

  it('explains how to produce results when no run exists', async () => {
    mockApi();
    renderAt('/dashboard/evaluate');
    expect(await screen.findByText('No evaluation has been run yet')).toBeTruthy();
    expect(screen.getByText(/run_benchmarks\.py --preset standard/)).toBeTruthy();
    expect(screen.queryByRole('heading', { name: 'Policy comparison' })).toBeNull();
  });

  it('shows the engine error instead of numbers', async () => {
    mockApi({ evaluation: 'error' });
    renderAt('/dashboard/evaluate');
    expect(await screen.findByText('Results unreadable.')).toBeTruthy();
    expect(screen.queryByRole('heading', { name: 'Policy comparison' })).toBeNull();
  });
});
