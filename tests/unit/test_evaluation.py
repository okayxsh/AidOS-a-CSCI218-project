"""Stage 4 evaluation: metrics, statistics, families, campaign, dynamic modes."""

import csv
import dataclasses
import hashlib
import json
import math

import pytest

import aidos.evaluation.campaign as campaign
from aidos.ai.baseline_fcfs import allocate_fcfs
from aidos.ai.constraints import allocate_aidos
from aidos.ai.policies import PolicyId
from aidos.evaluation import analysis, dynamic
from aidos.evaluation.families import FAMILIES, STATIC_FAMILIES, generate, generate_sized
from aidos.evaluation.metrics import compute_metrics
from aidos.evaluation.stats import describe, holm, paired, sign_test

# ---------------------------------------------------------------- metrics (hand-calculated)


def test_metrics_on_a_hand_calculated_two_zone_case(make_scenario):
    """Stock: 10 kits, 5 water. A wants 8 kits; B wants 8 kits + 10 water. Urgency A 80, B 40.

    AidOS gives A 8 kits, B 2 kits and 5 water.
      zone coverage A = 8/8 = 1, B = 7/18;  unit coverage = 15/26
      resource coverage kits = 10/16, water = 5/10  ->  mean 0.5625
      UWC = (80*8 + 40*7) / (80*8 + 40*18) = 920/1360
      critical (>= 75) = zone A only = 8/8;  usable stock = min(10,16) + min(5,10) = 15 -> 1.0
    """
    scenario = make_scenario(
        {"kits": 10, "water": 5},
        [("a", 1, (5, 5, 5), {"kits": 8}), ("b", 2, (5, 5, 5), {"kits": 8, "water": 10})],
    )
    urgency = {"a": 80.0, "b": 40.0}
    m = compute_metrics(scenario, allocate_aidos(scenario, urgency), urgency)
    assert m.coverage_by_zone == pytest.approx({"a": 1.0, "b": 7 / 18})
    assert m.unit_coverage == pytest.approx(15 / 26)
    assert m.mean_resource_coverage == pytest.approx(0.5625)
    assert m.urgency_weighted_coverage == pytest.approx(920 / 1360)
    assert m.critical_coverage == pytest.approx(1.0)
    assert m.usable_stock_utilization == pytest.approx(1.0)
    assert m.zones_with_demand == 2 and m.starved_zones == 0
    assert m.coverage_gap == pytest.approx(1 - 7 / 18)
    assert m.min_zone_coverage == pytest.approx(7 / 18)


def test_starvation_and_gap_detect_a_zone_left_with_nothing(make_scenario):
    scenario = make_scenario(
        {"kits": 5}, [("a", 1, (5, 5, 5), {"kits": 5}), ("b", 2, (5, 5, 5), {"kits": 5})]
    )
    m = compute_metrics(scenario, allocate_fcfs(scenario), {"a": 50.0, "b": 50.0})
    assert m.starved_zones == 1 and m.min_zone_coverage == 0.0 and m.coverage_gap == 1.0
    assert m.jain_fairness == pytest.approx(0.5)


def test_zero_stock_and_zero_demand_are_not_applicable_not_zero(make_scenario):
    empty = make_scenario({"kits": 0}, [("a", 1, (5, 5, 5), {"kits": 4})])
    m = compute_metrics(empty, allocate_fcfs(empty), {"a": 50.0})
    assert m.usable_stock_utilization is None and m.starved_zones == 1
    nothing = make_scenario({"kits": 3}, [("a", 1, (5, 5, 5), {})])
    m = compute_metrics(nothing, allocate_fcfs(nothing), {"a": 50.0})
    assert m.unit_coverage is None and m.mean_resource_coverage is None
    assert m.coverage_gap is None and m.zones_with_demand == 0 and m.critical_coverage is None


def test_metric_bounds_hold_on_generated_scenarios():
    from aidos.pipeline import POLICY_ORDER, compare

    for family in STATIC_FAMILIES:
        for run in compare(generate(family, 3), POLICY_ORDER).runs:
            m = run.metrics
            for value in (
                m.unit_coverage,
                m.mean_resource_coverage,
                m.urgency_weighted_coverage,
                m.min_zone_coverage,
                m.coverage_gap,
                m.jain_fairness,
                m.usable_stock_utilization,
                m.critical_coverage,
            ):
                assert value is None or -1e-12 <= value <= 1 + 1e-12
            assert 0 <= m.starved_zones <= m.zones_with_demand


# ---------------------------------------------------------------- statistics


def test_describe_known_values_and_missing_data():
    d = describe([1, 2, 3, 4, None, float("nan")])
    assert d.n == 4 and d.mean == 2.5 and d.median == 2.5
    assert d.sd == pytest.approx(1.2909944, rel=1e-6)
    assert (d.min, d.max) == (1.0, 4.0)
    assert describe([]).n == 0 and describe([]).mean is None
    assert describe([7]).sd is None


def test_paired_differences_pair_by_key_and_drop_missing():
    result = paired({"x": 3, "y": 5, "z": None, "w": 1}, {"x": 1, "y": 5, "z": 2, "w": 2})
    assert result.n == 3 and result.dropped == 1
    assert result.mean_diff == pytest.approx((2 + 0 - 1) / 3)
    assert (result.wins, result.ties, result.losses) == (1, 1, 1)
    low, high = result.ci_mean
    assert low <= result.mean_diff <= high


def test_bootstrap_is_seeded_and_degenerate_when_differences_are_constant():
    a = {str(i): i + 0.5 for i in range(30)}
    b = {str(i): float(i) for i in range(30)}
    first, again = paired(a, b, seed=1), paired(a, b, seed=1)
    assert first.ci_mean == again.ci_mean == pytest.approx((0.5, 0.5))
    assert first.effect_dz is None  # sd of differences is 0
    assert first.sign_p == pytest.approx(2 / 2**30)


def test_sign_test_and_holm_known_values():
    assert sign_test(9, 1) == pytest.approx(2 * 11 / 1024)
    assert sign_test(0, 0) is None
    assert sign_test(5, 5) == 1.0
    assert holm({"a": 0.01, "b": 0.04, "c": 0.03, "d": None}) == pytest.approx(
        {"a": 0.03, "b": 0.06, "c": 0.06, "d": None}
    )


def test_effect_size_matches_definition():
    a = {"1": 3.0, "2": 5.0, "3": 4.0}
    b = {"1": 1.0, "2": 2.0, "3": 4.0}
    diffs = [2.0, 3.0, 0.0]
    mean = sum(diffs) / 3
    sd = math.sqrt(sum((d - mean) ** 2 for d in diffs) / 2)
    assert paired(a, b).effect_dz == pytest.approx(mean / sd)


# ---------------------------------------------------------------- families


def test_families_are_deterministic_and_seeded_apart():
    seeds = set()
    for key in STATIC_FAMILIES:
        assert generate(key, 4) == generate(key, 4)
        assert generate(key, 4) != generate(key, 5)
        seeds |= {generate(key, i).seed for i in range(3)}
    assert len(seeds) == 3 * len(STATIC_FAMILIES)


def _shares(scenario):
    out = {}
    for rid in scenario.resource_ids():
        requested = sum(z.demand.get(rid, 0) for z in scenario.zones)
        if requested:
            out[rid] = scenario.stock[rid] / requested
    return out


@pytest.mark.parametrize("key", ["A", "B", "C"])
def test_scarcity_families_respect_their_stock_ranges(key):
    low, high = FAMILIES[key].stock_factor
    for i in range(10):
        for share in _shares(generate(key, i)).values():
            assert low - 0.05 <= share <= high + 1e-9  # int() floors, so allow a small margin


def test_family_d_is_bimodal_and_e_is_equal_or_near_equal():
    for i in range(10):
        d = generate("D", i)
        for z in d.zones:
            ratings = (z.severity, z.vulnerability, z.time_criticality)
            assert all(r >= 7 for r in ratings) or all(r <= 3 for r in ratings)
        e = generate("E", i)
        for field in ("severity", "vulnerability", "time_criticality"):
            values = [getattr(z, field) for z in e.zones]
            assert max(values) - min(values) <= 2


def test_family_f_has_large_requesters_and_g_one_ample_resource():
    for i in range(10):
        totals = sorted(sum(z.demand.values()) for z in generate("F", i).zones)
        assert totals[-1] >= 2 * totals[0]
        shares = _shares(generate("G", i))
        assert len(shares) == 4
        assert sum(1 for s in shares.values() if s >= 0.95) == 1
        assert sum(1 for s in shares.values() if s <= 0.6 + 1e-9) == 3


def test_sized_scenarios_have_the_requested_size():
    assert len(generate_sized(30, 1).zones) == 30
    assert generate_sized(30, 1) == generate_sized(30, 1)


# ---------------------------------------------------------------- dynamic modes


def test_recommendation_mode_is_deterministic_and_shares_state_across_policies():
    rows = dynamic.recommendation_rows(0)
    assert rows == dynamic.recommendation_rows(0) or all(
        {k: v for k, v in a.items() if k != "runtime_ms"}
        == {k: v for k, v in b.items() if k != "runtime_ms"}
        for a, b in zip(rows, dynamic.recommendation_rows(0), strict=True)
    )
    by_step: dict = {}
    for row in rows:
        by_step.setdefault(row["step"], set()).add(row["outcome_hash"])
        assert row["valid"] == 1
    assert all(len(hashes) == 1 for hashes in by_step.values())  # one shared state per step
    policies_per_step = {s: sum(1 for r in rows if r["step"] == s) for s in by_step}
    assert set(policies_per_step.values()) == {4}


def test_dispatch_scripts_are_identical_for_every_policy_and_accounting_holds():
    _, script = dynamic.dispatch_script(3)
    assert script == dynamic.dispatch_script(3)[1]
    for policy in PolicyId:
        row = dynamic.dispatch_run(3, policy).row
        assert row["inventory_conserved"] == 1
        assert row["ledger_consistent"] == 1
        assert row["double_dispatch_blocked"] == 1
        assert row["rejected_events"] == 0
        assert row["commits"] >= 1


def test_dispatch_base_starts_with_thirty_percent_of_requests():
    base = dynamic.dispatch_base(2)
    for rid, share in _shares(base).items():
        assert share <= dynamic.INITIAL_SHARE + 1e-9, rid


# ---------------------------------------------------------------- campaign


TINY = dataclasses.replace(
    campaign.PRESETS["smoke"],
    families=("B", "E"),
    dynamic_scripts=1,
    scaling_sizes=(5,),
    bootstrap_resamples=200,
)


@pytest.fixture(scope="module")
def tiny_run(tmp_path_factory):
    root = tmp_path_factory.mktemp("results")
    out = campaign.run_campaign(TINY, root, run_id="custom-20260101T000000Z", log=lambda _: None)
    return root, out


def _rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_campaign_writes_every_artifact_with_checksums(tiny_run):
    _, out = tiny_run
    manifest = json.loads((out / "manifest.json").read_text("utf-8"))
    assert manifest["status"] == "complete" and manifest["counts"]["failures"] == 0
    for name, digest in manifest["files"].items():
        assert hashlib.sha256((out / name).read_bytes()).hexdigest() == digest
    assert manifest["source_revision"].startswith("unavailable")


def test_static_rows_are_paired_on_identical_inputs(tiny_run):
    _, out = tiny_run
    rows = _rows(out / "static_records.csv")
    by_scenario: dict = {}
    for row in rows:
        by_scenario.setdefault(row["scenario_id"], []).append(row)
    for group in by_scenario.values():
        assert sorted(r["policy"] for r in group) == sorted(p.value for p in PolicyId)
        assert len({r["snapshot_hash"] for r in group}) == 1
        assert all(r["valid"] == "1" for r in group)


def test_summary_reconciles_with_the_raw_rows(tiny_run):
    _, out = tiny_run
    stored = json.loads((out / "summary.json").read_text("utf-8"))
    assert stored == json.loads(json.dumps(campaign.summarize_run(out, TINY)))
    rows = [r for r in _rows(out / "static_records.csv") if r["policy"] == "aidos"]
    values = [float(r["urgency_weighted_coverage"]) for r in rows]
    overall = stored["static"]["overall"]["aidos"]["urgency_weighted_coverage"]
    assert overall["n"] == len(values)
    assert overall["mean"] == pytest.approx(sum(values) / len(values))


def test_runs_are_never_overwritten(tiny_run):
    root, _ = tiny_run
    with pytest.raises(FileExistsError):
        campaign.run_campaign(TINY, root, run_id="custom-20260101T000000Z", log=lambda _: None)


def test_repeat_run_reproduces_every_logical_value(tiny_run, tmp_path):
    _, first = tiny_run
    second = campaign.run_campaign(
        TINY, tmp_path, run_id="custom-20260101T000001Z", log=lambda _: None
    )
    timing = {"runtime_ms", "runtime_ms_min", "solver_ms"}
    a, b = _rows(first / "static_records.csv"), _rows(second / "static_records.csv")
    assert [{k: v for k, v in r.items() if k not in timing} for r in a] == [
        {k: v for k, v in r.items() if k not in timing} for r in b
    ]
    hashes = lambda path: [r["outcome_hash"] for r in _rows(path / "dynamic_recommendation.csv")]  # noqa: E731
    assert hashes(first) == hashes(second)


def test_failures_are_recorded_not_hidden(tmp_path, monkeypatch):
    real = campaign.generate

    def flaky(family, index):
        if family == "E":
            raise RuntimeError("synthetic failure for the test")
        return real(family, index)

    monkeypatch.setattr(campaign, "generate", flaky)
    out = campaign.run_campaign(
        TINY, tmp_path, run_id="custom-20260101T000002Z", log=lambda _: None
    )
    manifest = json.loads((out / "manifest.json").read_text("utf-8"))
    failures = json.loads((out / "failures.json").read_text("utf-8"))
    assert manifest["status"] == "complete_with_failures"
    assert failures[0]["stage"] == "static" and "synthetic failure" in failures[0]["error"]
    assert {r["family"] for r in _rows(out / "static_records.csv")} == {"B"}


def test_primary_tests_are_holm_adjusted(tiny_run):
    _, out = tiny_run
    primary = json.loads((out / "summary.json").read_text("utf-8"))["static"]["primary_tests"]
    assert [(t["a"], t["b"], t["metric"]) for t in primary] == list(analysis.PRIMARY)
    for test in primary:
        if test["sign_p"] is not None:
            assert test["holm_p"] >= test["sign_p"]


def test_dynamic_comparisons_use_scripts_as_the_unit(tiny_run):
    _, out = tiny_run
    summary = json.loads((out / "summary.json").read_text("utf-8"))["dynamic_recommendation"]
    assert summary["comparisons"] and all(
        c["unit"] == "script mean" for c in summary["comparisons"]
    )
    assert all(c["n"] + c["dropped"] == summary["scripts"] for c in summary["comparisons"])
