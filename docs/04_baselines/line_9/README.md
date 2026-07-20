# 04 — Line 9: Baseline Variant

**Revision note:** stats below are now pooled across both directions
(section C); the baseline itself is the *merged* variant from
[docs/03_variants/line_9](../../03_variants/line_9/README.md) (direction_A:
raw 0+1 merged, `n=870`; direction_B: raw 0+1+3 merged, `n=776`).
Per-direction stop-by-stop figures (`baseline_direction_A.png`,
`baseline_direction_B.png`) are unchanged in style, just regenerated on
the merged baseline. See [docs/02_route_mapping](../../02_route_mapping/README.md)
for direction labels.

**Pooled (both directions): n=1,605 baseline blocks, mean end-to-end
time 89.7 ± 14.6 min** — the longest and, tied for one of the most
variable, trip duration of any line in scope (see
`docs/04_baselines/travel_time_all_lines.png`).

**Pooled weekday pattern (total rides by day, both directions):** Sun
3,593, Mon 3,120, Tue 3,325, Wed 2,836, Thu 3,370, Fri 1,951, Sat 132 —
the same Sun–Thu-even / Friday-reduced / Saturday-minimal shape seen
project-wide, with line 9's Saturday service the sparsest of any line
(132 pooled rides).

**Sources:** `govData/df_cleaned.csv`, `govData/variant_merges.json`,
`pipeline/variant_merges.py`, `pipeline/pooled_analysis.py`,
`pipeline/plot_baselines.py`, `pipeline/plot_travel_time_all_lines.py`.
