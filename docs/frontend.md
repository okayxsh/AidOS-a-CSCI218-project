# Frontend (apps/web)

Stage 1 frontend: a landing page at `/` and an operations dashboard at `/dashboard`. React 19, TypeScript, Vite 8, React Router 8, Recharts, Lucide icons, plain CSS tokens. No CSS framework and no global state library.

## Routes

| Route | Page | Status |
|---|---|---|
| `/` | `pages/Landing.tsx` | Built. Renders without the backend |
| `/dashboard` | `pages/Overview.tsx` | Built. Summary, chart, inventory, zones, allocation entry point |
| `/dashboard/scenarios` | `pages/Scenarios.tsx` | Built. Choose the active scenario |
| `/dashboard/inventory` | `pages/Inventory.tsx` | Built. Requests by zone against stock, request matrix |
| `/dashboard/allocate` | `pages/Allocate.tsx` | Built for FCFS. Matrix + per-cell explanation from the engine |
| `/dashboard/simulate` | `pages/Simulate.tsx` | Built (Stage 3). Simulation sessions: events, controls, before/after, timeline, dispatch ledger, replay |
| `/dashboard/evaluate` | `pages/Evaluate.tsx` | Built (Stage 4). Results of offline evaluation runs from `/api/evaluation` |

The active scenario lives in the URL (`?scenario=<id>`, default `triage-demo-001`), so refresh, deep links and back/forward keep it, and every dashboard page reads the same snapshot. Dashboard pages are lazy-loaded, so the landing bundle does not include Recharts.

## Data flow

```text
api/client.ts      the only module that calls fetch; typed by api/types.ts (mirrors apps/api/aidos/api/schemas.py)
state/useRequest   small hook + module-level promise cache (no refetch when moving between pages)
state/scenario     useHealth, useScenarioList, useScenarioDetail, useActiveScenarioId, useFcfsRun
DashboardLayout    fetches the active scenario once and passes it to pages via the router outlet
```

There is **no mock-data layer in the dashboard**. Its scenarios are the synthetic fixtures in `data/scenarios/`, served and validated by the engine, and every number shown (totals, shortfall, per-zone requests, FCFS allocations, coverage) is computed by the backend. If the engine is down, the dashboard shows an error state with the start command, never placeholder numbers.

The landing page is the one exception by design: `content/demoScenario.ts` imports `triage-demo-001.json` directly (same file the engine serves) so `/` renders without the backend. It restates inputs only (stock and requests) and is labelled as a synthetic preview.

## Components

| Area | Components |
|---|---|
| Primitives (`components/ui`) | `Button` (`LinkButton`, `LaunchDashboardButton`), `StatusBadge`, `SyntheticBadge`, `Panel`, `Metric`, `SectionHeading`, `Logo`, `States` (`LoadingState`, `ErrorState`, `EmptyState`) |
| Landing | `SiteHeader` (with mobile menu), `LandingHero`, `LandingBackdrop` + `LandscapeRidge`, `DashboardPreview`, `ProblemSection`, `HowItWorks`, `FeatureExplorer` (keyboard tabs), `MethodologyPreview`, `AboutSection`, `SiteFooter` (+ `ClosingCta`) |
| Dashboard | `ScenarioSelector`, `ScenarioGate` (+ `ScenarioHeader`), `StockDemandChart`, `InventoryPanel`, `ZoneTable` (sortable), `RequestBar`, `AllocationPreview`, `AllocationMatrix`, `ExplainabilityPanel`, `PolicyComparison`, `EventTimeline`, `PlannedFeature` |
| Content | `content/landing.ts` (workflow steps with build status), `content/demoScenario.ts` |
| Helpers | `lib/format.ts` (number, ratio N/A, labels), `lib/display.ts` (limit labels, policy descriptions, chart shades) |

## Design system

Defined in `src/styles/tokens.css`; recorded in `DESIGN.md` at the repository root.

- One dark world for both surfaces: night-navy ground, off-white text, teal for stock and availability, amber for shortfall, red only for critical states. Colour always has a text label beside it.
- Type: Mona Sans (UI and display), Instrument Serif italic for one accent phrase per heading, JetBrains Mono for ids, formulas and code. All three are self-hosted (`@fontsource`) so the demo works offline.
- Landing (cinematic): rounded hero frame, sky with faint aurora, a fictional relief landscape ridge (depot, camps, supply routes) with the dashboard window rising out of it, pill CTAs. One entrance motion (the window rising); everything is static under `prefers-reduced-motion`.
- Dashboard (dense): sidebar with "Workspace" and "Later stages" groups, sticky top bar with the scenario selector, panels, tables first, one grouped bar chart.
- Honesty rules built into the UI: planned items carry a dashed "Planned · Stage N" badge; plans are labelled "Candidate plan · not committed"; unbuilt policies are disabled radios, not dead buttons.

## Ready for backend integration (Stage 2+)

- `api/types.ts` + `api/client.ts`: add `urgencyEvaluate`, `transition`, `commit` beside the existing calls.
- `useFcfsRun` generalises to `usePolicyRun(policyId)`; `Allocate.tsx`'s policy picker already lists engine policies from `/api/health` and enables any that report `available: true`.
- `FeatureExplorer`'s urgency panel and `ZoneTable` have a slot for the fuzzy score; `ExplainabilityPanel` renders whatever `reason` the engine returns, so rule traces can extend the cell schema.
- `PolicyComparison` fills from experiment records once Stage 4 produces them.
- `EventTimeline` takes the snapshot history when the FSM lands.
- Update `content/landing.ts` statuses when a stage actually ships.

## Tests

`npm test` (Vitest + Testing Library, fetch mocked at the HTTP boundary only): landing renders without the backend, every Launch Dashboard link targets `/dashboard`, section anchors exist, workflow statuses, keyboard tabs, dashboard deep link shows backend totals, scenario switching updates summary and zone table, offline state, planned pages, scenario kept across navigation, unknown scenario, unbuilt policies disabled.

## Stage 1.5: scrollytelling, 3D network and dashboard refinement

### Landing narrative

`Landing.tsx` now tells one story: hero → **How a shortage becomes a decision** (pinned 3D story, 9 chapters) → How AidOS works → Features → Technology → About → **From the story to the system** (dashboard reveal). The earlier problem section and closing CTA were folded into the story and the reveal.

| Chapter (`content/story.ts`) | What the visitor learns | Status label (as shown since Stage 3) |
|---|---|---|
| depot, zones, routes, requests, shortage | one depot, three zones, per-resource contests, 560 requested vs 330 in stock | synthetic scenario data |
| fuzzy | imprecise ratings become a priority score | **Built** (zero-order Sugeno; scores computed live in the dashboard) |
| constraints | whole units, ≤ request, ≤ stock | **Built** (OR-Tools CP-SAT; every plan checked against the limits) |
| oversight | every cell explainable; a coordinator commits | **Built** (rule traces and allocation reasons; stock moves only on dispatch in the simulator) |
| adapt | a new zone and lost stock make a plan stale | **Built** (simulator); the zone and losses drawn in the story are a labelled example |

All numbers come from `data/scenarios/triage-demo-001.json` (the same file the engine serves). The story never shows allocation results; the adapt chapter's lost stock and zone D are labelled examples.

### ScrollTrigger architecture

- `ResourceStory.tsx` owns **one** ScrollTrigger on the chapter list (`start: top top`, `end: bottom bottom`). Native scroll is the source of truth; the trigger converts scroll offset into a fractional chapter `c = (scroll − start) / stepHeight`, written to a shared ref (`conductor.target`) and used to invalidate the canvas. No scroll-jacking, no smooth-scroll library.
- The stage is CSS `position: sticky`; chapters are ordinary HTML in document order (keyboard, screen reader and no-JS friendly).
- `Landing.tsx` (`useLandingMotion`) uses `gsap.matchMedia` with a `prefers-reduced-motion: no-preference` condition: hero parallax (atmosphere, copy recede, ridge offset via a CSS variable, preview forward), the workflow list stagger, and the reveal tilt. `mm.revert()` on unmount; `useGSAP` scopes and cleans up the story trigger.
- `ScrollTrigger.refresh()` runs after `document.fonts.ready`.

### Three.js scene (`components/story/NetworkScene.tsx`)

- React Three Fiber `Canvas` with `frameloop="demand"`: a frame renders only when scroll progress changes or the camera is still damping (no idle GPU work).
- One ambient + one directional light, linear fog, no shadows, DPR capped at 1.5 (1.25 on phones). Geometry is generated from the fixture: one merged polar grid, shared box/ring/edge geometries, ~60 draw calls.
- Camera endpoints and world state per chapter are data; values are interpolated with smoothstep and exponential damping. Phones pull the camera back and lens-shift the scene above the reading panel.
- Labels are HTML (`.story__label`), projected from 3D anchors each frame, clamped to the stage, hidden when their anchor is out of frame. Essential information is always in the chapter text.
- Lazy chunk, fetched by `IntersectionObserver` only when WebGL exists. `NetworkPoster` (SVG) shows while loading, when WebGL is unavailable, on chunk error (error boundary) and on WebGL context loss.
- Memoised geometries and materials are disposed explicitly on unmount.
- Reduced motion: the scene snaps to the nearest chapter with no damping; chapter panels stay fully opaque.

### Dashboard palette (`.dash-palette` in `styles/tokens.css`)

| Role | Token | Value |
|---|---|---|
| Application ground | `--ink-850` | `#080b10` |
| Sidebar | `--ink-900` | `#0b1017` |
| Panels, tiles | `--ink-800` | `#111821` |
| Raised (active nav, tray) | `--ink-700` | `#17212c` |
| Hairline / strong hairline | `--line` / `--line-strong` | `#1d2631` / `#2a3542` |
| Text / secondary / tertiary | `--text` / `--text-2` / `--text-3` | `#eaf0f4` / `#a2b0c0` (8.1:1) / `#7d8a9b` (5.1:1) |
| Stock / shortfall / critical | `--teal` / `--amber` / `--red` | `#43c9c1` / `#e9a84a` / `#e66b70` |

The landing preview window uses the same class, so the picture of the dashboard matches the real one.

### Dashboard motion

- Page sections enter once (320 ms, capped stagger); pages are keyed by snapshot hash so a scenario switch is a short crossfade.
- While the next scenario loads, the previous one stays visible but dimmed and inert (`useRequest({ keepPrevious })`, `ScenarioGate` `.gate.is-stale`); no skeleton flash when data is cached.
- A metric whose value differs from the previous scenario's flashes once (`.metric__value.is-changed`). No counting animations, which would show numbers the backend never returned.
- Chart bars grow on first render (480 ms) and are static under reduced motion.

### Dependencies added in Stage 1.5

`three@0.187`, `@react-three/fiber@9.8` (supports React 19.0–19.3), `gsap@3.15` with `ScrollTrigger`, `@gsap/react@2.1`; dev: `@types/three`.

## Stage 2: fuzzy urgency, CP-SAT allocation and comparison

### Data flow

| Hook (`state/scenario.ts`) | Request | When |
|---|---|---|
| `useUrgency(detail)` | `POST /api/urgency/evaluate {scenario}` | Automatically per snapshot (scoring is not an allocation) |
| `useAllocationRun(detail)` | `POST /api/allocations/compare {scenario, policies: [fcfs, greedy, aidos, aidos_balanced]}` | Only after the user clicks **Run allocation** |

Both cache keys contain the `snapshot_hash`, and both hooks discard any response whose `snapshot_hash` differs from the active snapshot, so a plan or score is never shown against another scenario. One compare request returns every policy, computed on the same snapshot with the same fuzzy scores; switching the policy view never re-runs anything. `useFcfsRun` is gone.

### Allocation workspace (`pages/Allocate.tsx`)

- Policy switcher (engine policies from `/api/health`), default view AidOS.
- Summary of the selected result: units allocated, unmet, urgency-weighted coverage, stock utilisation, hard checks passed, solver status and engine runtime.
- A result without a plan (`INFEASIBLE`, `UNKNOWN`, `MODEL_INVALID`) shows the engine's message and no matrix; nothing is filled in.
- Allocation matrix plus `ExplainabilityPanel`, which keeps two sources apart: **From the allocation constraints** (requested, allocated, unmet, the engine's reason, stock used by the plan) and **From the fuzzy rules** (score, category, objective coefficient, strongest rules with their point contributions).
- `UrgencyPanel`: every zone's Sugeno score, category, top rules with contributions, and a disclosure with membership degrees and every fired rule.
- `ValidationChecklist` (the engine's independent validator; hard vs quality checks), `RemainingInventory` (stock, allocated, remaining), `SolverDiagnostics` (status, objective, lexicographic phases, model size, coverage floors in balanced mode).
- `RunComparison`: FCFS, urgency greedy, AidOS and AidOS balanced side by side, plus coverage per zone. Values are unranked and unhighlighted; the page states that totals can tie under fixed stock, and says so when AidOS (urgency-first) produced the same allocation as greedy (the spec's planned control).

### Elsewhere

- Overview: `ZoneTable` gains a sortable **Urgency** column; `AllocationPreview` shows all four policies after one run, sharing the workspace's cache.
- Evaluate: (Stage 2 note, superseded) the experiment table stayed empty until the Stage 4 runner produced results; see the Stage 4 section.
- Landing truthfulness: fuzzy and constraint chapters, workflow steps and feature tabs now say **Built** (Stage 2) and name the real method (zero-order Sugeno, OR-Tools CP-SAT). Oversight stays **Partly built** (commit is Stage 3), the adapt chapter stays an **Illustration**, and the landing page still computes and shows no scores or allocations. `MethodologyPreview` draws the membership curves from the engine's own `apps/api/aidos/config/fuzzy_rules.json` (allowed in `vite.config.ts` `server.fs.allow`).

### Tests

`src/test/allocate.test.tsx` covers: scores before a run; the run action with its loading state; displayed values equal to the API values; one request carrying all four policies; switching policies without re-running; the explanation split; validation and comparison values; engine errors; no stale plan after switching scenario. The mocked API answers with real engine responses captured from the running backend (`src/test/fixtures/engine-*.json`), re-stamped with the mocked snapshot hash.

## Stage 3: crisis simulation page

`/dashboard/simulate` drives a backend simulation session (`/api/simulation/*`). The page never computes a score, an allocation, a diff or an explanation: it renders the engine's `SessionOut` and sends events.

### Data flow

```text
state/simulation.ts   useSimulation(scenarioId): the latest SessionOut, busy label, feedback, expired flag
api/client.ts         simApi: create, get, control (start|pause|resume|complete|reset), apply, replay,
                      exportSession, importSession; every change sends the session's current version
pages/Simulate.tsx    Workspace keyed by scenario id: switching scenario unmounts the session view
```

- The session id is mirrored in `?session=`, so a refresh reopens it. On mount the page fetches it and shows it only if its `scenario_id` is the active scenario; otherwise the parameter is dropped. A 404 (session expired after two idle hours, or the engine restarted) shows "That simulation session no longer exists" with **Start a new session**.
- `409 version_conflict`: the page refetches the session and says the state changed elsewhere, naming the version now shown. `500 engine_invariant` refetches too (the session is then in ERROR).
- Event refusals (`422 insufficient_stock`, `no_change`, `unknown_zone`, ..., `409 stale_plan`) appear inline under the event form, prefixed "The engine refused this event". The previous state stays on screen, because the engine applies events atomically.

### Components (`components/sim/`)

| Component | Shows |
|---|---|
| Control bar (in `Simulate.tsx`) | State badge, step, version, session id; Start / Pause / Resume / Complete / Reset enabled strictly from `allowed_actions`; Replay; Export JSON |
| `SimSummary` | Six tiles (state, events applied and clock step, active zones, requested vs stock, shortfall, dispatched) and the per-resource inventory with what the candidate plan would use |
| `EventComposer` | One form per event type (urgency change, new zone, shipment, loss, request change, zone resolved, clock advance, dispatch). Only clearly invalid input is blocked (non-numbers, ratings outside 0–10, a loss above stock, a no-op, resolving the last zone, dispatching an empty plan); the engine decides everything else |
| `SimExplanation` | `diff.explanation`, verbatim, with a "Plan changed / Plan unchanged" badge from `recommendation_changed` |
| `SimAllocation` | The recommended plan per zone (urgency order) and resource: allocated / requested bars, a faint mark at the previous step's value, and "was N" on changed cells |
| `StepComparison` | Urgency before → after (score, category, rank); the recommended policy next to FCFS on the same state (allocated, unmet, urgency-weighted coverage, cells changed); stock and shortfall before → after; the changed cells of both policies |
| `SimTimeline` | `history`, newest first, with each step's summary, totals, changed-cell count, clock step and snapshot hash |
| `SimLedger` | Dispatches (`plan_committed`) and resolved zones. Plans are labelled candidates until dispatched |

### Replay, export and the demo script

- **Replay** exports the session's own events, posts them to `/replay` (reset, then re-apply on the engine) and compares the engine's outcome hashes step by step with the run before. The result is stated: "all N steps reproduced the same outcome hash", or the first step that differs.
- **Export JSON** downloads the engine's export document (initial scenario, configuration, events, outcome hashes).
- **Load demo script** (shown only on `triage-demo-001`) imports `data/simulations/triage-demo-escalation.json`, which the web build reads directly like the landing fixture. The engine replays it and returns its own verification, which the page reports.

### Motion

Allocation fills keep their DOM node between steps, so a width change animates from the previous value (320 ms). Changed values flash once (the existing 350 ms `value-changed`); new zones, explanation lines and timeline entries rise in (240–260 ms). The global reduced-motion rule turns all of it off. Nothing animates unless the engine returned a changed value.

### Labels updated for Stage 3

The sidebar lists Simulation under Workspace (only Evaluation is a later stage). On the landing page, the workflow step "Respond to change", the feature tabs for simulation and oversight, the methodology's state machine row (states READY, ACTIVE, PAUSED, COMPLETED, ERROR) and the story's oversight and adapt chapters now say Built. The adapt chapter keeps its zone and losses labelled as an illustrated example. Allocation pages say stock is consumed only by a dispatch in the simulator. All synthetic-data and academic-prototype labels are unchanged.

### Tests

`src/test/simulate.test.tsx` (fetch mocked at the HTTP boundary; responses captured from the live engine in `test/fixtures/sim-triage.json`) covers:

- session creation and start, with controls following `allowed_actions`;
- an event updating the summary, the bars, the timeline and the explanation;
- an inline engine refusal, and client-side blocking of a loss above stock;
- reset clearing the history;
- switching scenario never showing the previous session;
- a version conflict;
- an expired session;
- the demo script import.

## Stage 4: evaluation dashboard

`/dashboard/evaluate` shows the results of offline evaluation runs (`experiments/run_benchmarks.py --preset …`). The page never computes a statistic: it renders `summary.json`, `manifest.json` and `config.json` of one run, served read-only by the engine.

### Data flow

| Piece | Source |
|---|---|
| `evalApi.runs()` | `GET /api/evaluation/runs` (newest first) |
| `evalApi.run(id)` | `GET /api/evaluation/runs/{run_id}` → `{manifest, config, summary, failures}` |
| `useEvaluationRuns`, `useEvaluationRun` | `state/evaluation.ts`; the run detail keeps the previous run visible (dimmed) while the next loads |
| Default run | the newest complete `extended` run, else the newest complete `standard` run, else the newest run (`lib/evaluation.ts::defaultRun`); a selector lists every run |

### Sections (`pages/Evaluate.tsx`, `components/eval/`)

| Section | What it shows |
|---|---|
| Overview | What is compared and why (four policies, the same scenarios, paired comparisons); run size tiles |
| Policy comparison | Mean (with median and n) of every metric for every policy; each metric labelled **Objective-aligned** or **External** from `summary.metrics[].aligned`, with its direction and note; valid plans / optimal proven; solver statuses; identical-plan counts. No winner colouring; "Same mean for every policy" where it applies |
| Policies on one metric | Bar chart of the chosen metric by policy: mean, or median with 25th–75th percentile whiskers (only real percentile fields). Fractions on a 0–100% axis |
| By scenario family | Grouped bars and a table of the chosen metric's family means; family chips filter A–G |
| Paired comparisons | For a chosen pair and scope (all or one family): mean difference with the 95% bootstrap CI, median difference, W/T/L, d_z and a plain reading derived from the CI (e.g. "No clear difference (CI includes 0)"); the pre-declared sign tests with Holm-adjusted p |
| Dynamic events | Recommendation mode (shared state, reallocation per event type) and dispatch mode (policy-specific trajectories, fulfilment and integrity) in separate panels, never mixed |
| Runtime and problem size | Median runtime by zones per policy on a log axis, labelled as one machine's wall clock |
| What these results do and do not show | Synthetic-only, circular metrics, same supply, equality is not fairness, timing, no humanitarian effectiveness |
| Run and reproducibility | Run id, preset, status, times, failures, versions, frozen AidOS configuration, family seed ranges, bootstrap settings and the source revision (which says the folder is not a git repository) |

States: no runs (explains the command to produce one), loading, engine error, a run with failures or an incomplete status (warning plus the failure list), and a run without `summary.json`.

Every chart has an accessible data table with the plotted values. Tables scroll horizontally on phones; charts fit at 390 px.

### Navigation and landing copy

- The sidebar lists Evaluation under Workspace; the "Later stages" group is hidden because it is empty.
- The landing dashboard preview no longer marks Evaluation as planned; the Features "Allocation comparison" tab says comparisons over many synthetic scenarios are on the Evaluation page (no performance claims); the About section says results come only from seeded experiments on synthetic scenarios.

### Tests

`src/test/evaluate.test.tsx` uses a real standard run captured from the engine (`src/test/fixtures/eval-standard.json`, comparisons trimmed to the "all" and "C" scopes). It checks: metadata (including the missing source revision); table values equal to the summary; aligned and external labels; identical-plan counts; pair and scope switching; family filtering; chart data; dispatch integrity kept apart from recommendation mode; the empty and error states.

Test setup (`src/test/setup.ts`, `vitest.config.ts`) now warms the lazily loaded routes before tests start and allows longer waits, because the first transform of the dashboard graph took several seconds on a loaded machine and caused time-outs (not assertion failures).

## Stage 5: final frontend audit

A targeted audit with the impeccable detector and ui-ux-pro-max guidance. The full record, with screenshots and journey results, is in `docs/submission/frontend-audit.md`.

- **Step labels.** The dashboard header now says "Scenario file · step N" (with a tooltip). The Simulate page hides it and shows the session's own counters: "N events · clock step K · version V". Previously three different "steps" could appear on one page.
- **Headings.** `EmptyState` renders an h2 (it always sits directly under a page h1), so the Allocate and Simulate empty states no longer skip from h1 to h3.
- **Reading measure.** The new `--measure` token (62ch, about 75–80 characters in Mona Sans) caps page and panel descriptions, empty-state text and evaluation notes. It also adds `text-wrap: pretty`.
- **Changed rows.** In the before/after urgency table, changed rows are now tinted (`--teal-soft`) instead of marked with a 2px left stripe.
- **Tokens.** `--teal-text`, `--stage-horizon`, `--scene-fog`, `--stage-floor`, `--ground-deep` and `--surface-window` replace literals; rendered colours are unchanged.
- **Small text.** Scenario ids in the scenario list are held at 12px; mono at 0.92em had rendered them at 11px.
- **Tests.** The dashboard test checks the "Scenario file · step 0" label. A new simulate test checks that the file step is hidden there and that the session clock label is shown (81 tests).
