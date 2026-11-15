# Items for instructor review

None of the items below has been confirmed by the instructor. They are listed so the team can raise them; this document does not claim any approval.

## 1. Fuzzy inference method: zero-order Sugeno instead of Mamdani (decision record 0004)

**What we use.**
- Three ratings (severity, time criticality, vulnerability, 0–10), each with low/medium/high sets. These are trapezoid/triangle sets whose degrees sum to 1.
- 27 rules covering every combination.
- A rule's strength is the product of its antecedent degrees.
- The urgency score is the strength-weighted average of the rules' constant outputs (12.5, 37.5, 62.5, 87.5).

**Why not Mamdani** (the specification's stated preference):
- **Monotonicity.** Measured on our own rules over 52,920 single-rating increases, Mamdani min/max with centroid lowered the score 1,062 times (2.0%, up to 0.9 points). Sugeno with product never did. That is guaranteed by construction: the score is an expectation over a distribution that shifts towards higher terms as a rating rises, and the rule table never lowers urgency. A zone whose situation worsens can therefore never become less urgent.
- **Exact explanations.** The rule contributions sum to the score.
- **Reproduce:** `experiments/fuzzy_method_comparison.py`.

**What we give up.** The visual of clipped output sets and a centroid, and the use of output membership functions.

**Sensitivity** (Stage 5, `docs/evaluation/stage5-supplementary.md`):
- Shifting the membership breakpoints by ±1 point changes the zone order in about half of the scenarios, but moves only 2–6% of allocated units.
- The rule-output values do not affect allocations at all.
- A min t-norm variant reintroduces non-monotonic dips.

**Question for the instructor.** Is a documented zero-order Sugeno system acceptable for the "fuzzy logic" component, given the specification allowed it "if fully documented"?

## 2. Technique combination and topic registration

- **Topic.** Topic 11 (Dubai Humanitarian, Project C).
- **Techniques.** Fuzzy logic (urgency), constraint optimisation (OR-Tools CP-SAT allocation with a coverage-floor variant), and a finite-state simulation of crisis events.
- **Confirm:** registration status, team composition and that this combination is accepted.

## 3. Optimiser equivalence

Under the urgency-first objective, CP-SAT provably returns the urgency-greedy plan (`docs/algorithms/greedy-vs-cpsat-analysis.md`). The project reports this openly. CP-SAT's added value lies in proven optimality, the coupled balanced mode, and extensibility to coupling constraints. Ask whether this framing is acceptable, or whether a transport-capacity extension (currently a documented proposal with a counterexample, not implemented) is expected.

## 4. Coverage-floor default (25%)

A design choice, not a validated policy. The Stage 5 sweep shows a 10% floor already removes starvation in our synthetic scenarios, and higher floors trade urgency-weighted coverage for equity monotonically. The default was not re-tuned on the benchmark.

## 5. AI-assistance policy

The guidelines defer to the subject descriptor, which was not available here. The prototype was built in AI-assisted sessions. Disclosure, and the attribution of work in the report and the reflections, must follow the descriptor.

## 6. Industry bonus

No partner engagement has taken place. Any claim of Dubai Humanitarian involvement would be false unless arranged and documented (meeting log, mentor form).
