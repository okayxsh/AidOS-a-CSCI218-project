/**
 * The resource network: one persistent Three.js world conducted by native scroll.
 *
 * Rendering is on demand: a frame is drawn only when scroll progress changes or while the
 * camera is still settling, so an idle page costs nothing. All geometry is generated from
 * the synthetic demo fixture at one scale (UNIT_SCALE world units per supply unit). Text
 * never lives in WebGL: labels are HTML elements positioned from projected 3D anchors.
 */
/* eslint-disable react-hooks/immutability -- Three.js cameras, materials and geometries are
   mutable by design: React Three Fiber mutates them in useFrame and effects instead of
   re-rendering React every frame. Scoped to this file, which owns only scene objects. */
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { useEffect, useMemo, useRef, type MutableRefObject } from 'react';
import * as THREE from 'three';
import { demoResources, demoZones } from '../../content/demoScenario';
import { ADAPT_EXAMPLE, CHAPTERS, UNIT_SCALE, type WorldState } from '../../content/story';
import {
  COMPACT_FOV,
  COMPACT_SHIFT_Y,
  DEPOT_TOP,
  DESKTOP_FOV,
  DESKTOP_LENS_SHIFT,
  EXAMPLE_ZONE,
  EXAMPLE_ZONE_BARS,
  FOCUS_ZONE,
  ZONE_POSITIONS,
  placeLabels,
  zoneLabelHeight,
} from '../../content/storyLayout';
import { damp, smoothstep } from '../../lib/motion';

export interface StoryConductor {
  /** Fractional chapter index from scroll (0 .. CHAPTERS.length - 1). */
  target: number;
  /** Set by the scene: asks the canvas for a frame after progress changes. */
  invalidate?: () => void;
  /** Right edge of the reading card, in px from the stage's left edge (0 when stacked). */
  cardRight: number;
  /** Top of the active reading panel, in px from the stage's top (phones; else Infinity). */
  panelTop: number;
}

interface NetworkSceneProps {
  conductor: MutableRefObject<StoryConductor>;
  labels: MutableRefObject<Map<string, HTMLElement>>;
  reduced: boolean;
  compact: boolean;
  onLost: () => void;
}

const FOG = '#0c2138';
const RESOURCE_COLOURS: Record<string, string> = {
  medical_kits: '#4f86c4',
  water_packs: '#2b9c96',
  shelter_kits: '#8774c2',
};
const INPUT_COLOURS = ['#a9c8ee', '#86ade0', '#6690cc'];
const ROUTE = '#7088a8';
const AMBER = '#f5b042';
const TEAL = '#3fd0c9';
const ROUTE_COLOUR = new THREE.Color(ROUTE);
const FOCUS_COLOUR = new THREE.Color('#e8eef7');

const BAR_W = 0.34;
const BAR_GAP = 0.44;

function lerpWorld(a: WorldState, b: WorldState, t: number): WorldState {
  const out = {} as WorldState;
  for (const key of Object.keys(a) as (keyof WorldState)[])
    out[key] = a[key] + (b[key] - a[key]) * t;
  return out;
}

/** One merged LineSegments for the polar grid: 10 rings and 24 spokes, a single draw call. */
function buildPolarGrid(): THREE.BufferGeometry {
  const points: number[] = [];
  const segments = 96;
  for (let r = 1; r <= 10; r++) {
    for (let i = 0; i < segments; i++) {
      const a0 = (i / segments) * Math.PI * 2;
      const a1 = ((i + 1) / segments) * Math.PI * 2;
      points.push(Math.cos(a0) * r, 0, Math.sin(a0) * r, Math.cos(a1) * r, 0, Math.sin(a1) * r);
    }
  }
  for (let i = 0; i < 24; i++) {
    const a = (i / 24) * Math.PI * 2;
    points.push(Math.cos(a) * 0.9, 0, Math.sin(a) * 0.9, Math.cos(a) * 10, 0, Math.sin(a) * 10);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(points, 3));
  return geometry;
}

function routeCurve(to: [number, number, number]): THREE.QuadraticBezierCurve3 {
  const start = new THREE.Vector3(0, 0.04, 0);
  const end = new THREE.Vector3(to[0], 0.04, to[2]);
  const mid = start.clone().lerp(end, 0.5);
  mid.y = 1.4 + start.distanceTo(end) * 0.08;
  return new THREE.QuadraticBezierCurve3(start, mid, end);
}

function World({ conductor, labels, reduced, compact }: Omit<NetworkSceneProps, 'onLost'>) {
  const { camera, size, invalidate } = useThree();
  const smooth = useRef(conductor.current.target);
  const lookTarget = useRef(new THREE.Vector3());
  const tmp = useRef({ a: new THREE.Vector3(), b: new THREE.Vector3(), p: new THREE.Vector3() });

  // ---------------------------------------------------------------- shared resources
  const res = useMemo(() => {
    const box = new THREE.BoxGeometry(1, 1, 1);
    box.translate(0, 0.5, 0); // grow upward from the ground
    const boxEdges = new THREE.EdgesGeometry(box);
    const square = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(-0.5, 0, -0.5),
      new THREE.Vector3(0.5, 0, -0.5),
      new THREE.Vector3(0.5, 0, 0.5),
      new THREE.Vector3(-0.5, 0, 0.5),
    ]);
    const ring = new THREE.RingGeometry(0.46, 0.54, 64).rotateX(-Math.PI / 2);
    const disc = new THREE.CircleGeometry(0.46, 48).rotateX(-Math.PI / 2);
    const depotRing = new THREE.RingGeometry(1.0, 1.06, 6).rotateX(-Math.PI / 2);
    const grid = buildPolarGrid();

    const gridMat = new THREE.LineBasicMaterial({
      color: '#a9c8ee',
      transparent: true,
      opacity: 0.13,
    });
    const depotRingMat = new THREE.MeshBasicMaterial({
      color: '#e8eef7',
      transparent: true,
      opacity: 0.8,
    });
    const ghostMat = new THREE.LineBasicMaterial({ color: AMBER, transparent: true, opacity: 0 });
    const capMat = new THREE.LineBasicMaterial({ color: TEAL, transparent: true, opacity: 0 });
    const zoneCapMat = new THREE.LineBasicMaterial({
      color: '#e8eef7',
      transparent: true,
      opacity: 0,
    });
    const resourceMat = (colour: string) =>
      new THREE.MeshLambertMaterial({ color: colour, transparent: true, opacity: 1 });

    const zoneIds = [...demoZones.map((z) => z.id), EXAMPLE_ZONE.id];
    const zoneMats = new Map(
      zoneIds.map((id) => [
        id,
        {
          ring: new THREE.MeshBasicMaterial({ color: '#e8eef7', transparent: true, opacity: 0 }),
          disc: new THREE.MeshBasicMaterial({ color: '#16304f', transparent: true, opacity: 0 }),
          bars: demoResources.map((r) => resourceMat(RESOURCE_COLOURS[r.id] ?? '#8fb0dd')),
          inputs: INPUT_COLOURS.map((c) => resourceMat(c)),
          route: new THREE.LineBasicMaterial({ color: ROUTE, transparent: true, opacity: 0 }),
          stale: new THREE.LineDashedMaterial({
            color: AMBER,
            dashSize: 0.16,
            gapSize: 0.12,
            transparent: true,
            opacity: 0,
          }),
        },
      ]),
    );
    const depotMats = demoResources.map((r) => resourceMat(RESOURCE_COLOURS[r.id] ?? '#8fb0dd'));

    const routes = new Map(
      zoneIds.map((id) => {
        const pos = id === EXAMPLE_ZONE.id ? EXAMPLE_ZONE.position : ZONE_POSITIONS[id];
        const points = routeCurve(pos).getPoints(80);
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        const dashed = new THREE.BufferGeometry().setFromPoints(points);
        const mats = zoneMats.get(id)!;
        const line = new THREE.Line(geometry, mats.route);
        const staleLine = new THREE.Line(dashed, mats.stale);
        staleLine.computeLineDistances(); // dashed lines need per-vertex distances once
        return [id, { geometry, dashed, line, staleLine, count: points.length }];
      }),
    );

    return {
      box,
      boxEdges,
      square,
      ring,
      disc,
      depotRing,
      grid,
      gridMat,
      depotRingMat,
      ghostMat,
      capMat,
      zoneCapMat,
      zoneMats,
      depotMats,
      routes,
    };
  }, []);

  useEffect(
    () => () => {
      // Explicit disposal: these resources are created imperatively, outside JSX ownership.
      const { zoneMats, depotMats, routes, ...rest } = res;
      Object.values(rest).forEach((r) => (r as THREE.BufferGeometry | THREE.Material).dispose?.());
      depotMats.forEach((m) => m.dispose());
      zoneMats.forEach((z) => {
        z.ring.dispose();
        z.disc.dispose();
        z.route.dispose();
        z.stale.dispose();
        z.bars.forEach((m) => m.dispose());
        z.inputs.forEach((m) => m.dispose());
      });
      routes.forEach((r) => {
        r.geometry.dispose();
        r.dashed.dispose();
      });
    },
    [res],
  );

  // Lens shift: desktop composes the network right of the reading column, phones above it.
  useEffect(() => {
    const cam = camera as THREE.PerspectiveCamera;
    const { width: w, height: h } = size;
    if (compact) cam.setViewOffset(w, h, 0, h * COMPACT_SHIFT_Y, w, h);
    else cam.setViewOffset(w, h, -w * DESKTOP_LENS_SHIFT, 0, w, h);
    cam.fov = compact ? COMPACT_FOV : DESKTOP_FOV;
    cam.updateProjectionMatrix();
    invalidate();
  }, [camera, size, compact, invalidate]);

  useEffect(() => {
    const shared = conductor.current;
    shared.invalidate = invalidate;
    invalidate();
    return () => {
      shared.invalidate = undefined;
    };
  }, [conductor, invalidate]);

  // ---------------------------------------------------------------- object refs
  const depotBars = useRef<(THREE.Mesh | null)[]>([]);
  const ghosts = useRef<(THREE.LineSegments | null)[]>([]);
  const caps = useRef<(THREE.LineLoop | null)[]>([]);
  const zoneCaps = useRef(new Map<string, (THREE.LineLoop | null)[]>());
  const labelWidths = useRef(new Map<string, number>());
  const labelHeights = useRef(new Map<string, number>());
  const zoneGroups = useRef(new Map<string, THREE.Group>());
  const zoneBars = useRef(new Map<string, (THREE.Mesh | null)[]>());
  const zoneInputs = useRef(new Map<string, (THREE.Mesh | null)[]>());

  const zoneAnchors = useMemo(() => {
    const anchors = new Map<string, THREE.Vector3>();
    anchors.set('depot', new THREE.Vector3(0, 0, 0)); // height set per frame
    for (const z of demoZones) {
      const p = ZONE_POSITIONS[z.id];
      anchors.set(z.id, new THREE.Vector3(p[0], zoneLabelHeight(z.id), p[2]));
    }
    const ex = EXAMPLE_ZONE.position;
    anchors.set(EXAMPLE_ZONE.id, new THREE.Vector3(ex[0], zoneLabelHeight(EXAMPLE_ZONE.id), ex[2]));
    return anchors;
  }, []);
  const depotTop = DEPOT_TOP;

  useFrame((state, delta) => {
    const goal = reduced ? Math.round(conductor.current.target) : conductor.current.target;
    if (reduced) smooth.current = goal;
    else smooth.current = damp(smooth.current, goal, 4.2, Math.min(delta, 1 / 30));
    if (Math.abs(smooth.current - goal) > 0.0008) state.invalidate();
    else smooth.current = goal;

    const last = CHAPTERS.length - 1;
    const c = Math.min(last, Math.max(0, smooth.current));
    const i = Math.min(last - 1, Math.floor(c));
    const t = smoothstep(c - i);
    const A = CHAPTERS[i];
    const B = CHAPTERS[Math.min(last, i + 1)];
    const w = lerpWorld(A.world, B.world, t);

    // Camera: interpolate authored endpoints; phones pull back along the view direction.
    const { a, b, p } = tmp.current;
    a.fromArray(A.camera.target);
    b.fromArray(B.camera.target);
    lookTarget.current.copy(a).lerp(b, t);
    // Phones use their own tested endpoints (storyFraming.test.ts), not a scaled copy.
    a.fromArray(compact ? A.camera.mobile : A.camera.position);
    b.fromArray(compact ? B.camera.mobile : B.camera.position);
    p.copy(a).lerp(b, t);
    camera.position.copy(p);
    camera.lookAt(lookTarget.current);

    // Depot: stock bars, illustrated medical loss, ghost outlines of total requests, caps.
    demoResources.forEach((r, k) => {
      const lost = r.id === ADAPT_EXAMPLE.resourceId ? ADAPT_EXAMPLE.lostUnits * w.adapt : 0;
      const h = Math.max(0.001, (r.stock - lost) * UNIT_SCALE);
      const bar = depotBars.current[k];
      if (bar) bar.scale.set(BAR_W * 1.5, h, BAR_W * 1.5);
      const ghost = ghosts.current[k];
      if (ghost) ghost.scale.set(BAR_W * 1.5 + 0.04, r.requested * UNIT_SCALE, BAR_W * 1.5 + 0.04);
      const cap = caps.current[k];
      if (cap) cap.position.y = h;
    });
    res.ghostMat.opacity = 0.9 * Math.max(w.shortage, w.caps);
    res.capMat.opacity = w.caps;
    res.zoneCapMat.opacity = 0.85 * w.caps;

    // Zones, their request bars, fuzzy input stems and routes.
    const zoneIds = [...demoZones.map((z) => z.id), EXAMPLE_ZONE.id];
    for (const id of zoneIds) {
      const isExample = id === EXAMPLE_ZONE.id;
      const presence = isExample ? w.adapt : w.zones;
      const dim = id === FOCUS_ZONE ? 1 : 1 - 0.7 * w.focus;
      const mats = res.zoneMats.get(id);
      const group = zoneGroups.current.get(id);
      if (!mats || !group) continue;
      const grow = 0.6 + 0.4 * presence;
      const focusGrow = id === FOCUS_ZONE ? 1 + 0.22 * w.focus : 1;
      group.scale.setScalar(grow * focusGrow);
      group.visible = presence > 0.01;
      mats.ring.opacity = presence * dim;
      mats.disc.opacity = 0.55 * presence * dim;

      const barValues = isExample
        ? EXAMPLE_ZONE_BARS
        : demoResources.map(
            (r) => (demoZones.find((z) => z.id === id)?.demand[r.id] ?? 0) * UNIT_SCALE,
          );
      const shown = isExample ? w.adapt : w.requests;
      (zoneBars.current.get(id) ?? []).forEach((bar, k) => {
        if (!bar) return;
        const h = Math.max(0.001, barValues[k] * shown);
        bar.scale.set(BAR_W, h, BAR_W);
        mats.bars[k].opacity = presence * dim;
        const cap = zoneCaps.current.get(id)?.[k];
        if (cap) cap.position.y = h;
      });

      const ratings = isExample
        ? [0, 0, 0]
        : (() => {
            const z = demoZones.find((zz) => zz.id === id);
            return z ? [z.severity, z.vulnerability, z.timeCriticality] : [0, 0, 0];
          })();
      (zoneInputs.current.get(id) ?? []).forEach((stem, k) => {
        if (!stem) return;
        stem.scale.set(0.2, Math.max(0.001, (ratings[k] / 10) * 1.8 * w.inputs), 0.2);
        mats.inputs[k].opacity = w.inputs * presence;
      });

      const route = res.routes.get(id);
      if (route) {
        const drawn = isExample ? w.adapt : w.routes;
        route.geometry.setDrawRange(0, Math.max(2, Math.round(route.count * drawn)));
        mats.route.opacity =
          (isExample ? 0 : 0.9) * dim * (1 - 0.75 * w.adapt) * Math.min(1, drawn * 4);
        mats.route.color.copy(id === FOCUS_ZONE && w.focus > 0.5 ? FOCUS_COLOUR : ROUTE_COLOUR);
      }
      mats.stale.opacity = w.adapt * 0.95;
    }

    // The depot label rides above whichever is taller: stock, or the request outlines.
    const depotAnchor = zoneAnchors.get('depot');
    if (depotAnchor) {
      const outline = Math.max(w.shortage, w.caps);
      depotAnchor.y = depotTop.stock + (depotTop.requested - depotTop.stock) * outline + 0.5;
    }

    // HTML labels follow their anchors; hidden when behind the camera or not yet relevant.
    const width = size.width;
    const height = size.height;
    // Measure label sizes once per text change (reads before writes: no layout thrash).
    labels.current.forEach((el, key) => {
      if (el.dataset.measured !== el.textContent) {
        labelWidths.current.set(key, el.offsetWidth);
        labelHeights.current.set(key, el.offsetHeight);
        el.dataset.measured = el.textContent ?? '';
      }
    });
    // Candidates in priority order: the depot and the illustrative zone are required (the
    // latter carries the "example" honesty label), then the zone in focus, then the rest.
    const keys = [...labels.current.keys()];
    const order = [
      'depot',
      EXAMPLE_ZONE.id,
      FOCUS_ZONE,
      ...keys.filter((k) => k !== 'depot' && k !== EXAMPLE_ZONE.id && k !== FOCUS_ZONE),
    ].filter((k) => labels.current.has(k));
    const presenceOf = (key: string) =>
      key === 'depot'
        ? w.depot
        : key === EXAMPLE_ZONE.id
          ? w.adapt
          : w.zones * (key === FOCUS_ZONE ? 1 : 1 - 0.6 * w.focus);
    const candidates = order.map((key) => {
      const anchor = zoneAnchors.get(key) ?? p.set(0, 0, 0);
      p.copy(anchor).project(camera);
      const x = ((p.x + 1) / 2) * width;
      const yAbove = ((1 - p.y) / 2) * height;
      const onScreen =
        p.z < 1 && Math.abs(p.x) < 1.1 && Math.abs(p.y) < 1.1 && presenceOf(key) > 0.02;
      p.set(anchor.x, 0, anchor.z).project(camera);
      const yBelow = ((1 - p.y) / 2) * height + 16;
      return {
        key,
        x,
        yAbove,
        yBelow,
        width: labelWidths.current.get(key) ?? 120,
        height: labelHeights.current.get(key) ?? 26,
        required: key === 'depot' || key === EXAMPLE_ZONE.id,
        onScreen,
      };
    });
    for (const place of placeLabels(candidates, {
      width,
      height,
      cardRight: conductor.current.cardRight,
      bottom: conductor.current.panelTop,
    })) {
      const el = labels.current.get(place.key);
      if (!el) continue;
      el.style.opacity = String(place.visible ? presenceOf(place.key) : 0);
      el.style.transform = `translate3d(${place.left}px, ${place.top}px, 0)`;
    }
  });

  const zoneEntries: { id: string; position: [number, number, number] }[] = [
    ...demoZones.map((z) => ({ id: z.id, position: ZONE_POSITIONS[z.id] })),
    EXAMPLE_ZONE,
  ];

  return (
    <>
      <lineSegments geometry={res.grid} material={res.gridMat} />

      {/* Depot */}
      <mesh geometry={res.depotRing} material={res.depotRingMat} position={[0, 0.01, 0]} />
      {demoResources.map((r, k) => {
        const x = (k - (demoResources.length - 1) / 2) * (BAR_W * 1.5 + 0.12);
        return (
          <group key={r.id} position={[x, 0, 0]}>
            <mesh
              ref={(m) => {
                depotBars.current[k] = m;
              }}
              geometry={res.box}
              material={res.depotMats[k]}
            />
            <lineSegments
              ref={(m) => {
                ghosts.current[k] = m;
              }}
              geometry={res.boxEdges}
              material={res.ghostMat}
            />
            <lineLoop
              ref={(m) => {
                caps.current[k] = m;
              }}
              geometry={res.square}
              material={res.capMat}
              scale={[BAR_W * 1.5 + 0.22, 1, BAR_W * 1.5 + 0.22]}
            />
          </group>
        );
      })}

      {/* Routes: solid while the plan is current, dashed amber once it is stale */}
      {zoneEntries.map(({ id }) => {
        const route = res.routes.get(id);
        const mats = res.zoneMats.get(id);
        if (!route || !mats) return null;
        return (
          <group key={`route-${id}`}>
            <primitive object={route.line} />
            <primitive object={route.staleLine} />
          </group>
        );
      })}

      {/* Zones */}
      {zoneEntries.map(({ id, position }) => {
        const mats = res.zoneMats.get(id);
        if (!mats) return null;
        return (
          <group
            key={id}
            position={position}
            ref={(g) => {
              if (g) zoneGroups.current.set(id, g);
            }}
          >
            <mesh geometry={res.disc} material={mats.disc} position={[0, 0.005, 0]} />
            <mesh geometry={res.ring} material={mats.ring} position={[0, 0.01, 0]} />
            {mats.bars.map((m, k) => (
              <group key={k} position={[(k - 1) * BAR_GAP, 0, 0]}>
                <mesh
                  ref={(mesh) => {
                    const list = zoneBars.current.get(id) ?? [];
                    list[k] = mesh;
                    zoneBars.current.set(id, list);
                  }}
                  geometry={res.box}
                  material={m}
                />
                <lineLoop
                  ref={(loop) => {
                    const list = zoneCaps.current.get(id) ?? [];
                    list[k] = loop;
                    zoneCaps.current.set(id, list);
                  }}
                  geometry={res.square}
                  material={res.zoneCapMat}
                  scale={[BAR_W + 0.14, 1, BAR_W + 0.14]}
                />
              </group>
            ))}
            {mats.inputs.map((m, k) => (
              <mesh
                key={`in-${k}`}
                ref={(mesh) => {
                  const list = zoneInputs.current.get(id) ?? [];
                  list[k] = mesh;
                  zoneInputs.current.set(id, list);
                }}
                geometry={res.box}
                material={m}
                position={[(k - 1) * BAR_GAP, 0, 0]}
              />
            ))}
          </group>
        );
      })}
    </>
  );
}

/** Lazy-loaded entry: the landing page renders fully before this chunk arrives. */
export default function NetworkScene({ onLost, ...props }: NetworkSceneProps) {
  return (
    <Canvas
      className="story__canvas"
      frameloop="demand"
      dpr={[1, props.compact ? 1.25 : 1.5]}
      gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
      camera={{ fov: 38, near: 0.1, far: 60, position: CHAPTERS[0].camera.position }}
      onCreated={({ gl }) => {
        gl.domElement.addEventListener('webglcontextlost', (event) => {
          event.preventDefault();
          onLost();
        });
      }}
      aria-hidden="true"
    >
      {/* No background: the stage's CSS sky shows through. Fog fades into the horizon. */}
      <fog attach="fog" args={[FOG, props.compact ? 26 : 13, props.compact ? 64 : 30]} />
      <ambientLight intensity={0.6} />
      <directionalLight position={[4, 9, 6]} intensity={1.1} />
      <World {...props} />
    </Canvas>
  );
}
