"""Reproduce the monotonicity measurement behind the choice of fuzzy method.

    cd apps/api
    uv run python ../../experiments/fuzzy_method_comparison.py

Uses the shipped membership functions and the shipped 27 rules, and compares three ways of
turning rule strengths into a score. For each it counts how often raising one rating by
0.25 (the other two held fixed) LOWERS the score, over a grid of the whole input domain.

  mamdani_min_max   AND = min, each output set clipped at the max strength of its rules,
                    centroid over 0..100. Output sets: triangles of half-width 12.5 centred
                    on the same four values the shipped engine uses.
  sugeno_min        AND = min, strength-weighted average of the rule outputs.
  sugeno_product    AND = product, strength-weighted average (the shipped method).

See docs/algorithms/fuzzy-logic.md for the interpretation.
"""

from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from aidos.ai.fuzzy import INPUT_TERMS, INPUTS, OUTPUT_TERMS, default_config  # noqa: E402

CONFIG = default_config()
CENTRE = {t: CONFIG.output_terms[t].value for t in OUTPUT_TERMS}
GRID_Y = range(0, 101)
HALF_WIDTH = 12.5


def degrees(ratings):
    return {
        n: {t: CONFIG.input_terms[n][t].degree(ratings[n]) for t in INPUT_TERMS} for n in INPUTS
    }


def strengths(ratings, combine):
    mu = degrees(ratings)
    return [(r.consequent, combine([mu[n][t] for n, t in r.antecedent])) for r in CONFIG.rules]


def sugeno(ratings, combine):
    fired = strengths(ratings, combine)
    return sum(CENTRE[c] * w for c, w in fired) / sum(w for _, w in fired)


def mamdani(ratings):
    level = dict.fromkeys(OUTPUT_TERMS, 0.0)
    for consequent, w in strengths(ratings, min):
        level[consequent] = max(level[consequent], w)
    num = den = 0.0
    for y in GRID_Y:
        m = max(min(level[t], max(0.0, 1 - abs(y - CENTRE[t]) / HALF_WIDTH)) for t in OUTPUT_TERMS)
        num, den = num + y * m, den + m
    return num / den


METHODS = {
    "mamdani_min_max": mamdani,
    "sugeno_min": lambda r: sugeno(r, min),
    "sugeno_product": lambda r: sugeno(r, math.prod),
}


def main() -> None:
    fine = [i / 4 for i in range(41)]  # the rating being raised, in steps of 0.25
    held = fine[::2]  # the two ratings held fixed, in steps of 0.5
    print(f"{'method':18} {'steps':>7} {'dips':>6} {'share':>7} {'worst dip':>10}")
    for name, score in METHODS.items():
        steps = dips = 0
        worst = 0.0
        for raised in INPUTS:
            others = [n for n in INPUTS if n != raised]
            for a, b in itertools.product(held, held):
                previous = None
                for value in fine:
                    current = score({raised: value, others[0]: a, others[1]: b})
                    if previous is not None:
                        steps += 1
                        if current < previous - 1e-9:
                            dips += 1
                            worst = max(worst, previous - current)
                    previous = current
        print(f"{name:18} {steps:>7} {dips:>6} {dips / steps:>7.2%} {worst:>10.4f}")


if __name__ == "__main__":
    main()
