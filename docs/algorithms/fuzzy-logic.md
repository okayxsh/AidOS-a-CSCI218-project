# Fuzzy urgency engine

Code: `apps/api/aidos/ai/fuzzy.py`. Parameters and rules: `apps/api/aidos/config/fuzzy_rules.json` (version 1.0). Tests: `tests/unit/test_fuzzy.py`.

The engine turns three imprecise ratings of a zone into one urgency score from 0 to 100, and keeps a full record of how it got there. The score is an **input** to allocation. It never authorises a plan that breaks a stock or demand limit.

Everything here is a design assumption for an academic simulation. The membership functions, rules and bands are not validated humanitarian or medical triage standards.

## 1. Inputs

Each zone carries three ratings, each a number from 0 to 10, already present in the scenario schema:

| Input | Meaning in the simulation |
|---|---|
| `severity` | how bad the situation in the zone is |
| `time_criticality` | how quickly help is needed |
| `vulnerability` | how fragile the affected population is |

"Affected population" is not an input. The schema has an optional `population` field, but the specification (section 5.1) defines urgency from these three ratings, and adding a fourth input would change the rule base from 27 to 81 rules. The field stays descriptive.

Normalisation: each rating is also reported as `rating / 10` (0 to 1) in the trace. Inference uses the raw 0–10 value.

Invalid input is rejected, never guessed: a missing rating, a non-number, NaN or infinity, or a value outside 0–10 raises `FuzzyInputError` (HTTP 422 through the API).

## 2. Membership functions

All three inputs use the same three sets.

| Set | Shape | Points | Full membership | Fades |
|---|---|---|---|---|
| low | trapezoid | (0, 0, 2, 5) | 0 to 2 | 2 → 5 |
| medium | triangle | (2, 5, 8) | at 5 | rises 2 → 5, falls 5 → 8 |
| high | trapezoid | (5, 8, 10, 10) | 8 to 10 | rises 5 → 8 |

```text
degree
1.0 |‾‾‾‾‾\        /\        /‾‾‾‾‾
    |      \      /  \      /
0.5 |       \    /    \    /
    |  low   \  / med  \  /  high
0.0 |_________\/________\/_________
    0    2    5         8    10
```

Overlap: low and medium overlap on 2–5; medium and high on 5–8. At every rating the three degrees **sum to exactly 1** (a Ruspini partition). So a rating of 3.5 is half low and half medium; a rating of 7 is one-third medium and two-thirds high. A test checks this at 1,001 points per input.

## 3. Rule base

27 rules, one for every combination of (severity, time criticality, vulnerability), so no input can fall into a gap. IDs are R01–R27 in the config file.

Urgency when vulnerability is **low or medium** (the two give the same result):

| severity ↓ / time criticality → | low | medium | high |
|---|---|---|---|
| **low** | low | low | moderate |
| **medium** | low | moderate | high |
| **high** | moderate | high | critical |

Urgency when vulnerability is **high** (one level up, capped at critical):

| severity ↓ / time criticality → | low | medium | high |
|---|---|---|---|
| **low** | moderate | moderate | high |
| **medium** | moderate | high | critical |
| **high** | high | critical | critical |

Example, as written in the config: R27 is `IF severity is high AND time criticality is high AND vulnerability is high THEN urgency is critical`.

Properties, each enforced by a test or by the config loader:

- **Complete:** all 27 combinations are covered; the loader refuses a config with a missing or duplicate antecedent.
- **Order-preserving:** raising any one input by one level never lowers the rule's output.
- **Vulnerability safeguard:** a highly vulnerable zone is never rated "low".

Limitation: low and medium vulnerability are treated alike. Only high vulnerability changes the outcome.

## 4. Inference: zero-order Sugeno

Each output term is a single number, the centre of its band:

| Urgency term | Rule output | Category band |
|---|---|---|
| low | 12.5 | 0 ≤ score < 25 |
| moderate | 37.5 | 25 ≤ score < 50 |
| high | 62.5 | 50 ≤ score < 75 |
| critical | 87.5 | 75 ≤ score ≤ 100 |

For one zone:

1. **Fuzzify.** Compute each rating's degree in low, medium and high.
2. **Fire.** A rule's strength is the **product** of its three antecedent degrees.
3. **Combine (defuzzify).** $\text{score} = \dfrac{\sum_i \text{strength}_i \times \text{output}_i}{\sum_i \text{strength}_i}$

Because the degrees of each input sum to 1, the strengths of all 27 rules also sum to 1. The score is therefore a plain weighted average, and the rules' **contributions** (strength × output) add up to the score. The explanation "R26 contributes 38.9 of the 70.8 points" is arithmetic, not approximation.

**Resolution.** The score is rounded to 4 decimal places. Binary floating point otherwise leaves noise such as 25.000000000000004 where the exact answer is 25, which could flip a category at a band edge or decide a tie between two zones with identical ratings. Rounding removes that, and gives the allocation model coefficients that represent the score exactly. The contributions therefore sum to the score to within 0.00005.

The category is the band the score falls in; a score exactly on a boundary takes the more urgent band.

**Range.** Scores lie between 12.5 (all inputs fully low) and 87.5 (all fully high). The scale is 0–100, but the engine never returns the extremes, because every score is an average of band centres. This compresses differences at the top: any zone rated 8 or above on all three inputs scores 87.5.

## 5. Why Sugeno and not Mamdani

The specification prefers Mamdani min/max with centroid defuzzification, or a fully documented zero-order Sugeno design. Sugeno was chosen, after measurement, for one reason: **monotonicity**.

The requirement: raising a zone's severity, time criticality or vulnerability must never lower its urgency.

`experiments/fuzzy_method_comparison.py` uses the shipped membership functions and rules and counts how often a 0.25-point increase in one rating lowers the score, over a grid of the whole domain. Output on this project's configuration:

```text
method               steps   dips   share  worst dip
mamdani_min_max      52920   1062   2.01%     0.8947
sugeno_min           52920    968   1.83%     2.5000
sugeno_product       52920      0   0.00%     0.0000
```

Why Mamdani dips: max-aggregation keeps only the strongest rule per output term, and min keeps only the weakest antecedent. Raising a rating can lower the strength of the strongest rule for a term without the centroid gaining enough elsewhere, so the centroid moves slightly down. The effect is small (under 1 point) but real, and it would let a zone's urgency fall when its situation gets worse.

Why product-Sugeno cannot dip (a proof sketch):

- With a Ruspini partition and product, the 27 strengths form a probability distribution: the product of three independent distributions over {low, medium, high}.
- Raising a rating moves that input's distribution toward higher terms and never back (low loses to medium, medium to high).
- The rule table never decreases when an input's term rises (section 3).
- So the score, which is the expected rule output under that distribution, cannot decrease.

A test (`test_monotone_in_every_input`) confirms it on a grid; the argument above is why it holds everywhere.

What is given up: Mamdani's picture of clipped output sets and a centroid. In exchange the trace is exact and additive, which is easier to defend line by line.

## 6. Explanation returned for each zone

| Field | Content |
|---|---|
| `score`, `category` | the urgency and its band |
| `inputs`, `normalized` | the three ratings, raw and scaled to 0–1 |
| `memberships` | degree of each rating in low, medium, high |
| `activations` | every rule that fired: ID, text, strength, output, contribution; strongest first |
| `term_support` | share of total rule strength behind each urgency term |
| `explanation` | one readable sentence built from the fields above |

The explanation describes the computation. It does not claim that an input *caused* a real-world outcome, and it says nothing about allocation: why a zone received a quantity is explained separately, from the allocation model.

## 7. Worked example: Zone C of `triage-demo-001`

Ratings: severity 7, time criticality 7, vulnerability 5.

| Input | low | medium | high |
|---|---|---|---|
| severity 7 | 0 | 1/3 | 2/3 |
| time criticality 7 | 0 | 1/3 | 2/3 |
| vulnerability 5 | 0 | 1 | 0 |

Four rules fire (all with vulnerability = medium):

| Rule | severity, time | Output | Strength | Contribution |
|---|---|---|---|---|
| R26 | high, high | critical 87.5 | 2/3 × 2/3 × 1 = 0.444 | 38.89 |
| R17 | medium, high | high 62.5 | 1/3 × 2/3 × 1 = 0.222 | 13.89 |
| R23 | high, medium | high 62.5 | 2/3 × 1/3 × 1 = 0.222 | 13.89 |
| R14 | medium, medium | moderate 37.5 | 1/3 × 1/3 × 1 = 0.111 | 4.17 |
| | | | **1.000** | **70.83** |

Score 70.83, category **high**. The engine's sentence for this zone:

> Urgency 70.8 (high). Severity 7/10 is mostly high (0.67); time criticality 7/10 is mostly high (0.67); vulnerability 5/10 is mostly medium (1.00). 4 rules fired; the strongest, R26, fired at 0.44 and contributes 38.9 points.

The other two zones: Zone A (9, 9, 8) is fully high on all three, so only R27 fires and the score is 87.5 (critical). Zone B (6, 5, 7) fires four rules and scores 62.5 (high).

## 8. Tests

`tests/unit/test_fuzzy.py` covers: membership degrees at boundaries and overlaps; the partition summing to 1; rule completeness and unique IDs; the order-preserving rule table; rejection of broken configs; minimum, maximum and category boundaries; score range over all 1,331 integer inputs; contributions summing to the score; the hand-computed example above; monotonicity; determinism across repeated runs; rejection of missing, out-of-range, NaN, infinite and non-numeric inputs; and that the explanation matches the computation.

## 9. Limitations

- Parameters are chosen for interpretability, not fitted to data. A different, equally defensible set would give different scores.
- Scores are confined to 12.5–87.5 and saturate once all inputs are fully high.
- Low and medium vulnerability are not distinguished.
- The three ratings are themselves simulated; the engine cannot be more meaningful than its inputs.
