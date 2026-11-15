# 0003 — Stage 1.5 scrollytelling, one 3D scene, dashboard palette

- **Status:** Chosen in the 10 Nov 2026 build session; team review pending
- **Date:** 2026-11-10

## Context

The Stage 1.5 brief asked for a scroll-driven narrative, one meaningful Three.js visual, and a near-black dashboard palette, while preserving the Aurora Ridge landing, all backend integrations and the honesty rules (planned work labelled, no fabricated outputs).

## Decision

1. **One 3D scene** (React Three Fiber, demand rendering) of an abstract resource network, conducted by native scroll through a single GSAP ScrollTrigger; text stays in HTML.
2. **Conceptual chapters are labelled** (Concept / Partly built / Illustration) because fuzzy logic, CP-SAT and the FSM are not built yet. No allocation result appears on the landing page.
3. **Fuzzy inputs** are the spec's severity, vulnerability and time-criticality. The brief mentioned "affected population"; the spec (canonical) does not use population as a fuzzy input, so it is not shown as one.
4. **Fallbacks:** SVG poster for no-WebGL, chunk failure and context loss; reduced motion snaps chapters and removes scroll-linked motion.
5. **Dashboard palette** moves from navy to near-black via a `.dash-palette` token class; the information architecture is unchanged.

## Consequences

- New dependencies: three, @react-three/fiber, gsap, @gsap/react. The 3D chunk (~245 kB gzipped) loads only near the story; GSAP adds ~46 kB gzipped to the main bundle.
- React Three Fiber 9.8 caps React at <19.4; upgrading React past 19.3 needs a matching Fiber release.
- R3F logs a `THREE.Clock` deprecation warning with three 0.187 (library internals, not project code).
