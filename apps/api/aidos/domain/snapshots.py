"""Built-in scenario fixtures and snapshot hashing.

A snapshot hash identifies the exact scenario state a result was computed from, so a
later commit (Stage 3) can reject stale plans.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from aidos.domain.models import Scenario
from aidos.domain.validation import parse_scenario

# apps/api/aidos/domain/snapshots.py -> repository root is four levels up.
REPO_ROOT = Path(__file__).resolve().parents[4]
SCENARIO_DIR = REPO_ROOT / "data" / "scenarios"


class ScenarioNotFoundError(LookupError):
    def __init__(self, scenario_id: str):
        self.scenario_id = scenario_id
        super().__init__(f"No built-in scenario with id '{scenario_id}'")


def snapshot_hash(scenario: Scenario) -> str:
    """SHA-256 of the scenario's canonical JSON (sorted keys, no whitespace)."""
    canonical = json.dumps(scenario.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_scenario_file(path: Path) -> Scenario:
    with path.open(encoding="utf-8") as handle:
        return parse_scenario(json.load(handle))


def list_builtin_scenarios(directory: Path = SCENARIO_DIR) -> list[Scenario]:
    """All fixtures in the scenario directory, sorted by file name for a stable order."""
    return [load_scenario_file(p) for p in sorted(directory.glob("*.json"))]


def load_builtin_scenario(scenario_id: str, directory: Path = SCENARIO_DIR) -> Scenario:
    for scenario in list_builtin_scenarios(directory):
        if scenario.scenario_id == scenario_id:
            return scenario
    raise ScenarioNotFoundError(scenario_id)
