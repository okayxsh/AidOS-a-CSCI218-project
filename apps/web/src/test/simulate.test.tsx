import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { clearRequestCache } from '../state/useRequest';
import { mockApi, renderAt, SIM } from './helpers';

const controls = () => screen.getByRole('group', { name: 'Session controls' });
const control = (name: string) =>
  within(controls()).getByRole('button', { name }) as HTMLButtonElement;
const applyButton = () => screen.getByRole('button', { name: 'Apply event' }) as HTMLButtonElement;

/** The value shown in a metric tile of the simulation summary. */
const tile = (label: string) => {
  const summary = screen.getByLabelText('Simulation state');
  const term = within(summary).getByText(label);
  return term.parentElement?.querySelector('.metric__value')?.textContent ?? '';
};

const openSimulator = async (path = '/dashboard/simulate?scenario=triage-demo-001') => {
  renderAt(path);
  fireEvent.click(
    await screen.findByRole('button', { name: 'Load into simulator' }, { timeout: 8000 }),
  );
  await screen.findByRole('group', { name: 'Session controls' });
};

const openAndStart = async () => {
  await openSimulator();
  fireEvent.click(control('Start'));
  await waitFor(() => expect(control('Pause').disabled).toBe(false));
};

const escalateZoneB = async () => {
  fireEvent.change(screen.getByLabelText('Zone'), { target: { value: 'zone-b' } });
  fireEvent.change(await screen.findByLabelText(/Severity \(now 6\)/), {
    target: { value: '9' },
  });
  fireEvent.click(applyButton());
};

describe('crisis simulator', () => {
  beforeEach(() => clearRequestCache());

  it('creates a session and enables only the controls the engine allows', async () => {
    mockApi();
    await openSimulator();
    // READY allows start and reset (the engine's allowed_actions).
    expect(SIM.created.allowed_actions).toEqual(['start', 'reset']);
    expect(control('Start').disabled).toBe(false);
    expect(control('Reset').disabled).toBe(false);
    for (const name of ['Pause', 'Resume', 'Complete', 'Replay'])
      expect(control(name).disabled).toBe(true);
    expect(tile('Session state')).toBe('READY');
    expect(screen.getByText('Start the session to apply events.')).toBeTruthy();
    expect(applyButton().disabled).toBe(true);

    fireEvent.click(control('Start'));
    await waitFor(() => expect(tile('Session state')).toBe('ACTIVE'));
    expect(control('Start').disabled).toBe(true);
    expect(control('Pause').disabled).toBe(false);
    expect(control('Complete').disabled).toBe(false);
    expect(control('Resume').disabled).toBe(true);
  });

  it('shows the session clock and event count, not the scenario file step', async () => {
    mockApi();
    await openSimulator();
    // The file's fixed step would be a second, different "step" on this page.
    expect(screen.queryByText(/Scenario file · step/)).toBeNull();
    expect(screen.getByText(/0 events · clock step 0 · version 1/)).toBeTruthy();
  });

  it('applies an event and shows the engine result everywhere', async () => {
    mockApi();
    await openAndStart();
    await escalateZoneB();

    // Explanation: the engine's sentences, verbatim.
    const explanation = SIM.escalated.diff?.explanation ?? [];
    expect(explanation.length).toBeGreaterThan(0);
    const explained = await screen.findByRole('list', { name: 'Engine explanation' });
    for (const line of explanation) expect(within(explained).getByText(line)).toBeTruthy();
    expect(screen.getByText('Plan changed')).toBeTruthy();
    expect(tile('Events applied')).toBe('1');

    // Timeline: the new step with the engine's summary.
    const timeline = screen.getByRole('list', { name: 'Event history' });
    expect(within(timeline).getAllByRole('listitem')).toHaveLength(2);
    expect(within(timeline).getByText(SIM.escalated.history[1].summary)).toBeTruthy();

    // Allocation bars: changed cells say what they were before.
    const bars = screen.getByRole('list', { name: 'Allocation by zone' });
    const changed = SIM.escalated.diff?.policies[0].cells.filter(
      (c) => c.allocated_before !== c.allocated_after,
    );
    expect(within(bars).getAllByText(/^was \d+$/)).toHaveLength(changed?.length ?? -1);

    // Before/after: Zone B's urgency after the event, as the engine scored it.
    const zoneB = SIM.escalated.diff?.urgency.find((u) => u.zone_id === 'zone-b');
    expect(zoneB?.score_after).not.toBe(zoneB?.score_before);
    expect(screen.getByText((zoneB?.score_after ?? 0).toFixed(1))).toBeTruthy();
  });

  it('shows the engine refusal inline and keeps the previous state', async () => {
    mockApi({ simEventFails: true });
    await openAndStart();
    fireEvent.change(screen.getByLabelText('Event'), { target: { value: 'supply_lost' } });
    fireEvent.change(await screen.findByLabelText(/Units lost/), { target: { value: '50' } });
    fireEvent.click(applyButton());
    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toContain('The engine refused this event');
    expect(alert.textContent).toContain('Stock never goes negative.');
    expect(tile('Events applied')).toBe('0');
  });

  it('blocks clearly invalid input before it reaches the engine', async () => {
    mockApi();
    await openAndStart();
    fireEvent.change(screen.getByLabelText('Event'), { target: { value: 'supply_lost' } });
    fireEvent.change(await screen.findByLabelText(/Units lost/), { target: { value: '500' } });
    expect(screen.getByText('Only 90 in stock: stock never goes negative.')).toBeTruthy();
    expect(applyButton().disabled).toBe(true);
  });

  it('reset returns to the initial snapshot and clears the history', async () => {
    mockApi();
    await openAndStart();
    await escalateZoneB();
    await screen.findByText('Plan changed');
    fireEvent.click(control('Reset'));
    await waitFor(() => expect(tile('Session state')).toBe('READY'));
    const timeline = screen.getByRole('list', { name: 'Event history' });
    expect(within(timeline).getAllByRole('listitem')).toHaveLength(1);
    expect(screen.queryByText('Plan changed')).toBeNull();
    expect(screen.getByText(/No event has been applied yet/)).toBeTruthy();
  });

  it('never shows a session from another scenario after switching', async () => {
    mockApi();
    await openAndStart();
    expect(screen.getByText(SIM.started.session_id)).toBeTruthy();
    const select = screen.getByLabelText('Scenario') as HTMLSelectElement;
    await waitFor(() => expect(select.disabled).toBe(false));
    fireEvent.change(select, { target: { value: 'no-scarcity' } });
    expect(
      await screen.findByText('No simulation session for this scenario', {}, { timeout: 8000 }),
    ).toBeTruthy();
    expect(screen.queryByText(SIM.started.session_id)).toBeNull();
    expect(screen.queryByRole('group', { name: 'Session controls' })).toBeNull();
  });

  it('explains a version conflict and shows the latest state', async () => {
    mockApi({ simConflict: true });
    await openAndStart();
    await escalateZoneB();
    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toContain('The session changed since you loaded it');
    expect(alert.textContent).toContain(`version ${SIM.escalated.version}`);
    await waitFor(() => expect(tile('Events applied')).toBe('1'));
  });

  it('offers a new session when the stored one has expired', async () => {
    mockApi();
    renderAt('/dashboard/simulate?scenario=triage-demo-001&session=sim-gone');
    expect(
      await screen.findByText('That simulation session no longer exists', {}, { timeout: 8000 }),
    ).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Start a new session' }));
    expect(await screen.findByRole('group', { name: 'Session controls' })).toBeTruthy();
  });

  it('loads the demo script and reports the engine verification', async () => {
    mockApi();
    renderAt('/dashboard/simulate?scenario=triage-demo-001');
    fireEvent.click(
      await screen.findByRole('button', { name: 'Load demo script' }, { timeout: 8000 }),
    );
    const status = await screen.findByText(/recorded outcome hashes match this engine/);
    expect(status.textContent).toContain(`All ${SIM.escalated.history.length}`);
  });
});
