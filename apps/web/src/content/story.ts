/**
 * Scene ledger for the landing page's resource-network story.
 *
 * Every quantity comes from the synthetic demo fixture (content/demoScenario.ts), the
 * same file the engine serves. Chapters 5–8 explain techniques, each with an explicit
 * build-status label (built, partly built or illustration). Nothing here is an engine
 * output: the landing page never computes scores or allocations; the dashboard does.
 */
import { demoResources, demoTotals, demoZones } from './demoScenario';

/** World state, each value 0..1, interpolated between chapters by scroll. */
export interface WorldState {
  depot: number; // depot stock bars
  zones: number; // zone nodes
  routes: number; // supply routes drawn (fraction of path length)
  requests: number; // per-zone request bars
  shortage: number; // ghost outlines of total requests on the depot
  inputs: number; // fuzzy-logic input stems (severity, vulnerability, time-criticality)
  caps: number; // constraint caps at stock and request heights
  focus: number; // one route and zone singled out for explanation
  adapt: number; // illustrated change: a new zone, reduced medical stock, stale routes
}

export type ChapterStatus = 'scenario' | 'built' | 'concept' | 'partial' | 'illustrated';

export interface Chapter {
  id: string;
  title: string;
  body: string;
  /** Honesty line shown under the title for anything that is not plain scenario data. */
  status?: { tone: ChapterStatus; text: string };
  /** Desktop endpoint; `mobile` is the phone endpoint (same target), tested for framing. */
  camera: {
    position: [number, number, number];
    target: [number, number, number];
    mobile: [number, number, number];
  };
  world: WorldState;
}

const none: WorldState = {
  depot: 1,
  zones: 0,
  routes: 0,
  requests: 0,
  shortage: 0,
  inputs: 0,
  caps: 0,
  focus: 0,
  adapt: 0,
};

const stockList = demoResources
  .map((r) => `${r.stock} ${r.label.toLowerCase()}`)
  .join(', ')
  .replace(/, ([^,]*)$/, ' and $1');

export const CHAPTERS: Chapter[] = [
  {
    id: 'depot',
    title: 'One depot holds everything there is to give.',
    body: `In the synthetic demo scenario the depot has ${stockList}: ${demoTotals.stock} units in all.`,
    camera: { position: [5.2, 4.6, 9.4], target: [0, 1.5, 0], mobile: [6.2, 5.2, 11.3] },
    world: { ...none },
  },
  {
    id: 'zones',
    title: 'Three zones ask for help at once.',
    body: 'Each is rated for severity, vulnerability and time-criticality. The places are fictional, invented for the simulator.',
    status: { tone: 'scenario', text: 'Synthetic scenario triage-demo-001' },
    camera: { position: [0, 9.6, 11.6], target: [0, 0, 0.2], mobile: [0, 21.5, 25.7] },
    world: { ...none, zones: 1 },
  },
  {
    id: 'routes',
    title: 'Every zone needs every resource.',
    body: 'Medical kits, water and shelter travel on separate routes. A water pack cannot stand in for a medical kit, so each resource is its own contest.',
    camera: { position: [0.9, 7.8, 12.1], target: [0, 0.4, 0], mobile: [2.1, 17.3, 27.6] },
    world: { ...none, zones: 1, routes: 1 },
  },
  {
    id: 'requests',
    title: `Together they ask for ${demoTotals.requested} units.`,
    body: demoZones
      .map(
        (z) =>
          `${z.name.split('·')[0].trim()} requests ${Object.values(z.demand).reduce((a, b) => a + b, 0)}`,
      )
      .join(', ')
      .concat('.'),
    camera: { position: [0.6, 7.1, 12.4], target: [0, 0.7, 0], mobile: [1.4, 15.3, 28.3] },
    world: { ...none, zones: 1, routes: 1, requests: 1 },
  },
  {
    id: 'shortage',
    title: `The depot can cover ${demoTotals.stock}.`,
    body: `${demoTotals.shortfall} units of requests cannot be met by any plan. The real question is which needs go unmet, and why.`,
    camera: { position: [3.4, 6.8, 14.4], target: [0, 1.1, 0.6], mobile: [7.8, 14.1, 32.1] },
    world: { ...none, zones: 1, routes: 1, requests: 1, shortage: 1 },
  },
  {
    id: 'fuzzy',
    title: 'First, how urgent is each zone?',
    body: 'Field ratings are imprecise. Fuzzy logic turns severity, vulnerability and time-criticality into one urgency score from 0 to 100, and keeps the rules that produced it.',
    status: {
      tone: 'built',
      text: 'Fuzzy logic · zero-order Sugeno rules · scores are computed live in the dashboard',
    },
    camera: { position: [0.6, 9.6, 12.6], target: [0.3, 0.2, 0], mobile: [1, 20.9, 27.7] },
    world: { ...none, zones: 1, routes: 1, inputs: 1 },
  },
  {
    id: 'constraints',
    title: 'Then, what is allowed?',
    body: 'A valid plan gives whole units, never more than a zone asked for and never more than the depot holds. The search happens only inside those limits.',
    status: {
      tone: 'built',
      text: 'Constraint satisfaction · OR-Tools CP-SAT · every plan is checked against these limits',
    },
    camera: { position: [3.9, 7.2, 14.7], target: [0, 1.1, 0.6], mobile: [8.7, 14.8, 32.2] },
    world: { ...none, zones: 1, routes: 1, requests: 1, shortage: 1, caps: 1 },
  },
  {
    id: 'oversight',
    title: 'Every decision can be questioned.',
    body: 'Each allocation records what was requested, what was given and which limit stopped it. AidOS proposes a candidate plan; a coordinator reviews it and decides whether to commit.',
    status: {
      tone: 'built',
      text: 'Explainability · rule traces and allocation reasons are live in the dashboard · stock moves only when a coordinator dispatches a plan in the simulator',
    },
    camera: { position: [4.8, 5.2, 12], target: [1.5, 0.7, 1.7], mobile: [9.7, 11.9, 27.2] },
    world: { ...none, zones: 1, routes: 1, requests: 1, focus: 1 },
  },
  {
    id: 'adapt',
    title: 'Then the situation changes.',
    body: 'Example events: a fourth zone reports, and part of the medical stock is lost in transit. Each change makes a new snapshot; urgency is rescored and the plan recomputed from it, never patched.',
    status: {
      tone: 'built',
      text: 'Crisis simulation · apply these events live in the dashboard simulator · the zone and losses shown here are an illustrated example',
    },
    camera: { position: [-0.8, 10.2, 12.9], target: [0, 0, 0.6], mobile: [-1.7, 22, 27.2] },
    world: { ...none, zones: 1, routes: 1, requests: 1, adapt: 1 },
  },
];

/** World units per supply unit for every bar in the scene. */
export const UNIT_SCALE = 1 / 60;

/** Illustrative change used by the "adapt" chapter only (not part of any fixture). */
export const ADAPT_EXAMPLE = { resourceId: 'medical_kits', lostUnits: 30 };
