"""Fuzzy urgency engine (spec Sections 5.1 and 11): memberships, rules, scores, traces."""

import copy
import itertools
import json
import math

import pytest

from aidos.ai.fuzzy import (
    CONFIG_PATH,
    INPUT_TERMS,
    INPUTS,
    OUTPUT_TERMS,
    FuzzyConfigError,
    FuzzyInputError,
    categorize,
    default_config,
    evaluate,
    explain,
    parse_config,
)

RAW = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
LEVEL = {"low": 0, "medium": 1, "high": 2}
OUT_LEVEL = {t: i for i, t in enumerate(OUTPUT_TERMS)}


def rate(severity, time_criticality, vulnerability):
    return {
        "severity": severity,
        "time_criticality": time_criticality,
        "vulnerability": vulnerability,
    }


# ---------------------------------------------------------------- membership functions


@pytest.mark.parametrize(
    ("x", "expected"),
    [
        (0, {"low": 1, "medium": 0, "high": 0}),
        (2, {"low": 1, "medium": 0, "high": 0}),
        (3.5, {"low": 0.5, "medium": 0.5, "high": 0}),
        (5, {"low": 0, "medium": 1, "high": 0}),
        (6.5, {"low": 0, "medium": 0.5, "high": 0.5}),
        (8, {"low": 0, "medium": 0, "high": 1}),
        (10, {"low": 0, "medium": 0, "high": 1}),
    ],
)
def test_membership_degrees_at_boundaries_and_overlaps(x, expected):
    sets = default_config().input_terms["severity"]
    for term, degree in expected.items():
        assert sets[term].degree(x) == pytest.approx(degree)


def test_input_sets_cover_the_range_and_sum_to_one():
    """A Ruspini partition: every rating belongs to some set, and degrees sum to 1."""
    config = default_config()
    for name in INPUTS:
        for i in range(0, 1001):
            x = i / 100
            total = sum(config.input_terms[name][t].degree(x) for t in INPUT_TERMS)
            assert total == pytest.approx(1.0), (name, x)


# ---------------------------------------------------------------- rule base


def test_rule_base_is_complete_with_unique_ids():
    config = default_config()
    assert len(config.rules) == 27
    assert len({r.id for r in config.rules}) == 27
    for combo in itertools.product(INPUT_TERMS, repeat=3):
        assert config.rule_for(combo)


def test_rule_table_never_lowers_urgency_when_one_input_rises():
    config = default_config()
    for combo in itertools.product(INPUT_TERMS, repeat=3):
        here = OUT_LEVEL[config.rule_for(combo).consequent]
        for position in range(3):
            if combo[position] == "high":
                continue
            raised = list(combo)
            raised[position] = INPUT_TERMS[LEVEL[combo[position]] + 1]
            assert OUT_LEVEL[config.rule_for(tuple(raised)).consequent] >= here, combo


def test_documented_rules():
    config = default_config()
    assert config.rule_for(("high", "high", "low")).consequent == "critical"
    assert config.rule_for(("low", "low", "low")).consequent == "low"
    # Vulnerability safeguard: a highly vulnerable zone is never scored "low".
    for sev, time in itertools.product(INPUT_TERMS, repeat=2):
        assert config.rule_for((sev, time, "high")).consequent != "low"


def test_config_rejects_a_gap_in_rule_coverage():
    raw = copy.deepcopy(RAW)
    raw["rules"] = raw["rules"][:-1]
    with pytest.raises(FuzzyConfigError, match="uncovered"):
        parse_config(raw)


def test_config_rejects_duplicates_and_unknown_terms():
    raw = copy.deepcopy(RAW)
    raw["rules"].append(dict(raw["rules"][0], id="R99"))
    with pytest.raises(FuzzyConfigError, match="duplicates"):
        parse_config(raw)
    raw = copy.deepcopy(RAW)
    raw["rules"][0]["then"] = "extreme"
    with pytest.raises(FuzzyConfigError, match="unknown consequent"):
        parse_config(raw)
    raw = copy.deepcopy(RAW)
    raw["inputs"]["severity"]["terms"]["medium"]["points"] = [5, 2, 8]
    with pytest.raises(FuzzyConfigError, match="non-decreasing"):
        parse_config(raw)


# ---------------------------------------------------------------- inference


def test_extremes_and_category_boundaries():
    assert evaluate(rate(0, 0, 0)).score == 12.5
    assert evaluate(rate(0, 0, 0)).category == "low"
    assert evaluate(rate(10, 10, 10)).score == 87.5
    assert evaluate(rate(10, 10, 10)).category == "critical"
    assert [categorize(s) for s in (0, 24.99, 25, 49.99, 50, 74.99, 75, 100)] == [
        "low",
        "low",
        "moderate",
        "moderate",
        "high",
        "high",
        "critical",
        "critical",
    ]


def test_score_is_always_within_range():
    for values in itertools.product(range(0, 11), repeat=3):
        result = evaluate(rate(*values))
        assert 12.5 - 1e-9 <= result.score <= 87.5 + 1e-9
        assert result.category == categorize(result.score)


def test_contributions_sum_to_the_score_and_strengths_sum_to_one():
    for values in [(9, 9, 8), (7, 7, 5), (3.5, 6.5, 2), (0, 10, 4.2)]:
        result = evaluate(rate(*values))
        assert sum(a.contribution for a in result.activations) == pytest.approx(result.score)
        assert sum(a.strength for a in result.activations) == pytest.approx(1.0)
        assert sum(result.term_support.values()) == pytest.approx(1.0)


def test_scores_carry_no_floating_point_noise():
    """Scores have exactly 4 decimals, so band edges and ties between zones are stable."""
    grid = [i / 4 for i in range(41)]
    for values in itertools.product(grid[::2], repeat=3):
        score = evaluate(rate(*values)).score
        assert score == round(score, 4)
    # 0, 2.5, 6.5 is mathematically 25 (the low/moderate edge); floats give 25.000000000000004.
    edge = evaluate(rate(0, 2.5, 6.5))
    assert edge.score == 25.0 and edge.category == "moderate"
    # Equal ratings in a different order of evaluation must tie exactly.
    assert evaluate(rate(6, 5, 7)).score == 62.5


def test_hand_computed_example():
    """severity 7, time 7, vulnerability 5: sev/time are (medium 1/3, high 2/3), vul medium 1.

    Rules: R14 (m,m,m)->moderate 1/9, R17 (m,h,m)->high 2/9, R23 (h,m,m)->high 2/9,
    R26 (h,h,m)->critical 4/9. Score = (37.5 + 2*62.5 + 2*62.5 + 4*87.5) / 9 = 70.8333.
    """
    result = evaluate(rate(7, 7, 5))
    assert result.score == pytest.approx(70.8333, abs=1e-4)
    assert result.category == "high"
    fired = {a.rule_id: a.strength for a in result.activations}
    assert fired == pytest.approx({"R14": 1 / 9, "R17": 2 / 9, "R23": 2 / 9, "R26": 4 / 9})
    assert result.top_rule.rule_id == "R26"


def test_rating_inside_a_flat_region_fires_exactly_one_rule():
    result = evaluate(rate(10, 9, 1))
    assert [a.rule_id for a in result.activations] == ["R25"]
    assert result.score == 87.5


def test_monotone_in_every_input():
    """Raising any one rating never lowers the score (fine grid over the whole domain)."""
    grid = [i / 4 for i in range(41)]
    coarse = grid[::4]
    for name in INPUTS:
        others = [n for n in INPUTS if n != name]
        for a, b in itertools.product(coarse, coarse):
            previous = -math.inf
            for value in grid:
                score = evaluate({name: value, others[0]: a, others[1]: b}).score
                assert score >= previous - 1e-9, (name, a, b, value)
                previous = score


def test_higher_urgency_inputs_score_higher_under_controlled_comparison():
    base = evaluate(rate(5, 5, 5)).score
    assert evaluate(rate(9, 5, 5)).score > base
    assert evaluate(rate(5, 9, 5)).score > base
    assert evaluate(rate(5, 5, 9)).score > base


def test_deterministic_repeated_runs():
    first = evaluate(rate(6.3, 4.1, 7.7))
    assert all(evaluate(rate(6.3, 4.1, 7.7)) == first for _ in range(20))


def test_normalized_inputs_and_trace_fields():
    result = evaluate(rate(2.5, 10, 0))
    assert result.normalized == {"severity": 0.25, "time_criticality": 1.0, "vulnerability": 0.0}
    assert set(result.memberships) == set(INPUTS)
    assert all(a.strength > 0 for a in result.activations)
    strengths = [a.strength for a in result.activations]
    assert strengths == sorted(strengths, reverse=True)
    assert result.config_version == "1.0"


@pytest.mark.parametrize(
    "ratings",
    [
        {"severity": 5, "time_criticality": 5},  # missing
        rate(-0.1, 5, 5),
        rate(5, 10.01, 5),
        rate(float("nan"), 5, 5),
        rate(float("inf"), 5, 5),
        rate("7", 5, 5),
        rate(True, 5, 5),
    ],
)
def test_invalid_inputs_are_rejected(ratings):
    with pytest.raises(FuzzyInputError):
        evaluate(ratings)


def test_explanation_matches_the_computation():
    result = evaluate(rate(7, 7, 5))
    text = explain(result)
    assert "70.8" in text and "(high)" in text
    assert "R26" in text and "4 rules fired" in text
    assert "because" not in text.lower()  # descriptive, not causal
