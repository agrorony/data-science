# 08 — Indirect Impact on Control Lines 15 and 14

**Approved as of revision round 2** — untouched except that both
figures were regenerated to drop hours 25/26 (01:00/02:00 next day)
per that round's global rule. Confirmed by diffing
`control_comparison_stats.csv` and `blockade_windows_used.csv` against
the pre-round-2 committed versions: byte-identical, so none of the
numbers or findings below changed.

**Revision round 3 (section G):** the two separate per-line delta
figures are replaced by **one combined figure**,
`control_lines_delta.png`, with both lines' curves on shared axes
(colors from the project palette, `pipeline.config.LINE_COLORS` —
`docs/README.md`), one legend, one zero line, shared Saturday-hour
shading. This is a display-only change — `control_comparison_stats.csv`
and `blockade_windows_used.csv` are confirmed unchanged (diffed again
after rerunning), so every number and finding below still stands. Worth
noting from the combined view: lines 14 and 15's delta curves track each
other closely across most of the day (both peak around 14:00–15:00 at
roughly the same magnitude), which is consistent with a shared
citywide daytime-traffic pattern rather than anything specific to the
Aza-corridor closure.

**fix_22b_central_prompt.md:** line 22 direction_B's non-reference variants
are now forced to `"non_corridor"` (never `"blocked"`) centrally in
`pipeline.variant_merges` — previously they leaked into this phase's window
definition (`SOURCE_LINES = [17, 19, 22]`, either direction), inflating the
Weekday window count from 112 (first pass) to 284. With direction_B's
spurious slots removed, the Weekday window count drops to **172** (Saturday
windows, 36, are unaffected — direction_B never drove a Saturday-only
window). This changes every Weekday/Combined number in the table below
(Saturday rows are untouched) and, notably, **resolves the Mann-Whitney/
Welch disagreement flagged in the previous pass** — see "Verified
conclusion" below.

**Revision round 4:** line 14's 14 flagged slots were reclassified from
`"blocked"` to `"noise"` ([docs/06_blockade_frequency/line_14](../06_blockade_frequency/line_14/README.md))
after being confirmed as stop-recording dropouts. **This phase is
unaffected — verified byte-identical** (`control_comparison_stats.csv`,
`blockade_windows_used.csv` diffed before/after): blockade windows are
built only from lines 17/19/22 (`SOURCE_LINES`), never line 14, so its
former "blocked" slots never leaked into the window definition; line
14's own control-group stats use only its `variant_type_v2 ==
"reference"` blocks, untouched by the reclassification.

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

**This produces a larger window set than the first pass: 208
distinct slots (36 Saturday, 172 Weekday), vs. 112 in the original
phase 08** (previously reported as 320/36/284 before `fix_22b_central_prompt.md`
removed the slots direction_B's spurious "blocked" classification had been
contributing — see the changelog note above). The new >15-stop rule labels
far more of 17/19/22A's raw variant activity as "blocked" than the old
fraction rule did (see [docs/07's addendum](../07_blockade_investigation/README.md)) —
so the window set is not just "line 22's closure added in," it also picks up
more one-off, low-volume weekday deviations on lines 17/19 that
the old rule filtered out as "regular." **This is a real trade-off of
the new rule, not a bug:** it makes the window definition mechanical
and line-22-inclusive, at the cost of being somewhat noisier and less
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
| 15 | Weekday | 153 | 746 | 64.8 | 66.6 | −1.8 | 0.941 (ns) | 0.543 (ns) |
| 15 | Combined | 186 | 758 | 61.7 | 66.4 | −4.8 | 0.077 (ns) | 0.292 (ns) |
| 14 | Saturday | 40 | 7 | 37.8 | 36.6 | +1.2 | 0.317 (ns) | 0.256 (ns) |
| 14 | Weekday | 198 | 1,108 | 48.0 | 47.1 | +0.9 | 0.156 (ns) | 0.064 (ns, borderline) |
| 14 | Combined | 238 | 1,115 | 46.2 | 46.9 | −0.7 | 0.119 (ns) | 0.641 (ns) |

## Verified conclusion — no significant effect on either control line

**Neither control line shows a significant effect under the corrected
windows.** Line 14's Weekday stratum still shows the same *direction* as
the first pass (blockade windows slower, +0.9 min) and the underlying
hourly chart (`control_lines_delta.png`) still shows a visible daytime
pattern (+2 to +8 min through midday/afternoon hours, near zero in the
evening) — but now **both** the rank-based Mann-Whitney test (p=0.156) and
the Welch t-test (p=0.064, borderline) agree it doesn't clear significance.
Line 15 shows no significant effect in either stratum, matching every prior
pass.

**The previous "two tests disagree" finding was itself the 22B artifact.**
Before `fix_22b_central_prompt.md`, the 320-slot window set (contaminated
by direction_B's spuriously-"blocked" slots) produced a Weekday Welch
p=0.006 (significant) against a Mann-Whitney p=0.071 (not) — a genuine
test disagreement that this README flagged as noteworthy. With the
corrected 208-slot window set, that disagreement is gone: both tests now
agree there's no effect. In hindsight the disagreement was a symptom of
window-set contamination, not a real second, rank-insensitive signal.

**Why there's still a small, non-significant directional hint on line
14:** even at 208 slots the window set includes many one-off, low-volume
weekday deviations on lines 17/19 alongside the sustained, well-supported
May/Saturday closure, which dilutes a real but geographically/temporally
localized signal. This remains a legitimate methodological trade-off: the
new blocked rule is more complete (it correctly counts line 22A) but less
selective than the first pass's hand-verified windows, and phase 08's
control-line test is sensitive to exactly that trade-off in a way phase
06's simple frequency count is not.

**Statistical backing** ([docs/12_statistics](../12_statistics/README.md)):
a day/hour-stratified permutation test -- which, unlike the plain
Mann-Whitney Combined row above, is valid evidence even with Saturday and
Weekday combined despite their different composition -- confirms neither
line reaches significance testing all data together (Line 15: p=0.973;
Line 14: p=0.998; both "suggestive, not conclusive"), consistent with this
section's finding that the effect is at most a stratum-specific hint, not
a robust combined result.

**Bottom line:** this revision's evidence for indirect (knock-on)
congestion on the control lines is weaker than the first pass reported,
and — now that the window-set contamination behind the earlier test
disagreement is fixed — more internally consistent too: both tests agree
on both lines. The directional hint (line 14, weekday hours,
midday/afternoon) is still visible in the chart, but should be described
as suggestive, not confirmed.

**Sources:** `govData/df_cleaned.csv`, `govData/variant_merges.json`,
[docs/02_route_mapping](../02_route_mapping/README.md),
[docs/03_variants](../03_variants/README.md),
[docs/04_baselines](../04_baselines/README.md),
[docs/06_blockade_frequency](../06_blockade_frequency/README.md),
[docs/07_blockade_investigation](../07_blockade_investigation/README.md),
`pipeline/variant_merges.py`, `pipeline/config.py`,
`pipeline/plot_control_comparison.py`.
