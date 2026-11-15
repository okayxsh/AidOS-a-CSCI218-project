import { cleanup, configure } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

// findBy*/waitFor wait up to 4 s: cold module loading of a lazy route can exceed the 1 s default.
configure({ asyncUtilTimeout: 4000 });

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

// jsdom does not implement these browser APIs; Recharts and the router's scroll reset use them.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver ??= ResizeObserverStub as unknown as typeof ResizeObserver;
window.scrollTo = (() => {}) as typeof window.scrollTo;

// GSAP's matchMedia and the motion hooks read media queries; jsdom has none. Report
// "no preference" and wide screens, so tests exercise the default motion path.
window.matchMedia ??= ((query: string) => ({
  matches: false,
  media: query,
  onchange: null,
  addEventListener: () => {},
  removeEventListener: () => {},
  addListener: () => {},
  removeListener: () => {},
  dispatchEvent: () => false,
})) as typeof window.matchMedia;

// Warm the lazily loaded routes once per test file, before any test starts. On a busy
// machine the first transform of the dashboard module graph can take several seconds; paying
// it here keeps that cost out of individual tests' time limits.
await Promise.all([
  import('../pages/DashboardLayout'),
  import('../pages/Overview'),
  import('../pages/Scenarios'),
  import('../pages/Inventory'),
  import('../pages/Allocate'),
  import('../pages/Simulate'),
  import('../pages/Evaluate'),
]);
