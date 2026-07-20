# 04 — Line 15: Baseline Variant (Control)

Line 15 has no direction split (single group, loop route — see
[docs/02_route_mapping](../../02_route_mapping/README.md)), so pooling
directions (section C) doesn't change anything here versus the first
pass. No merges apply
([docs/03_variants/line_15](../../03_variants/line_15/README.md)).

**n=1,187 baseline blocks, mean end-to-end time 65.5 ± 13.7 min.**

**Weekday pattern:** Sun 6,050, Mon 5,706, Tue 5,917, Wed 5,608, Thu
5,812, Fri 2,460, Sat 1,152 — by far the highest absolute ride volume
of any line in scope.

**Sources:** `govData/df_cleaned.csv`, `pipeline/pooled_analysis.py`,
`pipeline/plot_baselines.py`, `pipeline/plot_travel_time_all_lines.py`.
