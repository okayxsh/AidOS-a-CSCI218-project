/**
 * Landing-page illustration data.
 *
 * The landing page must render without the backend (spec Section 6.1), so it reads the
 * same synthetic fixture file the engine serves. It only restates inputs (stock and
 * requests); it never shows allocation results. Dashboard numbers come from the API.
 */
import raw from '../../../../data/scenarios/triage-demo-001.json';

export interface DemoZone {
  id: string;
  name: string;
  severity: number;
  vulnerability: number;
  timeCriticality: number;
  population: number | null;
  demand: Record<string, number>;
}

export interface DemoResource {
  id: string;
  label: string;
  unit: string;
  stock: number;
  requested: number;
  shortfall: number;
  byZone: { zoneId: string; units: number }[];
}

const stock = raw.stock as Record<string, number>;

export const demoScenarioId: string = raw.scenario_id;

export const demoZones: DemoZone[] = raw.zones.map((z) => ({
  id: z.id,
  name: z.name,
  severity: z.severity,
  vulnerability: z.vulnerability,
  timeCriticality: z.time_criticality,
  population: z.population ?? null,
  demand: z.demand as Record<string, number>,
}));

export const demoResources: DemoResource[] = raw.resources.map((r) => {
  const byZone = demoZones.map((z) => ({ zoneId: z.id, units: z.demand[r.id] ?? 0 }));
  const requested = byZone.reduce((sum, entry) => sum + entry.units, 0);
  return {
    id: r.id,
    label: r.label,
    unit: r.unit,
    stock: stock[r.id] ?? 0,
    requested,
    shortfall: Math.max(0, requested - (stock[r.id] ?? 0)),
    byZone,
  };
});

export const demoTotals = {
  zones: demoZones.length,
  stock: demoResources.reduce((s, r) => s + r.stock, 0),
  requested: demoResources.reduce((s, r) => s + r.requested, 0),
  shortfall: demoResources.reduce((s, r) => s + r.shortfall, 0),
};
