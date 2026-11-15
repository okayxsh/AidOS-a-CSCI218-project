# AidOS project info

> **Project:** AidOS — Explainable Emergency Resource Allocation Simulation  
> **Course:** CSCI218 Foundations of Artificial Intelligence · UOWD · Autumn 2026  
> **Source concept:** Dubai Humanitarian x UOWD, **Project C: Emergency Resource Allocation Simulation**  
> **Document status:** Planning specification v0.2 · 10 November 2026  
> **Build roles:** **Claude Code = primary implementer**; **Codex = scoped fixes, tests, QA, and polish**  
> **Approval status:** Team registration, selected topic, and any industry mentorship must be confirmed with the lab instructor.  
> **Important:** This is a *proposed build specification*, not evidence of implemented or validated features.

---

## 0. Read this first — the north star

Build a **working, reproducible, interactive humanitarian crisis simulation** with a polished public-facing **landing page** and a distinct **functional dashboard**. The landing page explains the project and invites users to launch the simulation; it must not become a marketing-only substitute for the actual AI system, a generic LLM chatbot, or a real-world automated aid dispatch service.

**In one sentence:** AidOS helps a simulated emergency coordinator make transparent, defensible decisions about how to distribute scarce relief supplies among competing requests as conditions change.

**Core academic argument:** A hybrid of **fuzzy urgency scoring**, **constraint-based allocation**, and **finite-state crisis updates** can be evaluated against simple baseline policies on feasibility, urgency-weighted demand met, coverage, fairness, and response time. The project must *test* this proposition; never assert it as a proven result before experiments.

**Scope guardrails:**

- Academic simulator with **synthetic or explicitly authorized anonymized data only**.
- Human decision support, **not** autonomous operational control.
- One depot, 3–8 crisis zones, 3–4 resource types for MVP; expand via configuration rather than special cases.
- Deterministic, explainable algorithms; no mandatory GPUs, external maps, LLM APIs, logins, or production database.
- Interactive crisis transitions are a real implemented behaviour, not a fake frontend animation.
- All allocation methods use the *same* scenario, constraints, and metrics for fair comparison.
- Academic honesty: distinguish planned, implemented, tested, and experimentally supported statements.

### What the files say versus our design choices

**Source-derived:** The accompanying spreadsheet describes **Project C** as allocating limited medicines, shelter items, and nutrition supplies across emergency requests of varying urgency and impact. It suggests FSMs, behaviour trees, fuzzy logic, or Q-learning and expects a **playable humanitarian decision simulation** with explanations plus beneficiaries served, delay, and fairness measures. It categorizes complexity as *Intermediate* and suggests synthetic/anonymized requests, stock limits, and priorities.

**Our proposed extension:** Add explicit **Constraint Satisfaction / CP-SAT** for hard resource constraints, an interactive web dashboard, distinct baselines, richer reproducibility, and optionally a transparent fairness trade-off. These are design choices, not text copied from the approved project description. Instructor should be told the finalized technique combination.

**Guidelines-derived:** The group must submit a report, a shared Git repository (with individual commit history), a live online demonstration, and individual contribution/reflection statements. The project grading allocates **80% group / 20% individual** within the assessment, which itself counts **20% of the course**. Exact Moodle due date is **not present** in the provided file. The instructor must approve a custom topic/partner as required; the Week 3 registration deadline has already passed as of this document's date, so confirm status now. The subject descriptor controls permitted AI-tool use and must be checked.

---

## 1. Product description

### The problem

During a crisis, several affected areas may simultaneously request critical supplies. A coordinating team has only a limited stock, incomplete or imprecise urgency reports, and potentially changing delivery capacity. A first-come-first-served policy can favor the earliest request even when later demand is more urgent. A simple highest-priority-first policy can starve lower-priority areas. A polished dashboard alone does not solve these decisions.

### The proposed solution

AidOS has **two clearly separated experiences**. First, a professionally designed **landing page at `/`** introduces the problem, explains what the team built, how the AI works, and why it matters, with a prominent **“Launch Dashboard”** call to action. Second, a functional **dashboard at `/dashboard`** displays available resources, active crisis zones, changing demand, and a timeline of events. From the dashboard the user can generate/load a scenario, examine urgency scoring, run an allocation policy, inspect explanations and shortages, then introduce a disruption (e.g., an inventory reduction, new crisis, changed vulnerability, or delayed delivery) and rerun the policy. A baseline comparison panel shows what happened under different policies with the same constraints.

### Primary users

- **Simulated emergency coordinator:** configures scenarios, reviews suggested allocations, inspects trade-offs, and approves simulated actions.
- **Lecturer/evaluator:** triggers scenario changes, asks why a decision was made, compares reproducible results.
- **Student developer/researcher:** builds the algorithms, evaluates their behaviour, and reports their limitations.

### MVP story (live demo)

1. Open `/` and understand the project from the landing-page hero, “How AidOS Works” explanation and the scope/academic-disclaimer note; click **Launch Dashboard** to enter `/dashboard`.
2. Launch the sample scenario: three zones request more medical kits, water packs, and shelter packs than the depot has.
3. Show the dashboard's demand, stock, shortages, and basic zone information.
4. Run **FCFS**, **priority greedy**, and **AidOS hybrid** policies on cloned scenario states.
5. View a per-zone/resource allocation matrix, unmet needs, urgency explanations, and comparative metrics.
6. Inject a new high-severity zone or reduce medical stock, then rerun. Show the allocation changes, and why.
7. Demonstrate a no-shortage scenario and an infeasible/zero-stock scenario with graceful handling.
8. Export results to JSON/CSV for the report's evidence.

**Definition of done for MVP:** all eight demo actions work reliably, including the landing-to-dashboard navigation, with tests and reproducible scenario IDs/seeds, *without* hidden hardcoded outcomes.

---

## 2. Objectives and evidence

| Objective | Measurable evidence | Target status |
|---|---|---|
| Feasible allocation | No resource over-allocation; nonnegative integer units; allocation ≤ demand | Hard invariant |
| Explainable priorities | Per-zone inputs, fuzzy memberships/rule contributions, score and allocation rationale | Implement & test |
| Adapt to updates | Inject a crisis event, transition simulator state, recompute on the updated scenario | Implement & test |
| Compare alternatives | FCFS, urgency-greedy, hybrid on identical scenarios | Implement & benchmark |
| Analyze trade-offs | Demand coverage, weighted coverage, fairness, unmet critical demand, runtime | Report repeated runs |
| Reproducibility | Seed, version, config, input fixture, algorithm name, output saved | Hard invariant |
| Reliable live demo | Fresh install instructions, smoke test, no mock engine behaviour | Demo-ready |

**Do not set an arbitrary guaranteed superiority threshold.** Prefer an explicit testable hypothesis: on some scarcity scenarios, the hybrid may improve urgency-weighted coverage versus FCFS; differences and trade-offs must be reported honestly, including ties, failures, and cases where baselines win.

---

## 3. Scope / non-goals

### MVP — must build

- Scenario import from JSON plus 3–5 curated synthetic scenarios.
- Editable zone characteristics, stock levels, and request quantities.
- Transparent, documented fuzzy-logic urgency engine.
- Resource allocation model with hard stock/demand constraints (proposed CP-SAT).
- Two deterministic baselines and explicit infeasibility handling.
- Discrete event/state update: new zone, stock change, urgency change, optionally delivery delay.
- Decision explanations and comparison views.
- Unit/integration tests, reproducible experiment runner, documented repository.
- Clean responsive **landing page + separate dashboard**, visible CTA navigation, accessible data labels, usable demo states.

### Stretch only after MVP and experiments

- Two allocation modes: urgency-first vs. coverage-balanced.
- Timed shipments, per-zone delivery capacities, and resource arrival schedules.
- Simple map-like schematic (not a fake geographic map).
- Scenario editor save/load; explainability breakdown visualization.
- Optional approved partner feedback and revised criteria.

### Explicitly out of scope for MVP

Real humanitarian deployment, live disaster/medical data, geospatial routing, predictive ML trained on scarce real datasets, multi-depot full supply-chain optimization, authentication, messaging, external agent orchestration, production security/compliance, AI chatbot, reinforcement learning, 3D robotics, and live APIs. Avoid spending weeks on appearance while engine tests remain incomplete.

---

## 4. Domain model and semantics (canonical)

**Unit of allocation:** discrete physical units, **separate per resource type**. Do not substitute a water pack for a medical kit.

Entities:

- **ResourceType**: stable string ID, label, unit, optional `beneficiaries_per_unit` (only if explicitly justified as a simulation assumption).
- **DepotStock**: `resource_id -> nonnegative integer available_units`.
- **CrisisZone**: ID, name, severity (0–10), vulnerability (0–10), time_criticality (0–10), activation step, requested units per resource, arrival order. Optional simulated population and distribution capacity.
- **Scenario**: schema version, ID, title, description, seed, simulation step, resource catalogue, stock, zones, event queue, metadata with `synthetic: true`.
- **Allocation**: `(zone_id, resource_id, allocated_units)` plus policy ID, effective snapshot ID.
- **DecisionExplanation**: rule inputs, urgency score, binding constraints, shortages, fairness effect, solver status, and readable summary based on computed data.
- **ExperimentRecord**: scenario/seed hash, policy, config, timings, metrics, allocations, status, software version, timestamp.

Initial resource IDs: `medical_kits`, `water_packs`, `shelter_kits`, `nutrition_packs` (4th optional in MVP fixture). Do not conflate resource *demand* with people *served*. If reporting beneficiaries, introduce a transparent conversion parameter, disclose that it is a synthetic proxy, and report kit-unit coverage as the primary robust metric.

### Example synthetic input (illustrative; not empirical data)

```json
{
  "schema_version": "1.0",
  "scenario_id": "triage-demo-001",
  "title": "Three-zone shortage",
  "seed": 2182026,
  "synthetic": true,
  "step": 0,
  "stock": {"medical_kits": 90, "water_packs": 180, "shelter_kits": 60},
  "zones": [
    {"id": "zone-a", "name": "Zone A", "arrival_order": 1, "severity": 9, "vulnerability": 8, "time_criticality": 9, "demand": {"medical_kits": 75, "water_packs": 100, "shelter_kits": 30}},
    {"id": "zone-b", "name": "Zone B", "arrival_order": 2, "severity": 6, "vulnerability": 7, "time_criticality": 5, "demand": {"medical_kits": 45, "water_packs": 130, "shelter_kits": 50}},
    {"id": "zone-c", "name": "Zone C", "arrival_order": 3, "severity": 7, "vulnerability": 5, "time_criticality": 7, "demand": {"medical_kits": 30, "water_packs": 60, "shelter_kits": 40}}
  ]
}
```

JSON must be schema-validated; reject invalid or negative units, duplicate IDs, out-of-range inputs, unknown resources, and pathological payload sizes with understandable messages.

---

## 5. AI algorithms — expected implementation

### 5.1 Fuzzy logic: urgency scoring

Purpose: translate imprecise **severity**, **vulnerability**, and **time criticality** into an explainable **urgency score** of 0–100. These are *simulated decision parameters*, not medically validated triage grades.

- Each input has linguistic sets `low`, `medium`, `high`, with parameterized triangular/trapezoidal membership functions over 0–10.
- Define and document a compact rule base (e.g., `IF severity is high AND time_criticality is high THEN urgency is critical`), including safeguards for vulnerability.
- Choose **Mamdani min/max** aggregation with discrete centroid defuzzification (e.g., grid of 0..100) *or* a fully documented zero-order Sugeno design. Prefer Mamdani for explanatory visuals. Never silently swap methods.
- Rule contribution and final score must be inspectable; write boundary and monotonicity tests for the selected rules.
- Configure weights/membership curves/rules in versioned files, not hidden UI constants.
- If no rule fires, use a documented fallback or complete coverage rules, and test it.

**Non-negotiable:** fuzzy scores do *not* authorize an allocation that violates stock/demand constraints. They are inputs to the next stage.

### 5.2 CSP / constraint optimization: allocation

For each zone `z` and resource `r`, let:

- `x[z,r]` = nonnegative **integer** allocated units.
- `d[z,r]` = requested units.
- `S[r]` = available stock.
- `u[z]` = fuzzy urgency score, 0–100.

Hard constraints:

```text
0 <= x[z,r] <= d[z,r]             for every z, r
sum_z x[z,r] <= S[r]              for every r
x[z,r] is an integer             for every z, r
```

**MVP objective:** maximize `sum_z,r (w_r * (epsilon + u[z]) * x[z,r])` using scaled **integer coefficients** in OR-Tools CP-SAT, where `w_r` are *documented* resource weights (default all 1) and `epsilon > 0` rewards useful allocations even at very low urgency. Explain that an unregularized linear objective may concentrate supplies and why this is an intended **urgency-first** baseline variant or limitation.

**Balanced variant (recommended after core works):** impose configurable minimum coverage ratios for eligible zones/resources *only when feasible*, or a lexicographic secondary objective maximizing the minimum fractional coverage. Report feasibility/priority trade-offs. Do not pretend Jain fairness is automatically maximized by the urgency-first objective. Keep the two objectives separate and named.

**Solver:** OR-Tools CP-SAT is proposed for small, discrete allocation instances. Wrap it behind an interface to permit unit tests and a diagnostic fallback if solver installation is problematic. Log `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, `UNKNOWN`, and timeout statuses accurately; zero-demand and zero-stock cases should return sensible zero allocations. No invented result when a solver fails.

**Explainability:** show urgency inputs, strongest matching fuzzy rules, allocated versus requested quantities, total stock binding, and why unmet demand remains. For scarce resources, state *which constraint limited allocation*. Do not fabricate counterfactual reasons.

### 5.3 Finite State Machine + scenario updates

Simulator lifecycle (example):

```text
DRAFT -> READY -> ALLOCATED -> COMMITTED -> UPDATED
           ^          |                     |
           |          +---- edit -----------+
           +-------------- reset -----------+
```

- `DRAFT`: loading/editing scenario.
- `READY`: validated snapshot; runnable.
- `ALLOCATED`: a candidate plan exists, but stock is *not* yet consumed.
- `COMMITTED`: user accepted a simulated plan; apply dispatched units exactly once.
- `UPDATED`: new crisis/stock/disruption event changes the snapshot; previous plan is stale until recomputed.

Transitions must be explicit and tested. In the MVP demo, do **not** automatically subtract inventory when comparing policies; compare cloned snapshots and only mutate stock when the user explicitly commits a plan. Keep immutable snapshots/event history so repeated comparison is fair. Event types: `ZONE_ADDED`, `STOCK_CHANGED`, `REQUEST_UPDATED`, `URGENCY_CHANGED`, optionally `SHIPMENT_DELAYED`. A delayed delivery metric requires real simulated dispatch/delivery time states; do not imply a delay measure exists if only an instantaneous allocation is implemented.

### 5.4 Baselines

1. **FCFS:** process zones by `arrival_order`, and each resource in canonical fixed order; allocate min(remaining stock, remaining demand). Deterministic tie break by zone ID.
2. **Urgency-greedy:** sort zones by fuzzy urgency descending then arrival order, allocate greedily per resource. This isolates the benefit of using optimization rather than only urgency scores.
3. **AidOS hybrid:** fuzzy urgency + CP-SAT resource allocation (and optionally named balanced mode).

All methods must see the same scenario and obey the same constraints. Report ties honestly. Importantly, under a purely linear additive objective and no extra constraints, a sorted greedy allocator can be mathematically equivalent to the optimizer: **this is a planned experimental control, not an embarrassment to hide.** The balanced or multi-period extension is only justified if it adds a real, measurable difference while remaining in scope.

### 5.5 Evaluation design

Run the same fixed scenario/seed set for all algorithms: start with 5 hand-curated demo fixtures, then generate ~100 synthetic instances across classes such as `no_scarcity`, `mild_scarcity`, `severe_scarcity`, `urgent_late_arrival`, `high_vulnerability`, `zero_stock`, `dynamic_shock`. Repeat timing with controlled measurement; distinguish **scenario repetitions** from **timing repetitions**.

Compute and document:

- **Feasibility violations:** count of negative allocations, allocations above demand, or stock overages. Expected 0 for valid methods.
- **Unit demand coverage:** `sum(x) / sum(d)` with clear convention for zero total demand; additionally report *per resource*.
- **Urgency-weighted coverage:** `sum(u_z * x_zr) / sum(u_z * d_zr)` (if denominator zero, mark N/A), with limitations because units and urgency scales are proxies.
- **Unmet high-urgency demand:** requested minus allocated for zones above a declared urgency threshold.
- **Fairness:** e.g., Jain's index on **per-zone fractional coverage**, `((sum f_z)^2)/(n * sum f_z^2)` over zones with nonzero demand, alongside min coverage and percentile/dispersion. This metric can be high even when everybody receives too little; never use it alone.
- **Latency:** measured wall-clock time excluding UI rendering, with timer methodology, hardware and solver conditions declared.
- **Dynamics:** allocation change after shock, shortage shift, and valid transition behaviour; delivery delay only if actual time simulation is built.
- **Optional simulated beneficiaries served:** only if conversion assumptions are explicit and applied consistently.

Output `experiments/results/*.csv` plus one machine-readable manifest recording seed, commit SHA, algorithm config and environment. Report mean/std, distributions, and cases where hybrid loses. No invented numeric findings.

---

## 6. Frontend UX specification

Design language: calm emergency-operations tooling, **not** gamified catastrophe imagery. Professional navy/charcoal, off-white surfaces, restrained teal, amber for caution and red only for urgent/invalid states. Accessible contrast and clear units. Landing and dashboard should feel like **one coherent product** with shared colors, typography, logo, navigation, and spacing tokens.

### 6.1 Information architecture — landing page first

**This is a product requirement, not an optional enhancement.** The first page a visitor sees is the **AidOS landing page**, never the raw dashboard. The landing page must explain the purpose and design of the project before the visitor begins the interactive simulation. The actual application must remain one obvious click away.

Required routes and navigation:

- **`/` → Landing page**, publicly accessible, frontend-only content (no backend required to read the page).
- **`/dashboard` → Interactive dashboard**, directly addressable by URL, with a real scenario/AI backend when its features are shown as working.
- **`/dashboard/allocate`, `/dashboard/simulate`, `/dashboard/evaluate`** may be nested routes or tab states; the choice is an implementation detail. Avoid creating navigation that hides the core simulation.
- Persistent **site header** on landing with AidOS wordmark/logo and an easily seen **`Launch Dashboard`** button. Repeat the primary CTA in the **hero section**. The nav CTA and hero CTA go to the **same `/dashboard` route**.
- Dashboard has obvious navigation back to **Home/About AidOS**, and internal navigation among Overview, Allocation, Simulation and Evaluation.
- The landing page must not demand signup, authentication, scrolling, or a tutorial completion before dashboard access.
- Direct navigation, refresh, and browser back/forward must work on both routes. Configure client-side routing and production fallback appropriately.

**Landing-page content — in recommended order:**

1. **Header/navigation:** AidOS logo/wordmark, anchor links such as `How It Works`, `AI Approach`, `About`, and a contrasting **Launch Dashboard** button.
2. **Hero:** succinct headline (e.g., *“Better decisions when resources are limited.”*); one-sentence product explanation; a primary **Launch Dashboard** CTA; optional `Explore How It Works` secondary action. Do **not** falsely claim deployment or lives saved.
3. **The challenge:** a clear and relatable explanation of multiple urgent requests competing for limited medical, water, nutrition and shelter supplies.
4. **How AidOS works:** a simple, preferably visual, 4-step flow: **load scenario → assess urgency → allocate with constraints → compare and adapt**.
5. **AI methodology:** honest, digestible explanations of **fuzzy urgency scoring**, **constraint-based optimization**, and **finite-state crisis updates**; note deterministic FCFS/greedy baselines. Explain AI techniques rather than using vague marketing labels.
6. **Product walkthrough:** three or four lightweight feature previews (crisis overview, allocation reasoning, dynamic events, policy comparison), captured from actual working UI once available; use neutral schematic placeholders during initial scaffolding, labelled as concept previews.
7. **Academic scope and trust:** explicitly identify this as a **CSCI218 UOWD student prototype / synthetic scenario simulator**, not a live emergency dispatch or medical decision system. Human oversight is required for real decisions.
8. **Final CTA/footer:** repeat **Launch Dashboard** and include project/team metadata when confirmed. Do not invent endorsements, affiliations beyond the course, or industry-partner validation.

**Copy direction:** concise and legible. Prioritize describing what the user can **actually do**; no inflated claims such as “AI guarantees fair distribution” or fictional statistics/testimonials. Before a capability is built, phrase it as a project goal or concept, not a finished claim. If a demo preview uses synthetic data, label it.

**Visual direction:** tasteful product landing page, not a generic SaaS template. Use a strong typographic hero, purposeful whitespace, soft data-inspired accents, and a polished diagram or mock preview of the dashboard. Avoid stock disaster imagery and decorative animations that impair readability or performance. Maintain good mobile/tablet layouts, keyboard focus styles, semantic sections, reduced-motion support when animating, and adequate color contrast.

### 6.2 Dashboard screens

1. **Scenario Overview (`/dashboard`)** — inventory KPIs, total requested vs. available, crisis zone tiles/table, selected scenario, run control.
2. **Allocation Workspace** — resource-by-zone matrix, unmet demand, urgency scores, policy selector, explanation drawer, commit action.
3. **Crisis Simulator** — timeline and event panel; inject new request/stock reduction/urgency escalation; transition history; recompute.
4. **Compare & Evaluate** — FCFS vs. greedy vs. AidOS charts, per-metric definitions, downloadable experiment runs; no fake metrics.
5. **Methodology** — short visual walkthrough of fuzzy sets, rules, constraints, baselines and limitations; helps viva and assessment. Can link from the landing page or appear as dashboard help.

### 6.3 Interaction contract

- Landing page is the **default route** with visible **Launch Dashboard** buttons in both navbar and hero; both navigate to `/dashboard`.
- Initial dashboard launch must have a one-click playable synthetic example.
- Every visual allocation number comes from actual backend result, not frontend placeholder.
- Show loading, error, empty, no-demand, all-satisfied, solver-failed states.
- Label whether a proposed plan is `candidate` or `committed`.
- Changes before committing are undoable or restorable through scenario reset.
- Use charts sparingly; tables are essential for auditability.
- Provide keyboard-accessible controls and clear accessible labels.
- Avoid misleading claims such as "lives saved" without a validated model.

---

## 7. Technology and architecture decisions

### Recommended stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | React + TypeScript + Vite + React Router | Landing page and deep-linkable interactive dashboard |
| Styling | Tailwind CSS or small design-token CSS system (choose one) | Consistent, maintainable visual system |
| Charts | Recharts (or equivalent; choose once) | Clear experiment charts |
| Backend/API | Python 3.11+ + FastAPI + Pydantic | Domain validation, quick typed APIs, interactive docs |
| Optimization | OR-Tools CP-SAT | Discrete, explainable hard constraints; no GPU |
| Fuzzy engine | Plain Python/Numpy (explicit membership/rules) | Makes actual logic auditable; avoid opaque black boxes |
| Storage | Versioned JSON scenarios + in-memory session state for MVP | Reproducibility; no DB overhead |
| Experiments | Python CLI + CSV/JSON outputs; pytest | Offline repeatable benchmark |
| CI | GitHub Actions (lint + tests) | Reliable delivery |

**Architecture principle:** domain and algorithms must run without React, browser, network, or mutable global state; FastAPI adapts input/output only. UI and experiments call the same engine.

### Request path

```text
React (landing page -> dashboard/scenario editor)
  -> FastAPI request validation (Pydantic)
  -> immutable ScenarioSnapshot
  -> FuzzyUrgencyEngine (score + rule traces)
  -> AllocationPolicy interface (FCFS / greedy / CP-SAT)
  -> ConstraintValidator + MetricsEvaluator
  -> policy result, decision traces, metrics, warnings
  -> React (comparison, audit table, explanations)

Crisis event -> FSM transition + next ScenarioSnapshot -> re-run selected policies
Experiment runner -> same engine, offline -> CSV/JSON evidence
```

### API contract (initial proposal)

- `GET /api/health` → status/version.
- `GET /api/scenarios` → built-in scenario manifests.
- `GET /api/scenarios/{id}` → validated fixture.
- `POST /api/urgency/evaluate` → fuzzy urgency + trace for one zone.
- `POST /api/allocations/compare` → on **one snapshot**, FCFS, greedy, AidOS result + metrics + solver metadata.
- `POST /api/simulation/transition` → current snapshot/state + event; returns new snapshot/state and event record.
- `POST /api/allocations/commit` → selected candidate + matching snapshot hash; applies once or rejects stale/duplicate commit.

Use `/api` prefix consistently, typed schemas, enums for policy ID/state, and stable error responses. Avoid server-side sessions until genuinely necessary. Version JSON schema; API request examples must match tests.

### Data invariants

- Integers only for kit allocations; no fractional boxes.
- Stock/demand are never negative.
- Every allocation resource ID is known and belongs to exactly one resource type.
- `allocated[z,r] <= requested[z,r]` and `sum_z allocated[z,r] <= stock[r]`.
- Comparison never mutates the input snapshot.
- Committing an allocation requires the same snapshot hash/step and an idempotency key.
- Score and explanations must correspond to the same input snapshot.
- Identical seed + config + engine version gives identical allocations and urgency scores (excluding timing).
- Failed validation returns a useful error, not a success-looking empty allocation.

---

## 8. Target repository structure

This is the **proposed** structure; don't create large empty modules without a reason. Make minimal functional vertical slices and expand as each milestone becomes real.

```text
AidOS/
├── README.md                          # setup, quickstart, demo, academic scope
├── CLAUDE.md                          # primary Claude Code instructions; link here
├── AGENTS.md                          # Codex instructions; link here
├── AidOS project info.md              # THIS canonical project specification
├── .gitignore
├── .env.example                      # no real secrets
├── .github/
│   └── workflows/ci.yml
├── apps/
│   ├── api/
│   │   ├── pyproject.toml
│   │   └── aidos/
│   │       ├── main.py
│   │       ├── api/
│   │       │   ├── routes_scenarios.py
│   │       │   ├── routes_allocation.py
│   │       │   ├── routes_simulation.py
│   │       │   └── schemas.py
│   │       ├── domain/
│   │       │   ├── models.py
│   │       │   ├── validation.py
│   │       │   └── snapshots.py
│   │       ├── ai/
│   │       │   ├── fuzzy.py           # real membership functions/rules
│   │       │   ├── constraints.py     # CP-SAT model
│   │       │   ├── policies.py        # common interface
│   │       │   ├── baseline_fcfs.py
│   │       │   └── baseline_greedy.py
│   │       ├── simulation/
│   │       │   ├── fsm.py
│   │       │   ├── events.py
│   │       │   └── reducer.py
│   │       ├── evaluation/
│   │       │   ├── metrics.py
│   │       │   ├── runner.py
│   │       │   └── exports.py
│   │       └── config/
│   │           └── fuzzy_rules.json
│   └── web/
│       ├── package.json
│       ├── vite.config.ts
│       ├── tsconfig.json
│       └── src/
│           ├── main.tsx
│           ├── app/App.tsx            # app shell + router (/, /dashboard)
│           ├── app/Router.tsx         # route definitions / fallback
│           ├── api/client.ts
│           ├── api/types.ts
│           ├── components/
│           │   ├── SiteHeader.tsx     # wordmark + global Launch Dashboard CTA
│           │   ├── LandingHero.tsx    # explainer + hero Launch Dashboard CTA
│           │   ├── HowItWorks.tsx
│           │   ├── MethodologyPreview.tsx
│           │   ├── SiteFooter.tsx
│           │   ├── ScenarioSelector.tsx
│           │   ├── InventoryPanel.tsx
│           │   ├── ZoneTable.tsx
│           │   ├── AllocationMatrix.tsx
│           │   ├── ExplainabilityPanel.tsx
│           │   ├── EventTimeline.tsx
│           │   └── PolicyComparison.tsx
│           ├── pages/
│           │   ├── Landing.tsx        # default / route, project explanation
│           │   ├── DashboardLayout.tsx # dashboard shell + Home navigation
│           │   ├── Overview.tsx
│           │   ├── Allocate.tsx
│           │   ├── Simulate.tsx
│           │   └── Evaluate.tsx
│           └── styles/tokens.css
├── data/
│   ├── scenarios/
│   │   ├── triage-demo-001.json
│   │   ├── no-scarcity.json
│   │   ├── late-critical-arrival.json
│   │   └── zero-stock.json
│   └── README.md                      # provenance: all synthetic unless proven otherwise
├── experiments/
│   ├── generate_scenarios.py
│   ├── run_benchmarks.py
│   ├── configs/
│   └── results/                      # sample manifests; bulk generated files gitignored
├── tests/
│   ├── unit/test_fuzzy.py
│   ├── unit/test_constraints.py
│   ├── unit/test_baselines.py
│   ├── unit/test_fsm.py
│   ├── unit/test_metrics.py
│   └── integration/test_api_flow.py
├── docs/
│   ├── report/AidOS_Group_Project_Report.docx
│   ├── architecture.md
│   ├── algorithm-design.md
│   ├── experimental-protocol.md
│   ├── demo-runbook.md
│   ├── contribution-log.md
│   ├── rubric-checklist.md
│   ├── api-contract.md
│   └── decisions/
│       └── 0001-hybrid-ai-and-synthetic-scenarios.md
└── scripts/
    ├── smoke_test.py
    └── export_report_assets.py
```

Do **not** allow `apps/web/` to implement its own allocation logic. There must be one canonical backend engine.

---

## 9. Delivery stages with acceptance gates

| Stage | Owner | Deliverables | Gate / proof |
|---|---|---|---|
| 0. Groundwork | Claude Code | Repo, docs, environment, scenario schema, test harness, initial `/` + `/dashboard` route skeleton | Fresh clone startup; fixture validated; landing CTA reaches dashboard route |
| 1. Vertical slice | Claude Code | Landing page explains project → CTA opens dashboard → scenario → fuzzy scoring → FCFS allocation → API → minimal UI | Both routes reload/deep-link correctly; real backend data visible in dashboard |
| 2. AI implementation | Claude Code | Documented fuzzy rules, CP-SAT solver, greedy baseline, explanations | Invariants and golden-case unit tests pass |
| 3. Dynamic simulation | Claude Code | FSM, event injection, snapshot versioning, commit/recompute | Event changes outcome and never double-consumes stock |
| 4. Evaluation | Claude Code | Experiment runner, seeds, CSV, metric definitions, comparisons | Repeatable runs with mean/std; honest result tables |
| 5. Professional UI & demo | Claude Code + Codex polish | Polished landing page, shared design system, full dashboard, state handling, charts, demo runbook | Home-to-dashboard-to-crisis-to-comparison live demo works without resets/hardcoded outputs |
| 6. Submission package | Team, Codex QA | Report figures/code excerpts, repo README, contribution evidence, viva prep | Rubric cross-check; placeholders replaced only with evidence |

Suggested work order: **scaffold both routes + landing-page information architecture first** → backend correctness → one working dashboard vertical slice → simulation → experiments → full design polish → report finalization. Landing-page copy can be static from day one; *dashboard claims/results must not pretend to be live* until connected to the real engine.

### Git workflow

- `main` stays runnable; small issue-scoped feature branches.
- Commit by each actual student contributor under their own identity; AI tools do **not** invent individual authorship.
- For material decisions, add a short `docs/decisions/NNNN-*.md` record.
- At every milestone: update `README`, change log, tests, and `docs/contribution-log.md` with factual entries.
- No fabricated commits, stakeholder meetings, approvals, screenshots, results, or external validation.

---

## 10. Claude Code / Codex operating protocol

### Source of truth hierarchy

1. CSCI218 official assessment guidelines + instructor clarifications.
2. Selected Project C description from the provided Dubai Humanitarian spreadsheet.
3. **This document** for approved working design choices.
4. Accepted architecture decision records, tests, and API contract.
5. UI aesthetic choices and personal agent preferences.

When conflict occurs, **flag it explicitly** and make the smallest correct adjustment; do not quietly reinterpret instructor requirements. Confirm institutional AI-assistance policy before submitting AI-authored content.

### Claude Code — primary builder instructions

- At session start: read this entire file, `README.md`, `docs/architecture.md` (if present), and recent open issues.
- Inspect actual repository/files before altering paths or rewriting code. State a brief task plan and acceptance criteria.
- Implement in **vertical slices**: schema → domain → algorithms → API → frontend integration → test.
- Make real, explainable algorithm choices. Fuzzy logic and solver must not be mocked in final code.
- Prefer boring dependencies, deterministic test fixtures, and modular named functions.
- Before a feature is "done": run unit tests, type/lint checks where configured, an end-to-end smoke test, and report failures truthfully.
- Prevent hidden coupling: UI imports only API types/client, policies implement common domain interface, metrics are shared.
- Do not overbuild: no auth, cloud deployment, AI agent swarm, or RL until core milestones pass and the team approves.
- Do not place synthetic benchmark outputs in the report as real-world operational proof.
- End each implementation session with: (1) files changed, (2) commands actually run and results, (3) known gaps, (4) next one or two tasks.

**Suggested first Claude Code prompt:**

```text
You are lead engineer for AidOS, a CSCI218 academic humanitarian resource-allocation simulator.
Read "AidOS project info.md" completely and use it as the working specification.
First audit the current repo (if empty, say so), then implement ONLY Stage 0 and the
smallest Stage 1 vertical slice. Start with a polished but lightweight landing page
at / explaining AidOS, its purpose, 4-step workflow and academic scope, with
visible Launch Dashboard CTA buttons in both navbar and hero linking to /dashboard.
Add proper routing, a Home link in the dashboard, and a minimal dashboard showing
live backend allocations. Implement validated synthetic scenario schema, deterministic
FCFS baseline, health/scenario/allocation APIs, and tests. Do not build a fake
dashboard or implement CP-SAT yet.
Create CLAUDE.md and AGENTS.md pointing to the canonical spec.
Use concise maintainable files, include a reproducible setup README, and run tests.
Afterward report what exists, exact commands executed, and remaining work.
```

### Codex — smaller scoped work

Good tasks: targeted unit tests; fix a failing type check; add responsive layout; enhance table accessibility; improve API error states; benchmark plotting; clean docs; verify a rubric checklist; perform code review with concrete file/line suggestions.

Avoid two AI coding agents modifying the same files simultaneously without worktrees/branches. **Claude Code owns core domain, fuzzy system, solver, simulation FSM, and architecture.** Codex edits only a clearly assigned module/branch and must run relevant tests.

**Suggested Codex task template:**

```text
Read "AidOS project info.md" and relevant source/tests first.
Scope: [ONE specific issue and file set]. Do not change architecture or core algorithms.
Acceptance criteria: [observable outcomes].
Implement the smallest patch, add/update tests, run relevant checks, and report
changed files, test output, and any remaining limitations. Do not fabricate data.
```

### Team coordination checklist

- Assign 4–5 real student owners, each owning a *substantive* code/report/experiment deliverable and able to explain all algorithms.
- Use pull requests or reviewed commits and small, verifiable task tickets.
- Once/week short internal walkthrough: each student explains a module they did *not* build.
- Maintain evidence for each student's 1–2 page reflection (specific code, tests, decisions, challenges).
- Instructor approval/registration and optional partner contact must be recorded only when genuinely confirmed.

---

## 11. Tests, quality gates, and anti-fabrication rules

### Navigation/UI acceptance tests

- Initial visit to `/` shows the landing page and explains AidOS.
- Header and hero **Launch Dashboard** links both open `/dashboard`; keyboard activation works.
- Dashboard has a visible route back to `/`.
- Refresh and direct deep-link to `/dashboard` work.
- Loading or failure of the API does **not** prevent the landing page from rendering; dashboard shows a clear error state.
- The landing page is readable on mobile and includes explicit academic/synthetic-use context.
- No placeholder metrics or fabricated performance claims are presented as experimentally verified results.

### Must-pass domain tests

- No shortage: every demand is met, exactly, when stock is sufficient.
- Shortage: never exceed stock; unmet need correctly computed.
- Zero stock: zero allocations, sensible explanations.
- Zero demand: no divide-by-zero in metrics; state marked N/A where appropriate.
- Single zone: behavior is straightforward and fully auditable.
- New critical zone arrives after an initial decision; recompute correctly from *current valid snapshot*.
- Duplicate commit or stale snapshot hash rejected.
- All policies respect stock/demand bounds.
- Different resources never substitute for one another.
- Tie-break rules make baseline results deterministic.
- Fuzzy input boundaries 0/10 and rule coverage tested.
- Same fixed seed gives same scenario/result; timing may vary.
- API validation errors not masked as successful results.

### Engineering gates

- API tests via pytest; frontend TS type check and production build.
- CI tests on pull requests or `main`, assuming project permits GitHub Actions.
- No secrets in repository; no live personal/medical case records.
- Document dependency versions; fix seeds and scenarios.
- Fuzzy scoring and allocation mathematics in `docs/algorithm-design.md` with executable examples.
- Benchmark input/output schema and metric formulas in `docs/experimental-protocol.md`.
- Identify every graph/report screenshot with source experiment record and git SHA.
- No benchmark result invented by Claude Code, Codex, or this spec.

---

## 12. Report and grading alignment

Official report structure in the CSCI218 document (keep this ordering):

1. **Executive summary** — problem, proposed/implemented methods, *actual* results once available, contributions.
2. **Motivation** — humanitarian allocation dilemma, project objectives, AI rationale and limits.
3. **Technical requirements** — features, constraints, hardware/software, acceptance tests.
4. **Main constructs** — entities, fuzzy logic, CSP, FSM, objectives, architecture, baselines.
5. **Implementation** — exact code modules, screenshots, diagrams, build steps; replace placeholders after coding.
6. **Experiments and results** — fair baselines, controlled repeatable runs, metrics, tables and real numbers.
7. **Limitations, difficulties and constraints** — synthetic assumptions, policy fairness, lack of validation, runtime, scope.
8. **Conclusion and discussion** — evidence-based findings, limitations, future work.
9. **References** — official project guidelines, Project C spreadsheet, and legitimately consulted technical/academic sources.
10. **Appendices** — repo URL, individual contribution table, extras; *if approved bonus*: meeting log and mentor feedback.

**Weighting:** group problem motivation 10%, technical depth 25%, implementation 15%, results 10%, report 10%, demo 10%; individual viva 10% and reflection 10%. Group project contributes **20% of the subject mark**, not a standalone guaranteed 20/20. For the top band, prioritize justified math, constraints, baseline comparisons, reliable demo, and genuine analysis over breadth.

### Evidence map / placeholders that must be filled

| Report claim | Evidence to capture from real work |
|---|---|
| Fuzzy logic is functional | rule config + unit tests + actual score traces |
| Solver respects constraints | formalization + validator tests + solver outputs |
| Handles dynamic shocks | before/after snapshots + event log + video/demo screenshots |
| Outperforms a baseline | actual repeated benchmark data (may be mixed/negative) |
| App is reproducible | tagged Git commit, pinned dependencies, README setup tests |
| Humanitarian impact | simulation relevance statement; never claim operational benefit without external validation |
| Student work distribution | actual authorship, commit history, contribution statement |

---

## 13. Risks and decisions awaiting confirmation

| Risk / unknown | Why it matters | Next action |
|---|---|---|
| Instructor approval or registration | Topic C and any extensions must match course process | Confirm status and whether fuzzy+CSP+FSM is accepted |
| AI-assistance policy | Claude Code and Codex usage must comply with subject rules | Check current subject descriptor and disclose appropriately |
| Exact due date | Source says Moodle/Turnitin only | Copy real due dates into README/project tracker |
| Actual team membership | 4–5 same-lab students; each has viva/reflection | Record accurate names/IDs and assign work |
| External mentor status | Optional bonus is conditional, not automatic | Do not add partner claims until approved |
| Algorithm comparison confound | Linear urgency objective can tie with greedy policy | Include meaningful fairness/constraints and report ties honestly |
| Ethical validity | Urgency inputs are hypothetical and potentially biased | Label simulations; human oversight; state proxy limits |
| UI scope creep | Excess polish can delay core algorithm testing | Freeze MVP before optional features |
| Dataset realism | Synthetic scenarios may not reflect real logistics | Publish generation assumptions and limitations |

---

## 14. Handoff and immediate next actions

**Now**

1. Add this file at repository root as `AidOS project info.md`.
2. Add the starter report at `docs/report/AidOS_Group_Project_Report.docx`.
3. Create Git repository and commit this spec/report as planning artifacts under the *actual* student's account.
4. Confirm project registration, deadline, team count, and permitted AI-tool use.
5. Run the **first Claude Code prompt** above for Stage 0/1.

**When Stage 1 passes:** move to fuzzy rule design and solver with exact mathematical definitions, then event-driven simulator, then experiments, then dashboard polish and final report.

**The real success condition:** when a lecturer changes a crisis input during a live demonstration, AidOS produces a new *valid* allocation, explains its decision, shows measurable trade-offs versus baseline policies, and every team member can explain the underlying algorithms.

---

## Appendix — original supplied source files and provenance

1. `CSCI218_Project_Guidelines_Grading_Criteria_AUT26(1).docx` — CSCI218 official project instructions, Autumn 2026. Sections 1, 3, 4, 5, 6, 7; appendices A–C.
2. `Dubai_Humanitarian_AI_Student_Projects.xlsx` — sheet `Proposed Projects`, row **Project ID C**. Used for the original stakeholder problem statement, suggested AI methods, prototype type and complexity.
3. `CSCI218_Presentation_Guidelines_Grading_Criteria_AUT26.docx` — separate **10% group presentation** assessment, not automatically the same project deliverable.

**Document-maintenance policy:** Any actual implementation deviation from this spec should be captured in an Architecture Decision Record and reflected in the report. A proposed plan is not proof of implementation.
