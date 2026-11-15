import type { ResourceType, Scenario } from '../api/types';

const integer = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 });
const percent = new Intl.NumberFormat('en-US', { style: 'percent', maximumFractionDigits: 1 });

export const formatInt = (value: number): string => integer.format(value);

/** Ratios the backend reports as null (zero denominator) are shown as N/A, never 0%. */
export const formatRatio = (value: number | null | undefined): string =>
  value === null || value === undefined ? 'N/A' : percent.format(value);

export const formatRating = (value: number): string =>
  Number.isInteger(value) ? String(value) : value.toFixed(1);

export const shortHash = (hash: string): string => hash.slice(0, 10);

const RESOURCE_COLOURS: Record<string, string> = {
  medical_kits: 'var(--res-medical)',
  water_packs: 'var(--res-water)',
  shelter_kits: 'var(--res-shelter)',
  nutrition_packs: 'var(--res-nutrition)',
};

const FALLBACK_COLOURS = ['var(--blue)', 'var(--teal)', 'var(--violet)', 'var(--green)'];

export function resourceColour(resourceId: string, index = 0): string {
  return RESOURCE_COLOURS[resourceId] ?? FALLBACK_COLOURS[index % FALLBACK_COLOURS.length];
}

export function resourceById(scenario: Scenario): Map<string, ResourceType> {
  return new Map(scenario.resources.map((r) => [r.id, r]));
}

/** Short zone label for dense views: "Zone A · Northern floodplain" -> "Zone A". */
export function zoneShortName(name: string): string {
  return name.split('·')[0].trim();
}

export function zonePlaceName(name: string): string | null {
  const parts = name.split('·');
  return parts.length > 1 ? parts.slice(1).join('·').trim() : null;
}
