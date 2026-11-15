"""Check an evaluation run before it is reported.

    cd apps/api
    uv run python ../../experiments/verify_results.py <run_id> [--against <other_run_id>]

Checks: file checksums match the manifest; summary.json equals the statistics recomputed from
the CSV files; every static scenario was run by all four policies on one snapshot; every
returned plan passed the independent validator; failures are disclosed; dispatch integrity
holds. With --against, every logical value (not timings) must match the other run on the
scenarios both contain. Exits non-zero on any failed check.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from aidos.evaluation.campaign import PRESETS, summarize_run  # noqa: E402

TIMING = {"runtime_ms", "runtime_ms_min", "solver_ms"}


def rows(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("run_id")
    parser.add_argument("--against")
    parser.add_argument("--results", type=Path, default=ROOT / "experiments" / "results")
    args = parser.parse_args()
    run = args.results / args.run_id
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    config = json.loads((run / "config.json").read_text(encoding="utf-8"))
    problems: list[str] = []

    def check(ok: bool, label: str) -> None:
        print(f"{'ok  ' if ok else 'FAIL'}  {label}")
        if not ok:
            problems.append(label)

    for name, digest in manifest["files"].items():
        check(hashlib.sha256((run / name).read_bytes()).hexdigest() == digest, f"checksum {name}")

    preset = PRESETS[config["preset"]["name"]]
    stored = json.loads((run / "summary.json").read_text(encoding="utf-8"))
    check(
        stored == json.loads(json.dumps(summarize_run(run, preset))), "summary recomputed from CSV"
    )

    static = rows(run / "static_records.csv")
    groups = defaultdict(list)
    for r in static:
        groups[r["scenario_id"]].append(r)
    check(
        all(
            sorted(r["policy"] for r in g) == sorted(["fcfs", "greedy", "aidos", "aidos_balanced"])
            for g in groups.values()
        ),
        f"all four policies on each of {len(groups)} scenarios",
    )
    check(
        all(len({r["snapshot_hash"] for r in g}) == 1 for g in groups.values()),
        "one snapshot per scenario",
    )
    check(
        all(r["valid"] == "1" for r in static if r["has_plan"] == "1"),
        "every returned static plan valid",
    )
    no_plan = sum(1 for r in static if r["has_plan"] != "1")
    print(f"      static records without a plan: {no_plan}")

    rec = rows(run / "dynamic_recommendation.csv")
    check(
        all(r["valid"] == "1" for r in rec),
        f"every recommendation-mode plan valid ({len(rec)} rows)",
    )
    steps = defaultdict(set)
    for r in rec:
        steps[(r["script_id"], r["step"])].add(r["outcome_hash"])
    check(
        all(len(h) == 1 for h in steps.values()), "recommendation mode: one shared state per step"
    )

    dispatch = rows(run / "dynamic_dispatch.csv")
    for field in ("inventory_conserved", "ledger_consistent", "double_dispatch_blocked"):
        check(all(r[field] == "1" for r in dispatch), f"dispatch {field} ({len(dispatch)} runs)")
    check(all(r["rejected_events"] == "0" for r in dispatch), "dispatch scripts applied in full")

    failures = json.loads((run / "failures.json").read_text(encoding="utf-8"))
    check(len(failures) == manifest["counts"]["failures"], f"failures disclosed ({len(failures)})")

    if args.against:
        other = args.results / args.against
        for table, key in (
            ("static_records.csv", ("scenario_id", "policy")),
            ("dynamic_recommendation.csv", ("script_id", "step", "policy")),
        ):
            mine = {tuple(r[k] for k in key): r for r in rows(run / table)}
            theirs = {tuple(r[k] for k in key): r for r in rows(other / table)}
            shared = mine.keys() & theirs.keys()
            same = all(
                {k: v for k, v in mine[s].items() if k not in TIMING}
                == {k: v for k, v in theirs[s].items() if k not in TIMING}
                for s in shared
            )
            check(
                bool(shared) and same,
                f"{table}: {len(shared)} shared rows identical to {args.against}",
            )

    print("all checks passed" if not problems else f"{len(problems)} check(s) failed")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
