"""Nonparametric statistical backing -- permutation tests, bootstrap CIs,
and Cliff's delta -- for the key comparisons already reported (in figures
and README tables) across phases 05, 06, 08 and 09.

One reusable engine, called from `pipeline/compute_stats_backing.py` (which
builds the results table for docs/12_statistics) and from the four affected
`pipeline/plot_*.py` modules (which call it directly on the same arrays they
already build, so figure captions and the results table can never drift
apart -- same inputs, same seed, same deterministic algorithm).

Method, exactly as specified:
- Permutation test: shuffle group labels `n_perm` times, two-sided
  p = share of shuffles with |difference in means| >= |observed|. When the
  comparison is matched (built from the same day-of-week/hour slot), pass
  `strata_a`/`strata_b` so labels are only shuffled *within* each stratum --
  this is what lets a "Combined" (Saturday+Weekday) comparison be tested
  validly despite the two groups having a different day/hour composition,
  which a plain pooled Mann-Whitney cannot do.
- Bootstrap CI: 10,000 resamples with replacement, independently within
  each group (not stratified -- the groups themselves, not the matching,
  are what is being resampled), percentile 95% CI on the difference in
  means and medians.
- Cliff's delta: computed from the Mann-Whitney U statistic
  (delta = 2U/(n1*n2) - 1), which is exact and avoids an O(n1*n2) pairwise
  loop; handles ties (including binary 0/1 data) correctly.

Seed: fixed at SEED = 20260726 (the date this module was written) for every
call in this project, so every reported p-value/CI is exactly reproducible.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

SEED = 20260726
N_PERM = 10_000
N_BOOTSTRAP = 10_000
CI_LEVEL = 0.95

CLIFFS_BANDS = [
    (0.147, "negligible"),
    (0.33, "small"),
    (0.474, "medium"),
]


def cliffs_band(abs_delta: float) -> str:
    for threshold, name in CLIFFS_BANDS:
        if abs_delta < threshold:
            return name
    return "large"


def cliffs_delta(a, b) -> tuple[float, str]:
    """Cliff's delta = P(X>Y) - P(X<Y), derived from the Mann-Whitney U
    statistic (delta = 2U/(n1*n2) - 1) rather than an O(n1*n2) pairwise
    count -- exact, tie-aware, and fast even for n in the thousands."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    n1, n2 = len(a), len(b)
    u = stats.mannwhitneyu(a, b, alternative="two-sided", method="asymptotic").statistic
    delta = 2 * u / (n1 * n2) - 1
    return float(delta), cliffs_band(abs(delta))


def permutation_test(
    a,
    b,
    strata_a=None,
    strata_b=None,
    n_perm: int = N_PERM,
    seed: int = SEED,
) -> dict:
    """Two-sided permutation test for the difference in means (a - b).
    Also reports the observed difference in medians (not itself permuted --
    the spec calls for one test per comparison, on the mean). If
    `strata_a`/`strata_b` are given, group labels are shuffled only within
    matching strata (matched/stratified design); otherwise labels are
    shuffled globally."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    n_a, n_b = len(a), len(b)
    obs_diff_mean = a.mean() - b.mean()
    obs_diff_median = float(np.median(a) - np.median(b))
    rng = np.random.default_rng(seed)

    if strata_a is not None or strata_b is not None:
        strata_a = np.asarray(strata_a)
        strata_b = np.asarray(strata_b)
        values_all = np.concatenate([a, b])
        strata_all = np.concatenate([strata_a, strata_b])
        group_a_flag = np.concatenate([np.ones(n_a, dtype=bool), np.zeros(n_b, dtype=bool)])

        total_a_sum = np.zeros(n_perm)
        total_b_sum = np.zeros(n_perm)
        for s in np.unique(strata_all):
            mask = strata_all == s
            v = values_all[mask]
            g = group_a_flag[mask]
            n_s = len(v)
            n_a_s = int(g.sum())
            if n_s == 0:
                continue
            idx = np.argsort(rng.random((n_perm, n_s)), axis=1)
            shuffled = v[idx]
            total_a_sum += shuffled[:, :n_a_s].sum(axis=1)
            total_b_sum += shuffled[:, n_a_s:].sum(axis=1)

        perm_diff = total_a_sum / n_a - total_b_sum / n_b
    else:
        combined = np.concatenate([a, b])
        n_total = len(combined)
        idx = np.argsort(rng.random((n_perm, n_total)), axis=1)
        shuffled = combined[idx]
        perm_a = shuffled[:, :n_a]
        perm_b = shuffled[:, n_a:]
        perm_diff = perm_a.mean(axis=1) - perm_b.mean(axis=1)

    p_value = float(np.mean(np.abs(perm_diff) >= abs(obs_diff_mean)))
    return {
        "n_a": n_a,
        "n_b": n_b,
        "diff_mean": float(obs_diff_mean),
        "diff_median": obs_diff_median,
        "p_value": p_value,
        "stratified": strata_a is not None,
    }


def bootstrap_ci(
    a,
    b,
    n_resamples: int = N_BOOTSTRAP,
    seed: int = SEED,
    ci_level: float = CI_LEVEL,
    chunk_size: int = 2000,
) -> dict:
    """Percentile bootstrap CI on the difference in means and medians (a - b),
    resampling with replacement independently within each group. Computed in
    chunks to bound peak memory for the larger groups (n in the low
    thousands) without changing the result (same seeded RNG stream)."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    rng = np.random.default_rng(seed)

    mean_diffs = np.empty(n_resamples)
    median_diffs = np.empty(n_resamples)
    done = 0
    while done < n_resamples:
        take = min(chunk_size, n_resamples - done)
        resampled_a = rng.choice(a, size=(take, len(a)), replace=True)
        resampled_b = rng.choice(b, size=(take, len(b)), replace=True)
        mean_diffs[done : done + take] = resampled_a.mean(axis=1) - resampled_b.mean(axis=1)
        median_diffs[done : done + take] = np.median(resampled_a, axis=1) - np.median(resampled_b, axis=1)
        done += take

    lo_pct, hi_pct = (1 - ci_level) / 2 * 100, (1 + ci_level) / 2 * 100
    return {
        "mean_ci": (float(np.percentile(mean_diffs, lo_pct)), float(np.percentile(mean_diffs, hi_pct))),
        "median_ci": (float(np.percentile(median_diffs, lo_pct)), float(np.percentile(median_diffs, hi_pct))),
    }


def run_full_comparison(
    a,
    b,
    strata_a=None,
    strata_b=None,
    n_perm: int = N_PERM,
    n_resamples: int = N_BOOTSTRAP,
    seed: int = SEED,
) -> dict:
    """One-call convenience wrapper combining the permutation test, bootstrap
    CI, and Cliff's delta -- everything one row of the results table (or one
    figure-caption annotation) needs."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)

    perm = permutation_test(a, b, strata_a=strata_a, strata_b=strata_b, n_perm=n_perm, seed=seed)
    boot = bootstrap_ci(a, b, n_resamples=n_resamples, seed=seed)
    delta, band = cliffs_delta(a, b)

    ci_lo, ci_hi = boot["mean_ci"]
    verdict = "statistically supported" if (ci_lo > 0 or ci_hi < 0) and perm["p_value"] < 0.05 else "suggestive, not conclusive"

    return {
        "n_a": perm["n_a"],
        "n_b": perm["n_b"],
        "mean_a": float(a.mean()),
        "mean_b": float(b.mean()),
        "diff_mean": perm["diff_mean"],
        "mean_ci_lo": ci_lo,
        "mean_ci_hi": ci_hi,
        "median_a": float(np.median(a)),
        "median_b": float(np.median(b)),
        "diff_median": perm["diff_median"],
        "p_value": perm["p_value"],
        "stratified": perm["stratified"],
        "cliffs_delta": delta,
        "cliffs_band": band,
        "verdict": verdict,
    }


def benjamini_hochberg(p_values) -> np.ndarray:
    """Benjamini-Hochberg adjusted p-values (FDR control), for the note on
    not correcting for multiple comparisons across the full results table."""
    p = np.asarray(p_values, dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order] * n / (np.arange(n) + 1)
    adjusted = np.minimum.accumulate(ranked[::-1])[::-1]
    adjusted = np.clip(adjusted, 0, 1)
    out = np.empty(n)
    out[order] = adjusted
    return out


def format_delta_annotation(result: dict, unit: str = "min", as_pct: bool = False) -> str:
    """Short figure-caption string: 'Δ = X min [95% CI lo, hi], p = Y
    (permutation)'. Shared formatting so every annotated figure reads the
    same way."""
    if as_pct:
        d = result["diff_mean"] * 100
        lo = result["mean_ci_lo"] * 100
        hi = result["mean_ci_hi"] * 100
        unit = "pp"
    else:
        d = result["diff_mean"]
        lo = result["mean_ci_lo"]
        hi = result["mean_ci_hi"]
    p = result["p_value"]
    if p < 0.001:
        p_str = "< 0.001"
    elif p > 0.999:
        p_str = "> 0.999"
    else:
        p_str = f"{p:.3f}"
    return f"Δ = {d:+.1f} {unit} [95% CI {lo:+.1f}, {hi:+.1f}], p = {p_str} (permutation, n={result['n_a']} vs n={result['n_b']})"
