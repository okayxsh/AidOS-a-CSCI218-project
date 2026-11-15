"""Aggregation of raw evaluation rows into the summary (docs/evaluation/metric-definitions.md).

Inputs are the raw row dictionaries the campaign writes to CSV; outputs are plain JSON-able
dictionaries. Every summary number is a function of those rows only, so the summary can be
re-derived from the CSV files (tests/unit/test_evaluation.py checks that it reconciles).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from aidos.evaluation.stats import describe, holm, paired


@dataclass(frozen=True)
class MetricSpec:
    key: str
    label: str
    unit: str
    better: str  # "higher" | "lower" | "n/a"
    aligned: bool  # True when the AidOS objective (or the urgency model) favours it by design
    note: str = ""


STATIC_METRICS: tuple[MetricSpec, ...] = (
    MetricSpec(
        "valid",
        "Feasible plans",
        "share",
        "higher",
        False,
        "A plan that breaks a hard constraint is a correctness failure.",
    ),
    MetricSpec(
        "unit_coverage",
        "Unit coverage",
        "fraction",
        "higher",
        False,
        "Adds units of different resources; read with mean_resource_coverage.",
    ),
    MetricSpec("mean_resource_coverage", "Mean resource coverage", "fraction", "higher", False),
    MetricSpec(
        "urgency_weighted_coverage",
        "Urgency-weighted coverage",
        "fraction",
        "higher",
        True,
        "AidOS maximises (almost) exactly this quantity.",
    ),
    MetricSpec(
        "critical_coverage",
        "Critical-zone coverage",
        "fraction",
        "higher",
        True,
        "Defined by the same fuzzy scores AidOS uses.",
    ),
    MetricSpec("min_zone_coverage", "Lowest zone coverage", "fraction", "higher", False),
    MetricSpec(
        "starved_zones",
        "Starved zones",
        "zones",
        "lower",
        False,
        "Zones with positive demand that receive nothing.",
    ),
    MetricSpec("starved_share", "Share of zones starved", "fraction", "lower", False),
    MetricSpec("coverage_gap", "Coverage gap (max - min)", "fraction", "lower", False),
    MetricSpec(
        "jain_fairness",
        "Jain index of zone coverage",
        "index",
        "higher",
        False,
        "Equality of coverage, not humanitarian fairness.",
    ),
    MetricSpec("usable_stock_utilization", "Usable-stock utilisation", "fraction", "higher", False),
    MetricSpec(
        "runtime_ms",
        "Policy runtime (median of repeats)",
        "ms",
        "lower",
        False,
        "Wall clock on one machine; varies between runs.",
    ),
)

PRIMARY = (  # the pre-declared family of hypothesis tests (Holm-adjusted)
    ("aidos", "fcfs", "urgency_weighted_coverage"),
    ("aidos", "fcfs", "min_zone_coverage"),
    ("aidos", "fcfs", "starved_zones"),
    ("aidos", "fcfs", "jain_fairness"),
)

COMPARISONS = (
    ("aidos", "fcfs"),
    ("aidos", "greedy"),
    ("aidos_balanced", "aidos"),
    ("aidos_balanced", "fcfs"),
    ("greedy", "fcfs"),
)

DYNAMIC_METRICS = (
    "reallocated_units",
    "reallocated_share",
    "plan_changed",
    "unmet_change",
    "mean_abs_zone_coverage_change",
    "uwc_after",
    "min_zone_coverage_after",
    "starved_zones_after",
    "runtime_ms",
)

DISPATCH_METRICS = (
    "dispatched_units",
    "fulfilment",
    "urgency_weighted_fulfilment",
    "min_zone_fulfilment",
    "zones_never_served",
    "inventory_conserved",
    "ledger_consistent",
    "double_dispatch_blocked",
    "rejected_events",
)


def _num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _mean(values: list[float | None]) -> float | None:
    present = [v for v in values if v is not None]
    return sum(present) / len(present) if present else None


def _by(rows: Iterable[Mapping[str, Any]], *keys: str) -> dict[tuple, list[Mapping[str, Any]]]:
    groups: dict[tuple, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(row[k] for k in keys)].append(row)
    return groups


def _series(
    rows: Iterable[Mapping[str, Any]], key_field: str, metric: str
) -> dict[str, float | None]:
    return {str(r[key_field]): _num(r.get(metric)) for r in rows}


def summarize_static(rows: list[Mapping[str, Any]], *, resamples: int, seed: int) -> dict[str, Any]:
    policies = list(dict.fromkeys(r["policy"] for r in rows))
    families = sorted({r["family"] for r in rows})
    by_policy = _by(rows, "policy")
    by_family_policy = _by(rows, "family", "policy")

    def stats_for(selection: list[Mapping[str, Any]]) -> dict[str, Any]:
        return {
            m.key: describe([_num(r.get(m.key)) for r in selection]).as_dict()
            for m in STATIC_METRICS
        }

    overall = {p: stats_for(by_policy[(p,)]) for p in policies}
    by_family = {
        f: {p: stats_for(by_family_policy.get((f, p), [])) for p in policies} for f in families
    }

    comparisons = []
    for scope in ["all", *families]:
        selection = rows if scope == "all" else [r for r in rows if r["family"] == scope]
        grouped = _by(selection, "policy")
        for a, b in COMPARISONS:
            if (a,) not in grouped or (b,) not in grouped:
                continue
            for m in STATIC_METRICS:
                if m.key in ("valid", "runtime_ms"):
                    continue
                result = paired(
                    _series(grouped[(a,)], "scenario_id", m.key),
                    _series(grouped[(b,)], "scenario_id", m.key),
                    resamples=resamples,
                    seed=seed,
                )
                comparisons.append(
                    {"scope": scope, "a": a, "b": b, "metric": m.key, **result.as_dict()}
                )

    primary_p = {
        f"{a}|{b}|{m}": next(
            (
                c["sign_p"]
                for c in comparisons
                if (c["scope"], c["a"], c["b"], c["metric"]) == ("all", a, b, m)
            ),
            None,
        )
        for a, b, m in PRIMARY
    }
    adjusted = holm(primary_p)
    primary = [
        {
            "a": a,
            "b": b,
            "metric": m,
            "sign_p": primary_p[f"{a}|{b}|{m}"],
            "holm_p": adjusted[f"{a}|{b}|{m}"],
        }
        for a, b, m in PRIMARY
    ]

    statuses: dict[str, dict[str, int]] = {}
    for p in policies:
        counts: dict[str, int] = {}
        for r in by_policy[(p,)]:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
        statuses[p] = counts
    feasibility = {
        p: {
            "plans": sum(int(r["has_plan"]) for r in by_policy[(p,)]),
            "valid": sum(int(r["valid"]) for r in by_policy[(p,)]),
            "total": len(by_policy[(p,)]),
            "optimal_proven": sum(int(r["optimal_proven"]) for r in by_policy[(p,)]),
        }
        for p in policies
    }
    identical = {
        f"{a}|{b}": sum(
            1
            for sid in {r["scenario_id"] for r in rows}
            if _plan_key(rows, sid, a) is not None
            and _plan_key(rows, sid, a) == _plan_key(rows, sid, b)
        )
        for a, b in COMPARISONS
    }
    return {
        "policies": policies,
        "families": families,
        "scenarios": len({r["scenario_id"] for r in rows}),
        "overall": overall,
        "by_family": by_family,
        "comparisons": comparisons,
        "primary_tests": primary,
        "statuses": statuses,
        "feasibility": feasibility,
        "identical_plans": identical,
    }


def _plan_key(rows: list[Mapping[str, Any]], scenario_id: str, policy: str) -> str | None:
    for r in rows:
        if r["scenario_id"] == scenario_id and r["policy"] == policy:
            return r.get("plan_hash")
    return None


def summarize_dynamic(
    rows: list[Mapping[str, Any]], *, resamples: int, seed: int
) -> dict[str, Any]:
    if not rows:
        return {"steps": 0}
    policies = list(dict.fromkeys(r["policy"] for r in rows))
    by_policy = _by(rows, "policy")
    by_event_policy = _by(rows, "event_type", "policy")
    events = sorted({r["event_type"] for r in rows})
    # Steps of one script are not independent, so comparisons use one value per script:
    # the mean over its steps. The script is the unit of resampling (cluster bootstrap).
    by_script = _by(rows, "policy", "script_id")
    grouped = {
        (policy,): [
            {
                "script_id": script,
                **{m: _mean([_num(r.get(m)) for r in group]) for m in DYNAMIC_METRICS},
            }
            for (p2, script), group in by_script.items()
            if p2 == policy
        ]
        for policy in policies
    }
    comparisons = []
    for a, b in COMPARISONS:
        if (a,) in grouped and (b,) in grouped:
            for metric in (
                "reallocated_units",
                "unmet_change",
                "min_zone_coverage_after",
                "starved_zones_after",
            ):
                result = paired(
                    _series(grouped[(a,)], "script_id", metric),
                    _series(grouped[(b,)], "script_id", metric),
                    resamples=resamples,
                    seed=seed,
                )
                comparisons.append(
                    {"a": a, "b": b, "metric": metric, "unit": "script mean", **result.as_dict()}
                )
    return {
        "scripts": len({r["script_id"] for r in rows}),
        "steps": len({(r["script_id"], r["step"]) for r in rows}),
        "policies": policies,
        "event_types": events,
        "overall": {
            p: {
                m: describe([_num(r.get(m)) for r in by_policy[(p,)]]).as_dict()
                for m in DYNAMIC_METRICS
            }
            for p in policies
        },
        "by_event": {
            e: {
                p: {
                    m: describe([_num(r.get(m)) for r in by_event_policy.get((e, p), [])]).as_dict()
                    for m in ("reallocated_units", "plan_changed", "unmet_change")
                }
                for p in policies
            }
            for e in events
        },
        "comparisons": comparisons,
        "valid_steps": {p: sum(int(r["valid"]) for r in by_policy[(p,)]) for p in policies},
    }


def summarize_dispatch(
    rows: list[Mapping[str, Any]], *, resamples: int, seed: int
) -> dict[str, Any]:
    if not rows:
        return {"scripts": 0}
    policies = list(dict.fromkeys(r["policy"] for r in rows))
    by_policy = _by(rows, "policy")
    comparisons = []
    for a, b in COMPARISONS:
        if (a,) in by_policy and (b,) in by_policy:
            for metric in (
                "fulfilment",
                "urgency_weighted_fulfilment",
                "min_zone_fulfilment",
                "zones_never_served",
            ):
                result = paired(
                    _series(by_policy[(a,)], "script_id", metric),
                    _series(by_policy[(b,)], "script_id", metric),
                    resamples=resamples,
                    seed=seed,
                )
                comparisons.append({"a": a, "b": b, "metric": metric, **result.as_dict()})
    return {
        "scripts": len({r["script_id"] for r in rows}),
        "policies": policies,
        "overall": {
            p: {
                m: describe([_num(r.get(m)) for r in by_policy[(p,)]]).as_dict()
                for m in DISPATCH_METRICS
            }
            for p in policies
        },
        "integrity": {
            p: {
                "runs": len(by_policy[(p,)]),
                "inventory_conserved": sum(int(r["inventory_conserved"]) for r in by_policy[(p,)]),
                "ledger_consistent": sum(int(r["ledger_consistent"]) for r in by_policy[(p,)]),
                "double_dispatch_blocked": sum(
                    int(r["double_dispatch_blocked"]) for r in by_policy[(p,)]
                ),
                "rejected_events": sum(int(r["rejected_events"]) for r in by_policy[(p,)]),
            }
            for p in policies
        },
        "comparisons": comparisons,
    }


def summarize_scaling(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"points": []}
    points = []
    for (zones, policy), group in sorted(
        _by(rows, "zones", "policy").items(), key=lambda kv: (int(kv[0][0]), kv[0][1])
    ):
        points.append(
            {
                "zones": int(zones),
                "policy": policy,
                "runtime_ms": describe([_num(r["runtime_ms"]) for r in group]).as_dict(),
                "variables": describe([_num(r.get("variables")) for r in group]).as_dict(),
                "optimal": sum(int(r["optimal_proven"]) for r in group),
                "runs": len(group),
            }
        )
    return {"points": points}
