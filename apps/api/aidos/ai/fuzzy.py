"""Fuzzy urgency engine: zero-order Sugeno (Takagi-Sugeno-Kang) inference.

Spec Section 5.1. Three simulated ratings per zone (severity, time criticality,
vulnerability, each 0-10) become one urgency score on 0-100, with a full trace:
membership degrees, every rule that fired, its strength and its contribution.

For one zone:
  1. fuzzify  each rating's degree in low / medium / high (versioned membership functions)
  2. fire     each rule's strength = product of its three antecedent degrees
  3. combine  score = sum(strength * rule output) / sum(strength)

Each rule's output is the centre of its urgency band (low 12.5, moderate 37.5, high 62.5,
critical 87.5). The input sets of each rating sum to 1 everywhere, so the strengths also
sum to 1 and the rules' contributions (strength * output) add up to the score, which is then
rounded to 4 decimals.

Why Sugeno and not Mamdani min/max: with these membership functions and a rule table that
never lowers urgency when a rating rises, this design is provably monotone (raising any
rating never lowers the score). Mamdani min/max with centroid was measured and dipped by
up to 0.9 points on about 2% of small rating increases. See docs/algorithms/fuzzy-logic.md.

Parameters and rules live in aidos/config/fuzzy_rules.json. They are design assumptions
for an academic simulation, not validated triage standards.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache
from itertools import product
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "fuzzy_rules.json"

# Scores are rounded to this many decimals. It removes floating-point noise (62.50000000000001
# vs 62.5) that would otherwise flip a category at a band edge or decide a tie between zones,
# and it is exactly the resolution of the allocation model's integer coefficients.
SCORE_DECIMALS = 4

INPUTS = ("severity", "time_criticality", "vulnerability")
INPUT_TERMS = ("low", "medium", "high")
OUTPUT_TERMS = ("low", "moderate", "high", "critical")


class FuzzyConfigError(ValueError):
    """The versioned fuzzy configuration is malformed or incomplete."""


class FuzzyInputError(ValueError):
    """A rating is missing, not a finite number, or outside its range."""


# ---------------------------------------------------------------- membership functions


@dataclass(frozen=True)
class MembershipFunction:
    """A triangular (a, b, c) or trapezoidal (a, b, c, d) membership function."""

    shape: str
    points: tuple[float, ...]

    def degree(self, x: float) -> float:
        if self.shape == "triangle":
            a, b, c = self.points
            return _trapezoid(x, a, b, b, c)
        a, b, c, d = self.points
        return _trapezoid(x, a, b, c, d)


def _trapezoid(x: float, a: float, b: float, c: float, d: float) -> float:
    """Degree of x in a trapezoid; a == b or c == d gives a vertical shoulder."""
    if x < a or x > d:
        return 0.0
    if b <= x <= c:
        return 1.0
    if x < b:
        return (x - a) / (b - a)
    return (d - x) / (d - c)


# ---------------------------------------------------------------- configuration


@dataclass(frozen=True)
class Rule:
    id: str
    antecedent: tuple[tuple[str, str], ...]  # ((input, term), ...) in INPUTS order
    consequent: str

    def text(self, labels: Mapping[str, str]) -> str:
        clauses = " AND ".join(
            f"{labels[name].lower()} is {term}" for name, term in self.antecedent
        )
        return f"IF {clauses} THEN urgency is {self.consequent}"


@dataclass(frozen=True)
class OutputTerm:
    value: float  # the rule output (a constant: zero-order Sugeno)
    band: tuple[float, float]  # scores in [low, high) take this category


@dataclass(frozen=True)
class FuzzyConfig:
    version: str
    method: str
    input_labels: Mapping[str, str]
    input_range: tuple[float, float]
    input_terms: Mapping[str, Mapping[str, MembershipFunction]]
    output_range: tuple[float, float]
    output_terms: Mapping[str, OutputTerm]
    rules: tuple[Rule, ...]

    def rule_for(self, terms: tuple[str, ...]) -> Rule:
        """The rule whose antecedent is exactly these terms (in INPUTS order)."""
        for rule in self.rules:
            if tuple(term for _, term in rule.antecedent) == terms:
                return rule
        raise FuzzyConfigError(f"no rule for {terms}")


def _membership(raw: Mapping[str, Any], where: str) -> MembershipFunction:
    shape, points = raw.get("shape"), tuple(float(p) for p in raw.get("points", ()))
    expected = {"triangle": 3, "trapezoid": 4}.get(str(shape))
    if expected is None or len(points) != expected:
        raise FuzzyConfigError(f"{where}: expected a triangle (3 points) or trapezoid (4 points)")
    if list(points) != sorted(points):
        raise FuzzyConfigError(f"{where}: points must be non-decreasing")
    return MembershipFunction(str(shape), points)


def parse_config(raw: Mapping[str, Any]) -> FuzzyConfig:
    """Validate a raw configuration. Rejects any gap or duplicate in rule coverage."""
    try:
        inputs, output, rules_raw = raw["inputs"], raw["output"], raw["rules"]
    except KeyError as missing:
        raise FuzzyConfigError(f"missing section {missing}") from None

    if set(inputs) != set(INPUTS):
        raise FuzzyConfigError(f"inputs must be exactly {INPUTS}")
    input_terms: dict[str, dict[str, MembershipFunction]] = {}
    ranges = set()
    for name in INPUTS:
        spec = inputs[name]
        ranges.add(tuple(float(v) for v in spec["range"]))
        if set(spec["terms"]) != set(INPUT_TERMS):
            raise FuzzyConfigError(f"inputs.{name}: terms must be exactly {INPUT_TERMS}")
        input_terms[name] = {
            t: _membership(spec["terms"][t], f"inputs.{name}.{t}") for t in INPUT_TERMS
        }
    if len(ranges) != 1:
        raise FuzzyConfigError("all inputs must share one range")

    if set(output["terms"]) != set(OUTPUT_TERMS):
        raise FuzzyConfigError(f"output terms must be exactly {OUTPUT_TERMS}")
    out_low, out_high = (float(v) for v in output["range"])
    output_terms: dict[str, OutputTerm] = {}
    previous_value = -math.inf
    for term in OUTPUT_TERMS:
        spec = output["terms"][term]
        value, band = float(spec["value"]), tuple(float(v) for v in spec["band"])
        if not (out_low <= band[0] <= value <= band[1] <= out_high) or value <= previous_value:
            raise FuzzyConfigError(f"output.{term}: values must rise and sit inside their bands")
        previous_value = value
        output_terms[term] = OutputTerm(value, (band[0], band[1]))

    rules: list[Rule] = []
    seen_ids: set[str] = set()
    covered: set[tuple[str, ...]] = set()
    for index, item in enumerate(rules_raw):
        rid, when, then = item.get("id"), item.get("if", {}), item.get("then")
        if not rid or rid in seen_ids:
            raise FuzzyConfigError(f"rules.{index}: missing or duplicate id")
        if set(when) != set(INPUTS) or any(when[n] not in INPUT_TERMS for n in INPUTS):
            raise FuzzyConfigError(f"rules.{index} ({rid}): antecedent must name every input")
        if then not in OUTPUT_TERMS:
            raise FuzzyConfigError(f"rules.{index} ({rid}): unknown consequent '{then}'")
        key = tuple(when[n] for n in INPUTS)
        if key in covered:
            raise FuzzyConfigError(f"rules.{index} ({rid}): duplicates another rule's antecedent")
        seen_ids.add(rid)
        covered.add(key)
        rules.append(Rule(rid, tuple((n, when[n]) for n in INPUTS), then))

    missing = [c for c in product(INPUT_TERMS, repeat=len(INPUTS)) if c not in covered]
    if missing:
        raise FuzzyConfigError(f"rule base leaves {len(missing)} input combination(s) uncovered")

    return FuzzyConfig(
        version=str(raw.get("version", "")),
        method=str(raw.get("method", "")),
        input_labels={n: str(inputs[n].get("label", n)) for n in INPUTS},
        input_range=next(iter(ranges)),
        input_terms=input_terms,
        output_range=(out_low, out_high),
        output_terms=output_terms,
        rules=tuple(rules),
    )


@cache
def default_config() -> FuzzyConfig:
    """The versioned configuration shipped with the engine (read once, immutable)."""
    with CONFIG_PATH.open(encoding="utf-8") as handle:
        return parse_config(json.load(handle))


# ---------------------------------------------------------------- inference


@dataclass(frozen=True)
class RuleActivation:
    rule_id: str
    text: str
    consequent: str
    strength: float  # product of the antecedent degrees
    output: float  # the rule's constant output
    contribution: float  # strength * output / total strength (these sum to the score)


@dataclass(frozen=True)
class UrgencyResult:
    score: float  # crisp urgency, 0-100
    category: str  # the band the score falls in
    inputs: Mapping[str, float]  # raw ratings
    normalized: Mapping[str, float]  # ratings rescaled to 0-1
    memberships: Mapping[str, Mapping[str, float]]  # input -> term -> degree
    activations: tuple[RuleActivation, ...]  # fired rules, strongest first
    term_support: Mapping[str, float]  # output term -> share of total rule strength
    config_version: str

    @property
    def top_rule(self) -> RuleActivation:
        return self.activations[0]


def _check_inputs(ratings: Mapping[str, Any], config: FuzzyConfig) -> dict[str, float]:
    low, high = config.input_range
    values: dict[str, float] = {}
    problems: list[str] = []
    for name in INPUTS:
        value = ratings.get(name)
        if isinstance(value, bool) or not isinstance(value, int | float):
            problems.append(f"{name} is missing or not a number")
        elif not math.isfinite(value):
            problems.append(f"{name} must be finite")
        elif not low <= value <= high:
            problems.append(f"{name}={value:g} is outside {low:g}-{high:g}")
        else:
            values[name] = float(value)
    if problems:
        raise FuzzyInputError("; ".join(problems))
    return values


def evaluate(ratings: Mapping[str, Any], config: FuzzyConfig | None = None) -> UrgencyResult:
    """Score one zone's ratings. Pure and deterministic: same inputs, same result."""
    config = config or default_config()
    values = _check_inputs(ratings, config)
    low, high = config.input_range

    memberships = {
        name: {t: config.input_terms[name][t].degree(values[name]) for t in INPUT_TERMS}
        for name in INPUTS
    }

    fired: list[tuple[Rule, float]] = []
    for rule in config.rules:
        strength = math.prod(memberships[name][term] for name, term in rule.antecedent)
        if strength > 0:
            fired.append((rule, strength))
    total = sum(strength for _, strength in fired)
    if total == 0:
        # Unreachable while the input sets cover the range and the rule base is complete
        # (both are checked); kept so a broken configuration fails loudly, never silently.
        raise FuzzyConfigError("no rule fired: the membership functions leave a gap")

    activations = []
    support = dict.fromkeys(OUTPUT_TERMS, 0.0)
    for rule, strength in fired:
        output = config.output_terms[rule.consequent].value
        weight = strength / total
        support[rule.consequent] += weight
        activations.append(
            RuleActivation(
                rule.id,
                rule.text(config.input_labels),
                rule.consequent,
                strength,
                output,
                weight * output,
            )
        )
    score = round(sum(a.contribution for a in activations), SCORE_DECIMALS)

    activations.sort(key=lambda a: (-a.strength, a.rule_id))
    return UrgencyResult(
        score=score,
        category=categorize(score, config),
        inputs=values,
        normalized={n: (values[n] - low) / (high - low) for n in INPUTS},
        memberships=memberships,
        activations=tuple(activations),
        term_support=support,
        config_version=config.version,
    )


def categorize(score: float, config: FuzzyConfig | None = None) -> str:
    """The band a score falls in. A score on a boundary takes the more urgent band."""
    config = config or default_config()
    for term in reversed(OUTPUT_TERMS):
        if score >= config.output_terms[term].band[0]:
            return term
    return OUTPUT_TERMS[0]


def explain(result: UrgencyResult, config: FuzzyConfig | None = None) -> str:
    """How the rules reached the score. Describes the computation; it is not a causal claim."""
    config = config or default_config()
    parts = []
    for name in INPUTS:
        degrees = result.memberships[name]
        term = max(INPUT_TERMS, key=lambda t: (degrees[t], INPUT_TERMS.index(t)))
        parts.append(
            f"{config.input_labels[name].lower()} {result.inputs[name]:g}/10 "
            f"is mostly {term} ({degrees[term]:.2f})"
        )
    top = result.top_rule
    fired = len(result.activations)
    return (
        f"Urgency {result.score:.1f} ({result.category}). {'; '.join(parts).capitalize()}. "
        f"{fired} rule{'s' if fired != 1 else ''} fired; the strongest, {top.rule_id}, fired "
        f"at {top.strength:.2f} and contributes {top.contribution:.1f} points."
    )
