# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Two audiences, weighted equally (confirmed 10 Nov 2026):

- **Lecturer and markers** of CSCI218 at UOWD. They judge the live demo and viva. They need to see what the AI techniques are, that they run for real, and where their limits are.
- **General visitors with no course context.** They should understand the problem and the product from the landing page alone.

Inside the dashboard the user plays a **simulated emergency coordinator**. They load a synthetic scenario, compare demand against depot stock, run allocation policies, inspect explanations, inject disruptions and commit plans.

## Product Purpose

AidOS is an academic simulator. It helps a simulated coordinator decide how to split scarce relief supplies (medical kits, water packs, shelter kits, nutrition packs) between competing crisis zones, and to explain each decision. Success means a reproducible, explainable allocation that respects hard stock limits and can be compared fairly against baseline policies.

## Positioning

AidOS combines three explainable techniques:

- **fuzzy urgency scoring**, which turns imprecise severity, vulnerability and time-criticality into a 0–100 score with an inspectable rule trace;
- **constraint-based allocation** (OR-Tools CP-SAT), which allocates whole units without exceeding stock or demand;
- **finite-state crisis updates**, where events create new snapshots and stock is consumed only on an explicit commit.

It is measured honestly against first-come-first-served and urgency-greedy baselines, which may tie with or beat it. It is not an LLM chatbot, an ML predictor or a dispatch service.

## Operating Context

The product runs in a live classroom demo and the viva. The demo story is in `AidOS project info.md` Section 1. It is also read as part of the report submission. It runs locally: a React/Vite frontend talks to a FastAPI backend. There are no logins and no database.

## Capabilities and Constraints

- Canonical spec: `AidOS project info.md`. It overrides this file.
- One canonical engine, in the backend. The frontend never computes allocations or scores, and every number shown in the dashboard comes from the backend.
- Integer allocations with `0 <= x <= demand` and `sum <= stock`. No substitution between resources.
- Synthetic data only. Every scenario declares `"synthetic": true`.
- Delivered in stages. Stages 1 and 1.5 cover the landing page, the dashboard, scenario fixtures, the scenarios API and the FCFS baseline. Stage 2 adds fuzzy urgency scoring, the CP-SAT allocator, the urgency-greedy baseline and the comparison. Stage 3 adds the crisis simulator: events, the session state machine, recomputation, dispatch with a ledger, and replay. Stage 4 adds the evaluation framework and its results; they describe behaviour on synthetic scenarios and must never be presented as humanitarian effectiveness.
- Landing page at `/`, readable without the backend. Dashboard at `/dashboard`, deep-linkable.

## Brand Commitments

- Name: **AidOS**. Tagline direction: "When every resource matters, every decision counts."
- Tone: calm emergency-operations tooling, never gamified catastrophe imagery, never hype.
- No claims of deployment, lives saved, endorsements, partners or results that experiments have not produced.

## Evidence on Hand

- The project specification and the synthetic scenario fixtures in `data/scenarios/`.
- **Absent, and must not be fabricated:** team member names (not confirmed yet), instructor approval, industry partner involvement, benchmark results, testimonials, screenshots of real deployments.

## Product Principles

1. Truth over polish: label every planned capability as planned, and every dataset as synthetic.
2. Auditability first: tables and traces beat decorative charts.
3. Human decides: AidOS suggests, and the coordinator commits.
4. Same scenario, same constraints, same metrics for every policy.

## Accessibility & Inclusion

WCAG 2.1 AA: 4.5:1 text contrast, visible keyboard focus, semantic landmarks, reduced-motion support, no meaning carried by colour alone. Must be usable on mobile without horizontal scroll.
