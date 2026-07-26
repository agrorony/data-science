# 06 — Line 14: Blockade Frequency (Control)

Definition and cross-line context: [docs/06_blockade_frequency](../README.md).
**Revision round:** single combined-direction heatmap, new >15-stop rule.

## Revision round 4 addendum — line 14 reclassified to never-blocked

**Before this round: 0.8% non-baseline (14/1,852 blocks); Saturday:
3.1% (n=65).** [docs/07's addendum](../../07_blockade_investigation/README.md)
attributed this to the new >15-stop rule occasionally catching a rare,
single-observation route deviation with no way to distinguish it from a
real detour except low frequency.

Round 4 investigated those exact 14 slots
([blocked_slots_investigation.md](blocked_slots_investigation.md)) and
confirmed they are not detours: line 14's route shares **0 stops** with
the 17/19 blockade footprint, so it cannot physically detour around the
closure at all; the 11 underlying merged variants are all
near-singletons (ten n=1, one n=4) that skip 1–6 stops clustered in two
zones of the route and **add zero new stops** — the signature of a
missed stop-detection event, not a route change; their timing scatters
across weekdays and hours with no Saturday-evening concentration (8 of
14 land on Tuesdays); and their travel time is unaffected (deltas from
−8.1 to +12.5 min, mean +1.8 min, mixed signs — ordinary traffic
variance).

**Fix:** `pipeline.variant_merges.build_effective_variant_summary` now
forces every non-reference line-14 merged variant to
`variant_type_v2 == "noise"` instead of classifying by stop count, so
line 14 can never register as `"blocked"` anywhere in the pipeline.

**After: 0.0% non-baseline everywhere (overall and every month/day
cell), including Saturday (n=65 blocks, all reference).**

**Figures/stats that changed as a result:**

- `line_14/blockade_frequency_14.png` (this line's own heatmap — now
  all-zero) and the two project-wide figures that include it:
  `docs/06_blockade_frequency/blockade_all_lines.png` and
  `blockade_saturday_summary.png` (both regenerated; every other line's
  numbers are unchanged).
- `docs/05_skip_comparison/`: line 14 already had no delta figure
  before this round (its "blocked" bucket was filtered out by that
  phase's own `count>5` significance floor) — round 4 makes that
  absence permanent at the classification level instead of a
  phase-local filter; no numeric change.
- `docs/08_control_lines_15_14/` and `docs/09_lines_9_97/`: **verified
  unchanged.** Line 14 is never one of the `SOURCE_LINES` ([17, 19,
  22]) that define a blockade window, so its former "blocked" slots
  never leaked into any window definition; `control_comparison_stats.csv`
  and `blockade_windows_used.csv` are byte-identical before/after this
  change (line 14's own stats there use only `variant_type_v2 ==
  "reference"` blocks, which this change doesn't touch).
- `docs/04_baselines/`: verified unchanged (baseline-only figures,
  never reference `"blocked"`).

**Sources:** `govData/df_cleaned.csv`, `pipeline/plot_blockade_frequency.py`,
`pipeline/variant_merges.py`,
[blocked_slots_investigation.md](blocked_slots_investigation.md).
