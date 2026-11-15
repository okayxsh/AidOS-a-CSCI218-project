/**
 * Authored layout of the story's abstract coordinate plane (not geography), shared by the
 * 3D scene, the SVG poster and the framing test. World units; y is up.
 */
import { demoResources, demoZones } from './demoScenario';
import { UNIT_SCALE } from './story';

export const ZONE_POSITIONS: Record<string, [number, number, number]> = {
  'zone-a': [-5.2, 0, -2.4],
  'zone-b': [4.9, 0, -3.3],
  'zone-c': [2.7, 0, 3.7],
};

export const EXAMPLE_ZONE = { id: 'zone-d', position: [-3.9, 0, 3.4] as [number, number, number] };
/** Relative heights only: the example zone is an illustration and carries no numbers. */
export const EXAMPLE_ZONE_BARS = [0.8, 1.15, 0.55];
export const FOCUS_ZONE = 'zone-c';

/** Lens shift applied on wide screens so the network sits right of the reading card. */
export const DESKTOP_LENS_SHIFT = 0.17;
export const DESKTOP_FOV = 38;

export const DEPOT_TOP = {
  stock: Math.max(...demoResources.map((r) => r.stock)) * UNIT_SCALE,
  requested: Math.max(...demoResources.map((r) => r.requested)) * UNIT_SCALE,
};

/** Height of a zone's label anchor: just above its tallest request bar. */
export function zoneLabelHeight(zoneId: string): number {
  if (zoneId === EXAMPLE_ZONE.id) return Math.max(...EXAMPLE_ZONE_BARS) + 0.75;
  const zone = demoZones.find((z) => z.id === zoneId);
  return zone ? Math.max(...Object.values(zone.demand)) * UNIT_SCALE + 0.75 : 1;
}

/** Phone lens: wider field of view, scene lifted above the reading panel. */
export const COMPACT_FOV = 46;
export const COMPACT_SHIFT_Y = 0.24;

export interface LabelCandidate {
  key: string;
  /** Screen x of the anchor, px. */
  x: number;
  /** Screen y of the anchor above the object (label sits above it), px. */
  yAbove: number;
  /** Screen y just below the object's base (label may sit below it instead), px. */
  yBelow: number;
  width: number;
  height: number;
  /** Required labels (the depot, the illustrative zone) are always shown. */
  required: boolean;
  onScreen: boolean;
}

export interface LabelPlacement {
  key: string;
  visible: boolean;
  left: number;
  top: number;
}

/**
 * Places labels in priority order. Each tries above its anchor, then below its base; a
 * placement must stay inside the stage, right of the reading card, and clear of labels
 * already placed. Optional labels with no valid spot hide; required ones never do.
 */
export function placeLabels(
  candidates: LabelCandidate[],
  stage: { width: number; height: number; cardRight: number; bottom?: number },
): LabelPlacement[] {
  const placed: { x0: number; x1: number; y0: number; y1: number }[] = [];
  const minLeft = stage.cardRight + 8;
  // On phones the reading panel covers the lower stage: labels must end above it.
  const maxBottom = Math.min(stage.height, stage.bottom ?? stage.height) - 4;
  return candidates.map((c) => {
    if (!c.onScreen) return { key: c.key, visible: false, left: 0, top: 0 };
    const left = Math.min(stage.width - c.width - 8, Math.max(minLeft, c.x - c.width / 2));
    const drift = Math.abs(left + c.width / 2 - c.x);
    const options = [c.yAbove - c.height, c.yBelow].map((top) => ({
      x0: left,
      x1: left + c.width,
      y0: top,
      y1: top + c.height,
    }));
    const valid = options.find(
      (box) =>
        box.y0 >= 4 &&
        box.y1 <= maxBottom &&
        drift <= Math.max(48, c.width / 2) &&
        !placed.some((o) => box.x0 < o.x1 && box.x1 > o.x0 && box.y0 < o.y1 && box.y1 > o.y0),
    );
    const chosen = valid ?? (c.required ? options[0] : undefined);
    if (!chosen) return { key: c.key, visible: false, left, top: options[0].y0 };
    placed.push(chosen);
    return { key: c.key, visible: true, left: chosen.x0, top: chosen.y0 };
  });
}
