# 08 — Indirect Impact on Control Lines 15 and 14

**Revision round (sections C, G): this phase has been rebuilt.** Both
directions of line 14 are now pooled into one distribution (line 15
already had no direction split); only the delta chart is kept (the
distribution/boxplot comparison and the per-direction hourly-pattern
files have been removed); and the blockade windows are recomputed from
the new absolute >15-stop blocked rule
([docs/07's addendum](../07_blockade_investigation/README.md),
`pipeline.variant_merges`) instead of stage5's fraction-based
`variant_type` column. This removes the need for the old line-22
direction_A special-case correction — its real closure now clears the
new rule automatically.

## Method

**Blockade windows:** a (month, day_of_week, scheduled_departure_time)
slot counts as a confirmed Aza-corridor blockade window if lines 17,
19, or 22 (**either direction**) have a `blocked` merged variant for
that exact slot. This is a straightforward generalization of the new
rule — no per-line hand-tuning is needed anymore, unlike the first
pass's hand-picked month/day windows.

**This produces a much larger window set than the first pass: 320
distinct slots (36 Saturday, 284 Weekday), vs. 112 in the original
phase 08.** The new >15-stop rule labels far more of 17/19/22's raw
variant activity as "blocked" than the old fraction rule did (see
[docs/07's addendum](../07_blockade_investigation/README.md): 141 of
155 merged variants project-wide, 91%, are now "blocked") — so the
window set is not just "line 22's closure added in," it also picks up
many more one-off, low-volume weekday deviations on lines 17/19 that
the old rule filtered out as "regular." **This is a real trade-off of
the new rule, not a bug:** it makes the window definition mechanical
and line-22-inclusive, at the cost of being noisier and less
specifically tied to the sustained Aza-corridor closure than the first
pass's hand-verified windows.

**Control-group construction:** for line 15 (`main`) and line 14 (both
directions pooled), every baseline block (`variant_type_v2 ==
"reference"`, `n_observations >= 8`) is tagged `blockade` if its
`(month, day_of_week, hour)` is itself a flagged slot, `matched_normal`
if it shares the `(day_of_week, hour)` with a flagged slot but its own
month isn't among the flagged months for that pair, or dropped if its
`(day_of_week, hour)` never appears among the flagged slots at all.

**Statistical test:** Mann-Whitney U (primary, travel time is
right-skewed) with Welch's t-test as a robustness check, stratified
Saturday / Weekday / Combined (Combined carries the same composition
caveat as the first pass — different day/hour mixes between groups can
distort a pooled comparison, so it's reported but not primary).

**Reproducing this analysis:** `python -m pipeline.plot_control_comparison`.

## Findings

| Line | Category | n blockade | n normal | Median blockade | Median normal | Δ (min) | Mann-Whitney p | Welch t p |
|---|---|---|---|---|---|---|---|---|
| 15 | Saturday | 33 | 12 | 52.9 | 52.0 | +0.9 | 0.376 (ns) | 0.353 (ns) |
| 15 | Weekday | 265 | 854 | 66.2 | 67.5 | −1.3 | 0.884 (ns) | 0.715 (ns) |
| 15 | Combined | 298 | 866 | 63.8 | 67.4 | −3.5 | 0.122 (ns) | 0.354 (ns) |
| 14 | Saturday | 40 | 7 | 37.8 | 36.6 | +1.2 | 0.317 (ns) | 0.256 (ns) |
| 14 | Weekday | 376 | 1,298 | 48.5 | 47.7 | +0.8 | 0.071 (ns, borderline) | **0.006 (p<0.01)** |
| 14 | Combined | 416 | 1,305 | 47.6 | 47.6 | −0.1 | 0.748 (ns) | 0.268 (ns) |

## Verified conclusion — the significant first-pass finding does not survive this revision at face value

**Neither control line shows a clearly significant effect under the new
windows.** Line 14's Weekday stratum shows the same *direction* as the
first pass (blockade windows slower, +0.8 min) and the underlying hourly
chart (`line_14_hourly_pattern.png`) still shows a visible daytime
pattern (+2 to +8 min through midday/afternoon hours, near zero in the
evening) — but the rank-based Mann-Whitney test is only borderline
(p=0.071) and the Welch t-test is significant (p=0.006) — **the two
tests disagree**, which did not happen in the first pass. Line 15 shows
no significant effect in either stratum, matching the first pass.

**Why the effect got weaker, not the same or clearer, after "fixing"
line 22:** pooling line 14's two directions together, and — more
importantly — nearly tripling the window set to include many low-volume,
one-off weekday deviations (not just the sustained, well-supported May/
Saturday closure), dilutes a real but geographically/temporally
localized signal with a lot of noisier "blocked" slots that may not
actually correspond to sustained congestion. This is a legitimate
methodological trade-off documented here, not swept under the rug: the
new blocked rule is more complete (it correctly counts line 22) but less
selective, and phase 08's control-line test is sensitive to exactly
that trade-off in a way phase 06's simple frequency count is not.

**Bottom line:** this revision's evidence for indirect (knock-on)
congestion on the control lines is weaker and less consistent than the
first pass reported. The directional hint (line 14, weekday hours,
midday/afternoon) is still visible in the chart and one of two tests,
but should now be described as suggestive, not confirmed.

**Sources:** `govData/df_cleaned.csv`, `govData/variant_merges.json`,
[docs/02_route_mapping](../02_route_mapping/README.md),
[docs/03_variants](../03_variants/README.md),
[docs/04_baselines](../04_baselines/README.md),
[docs/06_blockade_frequency](../06_blockade_frequency/README.md),
[docs/07_blockade_investigation](../07_blockade_investigation/README.md),
`pipeline/variant_merges.py`, `pipeline/plot_control_comparison.py`.
