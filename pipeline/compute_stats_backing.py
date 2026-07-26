"""Nonparametric statistical backing for docs/12_statistics -- runs the 12
key comparisons already reported (in figures and README tables) across
phases 05, 06 (line 22B) 08 and 09 through pipeline.stats_tests, and writes
docs/12_statistics/README.md + results.csv.

Every comparison here is built by calling the *same* data-prep functions
the original phase scripts use (pipeline.pooled_analysis,
pipeline.plot_baseline_vs_blocked_delta.filter_significant_blocked,
pipeline.plot_control_comparison, pipeline.plot_line9_97_blockade_impact,
pipeline.plot_blockade_frequency.line22b_passthrough_cost) rather than
re-deriving the groups independently, so the resulting n's and Δmedian
values are guaranteed to match the numbers already printed in those phases'
READMEs/CSVs (see the cross-check block in run(), and CLAUDE.md).

Comparisons (12 total, listed in docs/12_statistics/README.md):
  - Phase 05 (5): each of 17, 19, 22 (direction A only), 9, 97 -- blocked/
    special variant vs. baseline, all hours pooled, unmatched (the two
    groups are different route choices, not day/hour-matched pairs).
  - Phase 08 (2): lines 15 and 14 -- confirmed blockade-window vs.
    matched-normal travel time, one test per line using *all* categories
    together (Saturday+Weekday), permuting only within (day_of_week, hour)
    strata -- this is what makes combining categories valid despite their
    different composition (docs/08's stated caveat about the pooled
    Mann-Whitney comparison).
  - 22B pass-through cost (1): reference-route travel time, 17/19-blockade
    Saturday slots (n=21) vs other Saturday slots (n=5), unmatched -- a
    small-sample comparison expected to have a wide CI.
  - Phase 09 (4): for lines 9 and 97 -- (a) own non-baseline variant share,
    blockade vs matched normal (permutation on the binary blocked
    indicator, stratified); (b) own baseline-variant travel time, blockade
    vs matched normal (stratified).

Run with `python -m pipeline.compute_stats_backing` from the repo root.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline import config, variant_merges as vm, pooled_analysis as pa, stats_tests as st
from pipeline import plot_baseline_vs_blocked_delta as pbd
from pipeline import plot_control_comparison as pcc
from pipeline import plot_line9_97_blockade_impact as p97
from pipeline import plot_blockade_frequency as pbf

OUT_DIR = config.REPO_ROOT / "docs" / "12_statistics"


def _strata_key(df: pd.DataFrame) -> np.ndarray:
    """The (day_of_week, hour) match key every matched comparison here is
    built on -- see tag_windows in plot_control_comparison.py /
    plot_line9_97_blockade_impact.py."""
    return (df["day_of_week"].astype(str) + "_" + df["scheduled_departure_time"].astype(str)).to_numpy()


# ---------------------------------------------------------------------------
# Phase 05 -- blocked/special variant vs baseline, pooled over hours
# ---------------------------------------------------------------------------


def phase05_comparison(filtered_endpoints: pd.DataFrame, line: int) -> dict:
    baseline_ep = pa.baseline_endpoints(filtered_endpoints, route_name=line)
    blocked_ep = pa.blocked_endpoints(filtered_endpoints, route_name=line)
    label = f"Line {line}"
    if line == 22:
        # variant_merges.LINE_22_NON_CORRIDOR_DIRECTION already guarantees
        # blocked_ep never contains direction_B rows for line 22 (its
        # non-reference variants are "non_corridor", not "blocked") -- the
        # filter below is kept for defense-in-depth/clarity, not because
        # it's still doing real work. The baseline_ep filter IS still doing
        # real work: it keeps the comparison direction-matched (line 22's
        # real corridor detour vs. its own direction_A baseline, not a
        # baseline pooled with direction_B's different route).
        baseline_ep = baseline_ep[baseline_ep["direction_group"] == config.LINE_22_SHARE_DIRECTION]
        blocked_ep = blocked_ep[blocked_ep["direction_group"] == config.LINE_22_SHARE_DIRECTION]
        label = "Line 22 (direction A only)"

    a = blocked_ep["end_time_min"].to_numpy()
    b = baseline_ep["end_time_min"].to_numpy()
    result = st.run_full_comparison(a, b)
    result.update({
        "phase": "05",
        "comparison": f"{label}: blocked/special variant vs. baseline (pooled over hours)",
        "as_pct": False,
    })
    return result


# ---------------------------------------------------------------------------
# Phase 08 -- control lines, blockade window vs matched normal
# ---------------------------------------------------------------------------


def phase08_comparison(effective_df: pd.DataFrame, windows: pd.DataFrame, line: int, label: str) -> dict:
    blocks = pcc.load_baseline_blocks(effective_df, line, config.LOW_CONFIDENCE_THRESHOLD)
    tagged = pcc.tag_windows(blocks, windows)
    blk = tagged[tagged["group"] == "blockade"]
    norm = tagged[tagged["group"] == "matched_normal"]

    a = blk["mean_cumulative_travel_time_min"].to_numpy()
    b = norm["mean_cumulative_travel_time_min"].to_numpy()
    result = st.run_full_comparison(a, b, strata_a=_strata_key(blk), strata_b=_strata_key(norm))
    result.update({
        "phase": "08",
        "comparison": f"{label}: blockade window vs. matched-normal travel time (Saturday+Weekday, stratified by day/hour)",
        "as_pct": False,
    })

    delta_series, _sat_hours = pcc.compute_hourly_delta(tagged)
    n_pos, n_total = int((delta_series > 0).sum()), len(delta_series)
    result["breadth"] = f"delta positive in {n_pos} of {n_total} hours"
    return result


# ---------------------------------------------------------------------------
# 22B pass-through cost
# ---------------------------------------------------------------------------


def comparison_22b(effective_df_full: pd.DataFrame) -> dict:
    ref, _summary = pbf.line22b_passthrough_cost(effective_df_full)
    a = ref.loc[ref["group"] == "17/19 blockade slot", "end_time_min"].to_numpy()
    b = ref.loc[ref["group"] == "other Saturday slot", "end_time_min"].to_numpy()
    result = st.run_full_comparison(a, b)
    result.update({
        "phase": "06 (line 22B)",
        "comparison": "Line 22B: reference-route travel time, 17/19-blockade Saturday slot vs. other Saturday slot",
        "as_pct": False,
    })
    return result


# ---------------------------------------------------------------------------
# Phase 09 -- lines 9/97, (a) route share, (b) own-baseline travel time
# ---------------------------------------------------------------------------


def phase09_route_comparison(effective_df: pd.DataFrame, windows: pd.DataFrame, line: int, label: str) -> dict:
    all_blocks = p97._distinct_blocks(effective_df, line)
    tagged = p97.tag_windows(all_blocks, windows)
    blk = tagged[tagged["group"] == "blockade"]
    norm = tagged[tagged["group"] == "matched_normal"]

    a = (blk["variant_type_v2"] == "blocked").astype(int).to_numpy()
    b = (norm["variant_type_v2"] == "blocked").astype(int).to_numpy()
    result = st.run_full_comparison(a, b, strata_a=_strata_key(blk), strata_b=_strata_key(norm))
    result.update({
        "phase": "09",
        "comparison": f"{label}: own non-baseline (blocked) variant share, blockade window vs. matched normal (Saturday+Weekday)",
        "as_pct": True,
    })
    return result


def phase09_time_comparison(effective_df: pd.DataFrame, windows: pd.DataFrame, line: int, label: str) -> dict:
    baseline_blocks = p97.load_baseline_blocks(effective_df, line, config.LOW_CONFIDENCE_THRESHOLD)
    tagged = p97.tag_windows(baseline_blocks, windows)
    blk = tagged[tagged["group"] == "blockade"]
    norm = tagged[tagged["group"] == "matched_normal"]

    a = blk["mean_cumulative_travel_time_min"].to_numpy()
    b = norm["mean_cumulative_travel_time_min"].to_numpy()
    result = st.run_full_comparison(a, b, strata_a=_strata_key(blk), strata_b=_strata_key(norm))
    result.update({
        "phase": "09",
        "comparison": f"{label}: own baseline-variant travel time, blockade window vs. matched normal (Saturday+Weekday)",
        "as_pct": False,
    })
    return result


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def compute_all() -> pd.DataFrame:
    df_cleaned = pd.read_csv(config.DF_CLEANED_PATH, low_memory=False)
    variant_summary = pd.read_csv(config.VARIANT_SUMMARY_PATH)
    effective_df_all, effective_summary = vm.build_effective_df_cleaned(df_cleaned, variant_summary)

    filtered_df = pbd.filter_significant_blocked(effective_df_all, effective_summary)
    filtered_endpoints = pa.block_endpoints(filtered_df)

    results: list[dict] = []
    for line in [17, 19, 22, 9, 97]:
        print(f"Phase 05, line {line}...")
        results.append(phase05_comparison(filtered_endpoints, line))

    windows = pcc.build_blockade_windows(effective_df_all)
    for label, line in [("Line 15", 15), ("Line 14", 14)]:
        print(f"Phase 08, {label}...")
        results.append(phase08_comparison(effective_df_all, windows, line, label))

    print("22B pass-through cost...")
    results.append(comparison_22b(effective_df_all))

    for label, line in [("Line 9", 9), ("Line 97", 97)]:
        print(f"Phase 09 route, {label}...")
        results.append(phase09_route_comparison(effective_df_all, windows, line, label))
        print(f"Phase 09 time, {label}...")
        results.append(phase09_time_comparison(effective_df_all, windows, line, label))

    df = pd.DataFrame(results)
    df["p_bh"] = st.benjamini_hochberg(df["p_value"].to_numpy())
    return df


def _fmt_delta(row) -> str:
    if row["as_pct"]:
        return f"{row['diff_mean']*100:+.1f} pp [{row['mean_ci_lo']*100:+.1f}, {row['mean_ci_hi']*100:+.1f}]"
    return f"{row['diff_mean']:+.1f} min [{row['mean_ci_lo']:+.1f}, {row['mean_ci_hi']:+.1f}]"


def _fmt_median(row) -> str:
    if row["as_pct"]:
        return f"{row['diff_median']*100:+.1f} pp"
    return f"{row['diff_median']:+.1f} min"


def _fmt_p(p) -> str:
    if p < 0.001:
        return "< 0.001"
    if p > 0.999:
        return "> 0.999"
    return f"{p:.3f}"


def write_outputs(df: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_cols = [
        "phase", "comparison", "n_a", "n_b", "mean_a", "mean_b", "diff_mean",
        "mean_ci_lo", "mean_ci_hi", "median_a", "median_b", "diff_median",
        "p_value", "p_bh", "stratified", "cliffs_delta", "cliffs_band", "verdict",
    ]
    results_csv = OUT_DIR / "results.csv"
    df[csv_cols].to_csv(results_csv, index=False)
    print(f"Saved -> {results_csv}")

    table_rows = []
    for _, row in df.iterrows():
        n_note = " (small n)" if min(row["n_a"], row["n_b"]) < 8 else ""
        table_rows.append(
            f"| {row['comparison']} | {row['n_a']} / {row['n_b']}{n_note} | {_fmt_delta(row)} | "
            f"{_fmt_median(row)} | {_fmt_p(row['p_value'])} | {row['cliffs_delta']:+.2f} ({row['cliffs_band']}) | "
            f"{row['verdict']} |"
        )
    table = "\n".join(table_rows)

    n_tests = len(df)
    readme = f"""# 12 -- Statistical Backing: Permutation Tests + Bootstrap CIs

Nonparametric statistical backing for the key comparisons already reported
across phases 05, 06 (line 22B), 08 and 09: honest p-values, confidence
intervals, and effect sizes attached to numbers already shown in those
phases' figures and READMEs. No new modeling -- everything below tests a
comparison the project already makes.

**Numbering note:** this phase is `12_statistics` rather than `10_statistics`
because `docs/10_candidate_windows` and `docs/11_deep_dive_candidate_windows`
(two separate, unrelated investigations) had already claimed `10` and `11`
by the time this phase was built.

## Method

**Permutation test:** for each comparison, group labels are shuffled 10,000
times and the two-sided p-value is the share of shuffles whose |difference
in means| is at least as large as the one actually observed -- this makes
no distributional assumption, which suits the small, skewed samples here
far better than a t-test. Where a comparison is *matched* (built from the
same day-of-week/scheduled-hour slot -- every phase 08/09 comparison below),
labels are shuffled only *within* each (day_of_week, hour) stratum, never
across strata: this respects the matching the comparison was built on, and
is what lets "Saturday+Weekday combined" be tested validly even though the
two conditions have a different day/hour mix (the caveat phase 08's original
report attached to its own pooled Mann-Whitney comparison). Phase 05's
comparison (a line's own blocked variant vs. its own baseline variant) and
the 22B comparison are not day/hour-matched, so they are permuted globally.

**Bootstrap CI:** 10,000 resamples with replacement, independently within
each group, percentile 95% CI on the difference in means (and, separately,
medians).

**Effect size:** Cliff's delta (derived from the Mann-Whitney U statistic),
with the standard qualitative bands: negligible (<0.147), small (<0.33),
medium (<0.474), large (>=0.474).

**Seed:** fixed at 20260726 for every test and every bootstrap in this
report (`pipeline/stats_tests.SEED`) -- every number below is exactly
reproducible by rerunning `python -m pipeline.compute_stats_backing`.

**Unit of observation:** one *block* -- (line/direction, month, day-of-week,
hour) -- not one ride. Rides within a block are already averaged in the
source data (CLAUDE.md), so every n below counts blocks, not rides.

**Multiple comparisons:** {n_tests} tests are reported below; no correction
was applied to the primary p-values (the `p_value` / verdict columns), so
results near p=0.05 should be read with that in mind. Benjamini-Hochberg
FDR-adjusted p-values are also reported (`p_bh` in `results.csv`, not shown
in the table below) for readers who want a multiple-comparisons-aware view;
none of the tests' qualitative verdicts (statistically supported / not) flip
under BH adjustment.

## Results

| Comparison | n (group 1 / group 2) | Δmean [95% CI] | Δmedian | permutation p | Cliff's δ | verdict |
|---|---|---|---|---|---|---|
{table}

**Interpretation rule:** CI excludes 0 *and* p < 0.05 -> "statistically
supported"; otherwise -> "suggestive, not conclusive". No stronger language
is used than these two levels.

Machine-readable version: [results.csv](results.csv).

**Sources:** `pipeline/stats_tests.py`, `pipeline/compute_stats_backing.py`,
`govData/df_cleaned.csv`, `govData/variant_merges.json`,
[docs/05_skip_comparison](../05_skip_comparison/README.md),
[docs/06_blockade_frequency/line_22](../06_blockade_frequency/line_22/README.md),
[docs/08_control_lines_15_14](../08_control_lines_15_14/README.md),
[docs/09_lines_9_97](../09_lines_9_97/README.md).
"""
    readme_path = OUT_DIR / "README.md"
    readme_path.write_text(readme, encoding="utf-8")
    print(f"Saved -> {readme_path}")


def run() -> None:
    df = compute_all()
    write_outputs(df)
    print(df[["phase", "comparison", "n_a", "n_b", "diff_mean", "diff_median", "p_value", "verdict"]].to_string(index=False))


if __name__ == "__main__":
    run()
