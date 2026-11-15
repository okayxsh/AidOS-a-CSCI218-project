import { screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { demoTotals } from '../content/demoScenario';
import { CHAPTERS } from '../content/story';
import { clearRequestCache } from '../state/useRequest';
import { mockApiOffline, renderAt } from './helpers';

const storySection = () =>
  screen.getByRole('heading', { name: /How a shortage becomes/ }).closest('section') as HTMLElement;

describe('landing story', () => {
  beforeEach(() => clearRequestCache());

  it('tells every chapter in document order, as real text', () => {
    mockApiOffline();
    renderAt('/');
    const titles = within(storySection())
      .getAllByRole('heading', { level: 3 })
      .map((h) => h.textContent);
    expect(titles).toEqual(CHAPTERS.map((c) => c.title));
  });

  it('labels each technique with its true build status', () => {
    renderAt('/');
    const steps = within(storySection())
      .getAllByRole('listitem')
      .filter((li) => li.classList.contains('story__step'));
    const byId = Object.fromEntries(CHAPTERS.map((c, i) => [c.id, steps[i].textContent ?? '']));
    expect(byId.fuzzy).toMatch(/Built/);
    expect(byId.fuzzy).toMatch(/Sugeno/);
    expect(byId.fuzzy).not.toMatch(/Mamdani/);
    expect(byId.constraints).toMatch(/Built/);
    expect(byId.constraints).toMatch(/CP-SAT/);
    expect(byId.oversight).toMatch(/Built/);
    expect(byId.oversight).toMatch(/dispatches a plan in the simulator/);
    expect(byId.adapt).toMatch(/Built/);
    expect(byId.adapt).toMatch(/simulator/);
    // The adapt chapter's zone and losses stay labelled as an example.
    expect(byId.adapt).toMatch(/illustrated example/);
    expect(byId.adapt).not.toMatch(/Stage 3/);
  });

  it('uses the scenario totals and never shows an allocation', () => {
    renderAt('/');
    const text = storySection().textContent ?? '';
    expect(text).toContain(`${demoTotals.requested} units`);
    expect(text).toContain(`The depot can cover ${demoTotals.stock}`);
    expect(text).toContain(`${demoTotals.shortfall} units of requests cannot be met`);
    expect(text).not.toMatch(/allocated \d+/i);
    // Urgency scores are computed by the engine, never restated on the landing page.
    expect(text).toContain('In the dashboard');
  });

  it('shows the static network when WebGL is unavailable', () => {
    // jsdom has no WebGL, so this is the no-WebGL path.
    renderAt('/');
    const poster = within(storySection()).getByRole('img', { name: /Resource network/ });
    expect(poster.getAttribute('aria-label')).toContain(String(demoTotals.stock));
    expect(storySection().querySelector('canvas')).toBeNull();
  });
});
