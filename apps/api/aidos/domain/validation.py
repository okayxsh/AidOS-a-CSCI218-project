"""Scenario validation beyond field-level schema checks (spec Section 4).

`parse_scenario` is the single entry point for turning untrusted JSON into a Scenario.
It raises ScenarioValidationError listing every problem found, never a partial result.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from aidos.domain.models import Scenario


@dataclass(frozen=True)
class Issue:
    """One validation problem, located by a dotted path into the input."""

    path: str
    message: str


class ScenarioValidationError(ValueError):
    def __init__(self, issues: list[Issue]):
        self.issues = issues
        summary = "; ".join(f"{i.path}: {i.message}" for i in issues[:5])
        super().__init__(f"Invalid scenario ({len(issues)} issue(s)): {summary}")


def _location(loc: tuple[Any, ...]) -> str:
    return ".".join(str(part) for part in loc) or "(root)"


def parse_scenario(data: Mapping[str, Any]) -> Scenario:
    """Validate raw scenario data and return an immutable Scenario."""
    try:
        scenario = Scenario.model_validate(data)
    except ValidationError as exc:
        issues = [Issue(_location(err["loc"]), err["msg"]) for err in exc.errors()]
        raise ScenarioValidationError(issues) from None

    issues = check_scenario_consistency(scenario)
    if issues:
        raise ScenarioValidationError(issues)
    return scenario


def check_scenario_consistency(scenario: Scenario) -> list[Issue]:
    """Cross-field rules: unique IDs, known resources, and stock for every resource."""
    issues: list[Issue] = []
    resource_ids = [r.id for r in scenario.resources]
    known = set(resource_ids)

    seen: set[str] = set()
    for index, rid in enumerate(resource_ids):
        if rid in seen:
            issues.append(Issue(f"resources.{index}.id", f"duplicate resource id '{rid}'"))
        seen.add(rid)

    for rid in scenario.stock:
        if rid not in known:
            issues.append(Issue(f"stock.{rid}", f"unknown resource '{rid}'"))
    for rid in resource_ids:
        if rid not in scenario.stock:
            issues.append(Issue(f"stock.{rid}", "stock must be declared for every resource"))

    seen_zones: set[str] = set()
    for index, zone in enumerate(scenario.zones):
        if zone.id in seen_zones:
            issues.append(Issue(f"zones.{index}.id", f"duplicate zone id '{zone.id}'"))
        seen_zones.add(zone.id)
        for rid in zone.demand:
            if rid not in known:
                issues.append(Issue(f"zones.{index}.demand.{rid}", f"unknown resource '{rid}'"))

    return issues
