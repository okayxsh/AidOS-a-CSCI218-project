"""Structured exports of experiment records (JSON and flat CSV rows)."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any

from aidos.evaluation.runner import ExperimentRecord

SCALAR_METRICS = (
    "allocated_units",
    "unmet_units",
    "unit_coverage",
    "urgency_weighted_coverage",
    "stock_utilization",
    "min_zone_coverage",
    "jain_fairness",
    "unmet_high_urgency",
    "feasibility_violations",
)


def to_rows(records: Iterable[ExperimentRecord]) -> list[dict[str, Any]]:
    """One flat row per (scenario, policy). Ratios that were N/A stay empty, never 0."""
    rows = []
    for r in records:
        row: dict[str, Any] = {
            "scenario_id": r.scenario_id,
            "seed": r.seed,
            "snapshot_hash": r.snapshot_hash,
            "policy_id": r.policy_id,
            "status": r.status,
            "has_plan": r.has_plan,
            "valid": r.valid,
            "violations": r.violations,
            "runtime_ms": round(r.runtime_ms, 3),
        }
        for name in SCALAR_METRICS:
            value = r.metrics.get(name) if r.metrics else None
            row[name] = "" if value is None else value
        rows.append(row)
    return rows


def write_json(
    records: Iterable[ExperimentRecord], path: Path, manifest: Mapping[str, Any]
) -> None:
    payload = {"manifest": dict(manifest), "records": [asdict(r) for r in records]}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_csv(records: Iterable[ExperimentRecord], path: Path) -> None:
    rows = to_rows(records)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
