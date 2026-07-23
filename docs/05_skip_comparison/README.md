# 05 — Baseline vs. Blocked/Special Variant (Delta Style)

**Revision round (section F): the phase 05 figures have been replaced
entirely.** Instead of per-variant stop-skip bar charts, each line now
gets one delta-style line chart (anchor: the top panel of
[docs/08_control_lines_15_14](../08_control_lines_15_14/README.md)'s
`line_15_hourly_pattern.png`): for each hour of day, (median travel time
on the line's blocked/special variant) minus (median travel time on its
baseline variant), both directions pooled (section C), using only the
confirmed post-merge/post-exclude variant set from
[docs/03_variants](../03_variants/README.md) and the new >15-stop
blocked rule (section B). Grey bands mark hours with fewer than 8
blocked-variant observations (thin data).

**Revision round 2:** hours 25/26 (01:00/02:00 next day) are dropped
from every figure's data entirely (global rule — previously shown as
01:00/02:00, now just not plotted). Line 97's new exclusion
([docs/03_variants](../03_variants/README.md), direction B variant 2)
removes 8 blocked blocks from line 97's stats (n_blocked 108→100 vs.
the first revision round — see updated table below). A new combined
figure, `delta_all_lines.png`, plots lines 17/19/22 (reds) and 9/97
(purples) on shared axes so all five non-control lines' hourly detour
patterns can be compared directly.

## Headline finding: every line's blocked/special variant is faster overall

| Line | n baseline | n blocked | Overall median delta (min) | Verdict |
|---|---|---|---|---|
| 9 | 1,605 | 116 | **−15.8** | saves time |
| 14 (control) | 1,739 | 13 | −1.4 | ~neutral (thin data) |
| 15 (control) | 1,187 | 4 | −17.9 | thin data, not reliable |
| 17 | 944 | 121 | **−10.4** | saves time |
| 19 | 2,191 | 203 | **−8.7** | saves time |
| 22 | 1,879 | 236 | **−4.0** | saves time |
| 97 | 2,145 | 100 | **−8.2** | saves time |

Every non-control line's blocked/special variant is measurably *faster*
than its baseline overall, consistent with the first pass's finding
(under the old fraction-based classification): the routes classified as
"detours" in this dataset behave like short-turn/express service or
avoid a congested corridor, not like a slower forced detour. Line 22 —
now correctly showing a substantial blocked share
([docs/06_blockade_frequency](../06_blockade_frequency/README.md)) —
also shows the smallest time saving (−4.0 min) of the five non-control
lines, plausibly because its blocked variant only skips a small slice
of a much longer route.

**`delta_all_lines.png` (new, section B):** the combined view shows this
"saves time" pattern is not uniform across hours — several lines'
curves cross above zero at specific hours even though their all-hours
median is negative (see e.g. line 97's midday peak, discussed in
[docs/09](../09_lines_9_97/README.md) where the same variant behaves
very differently from line 9's).

**Control-line caveat:** lines 14 and 15 have very few blocked blocks
(13 and 4 respectively — see
[docs/07's addendum](../07_blockade_investigation/README.md) on why
control lines now have *any* "blocked" label at all) and most hours are
flagged "thin data." Their large negative deltas should **not** be read
as "control lines have a fast secret route" — with n=4/13 total blocked
observations, these numbers are noise, not a finding.

Per-line detail: [line_9](line_9/README.md), [line_14](line_14/README.md),
[line_15](line_15/README.md), [line_17](line_17/README.md),
[line_19](line_19/README.md), [line_22](line_22/README.md),
[line_97](line_97/README.md).

**Figures:** per-line `line_<N>/baseline_vs_blocked_delta.png`, plus the
combined `delta_all_lines.png` (lines 17/19/22/9/97, section B).

**Sources:** `govData/df_cleaned.csv`, `govData/variant_merges.json`,
`pipeline/variant_merges.py`, `pipeline/pooled_analysis.py`,
`pipeline/plot_baseline_vs_blocked_delta.py`.
