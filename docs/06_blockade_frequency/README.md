# 06 — Blockade/Variant Frequency Characterization

**Revision round (sections C, E):** this phase now shows only **one
combined, both-directions-pooled heatmap per line** — the per-direction
panels from the first pass have been removed. "Non-baseline (blocked)"
now uses the new absolute-stop-count rule (section B: any non-reference
merged variant with >15 stops, no fraction threshold) applied to the
merged/excluded variant set from [docs/03_variants](../03_variants/README.md),
not the original stage5 `variant_type` column. House style is
unchanged: Reds colormap, 0–1 scale, % annotated per cell, labeled
colorbar, bold panel title.

**Revision round 2 (section C):** two new figures add a project-wide
view on top of the existing per-line heatmaps: `blockade_all_lines.png`
(all 7 lines as subplots in a 4×2 grid, one shared colorbar, common
0–100% scale so panels are directly comparable) and
`blockade_saturday_summary.png` (rows = lines, columns = months, cell =
Saturday blockade share — a compact single-panel view of the
Saturday-concentration pattern already visible per line below). Line
97's new exclusion ([docs/03_variants](../03_variants/README.md),
direction B variant 2) drops its overall share slightly (5.0% → 4.7%);
every other line's numbers are unchanged (line 19's new exclusion was
already classified `regular`, not `blocked` — see docs/03).

**Revision round 3:**

- **Section A (palette):** row/panel labels for lines now use the
  single project-wide color per line (`pipeline.config.LINE_COLORS`,
  documented in `docs/README.md`) wherever more than one line appears —
  applied to `blockade_saturday_summary.png`'s row labels and
  `disagreement_windows.png`'s row labels below (the month×day heatmaps
  themselves stay on the Reds share-scale, which encodes share, not
  line identity).
- **Section D:** `blockade_saturday_summary.png`'s rows are now grouped
  and visually separated: **17/19/22** (shared blocked segment) →
  **9/97** (Aza St., non-shared) → **14/15** (controls), instead of the
  previous numeric-ish order.
- **Section C (new analysis below):** for the two (month, day) cells
  where most protest lines sit near 100% but one or two disagree
  substantially, a new figure (`disagreement_windows.png`) and CSV
  (`disagreement_windows.csv`) show each line's actual per-hour schedule
  and variant type for that exact cell.

**Revision round 4:**

- **Section C — line 14 reclassified to never-blocked:** line 14's 14
  "blocked" slots (11 merged variants, all near-singleton) were
  confirmed to be single-trip stop-recording dropouts, not detours —
  its route shares 0 stops with the 17/19 blockade footprint, the
  flagged variants add zero new stops, their timing has no
  Saturday-evening pattern, and their travel time is unaffected (see
  [docs/06_blockade_frequency/line_14/blocked_slots_investigation.md](line_14/blocked_slots_investigation.md)).
  `pipeline.variant_merges` now forces every non-reference line-14
  variant to `variant_type_v2 == "noise"` instead of `"blocked"`, so
  line 14's blockade share is **exactly 0% everywhere** (was 0.8%
  overall / 3.1% Saturday) — every figure below reflects this. See
  [line_14](line_14/README.md) for the full before/after.
- **Section B — Saturday summary excludes 22B:** `blockade_saturday_summary.png`'s
  line-22 row is now computed from **direction_A only** — direction_B
  barely touches the blockade footprint (2 of the 10 footprint stops)
  and its nominal share was inflated by non-corridor 1-stop variants,
  not genuine detours (see
  [disagreement_deep_dive.md](disagreement_deep_dive.md), Hypothesis
  1). The row is now labeled "Line 22 (dir A)"; every other row is
  unchanged (still both directions pooled). This affects only that one
  figure — the per-line `blockade_frequency_22.png` and the
  cross-line-summary table below still pool both directions, since the
  deep dive's finding is specific to Saturday-evening behavior.
- **Section A — new figure explaining 22B:** [line_22/saturday_timeline_and_cost_22B.png](line_22/README.md)
  shows why 22B disagrees instead of just excluding it: a Saturday-evening
  timeline (19:00–24:00, all six protest-line/direction rows) alongside
  22B's own pass-through time cost when it drives through the 17/19
  blockade instead of detouring.

## Cross-line summary (overall non-baseline share, both directions pooled)

| Line | Overall share | Saturday share | n (Saturday blocks) |
|---|---|---|---|
| 9 | 7.0% | 84.1% | 82 |
| 14 (control) | **0.0%** | **0.0%** | 65 |
| 15 (control) | 0.3% | 0.0% | 56 |
| 17 | 12.2% | 80.5% | 82 |
| 19 | 8.9% | 75.7% | 74 |
| 22 (dir A) | **9.9%** | 69.0% | 42 |
| 97 | 4.7% | 66.4% | 110 |

(This table pools both directions of every line **except line 22**, which
is direction_A only, matching every other figure in this phase --
`fix_22b_central_prompt.md` retired the previous "one exception" framing.
Before that fix this row *did* pool both directions like every other line
(11.7% overall / 51.2% Saturday, n=80), since direction_B's non-reference
variants were still occasionally mislabeled "blocked" and pooling didn't
look obviously wrong. Now that direction_B is centrally reclassified
`"non_corridor"` and never contributes to the numerator, pooling would
only dilute the denominator with its untouched-by-the-closure schedule --
recomputed both-directions-pooled the row would read 5.0%/36.2% (n=80),
which understates line 22's real corridor exposure and would visually
contradict `blockade_frequency_22.png` below. See
[disagreement_deep_dive.md](disagreement_deep_dive.md) and
[line_22/README.md](line_22/README.md).)

**Line 22 is fixed twice over.** In the first pass, line 22's overall
share (0.2%) sat at control-line level —
[docs/07_blockade_investigation](../07_blockade_investigation/README.md)
diagnosed this as a genuine classification bug (its real closure fell
just under the old 10%-of-route-length cutoff). The new >15-stop rule
fixed that, but introduced a second, subtler bug: direction_B's own
non-corridor variants sometimes cleared the same >15-stop threshold on
raw stop count alone, so pooling both directions inflated the numerator
with slots that were never real detours while also diluting it as a
denominator everywhere line 22 appears. `fix_22b_central_prompt.md`
closes that gap centrally
(`pipeline.variant_merges.LINE_22_NON_CORRIDOR_DIRECTION`). Direction_A
alone now shows **9.9%** overall — squarely with lines 9/17/19/97 — and
its May-weekday cells clearly show the same closure pattern as line 19
(see `blockade_frequency_22.png`: May Sat=100%, Sep Sat=100%, Tue/May=75%).

**Line 15 is not exactly 0%; line 14 is (round 4).** As documented in
[docs/07's addendum](../07_blockade_investigation/README.md), the new
>15-stop rule occasionally labels a rare, single-observation route
deviation as "blocked" simply because it has enough stops, with no way
to distinguish that from a real detour except low frequency — this is
still true of line 15 (0.3%). Line 14 was the same story (0.8%) until
round 4's investigation confirmed its flagged variants are specifically
stop-recording dropouts (see the addendum above); it is now reclassified
to `"noise"` and reads exactly 0%. Line 15 has not been investigated the
same way and keeps its small nonzero share.

## Why do protest lines disagree in "mostly-100%" windows? (revision round 3, section C)

Scanning every (month, day) cell for windows where most protest lines
(9/17/19/22/97) sit at ≥90% blockade share but at least one sits below
70% (n≥3 per line) finds exactly two: **Saturday April** and **Saturday
June**. In both, lines 17 (and usually 9/97) are at 100% while lines 19
and especially 22 are markedly lower (25–75%). This extends
[docs/07_blockade_investigation](../07_blockade_investigation/README.md)'s
Hypothesis 4 (line 22's smaller apparent exposure) with concrete
per-window schedule evidence, without modifying that folder.

`disagreement_windows.png` shows every protest line's exact per-(hour,
direction) slot for both Saturdays, colored by variant type. The answer
is unambiguous in both cases: **the disagreeing lines run the SAME
hour-slots as the 100% lines — not extra, out-of-window service — but on
their regular/baseline variant instead of a blocked one.**

- **Saturday April, hours 22:00–23:00** (the slots common to 17/19/22):
  line 17 is `blocked` in all 4 slots (100%); line 19 is `blocked` in 3
  of 4 (75%, `reference` at 23:00 direction_A); line 22 is `blocked` in
  only 1 of 4 (25%, `reference` at 22:00 direction_B and both 23:00
  slots).
- **Saturday June, hours 21:00–23:00**: line 17 is `blocked` in all 6
  slots (100%); line 19 in 4 of 6 (67%, `reference` at both 23:00
  slots); line 22 in **2 of 6 (33%**, `reference`/`non_corridor` at
  21:00 and 22:00 direction_B and both 23:00 slots — was reported as 3
  of 6 (50%) before `fix_22b_central_prompt.md`, when 22:00 direction_B's
  trivial off-footprint variant was still mislabeled `blocked`).

**Conclusion: this is genuine differential exposure at the same moment
in time, not a scheduling or denominator artifact.** At the exact hours
line 17's buses were detouring around the closure, some of line 19's
and (more often) line 22's buses passed through on their normal route.
This is consistent with line 22's longer, only-partially-overlapping
corridor exposure documented in docs/07 — the closure evidently doesn't
block 100% of line 22's (or, less often, line 19's) scheduled trips
through the area even during its most active hours, while it does for
line 17.

## Pattern: still concentrated on Saturdays

Every non-control line's Saturday share is now well above its overall
share (51–84% vs. 5–12% overall), consistent with `CLAUDE.md` issue #5's
documented Saturday sparsity — fewer total Saturday blocks per cell
means single occurrences swing the percentage more. Line 9 (84.1%) and
line 17 (80.5%) now show the strongest Saturday concentration of any
line.

Per-line detail: [line_9](line_9/README.md), [line_14](line_14/README.md),
[line_15](line_15/README.md), [line_17](line_17/README.md),
[line_19](line_19/README.md), [line_22](line_22/README.md),
[line_97](line_97/README.md).

**Figures:** per-line `line_<N>/blockade_frequency_<N>.png`, the
combined `blockade_all_lines.png` and the compact, grouped
`blockade_saturday_summary.png` (round 2 section C, round 3 sections A/D,
round 4 section B: line 22's row is direction_A only), and
`disagreement_windows.png` (round 3 section C). Round 4 section A adds
[line_22/saturday_timeline_and_cost_22B.png](line_22/README.md).

**Sources:** `govData/df_cleaned.csv`, `govData/variant_merges.json`,
`pipeline/variant_merges.py`, `pipeline/config.py`,
`pipeline/plot_blockade_frequency.py`,
[docs/07_blockade_investigation](../07_blockade_investigation/README.md),
[disagreement_deep_dive.md](disagreement_deep_dive.md),
[line_14/blocked_slots_investigation.md](line_14/blocked_slots_investigation.md).
