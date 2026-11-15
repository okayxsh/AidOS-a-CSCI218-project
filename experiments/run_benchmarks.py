"""Run the AidOS evaluation: every policy on the same scenarios, then statistics.

    cd apps/api
    uv run python ../../experiments/run_benchmarks.py --preset smoke      # ~10 s, pipeline check
    uv run python ../../experiments/run_benchmarks.py --preset standard   # the reported campaign
    uv run python ../../experiments/run_benchmarks.py --preset extended   # larger, optional

Each preset writes a new directory experiments/results/<preset>-<UTC timestamp>/ (never
overwriting an existing run). See docs/evaluation/experimental-protocol.md.

The legacy Stage 2 check is still available as --smoke (writes stage2-smoke.json/.csv).
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from aidos.domain.snapshots import list_builtin_scenarios  # noqa: E402
from aidos.evaluation.campaign import PRESETS, run_campaign  # noqa: E402
from aidos.evaluation.exports import write_csv, write_json  # noqa: E402
from aidos.evaluation.generator import generate_scenario  # noqa: E402
from aidos.evaluation.runner import run_experiment  # noqa: E402

SMOKE_SEEDS = (11, 12, 13, 14, 15)
SMOKE_CLASSES = ("none", "mild", "severe", "zero")


def smoke(out_dir: Path) -> int:
    scenarios = list(list_builtin_scenarios())
    scenarios += [generate_scenario(seed, c) for c in SMOKE_CLASSES for seed in SMOKE_SEEDS]
    records = run_experiment(scenarios)

    manifest = {
        "run": "stage2-smoke",
        "purpose": "correctness smoke check, not a performance comparison",
        "created_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "scenarios": len(scenarios),
        "seeds": list(SMOKE_SEEDS),
        "classes": list(SMOKE_CLASSES),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "engine_version": records[0].engine_version,
        "fuzzy_version": records[0].fuzzy_version,
        "ortools_version": records[0].ortools_version,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(records, out_dir / "stage2-smoke.json", manifest)
    write_csv(records, out_dir / "stage2-smoke.csv")

    print(f"{len(scenarios)} scenarios x {len(records) // len(scenarios)} policies")
    header = ("policy", "plans", "valid", "statuses", "mean uwc", "mean jain")
    print(
        f"{header[0]:16} {header[1]:>5} {header[2]:>5} {header[3]:24} {header[4]:>9} {header[5]:>9}"
    )
    failures = 0
    for policy in dict.fromkeys(r.policy_id for r in records):
        rows = [r for r in records if r.policy_id == policy]
        valid = sum(r.valid for r in rows)
        failures += len(rows) - valid
        statuses = ",".join(sorted({r.status for r in rows}))
        uwc = [r.metrics["urgency_weighted_coverage"] for r in rows if r.metrics]
        jain = [r.metrics["jain_fairness"] for r in rows if r.metrics]
        uwc = [v for v in uwc if v is not None]
        jain = [v for v in jain if v is not None]
        mean = lambda xs: f"{statistics.fmean(xs):.3f}" if xs else "n/a"  # noqa: E731
        print(
            f"{policy:16} {sum(r.has_plan for r in rows):>5} {valid:>5} {statuses:24} "
            f"{mean(uwc):>9} {mean(jain):>9}"
        )
    print(f"wrote {out_dir / 'stage2-smoke.json'} and .csv")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--smoke", action="store_true", help="the legacy Stage 2 smoke check")
    parser.add_argument("--preset", choices=sorted(PRESETS), help="run an evaluation campaign")
    parser.add_argument("--out", type=Path, default=ROOT / "experiments" / "results")
    args = parser.parse_args()
    if args.preset:
        out = run_campaign(PRESETS[args.preset], args.out)
        manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        return 0 if manifest["status"] == "complete" else 1
    if not args.smoke:
        parser.error("choose --preset smoke|standard|extended (or the legacy --smoke)")
    return smoke(args.out)


if __name__ == "__main__":
    raise SystemExit(main())
