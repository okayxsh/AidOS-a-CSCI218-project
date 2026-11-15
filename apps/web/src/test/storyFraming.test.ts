import { PerspectiveCamera, Vector3 } from 'three';
import { describe, expect, it } from 'vitest';
import { CHAPTERS } from '../content/story';
import {
  COMPACT_FOV,
  COMPACT_SHIFT_Y,
  DEPOT_TOP,
  DESKTOP_FOV,
  DESKTOP_LENS_SHIFT,
  EXAMPLE_ZONE,
  placeLabels,
  ZONE_POSITIONS,
  zoneLabelHeight,
} from '../content/storyLayout';

/**
 * Framing checks without WebGL. Every chapter's camera endpoint must keep the depot, the
 * active zones and their labels inside the stage: right of the reading card on desktop,
 * above the reading panel on phones. Label placement runs through the real placer.
 */
type Chapter = (typeof CHAPTERS)[number];
type Lens = 'desktop' | 'phone';

/** Phone reading-panel heights per chapter (px), measured at 390x844. */
const PANEL_H: Record<string, number> = { shortage: 380, fuzzy: 300, constraints: 270 };
const panelTop = (id: string) => STAGES.phone.height - (PANEL_H[id] ?? 230) - 14;

const STAGES = {
  desktop: { width: 1400, height: 860, cardRight: 500, charPx: 7, labelH: 28 },
  phone: { width: 374, height: 828, cardRight: 0, charPx: 6.4, labelH: 24 },
} as const;

function cameraFor(chapter: Chapter, lens: Lens) {
  const { width: w, height: h } = STAGES[lens];
  const cam = new PerspectiveCamera(lens === 'desktop' ? DESKTOP_FOV : COMPACT_FOV, w / h, 0.1, 80);
  if (lens === 'desktop') cam.setViewOffset(w, h, -w * DESKTOP_LENS_SHIFT, 0, w, h);
  else cam.setViewOffset(w, h, 0, h * COMPACT_SHIFT_Y, w, h);
  cam.position.fromArray(lens === 'desktop' ? chapter.camera.position : chapter.camera.mobile);
  cam.lookAt(new Vector3().fromArray(chapter.camera.target));
  cam.updateMatrixWorld();
  cam.updateProjectionMatrix();
  return cam;
}

function activeZones(chapter: Chapter): [string, [number, number, number]][] {
  const zones = chapter.world.zones > 0.5 ? Object.entries(ZONE_POSITIONS) : [];
  if (chapter.world.adapt > 0.5) zones.push([EXAMPLE_ZONE.id, EXAMPLE_ZONE.position]);
  return zones;
}

function depotTop(chapter: Chapter) {
  const outline = Math.max(chapter.world.shortage, chapter.world.caps) > 0.5;
  return (outline ? DEPOT_TOP.requested : DEPOT_TOP.stock) + 0.5;
}

const toScreen = (v: Vector3, lens: Lens) => ({
  x: ((v.x + 1) / 2) * STAGES[lens].width,
  y: ((1 - v.y) / 2) * STAGES[lens].height,
});

for (const lens of ['desktop', 'phone'] as const) {
  describe(`story framing (${lens})`, () => {
    for (const chapter of CHAPTERS) {
      it(`frames chapter "${chapter.id}"`, () => {
        const cam = cameraFor(chapter, lens);
        const stage = STAGES[lens];
        const cardNdc = (stage.cardRight / stage.width) * 2 - 1;
        const points = [
          { name: 'depot top', at: new Vector3(0, depotTop(chapter), 0) },
          // Each zone's full bar footprint, not just its centre.
          ...activeZones(chapter).flatMap(([id, [x, , z]]) => [
            { name: `${id} left`, at: new Vector3(x - 0.62, 0, z) },
            { name: `${id} right`, at: new Vector3(x + 0.62, 0, z) },
            { name: `${id} label`, at: new Vector3(x, zoneLabelHeight(id), z) },
          ]),
        ];
        const problems = points
          .map(({ name, at }) => {
            const p = at.clone().project(cam);
            const edge = lens === 'desktop' ? 0.98 : 0.92;
            const inFrame = p.z < 1 && Math.abs(p.x) <= edge && p.y <= 0.96 && p.y >= -0.96;
            const panelNdc = 1 - (2 * panelTop(chapter.id)) / stage.height;
            const clear = lens === 'desktop' ? p.x >= cardNdc : p.y >= panelNdc; // above the panel
            return inFrame && clear ? null : `${name} at (${p.x.toFixed(2)}, ${p.y.toFixed(2)})`;
          })
          .filter(Boolean);
        expect(problems).toEqual([]);
      });

      it(`labels chapter "${chapter.id}"`, () => {
        const cam = cameraFor(chapter, lens);
        const stage = STAGES[lens];
        const zones = activeZones(chapter);
        const keys = ['depot', ...zones.map(([id]) => id)];
        const text = (key: string) => (key === 'depot' ? 36 : 24); // longest label per kind
        const candidates = keys.map((key) => {
          const pos =
            key === 'depot' ? [0, 0, 0] : (zones.find(([id]) => id === key)?.[1] ?? [0, 0, 0]);
          const top = key === 'depot' ? depotTop(chapter) : zoneLabelHeight(key);
          const above = toScreen(new Vector3(pos[0], top, pos[2]).project(cam), lens);
          const base = toScreen(new Vector3(pos[0], 0, pos[2]).project(cam), lens);
          return {
            key,
            x: above.x,
            yAbove: above.y,
            yBelow: base.y + 16,
            width: text(key) * stage.charPx + 20,
            height: stage.labelH,
            required: key === 'depot' || key === EXAMPLE_ZONE.id,
            onScreen: true,
          };
        });
        const bounds = lens === 'phone' ? { ...stage, bottom: panelTop(chapter.id) } : stage;
        const shown = placeLabels(candidates, bounds)
          .filter((pl) => pl.visible)
          .map((pl) => pl.key);
        // Desktop names every active zone; phones keep the required labels plus most zones.
        const minimum =
          lens === 'desktop'
            ? keys
            : keys.filter((k) => candidates.find((c) => c.key === k)?.required);
        for (const key of minimum) expect(shown, `${key} should be labelled`).toContain(key);
        if (lens === 'phone' && zones.length)
          expect(shown.length).toBeGreaterThanOrEqual(Math.min(3, keys.length));
      });
    }
  });
}
