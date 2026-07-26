# 05 — Line 97: Baseline vs. Blocked/Special Variant

Method and headline finding: [docs/05_skip_comparison](../README.md).

**n=61 blocked vs n=2,145 baseline blocks (pooled directions, after the
round-3 count>5 significance floor — see main README section B2);
overall median delta: −8.0 min.**

**Answer:** line 97's blocked/special variant saves time overall,
consistent with every other line in this phase.

## Detour-distance figure (revision round 3, section F)

`detour_distance.png` — cumulative distance (km) along line 97's
baseline route vs. its dominant detour variant (direction_A). The
detour ends **7.94 km vs. the baseline's 9.64 km (−1.70 km, −17.7%)** —
counterintuitively *shorter*, not longer. Read together with
[docs/09_lines_9_97](../../09_lines_9_97/README.md)'s finding that line
97's own detour costs up to +14 minutes during hours 14:00–17:00 despite
saving time overall: the delay during those specific hours cannot be
explained by extra distance, so it must be congestion or signal time on
the (shorter) detour route itself. See
`detour_distance_all_lines.png` (in the parent
[docs/05_skip_comparison](../README.md) folder) for the same comparison
on lines 9/17/19/22, for context.

**Sources:** `govData/df_cleaned.csv`, `pipeline/plot_baseline_vs_blocked_delta.py`.
