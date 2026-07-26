# 10 — Candidate (Month, Day-of-Week) Windows for an Hour-Level Deep Dive

**Purpose:** scan the full year, all 7 lines, for NEW (month, day_of_week)
cells worth a follow-up hour-level deep dive, using a signal that is the
*opposite* of the one already investigated in
[docs/06_blockade_frequency/disagreement_deep_dive.md](../06_blockade_frequency/disagreement_deep_dive.md).
That analysis found cells where most protest lines sit near 100%
blockade-share and one disagrees (line 22 direction B's geometry, fully
explained). Here we instead look for cells where **no line is near
saturation, but several lines simultaneously show a similar, moderate,
above-their-own-typical share** -- a pattern that would not stand out as a
"wall of red" in the existing per-line heatmaps but is suspicious precisely
because independent lines agree on it. This deliverable is **only** the
scan, figures, and ranked candidate list -- no hour-level investigation was
run; that is the next stage, pending review.

**Data / method:** same effective, merged classification as phase 06 --
`pipeline.variant_merges.build_effective_df_cleaned` applied to
`govData/df_cleaned.csv` + `govData/variant_summary.csv`, `variant_type_v2`
as the blocked/regular/reference/noise/non_corridor label, hours and
directions pooled per (line, month, day_of_week) exactly as
`pipeline/plot_blockade_frequency.py`'s `fraction_pivot` does -- **except
line 22, which is direction_A only** (`config.LINE_22_SHARE_DIRECTION`),
matching phase 06's policy (see `fix_22b_central_prompt.md` note below).
(The on-disk copy of `plot_blockade_frequency.py` in this checkout is
truncated -- it ends mid-docstring around line 310, confirmed shorter
than the same file at `git show HEAD` -- so
`pipeline/analyze_candidate_windows.py`, which produced everything in
this folder, reimplements `fraction_pivot` / `draw_panel` verbatim rather
than importing the broken module. That file was not modified.)

**`fix_22b_central_prompt.md`:** this phase originally pooled both
directions of line 22 like every other line (no special case existed
here at all). Line 22 direction_B's non-reference variants are now
centrally reclassified `"non_corridor"` (never `"blocked"`) in
`pipeline.variant_merges`, so pooling would have diluted line 22's real
corridor exposure with direction_B's untouched-by-the-closure schedule
sitting in the denominator -- this phase now filters line 22 to
direction_A only, matching docs/06. **Every line-22 number below changed**
(usually roughly doubling the share and roughly halving the n, since
direction_B contributed real denominator volume but essentially zero
numerator); every other line's numbers are exactly as before, since only
line 22's classification/pooling changed.

**Thresholds used** (all in `pipeline/analyze_candidate_windows.py`):
- A cell is reliable only if `n >= 8` (CLAUDE.md's own low-confidence
  floor, issue #6).
- "No line near saturation" = every reliable line in that cell has share
  `< 85%`.
- A line's own baseline = the median share across all of *its* reliable,
  non-Saturday cells (Saturday is excluded from the baseline itself since
  it is already known/expected to run higher -- CLAUDE.md issue #5,
  docs/06's Saturday-concentration finding). **Every one of the 7 lines'
  weekday baseline came out to 0%** -- on a typical weekday, a line's
  month/day cell has essentially no blocked variants at all. This means
  "elevated" here is effectively an absolute-threshold test (share ≥ 15pp
  above an already-zero baseline), not a relative one -- worth keeping in
  mind when reading "elevated vs. baseline" below.
- "Elevated" = reliable, non-saturating, and share ≥ baseline + 15
  percentage points.
- A cell qualifies as a candidate if **≥ 3 lines** are elevated
  simultaneously.

**Figures:** `blockade_frequency_<line>.png` for all 7 lines (same house
style as docs/06: Reds colormap, 0-1 scale, % annotated, labeled colorbar)
and `blockade_all_lines_grid.png` (7-panel grid, shared 0-100% scale, for
scanning by eye). **Data:** `all_lines_month_day_share.csv` (every line x
month x day_of_week cell, share + n) and `candidate_windows.csv` (the
ranked list below).

## Ranked candidate list

| Rank | Month, Day | Lines elevated (share, n) | Max share in cell | Assessment |
|---|---|---|---|---|
| 1 | **Nov, Wed** | 17: 67% (n=21), 9: 55% (n=29), 22: 53% (n=19, dir A), 19: 51% (n=43), 97: 35% (n=37) | 67% | **Strongest candidate.** All 5 protest lines elevated together, decent n throughout (19-43), nothing near saturation. Crucially, this spans **both** documented exposure groups at once -- the shared-corridor lines (17/19/22) *and* the Aza St. lines (9/97), which docs/06 treats as physically separate ("9/97 Aza St. non-shared" vs. "17/19/22 shared blocked segment" -- see `SATURDAY_SUMMARY_GROUPS` in `pipeline/plot_blockade_frequency.py`). Two supposedly-independent exposure groups agreeing on the same weekday is the kind of signal that would not show up as a red wall (nothing exceeds 67%) but is hard to explain as coincidence. Line 22's rank within the cell moved up (37%→53%) once isolated to direction A, but the cell's own ranking and verdict are unchanged. |
| 2 | **Dec, Wed** | 22: 21% (n=19, dir A), 19: 20% (n=41), 17: 19% (n=21), 9: 16% (n=32) | 21% | Good n (19-41), crosses groups (corridor 17/19/22 + line 9). **The old caveat here is resolved, not just softened:** before `fix_22b_central_prompt.md`, line 22's pooled share was 61% (n=38), pinned near 50% every December weekday -- a red flag for a construction artifact rather than a real pattern (see docs/11 Part B, which diagnosed the exact cause: direction_B's non-corridor variant ran on effectively 100% of its December trips that month). With direction_B centrally excluded, line 22's real (direction_A) December-Wednesday share is a modest **21%** -- squarely in the same range as the other three lines, consistent with a small, genuine, footprint-matching closure (docs/11 confirms 4 real corridor-detour blocks, 13:00-17:00), not an outsized anomaly. |
| 3 | **Oct, Mon** | 17: 55% (n=11), 19: 50% (n=42), 22: 50% (n=18, dir A), 9: 17% (n=23) | 55% | Crosses groups (corridor + line 9). Line 17's n=11 is thin; 19/22 have solid n (18-42). Line 22's share nearly doubled (32%→50%) once isolated to direction A. |
| 4 | Apr, Thu | 22: 42% (n=19, dir A), 17: 38% (n=16), 19: 32% (n=38) | 42% | Only the already-linked corridor trio (17/19/22) -- consistent with the known closure simply running at partial weekday intensity, so less novel than #1-3, but still not previously examined at the hour level. Line 22 is now the *highest* of the three (was the lowest, 27%→42%, once isolated to direction A). |
| 5 | Apr, Wed | 19: 29% (n=41), 17: 21% (n=14), 22: 19% (n=16, dir A) | 29% | **New candidate, not present in the pre-fix scan** -- corridor trio only. Plausibly went unflagged before because line 22's diluted, pooled share sat below the elevation threshold or blurred together with the adjacent Apr/Thu cell; worth an hour-level look alongside #4. |
| 6 | May, Sun | 17: 60% (n=10), 19: 43% (n=23), 22: 32% (n=19, dir A) | 60% | Corridor trio only (matches rony's original illustrative guess of a May pattern, but only Sunday holds up -- see caveats). Line 22's share doubled (16%→32%) once isolated to direction A. |
| 7 | May, Tue | 22: 75% (n=16, dir A), 19: 64% (n=25), 9: 50% (n=10) | 75%* | *Line 17 is at 86% share this cell but on n=7, just under the n≥8 reliability floor, so it was excluded from the saturation check -- meaning this cell likely IS close to saturation and is really an extension of the already-documented corridor closure, not a new moderate-agreement pattern. Downgraded accordingly (unchanged by the line-22 fix: line 17 isn't line 22). Line 22's own share jumped sharply (62%→75%) once isolated to direction A, reinforcing the near-saturation read. |

**Not included as new findings (already-known / low-confidence):**
- **Jan Sat, Feb Sat, Mar Sat** (4, 4, 3 lines elevated respectively,
  shares up to 80%): all have n = 8-12 per line, right at or barely above
  CLAUDE.md's own low-confidence floor (issue #6) and consistent with the
  general Saturday sparsity already flagged in CLAUDE.md issue #5 --
  Saturdays project-wide already run at 51-84% share per
  docs/06_blockade_frequency/README.md's cross-line summary table, so a
  handful more elevated Saturdays is the expected pattern continuing, not
  a new signal. **Line 22 no longer appears as elevated in any of these
  three cells** -- not because its share dropped (it's 50-75%, same range
  as the other lines), but because splitting to direction_A alone pushes
  its n below the reliability floor here (n=4-6, was n=8-12 pooled) --
  worth remembering if line 22 is ever specifically wanted from a winter
  Saturday: the data may simply be too thin post-split. Flagging as
  **low-confidence, not novel** -- explicitly excluded from the ranked
  list above per the task's instruction not to re-flag known Saturday
  behavior.
- **May Mon** (9: 85%, 17: 90%, 19: 85%, 22: 94% [dir A, was 60% pooled],
  all n=10-35): excluded entirely by the saturation filter -- most lines
  are already at/near 100% here, so this is the *already-known* pattern
  (docs/06's near-saturation disagreement story), not the moderate-agreement
  pattern being hunted. Line 22's own share rose sharply once isolated to
  direction A, reinforcing that this cell is genuinely saturated, not a
  borderline case the old pooled number understated.

## Reliability notes for rony

- Every candidate's supporting n is reported in the table above --
  cross-check anything with n below ~15-20 per line carefully before
  committing analysis time; n in the 8-19 range (all three flagged
  Saturdays, line 17 in Oct/May, and now every line-22 dir-A cell) is
  barely above the project's own low-confidence floor. **Line 22's n
  roughly halved project-wide** once split to direction_A only
  (`fix_22b_central_prompt.md`) -- treat any line-22 cell here with
  slightly more caution on sample size than before, even though the
  share itself is now more trustworthy.
- The three winter Saturdays and "May Mon" were deliberately excluded as
  not-novel per the task brief; they are listed above for transparency,
  not as recommendations.
- December's line-22 pattern (rank #2) is **no longer** a December-wide
  weekday artifact -- see docs/11 Part B, which traced and fixed exactly
  this (direction_B's spurious near-100% December activity). The
  remaining Wednesday-specific 21% is a small, real, footprint-matching
  signal.
- Control lines 14 and 15 never appear in any candidate row (their few
  non-zero cells top out at 10-15%, below the elevation threshold, and
  never co-occur with 2 others), consistent with docs/06's finding that
  their small nonzero shares are noise, not real detours -- this is a
  useful sanity check that the elevation criterion isn't just picking up
  general classification noise.

**Sources:** `govData/df_cleaned.csv`, `govData/variant_summary.csv`,
`govData/variant_merges.json`, `pipeline/variant_merges.py`,
`pipeline/analyze_candidate_windows.py` (this phase's script; reimplements
`pipeline/plot_blockade_frequency.py`'s `fraction_pivot`/`draw_panel` since
that file is truncated on disk in this checkout -- see note above),
[docs/06_blockade_frequency](../06_blockade_frequency/README.md),
[disagreement_deep_dive.md](../06_blockade_frequency/disagreement_deep_dive.md).
