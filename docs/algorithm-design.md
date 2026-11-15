# Algorithm design

> Canonical source: `AidOS project info.md` Section 5. The detailed, implemented design lives in `docs/algorithms/`.

| Topic | Document | Status |
|---|---|---|
| Allocation problem: sets, variables, hard constraints, objectives, scaling, worked example | [`algorithms/allocation-formulation.md`](algorithms/allocation-formulation.md) | Implemented (Stage 2) |
| Fuzzy urgency scoring: inputs, membership functions, 27 rules, zero-order Sugeno inference, why not Mamdani | [`algorithms/fuzzy-logic.md`](algorithms/fuzzy-logic.md) | Implemented (Stage 2) |
| CP-SAT engine, pipeline, solver statuses, explanations, edge cases, metrics, experiment interface | [`algorithms/cp-sat-allocation.md`](algorithms/cp-sat-allocation.md) | Implemented (Stage 2) |

## Policies

| ID | What it does | Uses urgency | Uses a solver |
|---|---|---|---|
| `fcfs` | serves zones in arrival order | no | no |
| `greedy` | serves zones in urgency order | yes | no |
| `aidos` | maximises urgency-weighted units (CP-SAT) | yes | yes |
| `aidos_balanced` | first maximises a common coverage floor per resource (up to the 25% target, reduced when stock cannot support it), then maximises urgency-weighted units (CP-SAT) | yes | yes |

`aidos` and `greedy` always return the same plan, because the urgency-first objective is linear, resources are separable and both break ties by arrival order. This is the specification's planned experimental control; the full proof, exhaustive checks and the conditions under which they would differ are in [`algorithms/greedy-vs-cpsat-analysis.md`](algorithms/greedy-vs-cpsat-analysis.md).

## Evaluation

[`evaluation/policies.md`](evaluation/policies.md), [`metric-definitions.md`](evaluation/metric-definitions.md), [`experimental-protocol.md`](evaluation/experimental-protocol.md), [`results.md`](evaluation/results.md), [`scientific-review.md`](evaluation/scientific-review.md).

## Crisis simulation

| Topic | Document | Status |
|---|---|---|
| Session state machine, atomic steps, versions, determinism | [`simulation/state-machine.md`](simulation/state-machine.md) | Implemented (Stage 3) |
| Event types, inventory and dispatch semantics, explanations, executed example | [`simulation/events.md`](simulation/events.md) | Implemented (Stage 3) |
| Replay, export format, import verification | [`simulation/replay.md`](simulation/replay.md) | Implemented (Stage 3) |
| Demo scenarios and the live-demo script | [`simulation/demo-scenarios.md`](simulation/demo-scenarios.md) | Implemented (Stage 3) |
