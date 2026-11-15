"""Stage 4 evaluation campaign: scenario generation -> policies -> metrics -> statistics -> files.

    run_campaign("standard", out_root)  ->  experiments/results/<run_id>/
        config.json                 the frozen configuration of this run
        manifest.json               versions, counts, failures, file checksums, status
        static_records.csv          one row per (scenario, policy)
        static_zones.csv            one row per (scenario, policy, zone)
        dynamic_recommendation.csv  one row per (script, step, policy), shared state
        dynamic_dispatch.csv        one row per (script, policy), own trajectory
        dispatch_zones.csv          one row per (script, policy, zone)
        scaling.csv                 one row per (size, seed, policy, repeat)
        failures.json               every scenario or script that raised
        summary.json                statistics computed from the CSV rows only

Every policy runs on the same scenario object with the same fuzzy scores (pipeline.compare).
Run directories are never overwritten: a run id that exists is an error.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import statistics
import sys
import traceback
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy
from ortools import __version__ as ORTOOLS_VERSION

from aidos import __version__ as ENGINE_VERSION
from aidos.ai.constraints import AidosConfig
from aidos.ai.fuzzy import default_config
from aidos.domain.models import Scenario
from aidos.evaluation import analysis
from aidos.evaluation.dynamic import dispatch_run, recommendation_rows
from aidos.evaluation.families import FAMILIES, STATIC_FAMILIES, generate, generate_sized
from aidos.pipeline import POLICY_ORDER, compare, run_policy

RUN_ID_PATTERN = r"^(smoke|standard|extended|custom)-\d{8}T\d{6}Z$"


@dataclass(frozen=True)
class Preset:
    name: str
    per_family: int  # static scenarios per family A-G
    dynamic_scripts: int  # family H scripts (each runs in both modes)
    timing_repeats: int  # extra timed runs of each policy per static scenario (median kept)
    scaling_sizes: tuple[int, ...]
    scaling_seeds: int
    scaling_repeats: int
    bootstrap_resamples: int = 5000
    bootstrap_seed: int = 20261111
    families: tuple[str, ...] = STATIC_FAMILIES


PRESETS = {
    "smoke": Preset("smoke", 1, 2, 1, (5, 10), 1, 1, bootstrap_resamples=1000),
    "standard": Preset("standard", 20, 20, 3, (5, 10, 20, 30, 40, 50), 3, 3),
    "extended": Preset("extended", 72, 60, 3, (5, 10, 20, 30, 40, 50), 5, 5),
}


@dataclass
class Progress:
    failures: list[dict[str, Any]] = field(default_factory=list)


def _plan_hash(cells) -> str:
    payload = sorted((c.zone_id, c.resource_id, c.allocated) for c in cells)
    return hashlib.sha256(json.dumps(payload).encode()).hexdigest()[:16]


def static_rows(
    scenario: Scenario, family: str, repeats: int, config: AidosConfig
) -> tuple[list, list]:
    """All four policies on one scenario: one row per policy, plus per-zone rows."""
    comparison = compare(scenario, POLICY_ORDER, config)
    scores = {u.zone_id: u.result.score for u in comparison.urgency}
    rows, zone_rows = [], []
    for run in comparison.runs:
        result, metrics = run.result, run.metrics
        timings = [run.runtime_ms]
        for _ in range(max(0, repeats - 1)):
            timings.append(run_policy(result.policy_id, scenario, scores, config).runtime_ms)
        solver_ms = sum(p.wall_time_ms for p in result.solver.phases) if result.solver else None
        m = asdict(metrics) if metrics else {}
        demanding = m.get("zones_with_demand", 0)
        rows.append(
            {
                "family": family,
                "scenario_id": scenario.scenario_id,
                "seed": scenario.seed,
                "snapshot_hash": comparison.snapshot_hash,
                "zones": len(scenario.active_zones()),
                "resources": len(scenario.resources),
                "policy": result.policy_id.value,
                "status": result.status.value,
                "has_plan": int(result.has_plan),
                "valid": int(run.validation.valid),
                "optimal_proven": int(result.status.value == "OPTIMAL"),
                "plan_hash": _plan_hash(result.cells),
                "allocated_units": m.get("allocated_units"),
                "unmet_units": m.get("unmet_units"),
                "unit_coverage": m.get("unit_coverage"),
                "mean_resource_coverage": m.get("mean_resource_coverage"),
                "urgency_weighted_coverage": m.get("urgency_weighted_coverage"),
                "critical_coverage": m.get("critical_coverage"),
                "min_zone_coverage": m.get("min_zone_coverage"),
                "zones_with_demand": demanding,
                "starved_zones": m.get("starved_zones"),
                "starved_share": (m["starved_zones"] / demanding) if demanding else None,
                "coverage_gap": m.get("coverage_gap"),
                "jain_fairness": m.get("jain_fairness"),
                "usable_stock_utilization": m.get("usable_stock_utilization"),
                "runtime_ms": statistics.median(timings),
                "runtime_ms_min": min(timings),
                "solver_ms": solver_ms,
                "objective_value": result.solver.objective_value if result.solver else None,
            }
        )
        for zone_id, coverage in (metrics.coverage_by_zone if metrics else {}).items():
            requested = sum(c.requested for c in result.cells if c.zone_id == zone_id)
            zone_rows.append(
                {
                    "family": family,
                    "scenario_id": scenario.scenario_id,
                    "policy": result.policy_id.value,
                    "zone_id": zone_id,
                    "urgency": scores[zone_id],
                    "requested": requested,
                    "allocated": sum(c.allocated for c in result.cells if c.zone_id == zone_id),
                    "coverage": coverage,
                }
            )
    return rows, zone_rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: "" if v is None else v for k, v in row.items()})


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def new_run_id(preset: str, now: datetime | None = None) -> str:
    return f"{preset}-{(now or datetime.now(UTC)).strftime('%Y%m%dT%H%M%SZ')}"


def run_campaign(
    preset: Preset,
    out_root: Path,
    run_id: str | None = None,
    log: Callable[[str], None] = print,
    config: AidosConfig | None = None,
) -> Path:
    config = config or AidosConfig()
    run_id = run_id or new_run_id(preset.name)
    out = out_root / run_id
    out.mkdir(parents=True, exist_ok=False)  # never overwrite an existing run
    started = perf_counter()
    created = datetime.now(UTC).isoformat(timespec="seconds")
    progress = Progress()

    frozen = {
        "run_id": run_id,
        "preset": asdict(preset),
        "families": {k: asdict(FAMILIES[k]) for k in preset.families},
        "family_seeds": {
            k: [FAMILIES[k].seed_base, FAMILIES[k].seed_base + preset.per_family - 1]
            for k in preset.families
        },
        "dynamic": {
            "base_family": "B",
            "base_seeds": "800000 + i (family-B generator)",
            "script_seeds": "800000 + i (recommendation), 850000 + i (dispatch)",
            "dispatch_initial_stock_share": 0.30,
            "dispatch_wave_share": 0.15,
        },
        "policies": [p.value for p in POLICY_ORDER],
        "aidos_config": {
            "epsilon": config.epsilon,
            "resource_weights": dict(config.resource_weights),
            "min_coverage": config.min_coverage,
            "time_limit_s": config.time_limit_s,
            "random_seed": config.random_seed,
            "workers": config.workers,
        },
        "fuzzy_config_version": default_config().version,
        "fuzzy_method": default_config().method,
    }
    (out / "config.json").write_text(json.dumps(frozen, indent=2) + "\n", encoding="utf-8")
    manifest: dict[str, Any] = {"run_id": run_id, "status": "running", "created_utc": created}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # ---- static families A-G (paired: every policy on the same scenario)
    rows: list[dict[str, Any]] = []
    zone_rows: list[dict[str, Any]] = []
    for family in preset.families:
        t0 = perf_counter()
        for i in range(preset.per_family):
            try:
                scenario = generate(family, i)
                r, z = static_rows(scenario, family, preset.timing_repeats, config)
                rows += r
                zone_rows += z
            except Exception as err:  # recorded and reported, never hidden
                progress.failures.append(_failure("static", f"{family}:{i}", err))
        log(f"family {family}: {preset.per_family} scenarios in {perf_counter() - t0:.1f}s")
    _write_csv(out / "static_records.csv", rows)
    _write_csv(out / "static_zones.csv", zone_rows)

    # ---- dynamic family H: recommendation mode (shared state)
    dyn_rows: list[dict[str, Any]] = []
    t0 = perf_counter()
    for i in range(preset.dynamic_scripts):
        try:
            dyn_rows += recommendation_rows(i)
        except Exception as err:
            progress.failures.append(_failure("dynamic_recommendation", f"dyn-{i}", err))
    log(f"dynamic recommendation: {preset.dynamic_scripts} scripts in {perf_counter() - t0:.1f}s")
    _write_csv(out / "dynamic_recommendation.csv", dyn_rows)

    # ---- dynamic family H: dispatch mode (each policy's own trajectory)
    dispatch_rows: list[dict[str, Any]] = []
    dispatch_zone_rows: list[dict[str, Any]] = []
    t0 = perf_counter()
    for i in range(preset.dynamic_scripts):
        for policy in POLICY_ORDER:
            try:
                outcome = dispatch_run(i, policy)
                dispatch_rows.append(outcome.row)
                dispatch_zone_rows += outcome.zone_rows
            except Exception as err:
                progress.failures.append(
                    _failure("dynamic_dispatch", f"dyn-{i}:{policy.value}", err)
                )
    log(
        f"dynamic dispatch: {preset.dynamic_scripts} scripts x 4 policies "
        f"in {perf_counter() - t0:.1f}s"
    )
    _write_csv(out / "dynamic_dispatch.csv", dispatch_rows)
    _write_csv(out / "dispatch_zones.csv", dispatch_zone_rows)

    # ---- runtime scaling
    scale_rows: list[dict[str, Any]] = []
    t0 = perf_counter()
    for size in preset.scaling_sizes:
        for seed in range(preset.scaling_seeds):
            try:
                scenario = generate_sized(size, seed)
                comparison = compare(scenario, POLICY_ORDER, config)
                scores = {u.zone_id: u.result.score for u in comparison.urgency}
                for run in comparison.runs:
                    for repeat in range(preset.scaling_repeats):
                        timed = (
                            run
                            if repeat == 0
                            else run_policy(run.result.policy_id, scenario, scores, config)
                        )
                        solver = timed.result.solver
                        scale_rows.append(
                            {
                                "zones": size,
                                "seed": seed,
                                "policy": run.result.policy_id.value,
                                "repeat": repeat,
                                "runtime_ms": timed.runtime_ms,
                                "solver_ms": sum(p.wall_time_ms for p in solver.phases)
                                if solver
                                else "",
                                "variables": solver.variables if solver else "",
                                "status": timed.result.status.value,
                                "optimal_proven": int(timed.result.status.value == "OPTIMAL"),
                                "valid": int(timed.validation.valid),
                            }
                        )
            except Exception as err:
                progress.failures.append(_failure("scaling", f"{size}:{seed}", err))
    log(f"scaling: {len(preset.scaling_sizes)} sizes in {perf_counter() - t0:.1f}s")
    _write_csv(out / "scaling.csv", scale_rows)

    (out / "failures.json").write_text(
        json.dumps(progress.failures, indent=2) + "\n", encoding="utf-8"
    )
    summary = summarize_run(out, preset)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    files = sorted(p.name for p in out.iterdir() if p.is_file() and p.name != "manifest.json")
    manifest = {
        "run_id": run_id,
        "status": "complete" if not progress.failures else "complete_with_failures",
        "created_utc": created,
        "finished_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "duration_s": round(perf_counter() - started, 2),
        "preset": preset.name,
        "counts": {
            "static_scenarios": len({r["scenario_id"] for r in rows}),
            "static_records": len(rows),
            "dynamic_scripts": len({r["script_id"] for r in dyn_rows}),
            "dynamic_steps": len({(r["script_id"], r["step"]) for r in dyn_rows}),
            "dispatch_runs": len(dispatch_rows),
            "scaling_records": len(scale_rows),
            "failures": len(progress.failures),
        },
        "versions": {
            "engine": ENGINE_VERSION,
            "fuzzy_config": default_config().version,
            "ortools": ORTOOLS_VERSION,
            "numpy": numpy.__version__,
            "python": platform.python_version(),
        },
        "environment": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "executable": Path(sys.executable).name,
        },
        "source_revision": "unavailable: the project folder is not a git repository",
        "files": {name: _sha256(out / name) for name in files},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    log(f"done: {out} ({manifest['status']}, {manifest['duration_s']}s)")
    return out


def summarize_run(out: Path, preset: Preset) -> dict[str, Any]:
    """Statistics from the CSV files of a run directory (the same files a reader can inspect)."""
    kwargs = {"resamples": preset.bootstrap_resamples, "seed": preset.bootstrap_seed}
    return {
        "static": analysis.summarize_static(_read_csv(out / "static_records.csv"), **kwargs),
        "dynamic_recommendation": analysis.summarize_dynamic(
            _read_csv(out / "dynamic_recommendation.csv"), **kwargs
        ),
        "dynamic_dispatch": analysis.summarize_dispatch(
            _read_csv(out / "dynamic_dispatch.csv"), **kwargs
        ),
        "scaling": analysis.summarize_scaling(_read_csv(out / "scaling.csv")),
        "metrics": [asdict(m) for m in analysis.STATIC_METRICS],
        "families": {
            k: {"name": FAMILIES[k].name, "description": FAMILIES[k].description}
            for k in preset.families
        },
        "bootstrap": {
            "resamples": preset.bootstrap_resamples,
            "seed": preset.bootstrap_seed,
            "level": 0.95,
        },
    }


def _failure(stage: str, item: str, err: Exception) -> dict[str, Any]:
    return {
        "stage": stage,
        "item": item,
        "error": f"{type(err).__name__}: {err}",
        "trace": traceback.format_exc(limit=3),
    }
