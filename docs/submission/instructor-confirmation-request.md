# Request for instructor confirmation

A short note the team can send to (or discuss with) the lab instructor. **None of these items has been confirmed.** The report states each one as pending. The longer background is in `instructor-review.md`.

---

Dear [instructor name],

Our group ([group / member names]) would be grateful for your confirmation on three points about our CSCI218 project, AidOS (Topic 11, Dubai Humanitarian Project C: Emergency Resource Allocation Simulation).

**1. Fuzzy inference method: zero-order Sugeno instead of Mamdani.**
Our urgency engine uses a fully documented zero-order Takagi–Sugeno system: three inputs with low/medium/high sets, 27 rules, product firing strength, and a weighted average of constant outputs. We moved away from Mamdani min/max with centroid because we measured it on our own rule base. Over 52,920 single-rating increases, Mamdani lowered the urgency score 1,062 times (2.0%, by up to 0.9 points). In other words, a zone could become less urgent when its situation got worse. Product-Sugeno never did, and we can show why it cannot on this rule base. We still report Mamdani as a measured comparison. *Is a documented Sugeno system acceptable for the fuzzy-logic component?*

**2. Topic registration and technique combination.**
We are working on Topic 11, Project C, combining:
- fuzzy logic (urgency scoring);
- constraint optimisation with Google OR-Tools CP-SAT, with an urgency-first and a coverage-floor ("balanced") model;
- a finite-state simulation of crisis events.

*Could you confirm that our registration and this combination are recorded as approved?*

**3. Use of AI tools.**
The project guidelines refer to the subject descriptor for the rules on AI tools. Parts of the prototype were developed with an AI coding assistant, and we intend to disclose this in the report and in our individual statements. *Could you point us to the applicable rules, or confirm what form the disclosure should take?*

Thank you for your time.

[names]

---

## Risk if an answer is negative

| Item | If not approved | Effort to change |
|---|---|---|
| Sugeno vs Mamdani | Switch the engine to Mamdani, or present Mamdani as the primary method | **Substantial.** The engine, its tests, the explanations and the dashboard are built on Sugeno's exact additive contributions. Mamdani's non-monotonic dips would also need a mitigation. The benchmark would have to be re-run (allocations depend only on the order of the scores, so most plans would be similar, but they would have to be re-measured). Raise this as early as possible. |
| Technique combination | Add or replace a technique | Depends on the request; potentially substantial. |
| AI-tool disclosure | Revise the disclosure wording or attribution | Small for the documents; the per-member Git history and reflections must be truthful in any case. |
