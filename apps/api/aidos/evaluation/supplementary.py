"""Shared plumbing for Stage 5 supplementary experiments.

Every supplementary experiment writes to a NEW directory
experiments/results/supplementary-<name>-<UTC time>/ with config.json, CSV files,
summary.json and a manifest.json holding versions and a SHA-256 per file. Existing run
directories (including the frozen Stage 4 runs) are never written to.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy
from ortools import __version__ as ORTOOLS_VERSION

from aidos import __version__ as ENGINE_VERSION
from aidos.ai.fuzzy import default_config

SUPPLEMENTARY_PATTERN = r"^supplementary-[a-z0-9-]+-\d{8}T\d{6}Z$"


def new_run_dir(root: Path, name: str, now: datetime | None = None) -> Path:
    stamp = (now or datetime.now(UTC)).strftime("%Y%m%dT%H%M%SZ")
    out = root / f"supplementary-{name}-{stamp}"
    out.mkdir(parents=True, exist_ok=False)
    return out


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: "" if v is None else v for k, v in row.items()})


def cpu_load_percent() -> int | None:
    """Current CPU load on Windows (Win32_Processor.LoadPercentage); None elsewhere or on error."""
    if sys.platform != "win32":
        return None
    try:
        out = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-CimInstance Win32_Processor"
                " | Measure-Object LoadPercentage -Average).Average",
            ],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        ).stdout.strip()
        return int(float(out)) if out else None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def environment() -> dict[str, Any]:
    return {
        "engine": ENGINE_VERSION,
        "fuzzy_config": default_config().version,
        "ortools": ORTOOLS_VERSION,
        "numpy": numpy.__version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "logical_cpus": __import__("os").cpu_count(),
        "source_revision": _revision(),
    }


def _revision() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10, check=False
        )
        return out.stdout.strip() or "unavailable: no commit yet"
    except OSError:
        return "unavailable: git not found"


def finalize(
    out: Path, *, name: str, started: datetime, counts: dict[str, int], notes: str
) -> None:
    files = sorted(p.name for p in out.iterdir() if p.is_file() and p.name != "manifest.json")
    write_json(
        out / "manifest.json",
        {
            "run_id": out.name,
            "experiment": name,
            "status": "complete",
            "classification": (
                "supplementary / exploratory (Stage 5); not the frozen Stage 4 benchmark"
            ),
            "created_utc": started.isoformat(timespec="seconds"),
            "finished_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "counts": counts,
            "notes": notes,
            "environment": environment(),
            "files": {f: hashlib.sha256((out / f).read_bytes()).hexdigest() for f in files},
        },
    )
