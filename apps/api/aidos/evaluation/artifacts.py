"""Read-only access to completed evaluation runs (experiments/results/<run_id>/).

Only run ids matching RUN_ID_PATTERN are accepted, the resolved directory must sit directly
inside the results root, and only the fixed file names below can be read. No path from a
request is ever joined to the filesystem unchecked.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from aidos.domain.snapshots import REPO_ROOT
from aidos.evaluation.campaign import RUN_ID_PATTERN

RESULTS_ROOT = REPO_ROOT / "experiments" / "results"
TABLES = {
    "static": "static_records.csv",
    "static_zones": "static_zones.csv",
    "recommendation": "dynamic_recommendation.csv",
    "dispatch": "dynamic_dispatch.csv",
    "dispatch_zones": "dispatch_zones.csv",
    "scaling": "scaling.csv",
}
_RUN_ID = re.compile(RUN_ID_PATTERN)


class InvalidRunIdError(ValueError):
    def __init__(self, run_id: str):
        super().__init__(f"'{run_id}' is not a valid evaluation run id.")


class RunNotFoundError(LookupError):
    def __init__(self, run_id: str):
        super().__init__(f"No completed evaluation run '{run_id}'.")


def run_dir(run_id: str, root: Path = RESULTS_ROOT) -> Path:
    if not _RUN_ID.fullmatch(run_id):
        raise InvalidRunIdError(run_id)
    path = (root / run_id).resolve()
    if path.parent != root.resolve() or not (path / "manifest.json").is_file():
        raise RunNotFoundError(run_id)
    return path


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def list_runs(root: Path = RESULTS_ROOT) -> list[dict[str, Any]]:
    """Every run directory with a manifest, newest first. Incomplete runs are listed too."""
    runs = []
    if not root.is_dir():
        return runs
    for child in root.iterdir():
        if child.is_dir() and _RUN_ID.fullmatch(child.name) and (child / "manifest.json").is_file():
            manifest = _json(child / "manifest.json")
            runs.append(
                {
                    "run_id": child.name,
                    "preset": manifest.get("preset", child.name.split("-")[0]),
                    "status": manifest.get("status", "unknown"),
                    "created_utc": manifest.get("created_utc"),
                    "duration_s": manifest.get("duration_s"),
                    "counts": manifest.get("counts", {}),
                }
            )
    return sorted(runs, key=lambda r: r["run_id"].split("-", 1)[1], reverse=True)


def load_run(run_id: str, root: Path = RESULTS_ROOT) -> dict[str, Any]:
    path = run_dir(run_id, root)
    out = {"manifest": _json(path / "manifest.json")}
    for name in ("config", "summary", "failures"):
        file = path / f"{name}.json"
        out[name] = _json(file) if file.is_file() else None
    return out


def _value(text: str) -> Any:
    if text == "":
        return None
    for cast in (int, float):
        try:
            return cast(text)
        except ValueError:
            continue
    return text


def load_table(
    run_id: str,
    table: str,
    *,
    filters: dict[str, str] | None = None,
    limit: int = 1000,
    offset: int = 0,
    root: Path = RESULTS_ROOT,
) -> dict[str, Any]:
    """Rows of one result table, optionally filtered by exact column values."""
    if table not in TABLES:
        raise RunNotFoundError(f"{run_id}/{table}")
    file = run_dir(run_id, root) / TABLES[table]
    rows: list[dict[str, Any]] = []
    if file.is_file() and file.stat().st_size:
        with file.open(newline="", encoding="utf-8") as handle:
            for raw in csv.DictReader(handle):
                if filters and any(raw.get(k) != v for k, v in filters.items() if v is not None):
                    continue
                rows.append({k: _value(v) for k, v in raw.items()})
    return {"total": len(rows), "offset": offset, "rows": rows[offset : offset + limit]}
