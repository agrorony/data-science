# 06 — Line 22: Blockade Frequency

Definition and cross-line context: [docs/06_blockade_frequency](../README.md).
**Revision round:** single combined-direction heatmap, new >15-stop rule.

**Overall (direction A only): 9.9% non-baseline (113/1,136 blocks) — up
from 0.2% in the first pass; Saturday: 69.0% (n=42).** This is the direct
fix for the contradiction investigated in
[docs/07_blockade_investigation](../../07_blockade_investigation/README.md):
line 22 direction_A's largest closure variant (n=96, 51 stops) now clears
the new >15-stop threshold and is correctly counted. The May weekday
pattern (Tue/May=75%, Mon/May=94%) is now visible for line 22 for the
first time, matching the shape already seen on lines 17/19.

**`fix_22b_central_prompt.md`:** every number on this page is now
direction_A only, not both-directions-pooled. Previously reported as
11.7% overall / 51.2% Saturday (n=80, Tue/May=62%, Mon/May=60%) — that
was the both-directions-pooled figure, which (per the direction split
below) always overstated direction_B's real exposure and, after
direction_B's non-reference variants were centrally reclassified
`"non_corridor"` (never `"blocked"`), would instead have understated line
22's real corridor exposure by diluting the denominator with
direction_B's untouched-by-the-closure schedule. Recomputed
both-directions-pooled with the current, correct classification, this
line's overall/Saturday share would read 5.0%/36.2% (n=80) — neither
number is used anywhere on this page anymore; see
[docs/06_blockade_frequency/README.md](../README.md) for the project-wide
version of this same correction.

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
  Saturday comparison) computes line 22's row from **direction_A
  only** ("Line 22 (dir A)") — direction_B is excluded from that figure
  entirely. As of `fix_22b_central_prompt.md`, the per-line figure on
  this page (`blockade_frequency_22.png`) and the headline above are
  **also** direction_A only now, for the same reason (see the note
  above) — this used to be Section B's one exception, it no longer is.
- **Section A — new figure:** [saturday_timeline_and_cost_22B.png](saturday_timeline_and_cost_22B.png)
  shows what direction_B does instead of detouring: on Saturday evenings
  (19:00–24:00) when every other shared-corridor line/direction shifts
  from blocked to regular later in the evening, 22B's detour share is
  **0% throughout** (`fix_22b_central_prompt.md` — direction_B's
  non-reference variants are all non-corridor 1-stop swaps, never a real
  detour, so they're centrally reclassified `"non_corridor"` and never
  count as `"blocked"`; before that fix this row showed a low-but-nonzero
  20–67% share) — it drives straight through the closure rather
  than detouring around it. Doing so isn't free: in the confirmed 17/19
  blockade slots, 22B's own reference-route travel time averages ~5 min
  more than in other Saturday slots (n=21 vs n=5, small control group —
  reproduces the deep dive's ~4.5 min finding). It passes, but pays.

  **Statistical backing** ([docs/12_statistics](../../12_statistics/README.md)):
  a permutation test on the pass-through cost gives Δmean = +5.1 min [95%
  CI +2.8, +7.3], p = 0.017 -- statistically supported despite the small
  n=5 control group, though the wide CI (nearly 2x the point estimate)
  reflects exactly that small sample and should be read accordingly.

  **Revision round 5:** the top panel plots a share gradient instead
  of a binary majority-vote status — each cell is the % of Saturdays
  (distinct months with data for that hour-slot, up to 12, Jan–Dec) on
  which the line ran a detour variant, annotated with its evidence base
  as `k/n` Saturdays, with hatched gray cells marking hours the line
  never ran on any Saturday (visually distinct from a real 0% cell).
  Summing each row's hourly `k`/`n` across 19:00–24:00 gives 22A =
  29/42 = 69.0%, matching this page's headline Saturday share above
  exactly. **22B = 0/38 = 0%** as of `fix_22b_central_prompt.md` (was
  12/38 = 31.6% before direction_B's non-corridor variants were
  centrally reclassified out of `"blocked"` — that 31.6% figure had
  matched `disagreement_deep_dive.md`'s pooled-share breakdown at the
  time, which is itself the investigation that diagnosed this exact bug;
  see the historical note in that document). The underlying `k`/`n`
  table is saved as [saturday_timeline_data.csv](saturday_timeline_data.csv).

**Sources:** `govData/df_cleaned.csv`, `pipeline/plot_blockade_frequency.py`,
[docs/06_blockade_frequency/disagreement_deep_dive.md](../disagreement_deep_dive.md).
