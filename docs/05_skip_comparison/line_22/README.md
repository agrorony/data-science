# 05 — Line 22: Baseline vs. Blocked/Special Variant

Method and headline finding: [docs/05_skip_comparison](../README.md).

**n=210 blocked vs n=1,879 baseline blocks (pooled directions, after the
round-3 count>5 significance floor — see main README section B2);
overall median delta: −3.1 min — the smallest time saving of any
line**, and 18 of 19 hours have enough data to be well-supported (the
best coverage in this phase).

**Answer:** line 22's blocked/special variant still saves time on
average, but by less than lines 9/17/19/97 — plausibly because line
22's baseline route (55/52 stops, the longest scope) means its blocked
variant skips a proportionally smaller slice of a much longer trip (see
[docs/07_blockade_investigation](../../07_blockade_investigation/README.md)
on why line 22's route length matters for classification too), and per
[docs/05_skip_comparison](../README.md) section F, line 22's detour is
barely different in distance from its baseline at all (+0.9%).

**Sources:** `govData/df_cleaned.csv`, `pipeline/plot_baseline_vs_blocked_delta.py`.
