# 06 — Line 22: Blockade Frequency

Definition and cross-line context: [docs/06_blockade_frequency](../README.md).
**Revision round:** single combined-direction heatmap, new >15-stop rule.

**Overall: 11.7% non-baseline (266/2,267 blocks) — up from 0.2% in the
first pass; Saturday: 51.2% (n=80).** This is the direct fix for the
contradiction investigated in
[docs/07_blockade_investigation](../../07_blockade_investigation/README.md):
line 22's largest closure variant (n=96, 51 stops) now clears the
new >15-stop threshold and is correctly counted. The May weekday
pattern (Tue/May=62%, Mon/May=60%) is now visible for line 22 for the
first time, matching the shape already seen on lines 17/19.

## Revision round 4 — why direction B disagrees, and what it does instead

[disagreement_deep_dive.md](../disagreement_deep_dive.md) traced line
22's 51.2% pooled Saturday share to a direction split: direction_A is
69%, direction_B only 32%. Direction_B's reference route touches only 2
of the 10 stops in the 17/19 blockade footprint (vs. 3 for direction_A,
whose main non-baseline variant skips exactly those 3 — a genuine
corridor detour), and its own "blocked" variants are 1-stop swaps
elsewhere on the route, not corridor detours — so direction_B's 32%
overstates its real exposure to the closure. Two consequences:

- **Section B:** `blockade_saturday_summary.png` (the project-wide
  Saturday comparison) now computes line 22's row from **direction_A
  only** ("Line 22 (dir A)") — direction_B is excluded from that figure
  entirely. The per-line figures on this page (`blockade_frequency_22.png`,
  both directions pooled) and the 11.7%/51.2% headline above are
  unchanged — they describe the whole line, not this one comparison.
- **Section A — new figure:** [saturday_timeline_and_cost_22B.png](saturday_timeline_and_cost_22B.png)
  shows what direction_B does instead of detouring: on Saturday evenings
  (19:00–24:00) when every other shared-corridor line/direction shifts
  from blocked to regular later in the evening, 22B is regular-majority
  almost throughout — it drives straight through the closure rather than
  detouring around it. Doing so isn't free: in the confirmed 17/19
  blockade slots, 22B's own reference-route travel time averages ~5 min
  more than in other Saturday slots (n=21 vs n=5, small control group —
  reproduces the deep dive's ~4.5 min finding). It passes, but pays.

**Sources:** `govData/df_cleaned.csv`, `pipeline/plot_blockade_frequency.py`,
[docs/06_blockade_frequency/disagreement_deep_dive.md](../disagreement_deep_dive.md).
