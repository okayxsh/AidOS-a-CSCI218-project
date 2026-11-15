"""Independent audit of the Stage 4 statistics (Stage 5). Read-only on the Stage 4 runs.

    cd apps/api
    uv run python ../../experiments/audit_stage4.py

Recomputes key numbers with pandas and a hand-written exact sign test (a different code path
from aidos.evaluation.stats) and compares them with summary.json, the generated results tables
and the published figures. Writes supplementary-stage4-audit-*/audit.json.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

import pandas as pd  # noqa: E402

from aidos.evaluation import supplementary as sup  # noqa: E402

RUN = ROOT / "experiments" / "results" / "extended-20261112T100136Z"
METRICS = [
    "unit_coverage",
    "urgency_weighted_coverage",
    "critical_coverage",
    "min_zone_coverage",
    "starved_zones",
    "starved_share",
    "coverage_gap",
    "jain_fairness",
]


def sign_p(diffs):
    wins = int((diffs > 1e-9).sum())
    losses = int((diffs < -1e-9).sum())
    n = wins + losses
    if n == 0:
        return None
    k = min(wins, losses)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2**n)


def main() -> int:
    started = datetime.now(UTC)
    summary = json.loads((RUN / "summary.json").read_text(encoding="utf-8"))
    static = pd.read_csv(RUN / "static_records.csv")
    checks = []

    def check(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    # Counts and pairing
    check("504 scenarios x 4 policies", len(static) == 2016 and static.scenario_id.nunique() == 504)
    check("72 scenarios per family", set(static.groupby("family").scenario_id.nunique()) == {72})
    seeds_ok = all(
        set(static[static.family == f].seed) == set(range(base, base + 72))
        for f, base in zip("ABCDEFG", range(100_000, 800_000, 100_000), strict=True)
    )
    check("seeds are seed_base + 0..71 per family", seeds_ok)

    # Denominators: unit coverage = allocated / (allocated + unmet)
    derived = static.allocated_units / (static.allocated_units + static.unmet_units)
    check(
        "unit_coverage = allocated / requested",
        (derived - static.unit_coverage).abs().max() < 1e-12,
    )
    check(
        "starved_share = starved / zones with demand",
        ((static.starved_zones / static.zones_with_demand) - static.starved_share).abs().max()
        < 1e-12,
    )
    check(
        "all metric values in [0, 1] where fractions",
        all(
            static[m].dropna().between(-1e-12, 1 + 1e-12).all()
            for m in METRICS
            if m not in ("starved_zones",)
        ),
    )

    # Means against summary.json
    worst = 0.0
    for metric in METRICS:
        for policy, group in static.groupby("policy"):
            stored = summary["static"]["overall"][policy][metric]["mean"]
            mine = group[metric].mean()
            worst = max(worst, abs(stored - mine))
    check("policy means match summary.json", worst < 1e-12, f"max abs diff {worst:.2e}")

    # Paired AidOS - FCFS: mean, effect size, sign test, Holm
    wide = {m: static.pivot(index="scenario_id", columns="policy", values=m) for m in METRICS}
    primary = {"urgency_weighted_coverage", "min_zone_coverage", "starved_zones", "jain_fairness"}
    pvals = {}
    for metric in METRICS:
        d = (wide[metric]["aidos"] - wide[metric]["fcfs"]).dropna()
        stored = next(
            c
            for c in summary["static"]["comparisons"]
            if (c["scope"], c["a"], c["b"], c["metric"]) == ("all", "aidos", "fcfs", metric)
        )
        sd = d.std(ddof=1)
        dz = d.mean() / sd if sd > 1e-9 else None
        ok = (
            stored["n"] == len(d)
            and abs(stored["mean_diff"] - d.mean()) < 1e-12
            and (dz is None) == (stored["effect_dz"] is None)
            and (dz is None or abs(stored["effect_dz"] - dz) < 1e-9)
            and stored["ci_mean"] is not None
            and stored["ci_mean"][0] <= d.mean() <= stored["ci_mean"][1]
        )
        check(f"paired AidOS-FCFS {metric}: n, mean, d_z, CI contains mean", ok)
        if metric in primary:
            pvals[metric] = sign_p(d)
    ordered = sorted(pvals.items(), key=lambda kv: kv[1])
    running, holm = 0.0, {}
    for i, (metric, p) in enumerate(ordered):
        running = max(running, min(1.0, (len(ordered) - i) * p))
        holm[metric] = running
    stored_tests = {t["metric"]: t for t in summary["static"]["primary_tests"]}
    check(
        "sign tests and Holm match",
        all(
            abs(stored_tests[m]["sign_p"] - pvals[m]) < 1e-12
            and abs(stored_tests[m]["holm_p"] - holm[m]) < 1e-12
            for m in pvals
        ),
    )

    # AidOS == greedy on every scenario
    plans = static.pivot(index="scenario_id", columns="policy", values="plan_hash")
    check("AidOS plan == greedy plan in all 504", int((plans.aidos == plans.greedy).sum()) == 504)

    # Dynamic: script-level aggregation
    rec = pd.read_csv(RUN / "dynamic_recommendation.csv")
    per_script = rec.groupby(["policy", "script_id"]).reallocated_units.mean().unstack(0)
    d = per_script["aidos"] - per_script["fcfs"]
    stored = next(
        c
        for c in summary["dynamic_recommendation"]["comparisons"]
        if (c["a"], c["b"], c["metric"]) == ("aidos", "fcfs", "reallocated_units")
    )
    check(
        "dynamic comparisons use 60 script means",
        stored["n"] == 60 == len(d) and abs(stored["mean_diff"] - d.mean()) < 1e-9,
    )

    # Failures and figures
    check(
        "failures.json empty and manifest says complete",
        json.loads((RUN / "failures.json").read_text()) == []
        and json.loads((RUN / "manifest.json").read_text())["status"] == "complete",
    )
    fig_ok = all(
        hashlib.sha256((ROOT / "docs" / "evaluation" / "figures" / f.name).read_bytes()).hexdigest()
        == hashlib.sha256(f.read_bytes()).hexdigest()
        for f in (RUN / "figures").glob("*")
    )
    check("docs/evaluation/figures are byte-identical to the run's figures", fig_ok)
    tables = (ROOT / "docs" / "evaluation" / "results-tables.md").read_text(encoding="utf-8")
    check(
        "results-tables.md is generated from this run",
        "extended-20261112T100136Z" in tables
        and "0.765 (0.153)" in tables
        and "0.1020 [0.0922, 0.1119]" in tables,
    )

    out = sup.new_run_dir(ROOT / "experiments" / "results", "stage4-audit", started)
    sup.write_json(out / "audit.json", {"run": RUN.name, "checks": checks})
    sup.finalize(
        out,
        name="stage4-audit",
        started=started,
        counts={"checks": len(checks)},
        notes="Independent recomputation; the Stage 4 run is read, never written.",
    )
    for c in checks:
        print(("ok  " if c["ok"] else "FAIL"), c["check"], c["detail"])
    print(f"wrote {out}")
    return 0 if all(c["ok"] for c in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
