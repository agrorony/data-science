# 12 -- Statistical Backing: Permutation Tests + Bootstrap CIs

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

**Multiple comparisons:** 12 tests are reported below; no correction
was applied to the primary p-values (the `p_value` / verdict columns), so
results near p=0.05 should be read with that in mind. Benjamini-Hochberg
FDR-adjusted p-values are also reported (`p_bh` in `results.csv`, not shown
in the table below) for readers who want a multiple-comparisons-aware view;
none of the tests' qualitative verdicts (statistically supported / not) flip
under BH adjustment.

## Results

| Comparison | n (group 1 / group 2) | Δmean [95% CI] | Δmedian | permutation p | Cliff's δ | verdict |
|---|---|---|---|---|---|---|
| Line 17: blocked/special variant vs. baseline (pooled over hours) | 93 / 944 | -9.5 min [-11.6, -7.3] | -11.4 min | < 0.001 | -0.52 (large) | statistically supported |
| Line 19: blocked/special variant vs. baseline (pooled over hours) | 183 / 2191 | -5.9 min [-7.4, -4.3] | -8.7 min | < 0.001 | -0.36 (medium) | statistically supported |
| Line 22 (direction A only): blocked/special variant vs. baseline (pooled over hours) | 81 / 972 | -6.1 min [-9.0, -3.0] | -8.4 min | < 0.001 | -0.31 (small) | statistically supported |
| Line 9: blocked/special variant vs. baseline (pooled over hours) | 93 / 1605 | -12.4 min [-15.4, -9.1] | -15.9 min | < 0.001 | -0.49 (large) | statistically supported |
| Line 97: blocked/special variant vs. baseline (pooled over hours) | 61 / 2145 | -3.3 min [-6.3, -0.0] | -8.0 min | 0.005 | -0.31 (small) | statistically supported |
| Line 15: blockade window vs. matched-normal travel time (Saturday+Weekday, stratified by day/hour) | 186 / 758 | -1.2 min [-3.4, +1.0] | -4.8 min | 0.973 | -0.08 (negligible) | suggestive, not conclusive |
| Line 14: blockade window vs. matched-normal travel time (Saturday+Weekday, stratified by day/hour) | 238 / 1115 | -0.4 min [-1.9, +1.2] | -0.7 min | 0.998 | -0.06 (negligible) | suggestive, not conclusive |
| Line 22B: reference-route travel time, 17/19-blockade Saturday slot vs. other Saturday slot | 21 / 5 (small n) | +5.1 min [+2.8, +7.3] | +4.4 min | 0.017 | +0.81 (large) | statistically supported |
| Line 9: own non-baseline (blocked) variant share, blockade window vs. matched normal (Saturday+Weekday) | 205 / 1225 | +48.3 pp [+41.4, +55.2] | +0.0 pp | < 0.001 | +0.48 (large) | statistically supported |
| Line 9: own baseline-variant travel time, blockade window vs. matched normal (Saturday+Weekday) | 98 / 1172 | -0.2 min [-2.4, +2.1] | -2.2 min | 0.869 | -0.05 (negligible) | suggestive, not conclusive |
| Line 97: own non-baseline (blocked) variant share, blockade window vs. matched normal (Saturday+Weekday) | 350 / 1572 | +22.4 pp [+18.1, +27.0] | +0.0 pp | < 0.001 | +0.22 (small) | statistically supported |
| Line 97: own baseline-variant travel time, blockade window vs. matched normal (Saturday+Weekday) | 241 / 1447 | -1.2 min [-2.2, -0.1] | -1.3 min | 0.005 | -0.07 (negligible) | statistically supported |

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
