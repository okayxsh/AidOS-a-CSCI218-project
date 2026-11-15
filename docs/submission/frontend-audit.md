# Frontend and design audit (Stage 5)

**Date:** 12 November 2026.

**Scope:**
- the landing page and nine-chapter story;
- the dashboard: overview, scenarios, inventory, allocate, simulate and evaluate;
- the four lecturer journeys A–D;
- accessibility, the dependency audit, and the known issues carried over from Stages 1.5–4.

**Method:**
- the impeccable detector (`impeccable detect`, URL scans of the running app and a source scan);
- the impeccable audit reference;
- ui-ux-pro-max guidance queries (responsive tables, reduced motion);
- headless Edge through a CDP driver at 1440×900, 820×1180 and 390×844, with probes evaluated in the page;
- direct API calls where driving the UI was impractical.

The audit screenshots were kept in a temporary local folder and are not part of the repository. The report's genuine screenshots are in `docs/report/figures/screenshots/`.

The audit was run by a subagent, so the impeccable skill's interactive steps (asking the user) were not possible. Design decisions were inferred from the brief and the existing DESIGN.md / PRODUCT.md, and no direction was changed.

## Summary

| Area | Result |
|---|---|
| Journeys A–D | **Pass** (details below) |
| Horizontal overflow, every page, 1440/820/390 | none (`scrollWidth == viewport`) |
| Browser console | clean on every dashboard page; landing shows one upstream warning (see "Left as is") |
| Accessible names on focusable controls | 0 missing on all 7 routes |
| Heading structure | one h1 per page; 0 level skips (2 fixed) |
| Detector, dashboard URLs | 0 findings after the fixes (previously 12) |
| Detector, source scan | 0 findings after the fixes (previously 1) |
| Production dependencies (`npm audit --omit=dev`) | 0 vulnerabilities |
| typecheck / lint / format / tests / build | 0 errors / 0 problems / clean / 81 passed / built |

## Issues found and fixed

| Issue | Severity | Fix | Evidence |
|---|---|---|---|
| Three different meanings of "step" could appear on the Simulate page: the scenario file's fixed step 0 in the header, the event sequence ("Step 1") and the scenario clock ("clock step 0"). | Medium (misleading) | The header reads "Scenario file · step N" with an explanatory tooltip, and is hidden on Simulate. The session bar reads "N events · clock step K · version V". | `fx-overview-head-1440.png`, `jC-sim-1440-p0.png`; dashboard and simulate tests |
| `EmptyState` used h3 directly under the page h1 on Allocate and Simulate (a heading-level skip). | Low (a11y) | `EmptyState` now renders h2, consistent with `ErrorState`. | Detector: `skipped-heading` cleared; probe: 0 skips |
| Long lines (92–150 characters) in descriptions and notes on Evaluate and Simulate; `72ch` renders as about 92 characters in Mona Sans. | Low (readability) | `--measure: 62ch` token plus `text-wrap: pretty` on descriptions, empty-state text and evaluation notes. | Detector: `line-length` cleared at 1440 and 390 |
| A 2px left-stripe marked changed rows in the before/after urgency table. | Low (design tell) | Replaced by a `--teal-soft` row tint. | `fx-sim-compare-1440.png`; detector `side-tab` cleared |
| Hardcoded colours: `#8ff0e9` (3 uses), the story-stage gradient stops, the hero ground and the preview window surface. | Low (maintainability) | Tokenised as `--teal-text`, `--stage-horizon`, `--scene-fog`, `--stage-floor`, `--ground-deep` and `--surface-window`, reusing `--sky-top` / `--ink-950`. Values are identical. | `tokens.css`; DESIGN.md Colors note |
| Scenario ids in the scenario list rendered at 11.04px (mono at 0.92em of 12px). | Low (a11y) | Held at 12px. | Detector `tiny-text` cleared |

## Investigated and left as is

| Item | Decision | Why |
|---|---|---|
| `THREE.Clock: This module has been deprecated` warning on the landing page | Left; documented | `@react-three/fiber` 9.8.2 (the latest stable; v10 is only alpha/canary) creates `new THREE.Clock()` in its store, and three 0.187 warns in the constructor. No Canvas prop avoids it. Filtering console output would hide the message, not fix it. It is harmless, and clears when R3F moves to `THREE.Timer`. |
| Phone story labels: Zone C's label overlaps the depot bars' base in chapters 4 and 6; Zone A's label is hidden in chapter 8 | Left; documented | The label placer avoids other labels and the reading panel, not 3D bar footprints. Fixing it means projecting bar boxes into the placer, which is not cheap or low-risk. The information is in the chapter text, and the 3D scene is decorative. |
| Spinner (`LoaderCircle`) on "Running four policies on the engine…" (Allocate and the Overview preview) | Kept | It renders only while the compare request is in flight (`status === 'loading'`), so it reflects real work. No other spinner exists. |
| Low-contrast findings on the landing page (story panels and badges at 1.5–2.2:1) | Kept; false positive in context | These are the inactive story chapters, dimmed to 28% opacity (`--focus`) while another chapter is active. Each becomes fully opaque when its chapter is in focus, and always under reduced motion (`jA-reduced-1440.png`). The detector scans the page at load, when only chapter 1 is active. |
| Italic-serif headings (`italic-serif-display`) | Kept | The user's Aurora Ridge direction pinned the italic serif accent. It is already recorded as an ignore value for `apps/web/src/**`; URL scans cannot see that file mapping. |
| Grid background on the hero (advisory) | Kept | It is part of the approved Aurora Ridge landscape. |
| `.impeccable/mocks/decision/` (old design mockups) | **Not changed: user decision needed** | The impeccable hooks reference allows agents to add value-level ignores only. `ignore-file` "silences too much to add on your own judgment; ask the user first". The hook scans only files that are edited, and the mockups are never edited, so they produce no noise today. If the team wants them excluded from manual scans, run `impeccable hooks ignore-file ".impeccable/mocks/**"`. |
| On phones, the Evaluate policy-comparison table scrolls sideways inside its container (one policy column visible at a time) | Kept (minor) | It sits in a `table-scroll` wrapper with a scroll shadow, and the page itself does not scroll sideways. This matches the ui-ux-pro-max guidance for wide tables ("horizontal scroll or card layout"). A card layout would be a redesign of a dense comparison table. |

## Journeys

### A: landing (PASS)

- **Layout:** hero at 1440, 820 and 390 with no overflow (`jA-landing-1440.png`, `jA-landing-820.png`, `jA-landing-390.png`).
- **Story labels:** the chapters show "Synthetic data" for the scenario chapters and "Built" for fuzzy logic (zero-order Sugeno), constraints (CP-SAT), explainability and simulation. The simulation chapter keeps "the zone and losses shown here are an illustrated example" (`jA-story-ch5-1440.png` probe; `jA-story-ch8-390.png`).
- **No-WebGL path** (Edge with `--disable-3d-apis --disable-webgl`): the SVG poster renders, there is no canvas, and the console is clean (`jA-nowebgl-ch4-1440.png`).
- **Reduced motion:** chapter panels are fully opaque and the scene snaps (`jA-reduced-1440.png`).
- **Launch Dashboard:** lands on `/dashboard`, with the h1 "Three-zone shortage".

### B: allocation (PASS) on `late-critical-arrival`

- **Overview and inventory:** render at 1440 and 390 (`jB-overview-1440.png`, `jB-inventory-1440.png`, `jB-inventory-390.png`).
- **Run allocation:** after the run, the tiles for all four policies equal the engine's own `/api/allocations/compare` response:

  | Policy | Allocated / requested | Unmet | Urgency-weighted coverage |
  |---|---|---|---|
  | FCFS | 580 / 745 | 165 | 58.7% |
  | Greedy | 580 / 745 | 165 | 90.7% |
  | AidOS | 580 / 745 | 165 | 90.7% |
  | AidOS balanced | 580 / 745 | 165 | 90.2% |

  580 + 165 = 745, so the totals reconcile.
- **Checks shown:** the validation checklist reads 5/5 hard checks plus the quality check passed. Inventory after the plan, solver diagnostics (OPTIMAL in both phases) and the baseline comparison are consistent (`jB-allocate-1440-p*.png`, `jB-allocate-390-p*.png`).

### C: dynamic crisis (PASS), through the real UI controls on `triage-demo-001`

- **Load and start:** the session loads into the simulator and starts.
- **Zone B severity 6 → 9:** urgency 62.5 → 79.2, and the plan moves C's share to B.
- **Add Zone D:** urgency 87.5; requested 560 → 660.
- **Lose 30 medical kits:** stock 330 → 300.
- **Dispatch the plan:** 300 units dispatched; stock falls to 0 and requests to 360.
- **Conservation:** initial stock − losses − dispatched = final stock, for every resource (checked from the export and the ledger).
- **Reset:** READY, 0 events, empty ledger.
- **Replay:** all 5 outcome hashes match.
- **Import of the export:** `matches: true`.
- **Captures:** console clean; no overflow at 390 (`jC-sim-1440-p*.png`, `jC-sim-replayed-390-p*.png`).

### D: evaluation (PASS)

- **Default run:** the page defaults to `extended-20261112T100136Z`.
- **Values:** every displayed mean in the policy table equals `experiments/results/extended-20261112T100136Z/summary.json`. Checked programmatically for urgency-weighted coverage, critical-zone coverage, lowest zone coverage, starved share, coverage gap and Jain index, all four policies.
- **Metric switching:** switching the chart metric to lowest zone coverage shows the summary's real percentiles (AidOS balanced: median 26.0%, p25 25.4%, p75 35.1%).
- **Limitations:** all six limitation statements are present. Clean console; no overflow at 390 (`jD-eval-1440.png`, `jD-eval-390-p*.png`).

## Accessibility notes

- **Focus:** a global `:focus-visible` ring (2px, `--line-focus`) covers every interactive element. The only `outline: none` rules are on `<main>` skip-link targets.
- **Forms:** every select and input in the event composer, the evaluation controls and the run picker has a visible `<label>`. The metric picker defaults to "Metric".
- **Landmarks:** one `main`, labelled navigation, `lang="en"`.
- **Reduced motion:** honoured (GSAP `matchMedia`, CSS `prefers-reduced-motion`). The story shows its final readable state, with no parallax or scroll-jacking.
- **Colour is never the only signal:** statuses carry text, and changed values carry "was N".
- **Contrast:** dashboard text tokens are documented in DESIGN.md (secondary 8.1:1, tertiary 5.1:1 on panels).

## Dependency audit

```text
npm audit --omit=dev   ->  found 0 vulnerabilities
npm audit              ->  10 moderate severity vulnerabilities
                           all one advisory: minimatch 7.0.0-11.0.0, reached through the
                           ESLint toolchain (@eslint/config-array, @typescript-eslint/*, eslint)
                           "fix available via npm audit fix --force" (a breaking upgrade)
```

These are dev-only (lint tooling; not shipped in the build). No upgrade was made, to avoid breaking the lint toolchain for a development-time issue.

## Checks run

From `apps/web`:

| Command | Result |
|---|---|
| `npm run typecheck` | 0 errors |
| `npm run lint` | 0 problems |
| `npm run format:check` | clean |
| `npm test` | 81 passed in 7 files (80 before this audit) |
| `npm run build` | built |

## Files changed

- `apps/web/src/components/ScenarioGate.tsx`: `showFileStep` prop; "Scenario file · step N" label.
- `apps/web/src/pages/Simulate.tsx`: hides the file step; session bar reads "N events · clock step K · version V".
- `apps/web/src/components/ui/States.tsx`: `EmptyState` heading h3 → h2.
- `apps/web/src/styles/tokens.css`: the new colour tokens and `--measure`.
- `apps/web/src/styles/story.css`, `landing.css`, `global.css`, `dashboard.css`: literals replaced by tokens; the reading measure; the changed-row tint; the scenario-id size.
- `apps/web/src/test/dashboard.test.tsx`, `simulate.test.tsx`: label tests.
- `DESIGN.md`: a Colors note on the new tokens and the measure.
- `docs/frontend.md`: the Stage 5 section.
- `docs/submission/frontend-audit.md`: this file.
