# 04 — Baseline (Most Common) Variant per Line

**Revision note:** as of this revision round, stats and the headline
figure are pooled across both directions of each line (section C) — a
line's baseline trip-time distribution combines rides from both
directions into one sample. The per-direction stop-by-stop figures
(`baseline_direction_A.png` / `_B.png`) are kept for route-shape detail,
now built on the *merged* baseline variant from
[docs/03_variants](../03_variants/README.md) instead of the raw stage4
reference.

## Headline figure

**`travel_time_all_lines.png`** — mean end-to-end baseline travel time
per line (both directions pooled), sorted longest to shortest, with
error bars = one standard deviation (tall bars = unpredictable line):

| Line | Mean end-to-end (min) | Std dev | n (pooled blocks) |
|---|---|---|---|
| 9 | 89.7 | 14.6 | 1,605 |
| 22 | 74.3 | 11.6 | 1,879 |
| 15 | 65.5 | 13.7 | 1,187 |
| 17 | 59.7 | 9.6 | 944 |
| 19 | 55.5 | 10.5 | 2,191 |
| 14 | 48.7 | 10.3 | 1,739 |
| 97 | 43.6 | 9.1 | 2,145 |

Line 9 is both the longest-duration and one of the most variable trips
in the network; line 97 is the shortest and most predictable. Every
line's weekday pattern follows the same shape: Sun–Thu roughly even,
Friday cut, Saturday lowest — with line 15 carrying by far the highest
absolute ride volume.

Per-line detail: [line_9](line_9/README.md), [line_14](line_14/README.md),
[line_15](line_15/README.md), [line_17](line_17/README.md),
[line_19](line_19/README.md), [line_22](line_22/README.md),
[line_97](line_97/README.md).

**Sources:** `govData/df_cleaned.csv`, `govData/variant_merges.json`,
`pipeline/variant_merges.py`, `pipeline/pooled_analysis.py`,
`pipeline/plot_baselines.py`, `pipeline/plot_travel_time_all_lines.py`.
