# 0004 — Stage 2: fuzzy method, allocation objective and policy set

Date: 11 November 2026. Status: accepted.

## Context

Stage 2 implements the fuzzy urgency engine and the CP-SAT allocator. The specification (`AidOS project info.md` Section 5) leaves three choices open or stated as preferences.

## Decisions

### 1. Zero-order Sugeno with product AND, not Mamdani min/max

The specification prefers Mamdani with centroid defuzzification "or a fully documented zero-order Sugeno design", and says never to swap silently. This record is the explicit swap.

Measured on the shipped membership functions and rules (`experiments/fuzzy_method_comparison.py`): Mamdani min/max lowered the score on 1,062 of 52,920 single-rating increases (2.01%, worst 0.89 points); Sugeno with min, 968 (worst 2.5); Sugeno with product, 0. Product-Sugeno is monotone by construction given a Ruspini partition and an order-preserving rule table. Its rule contributions also sum exactly to the score.

The choice was presented with these numbers to the team member running the build session, who selected Sugeno. The instructor has not been asked; the specification (Section 0) says the final technique combination should be confirmed with them.

Cost: the Mamdani "clipped sets and centroid" visual is not available; scores are confined to 12.5–87.5.

### 2. Inputs are severity, time criticality and vulnerability

The Stage 2 brief suggested "affected population" as a possible input. The specification's three ratings are used instead, because they are the canonical schema and a fourth input would triple the rule base. `population` remains a descriptive field. No schema change was needed.

### 3. Primary objective: urgency-weighted units (the specification's MVP objective)

`max Σ w_r (p_z + ε) x[z,r]`, with exact integer coefficients (scores have 4 decimals and are multiplied by 10,000). A coverage-fraction objective (`… / d[z,r]`) was considered and rejected because it rewards small requests over urgent ones. Details in `docs/algorithms/allocation-formulation.md` section 4.

Known consequence: the optimum always equals the urgency-greedy plan (same order, same tie-break). The specification anticipates this as an experimental control.

### 4. A fourth policy ID, `aidos_balanced`

The specification lists three policies and a "named balanced mode". The balanced mode is exposed as its own policy ID so it appears as a separate, comparable row everywhere. It guarantees a per-resource coverage floor (target 25% of each request, reduced when stock cannot support it) before optimising urgency. It does not guarantee equal or proportional shares.

### 5. Deterministic tie-breaking by a second objective

Ties are resolved by a lexicographic second solve that prefers earlier arrival, rather than by solver internals. With one worker and a fixed seed, the optimal plan is unique and reproducible.

### 6. API shape

- `POST /api/urgency/evaluate` accepts a whole scenario or one set of ratings (the specification proposed one zone).
- `POST /api/allocations/compare` serves both "run AidOS" and "compare with baselines". No separate AI-allocation endpoint was added, so results in one response always share a snapshot and urgency scores.
- The response gained fields (`urgency`, `validation`, `solver`, extra metrics). Existing Stage 1 fields kept their names and meaning. `501 policy_not_implemented` is no longer returned.

## Consequences

- The landing page and docs say "zero-order Sugeno", never "Mamdani".
- The evaluation (Stage 4) must report the AidOS/greedy tie as a result, and treat balanced mode as the variant where optimisation changes the plan.
