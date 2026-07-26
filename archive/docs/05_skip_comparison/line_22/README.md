# 05 — Line 22: Baseline vs. Blocked/Special Variant

Method and headline finding: [docs/05_skip_comparison](../README.md).

**fix_22b_central_prompt.md:** this page's numbers are now computed from
**direction A only**, both the plotted curve and the stats test (see
[docs/06_blockade_frequency/line_22](../../06_blockade_frequency/line_22/README.md)
for why direction B is excluded project-wide). Previously the plotted
curve stayed both-directions-pooled while only the stats test filtered to
direction_A — an inconsistency introduced by the fact that direction_B's
own non-reference variants used to be (wrongly) labeled "blocked" too, so
pooling them in didn't obviously look wrong. Now that direction_B is
centrally reclassified `"non_corridor"`, pooling would still dilute the
comparison (direction_B's untouched-by-the-closure baseline rides sitting
in the denominator), so both halves of this figure use direction_A only.

**n=81 blocked vs n=972 baseline blocks (direction A only, after the
round-3 count>5 significance floor — see main README section B2);
overall median delta: −8.4 min**, in the same range as lines 19 (−8.7)
and 97 (−8.0), not the outlier smallest saving the old pooled curve
showed (−3.1 min, n=210/1,879 — that number mixed in direction_B's
trivial, non-corridor variant, which barely changes travel time and
dragged the pooled median toward zero).

**Answer:** line 22 direction_A's real corridor detour saves about as
much time as the other shared-corridor lines. Per
[docs/05_skip_comparison](../README.md) section F, its detour is also
meaningfully *shorter* in distance than its baseline (−7.1%, not the
previously-reported "~flat +0.9%" — that number was accidentally built
from direction_B's dominant variant, the wrong one for this comparison).

**Sources:** `govData/df_cleaned.csv`, `pipeline/plot_baseline_vs_blocked_delta.py`,
`pipeline/variant_merges.py`.
