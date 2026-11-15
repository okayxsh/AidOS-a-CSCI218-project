"""Write seeded synthetic scenarios as JSON files.

    cd apps/api
    uv run python ../../experiments/generate_scenarios.py --class severe --seeds 1 2 3 --out /tmp/x

Same seed and class always produce the same file. Generated scenarios are synthetic.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from aidos.evaluation.generator import STOCK_FACTOR, generate_scenario  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--class", dest="scarcity", choices=sorted(STOCK_FACTOR), required=True)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for seed in args.seeds:
        scenario = generate_scenario(seed, args.scarcity)
        path = args.out / f"{scenario.scenario_id}.json"
        path.write_text(json.dumps(scenario.model_dump(mode="json"), indent=2) + "\n", "utf-8")
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
