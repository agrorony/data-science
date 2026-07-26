# 04 — Baseline (Most Common) Variant per Line

**Revision note:** as of this revision round, stats and the headline
figure are pooled across both directions of each line (section C) — a
line's baseline trip-time distribution combines rides from both
directions into one sample. The per-direction stop-by-stop figures
(`baseline_direction_A.png` / `_B.png`) are kept for route-shape detail,
now built on the *merged* baseline variant from
[docs/03_variants](../03_variants/README.md) instead of the raw stage4
reference.

**Revision round 3 (section E):** the headline barplot's error bars now
show the standard error of the mean (SEM = std / sqrt(n)) instead of the
raw standard deviation — SEM says how precisely the mean itself is
known (and is tiny for every line here, given n in the thousands); std
is kept as a reported column since it's still the "how chaotic is this
line" number. Bars are colored per line via the project palette
(`pipeline.config.LINE_COLORS`, documented in `docs/README.md`). A new
figure, `baseline_travel_time_by_hour.png`, adds each line's baseline
travel time by departure hour (one curve per line, ±1 SEM shading).

## Headline figures

**`travel_time_all_lines.png`** — mean end-to-end baseline travel time
per line (both directions pooled), sorted longest to shortest, with
error bars = SEM (std kept as a separate column — it still tells the
chaos story: a large std means individual trip durations vary a lot):

| Line | Mean end-to-end (min) | SEM | Std dev | n (pooled blocks) |
|---|---|---|---|---|
| 9 | 89.7 | 0.36 | 14.6 | 1,605 |
| 22 | 74.3 | 0.27 | 11.6 | 1,879 |
| 15 | 65.5 | 0.40 | 13.7 | 1,187 |
| 17 | 59.7 | 0.31 | 9.6 | 944 |
| 19 | 55.5 | 0.22 | 10.5 | 2,191 |
| 14 | 48.7 | 0.25 | 10.3 | 1,739 |
| 97 | 43.6 | 0.20 | 9.1 | 2,145 |

Line 9 is both the longest-duration and one of the most variable trips
in the network; line 97 is the shortest and most predictable. Every
SEM is small relative to its line's std (n is in the thousands for
every line), so the *mean* end-to-end time is known precisely for all 7
lines — std, not SEM, is the number that distinguishes "reliable" from
"chaotic" lines here. Every line's weekday pattern follows the same
shape: Sun–Thu roughly even, Friday cut, Saturday lowest — with line 15
carrying by far the highest absolute ride volume.

**`baseline_travel_time_by_hour.png`** (new) — the same 7 lines' mean
baseline travel time by departure hour, one curve per line. Every line
follows a similar midday-peak shape (slowest around 14:00–15:00,
fastest early morning and late evening), confirming the aggregate
day-of-week story above isn't hiding very different within-day shapes
across lines — the lines mainly differ in overall level, not in when
during the day they're slowest.

Per-line detail: [line_9](line_9/README.md), [line_14](line_14/README.md),
[line_15](line_15/README.md), [line_17](line_17/README.md),
[line_19](line_19/README.md), [line_22](line_22/README.md),
[line_97](line_97/README.md).

**Sources:** `govData/df_cleaned.csv`, `govData/variant_merges.json`,
`pipeline/variant_merges.py`, `pipeline/pooled_analysis.py`,
`pipeline/config.py`, `pipeline/plot_baselines.py`,
`pipeline/plot_travel_time_all_lines.py`.
