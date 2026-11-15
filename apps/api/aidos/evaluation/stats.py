"""Descriptive and paired statistics for the evaluation (docs/evaluation/experimental-protocol.md).

Small and explicit on purpose: every number in the summaries can be recomputed by hand from
the raw CSV files.

- describe():        n, mean, sample sd, median, min, max, 10/25/75/90th percentiles
- paired():          differences a_i - b_i over scenarios present in both (missing dropped,
                     and counted), wins/ties/losses, a percentile bootstrap CI for the mean
                     and median difference, the paired effect size d_z, and an exact
                     two-sided sign test (ties excluded)
- holm():            Holm-Bonferroni adjustment for the planned family of sign tests

Uncertainty here is uncertainty *within the synthetic scenario distribution*. It says nothing
about real disasters.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass

import numpy as np

TIE_TOLERANCE = 1e-9


@dataclass(frozen=True)
class Description:
    n: int
    mean: float | None
    sd: float | None
    median: float | None
    min: float | None
    max: float | None
    p10: float | None
    p25: float | None
    p75: float | None
    p90: float | None

    def as_dict(self) -> dict:
        return asdict(self)


def _clean(values: Sequence[float | None]) -> list[float]:
    out = []
    for v in values:
        if v is None:
            continue
        f = float(v)
        if math.isfinite(f):
            out.append(f)
    return out


def describe(values: Sequence[float | None]) -> Description:
    """Summary of the observed values; None and non-finite values are excluded (and not
    counted in n)."""
    data = _clean(values)
    if not data:
        return Description(0, None, None, None, None, None, None, None, None, None)
    arr = np.asarray(data, dtype=float)
    pct = np.percentile(arr, [10, 25, 50, 75, 90])
    return Description(
        n=len(data),
        mean=float(arr.mean()),
        sd=float(arr.std(ddof=1)) if len(data) > 1 else None,
        median=float(pct[2]),
        min=float(arr.min()),
        max=float(arr.max()),
        p10=float(pct[0]),
        p25=float(pct[1]),
        p75=float(pct[3]),
        p90=float(pct[4]),
    )


@dataclass(frozen=True)
class Paired:
    n: int  # pairs with both values present
    dropped: int  # keys missing a value in either series
    mean_diff: float | None
    median_diff: float | None
    sd_diff: float | None
    ci_mean: tuple[float, float] | None  # percentile bootstrap, `level`
    ci_median: tuple[float, float] | None
    level: float
    effect_dz: float | None  # mean / sd of differences; None when sd is 0 or n < 2
    wins: int  # a > b
    ties: int
    losses: int  # a < b
    sign_p: float | None  # exact two-sided sign test on non-tied pairs

    def as_dict(self) -> dict:
        d = asdict(self)
        d["ci_mean"] = list(self.ci_mean) if self.ci_mean else None
        d["ci_median"] = list(self.ci_median) if self.ci_median else None
        return d


def sign_test(wins: int, losses: int) -> float | None:
    """Exact two-sided binomial test of P(win) = 0.5 on the non-tied pairs."""
    n = wins + losses
    if n == 0:
        return None
    k = min(wins, losses)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * tail)


def paired(
    a: Mapping[str, float | None],
    b: Mapping[str, float | None],
    *,
    resamples: int = 5000,
    seed: int = 20261111,
    level: float = 0.95,
) -> Paired:
    """Paired comparison of a and b keyed by scenario id (difference = a - b)."""
    keys = sorted(set(a) | set(b))
    diffs = []
    dropped = 0
    for k in keys:
        x, y = a.get(k), b.get(k)
        if x is None or y is None or not math.isfinite(float(x)) or not math.isfinite(float(y)):
            dropped += 1
            continue
        diffs.append(float(x) - float(y))
    n = len(diffs)
    if n == 0:
        return Paired(0, dropped, None, None, None, None, None, level, None, 0, 0, 0, None)
    arr = np.asarray(diffs)
    wins = int(np.sum(arr > TIE_TOLERANCE))
    losses = int(np.sum(arr < -TIE_TOLERANCE))
    ties = n - wins - losses
    sd = float(arr.std(ddof=1)) if n > 1 else None
    effect = arr.mean() / sd if sd and sd > TIE_TOLERANCE else None

    ci_mean = ci_median = None
    if n > 1:
        rng = np.random.default_rng(seed)
        idx = rng.integers(0, n, size=(resamples, n))
        samples = arr[idx]
        alpha = (1 - level) / 2
        means = samples.mean(axis=1)
        medians = np.median(samples, axis=1)
        ci_mean = (float(np.quantile(means, alpha)), float(np.quantile(means, 1 - alpha)))
        ci_median = (float(np.quantile(medians, alpha)), float(np.quantile(medians, 1 - alpha)))
    return Paired(
        n=n,
        dropped=dropped,
        mean_diff=float(arr.mean()),
        median_diff=float(np.median(arr)),
        sd_diff=sd,
        ci_mean=ci_mean,
        ci_median=ci_median,
        level=level,
        effect_dz=float(effect) if effect is not None else None,
        wins=wins,
        ties=ties,
        losses=losses,
        sign_p=sign_test(wins, losses),
    )


def holm(pvalues: Mapping[str, float | None]) -> dict[str, float | None]:
    """Holm-Bonferroni adjusted p-values (monotone). None stays None and is not counted."""
    present = sorted(((p, k) for k, p in pvalues.items() if p is not None))
    m = len(present)
    adjusted: dict[str, float | None] = {k: None for k in pvalues}
    running = 0.0
    for i, (p, k) in enumerate(present):
        running = max(running, min(1.0, (m - i) * p))
        adjusted[k] = running
    return adjusted
