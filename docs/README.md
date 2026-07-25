# Project Documentation — Navigation Index

Prepared for the final course presentation on Israeli Jerusalem bus
transit EDA (course 71253). Each numbered folder is a report + figures
covering one phase of the analysis, in dependency order. **Phases 01
and 02 are approved and untouched.** Phases 03–09 were revised in a
second pass (see `prompts/revision_round_prompt.md`): clustering was
removed in favor of manual variant merges, the blocked-variant rule
changed from a 10%-missing-fraction threshold to a simple >15-stop
absolute rule, and phases 04/05/08/09 now pool both directions of a
line into one distribution instead of reporting them separately.

**Revision round 2** (see `prompts/revision_round_2_prompt.md`) added a
third pass on top of that: **phases 01, 02, 04, 07, 08 are now approved
and untouched** (phase 08's two figures were regenerated only to apply
the global hour rule below — their numbers did not change). Global rule:
**hours 25/26 (01:00/02:00 next day) no longer appear in any figure** —
dropped from the data entirely rather than relabeled. Two more variants
are excluded (line 19B variant 5, line 97B variant 2 — see
[docs/03_variants](03_variants/README.md)), phase 03's figures are now
one-per-line with vertical direction subplots, and phases 05/06/09 each
gained a new cross-line/combined figure.

**Revision round 3** (see `prompts/revision_round_3_prompt.md`) is a
fourth pass, all within phases 04, 05, 06, 08, 09 (01/02/03/07 untouched):
a single fixed color per line, used everywhere more than one line
appears (see "Color palette" below); phase 05 audited and fixed —
control lines 14/15 no longer appear there at all, having turned out to
be a pure artifact of the >15-stop rule with no volume floor (see
[docs/05](05_skip_comparison/README.md) section B2); phase 06 gained a
new per-window schedule analysis explaining why protest lines disagree
in "mostly-100%" windows, and its Saturday summary heatmap is now
grouped by physical exposure; phase 04 gained SEM error bars (std kept
alongside) and a new by-hour figure; a line-97 detour-distance figure
was added to phase 05; phase 08's two control-line figures are now one;
and a legend-overlap bug in phase 09's round-2 figures is fixed.

**Revision round 4** (see `prompts/revision_round_4_prompt.md`) is a
fifth pass on top of two data-backed investigations
([disagreement_deep_dive.md](06_blockade_frequency/disagreement_deep_dive.md),
[blocked_slots_investigation.md](06_blockade_frequency/line_14/blocked_slots_investigation.md)):
**line 14 is reclassified to never-blocked project-wide** — its 14
"blocked" slots were confirmed to be stop-recording dropouts, not
detours, so `variant_type_v2` now forces every non-reference line-14
variant to `"noise"` and its blockade share reads exactly 0% everywhere
(phases 04/05/08/09 verified unaffected or byte-identical, since none of
them treat line 14 as a blockade source); **line 22's Saturday summary
row now excludes direction B**, computed from direction_A only, since
direction_B barely touches the blockade footprint and its nominal share
was inflated by non-corridor variants; and a **new figure**
(`line_22/saturday_timeline_and_cost_22B.png`) explains what direction B
does instead of detouring — it drives through the closure on its
reference route at a small (~5 min) time cost, rather than rerouting
like every other shared-corridor line/direction.

## Color palette (revision round 3, section A)

One fixed color per line, defined once in `pipeline.config.LINE_COLORS`
and reused in every figure where more than one line appears (phases 04,
05's cross-line figures, 06's row/panel labels, 08's combined figure).
Phase 09 has no figure that overlays multiple *lines* against each other
(its dual-curve figures contrast two *conditions* for one line), so it
keeps its existing red/blue condition coding rather than forcing an
inapplicable per-line palette.

| Line | Color | Family |
|---|---|---|
| 17 | `#b30000` (dark red) | Shared blocked segment (Aza corridor) |
| 19 | `#e34a33` (red-orange) | Shared blocked segment |
| 22 | `#fc8d59` (orange) | Shared blocked segment |
| 9 | `#54278f` (dark purple) | Aza St., non-shared |
| 97 | `#9e9ac8` (light purple) | Aza St., non-shared |
| 14 | `#045a8d` (dark blue) | Control |
| 15 | `#74a9cf` (light teal) | Control |

The reds/purples are unchanged from round 2's
`plot_baseline_vs_blocked_delta.CROSS_LINE_COLORS` (now a thin wrapper
around `config.LINE_COLORS`), so no already-published figure's colors
shifted — only the two new blues for 14/15 are new.

1. **[Data cleaning](01_data_cleaning/README.md)** *(unchanged)* — how
   the raw government export becomes `govData/df_cleaned.csv`.
2. **[Route mapping](02_route_mapping/README.md)** *(unchanged)* — the
   key table every later phase links to: `route_id` → commercial line →
   `direction_A`/`direction_B` → terminal stops.
3. **[Raw and merged variants](03_variants/README.md)** *(revised, then
   revised again)* — clustering removed; raw stop-presence grids now
   show only variants observed >5 times, followed by a manual
   merge/exclude table (`govData/variant_merges.json`) that consolidates
   trivially-different variants and drops a handful entirely. Round 2:
   two more exclusions (19B variant 5, 97B variant 2), and figures are
   now one PNG per line (`variants_raw.png`, `variants_merged.png`) with
   each direction as a subplot instead of one PNG per (line, direction).
   This merged/excluded variant set is the source of truth for every
   later phase.
4. **[Baseline variants](04_baselines/README.md)** *(revised, untouched
   in round 2, revised again in round 3)* — stats pool both directions
   of a line; headline figure (`travel_time_all_lines.png`) ranks all 7
   lines by mean end-to-end baseline travel time, now with SEM error
   bars (std kept as a reported column) and the section-A palette. Round
   3 adds `baseline_travel_time_by_hour.png`, all 7 lines' baseline
   travel time by departure hour on one figure.
5. **[Baseline vs. blocked/special variant](05_skip_comparison/README.md)**
   *(revised three times)* — delta-style per-hour line charts (baseline
   vs. blocked variant, directions pooled). Round 2 added
   `delta_all_lines.png`. **Round 3: control lines 14 and 15 no longer
   appear in this phase at all** — audited and found to be a pure
   artifact of the >15-stop rule with no volume floor (their entire
   "blocked" bucket was singleton recording noise); a `count>5`
   significance floor removes them and trims a little noise from the
   five real protest lines. Also adds line 97's detour-distance figure
   (its detour is *shorter* than baseline, −17.7%, so its outsized delay
   at some hours is congestion, not extra distance).
6. **[Blockade/variant frequency](06_blockade_frequency/README.md)**
   *(revised four times)* — one combined (both-directions) heatmap per
   line under the new >15-stop rule; line 22 correctly lands alongside
   lines 9/17/19/97. Round 2 added `blockade_all_lines.png` and
   `blockade_saturday_summary.png`. **Round 3:** the Saturday summary is
   now grouped (17/19/22 → 9/97 → 14/15) with the section-A palette on
   row labels, and a new `disagreement_windows.png` explains two windows
   where line 22 (and sometimes 19) shows a much lower blockade share
   than lines 17/9/97 — genuine differential exposure at the same hours,
   not a scheduling artifact. **Round 4:** line 14 reclassified to
   `"noise"` — its blockade share is now exactly 0% everywhere (was
   0.8%/3.1%); the Saturday summary's line-22 row now excludes direction
   B (computed from direction_A only, labeled "22 (dir A)"); and a new
   `line_22/saturday_timeline_and_cost_22B.png` shows direction B driving
   through the closure instead of detouring, at a small time cost.
7. **[Blockade investigation](07_blockade_investigation/README.md)**
   *(original investigation unchanged; addendum added; approved since —
   untouched in rounds 2 and 3)* — the addendum documents the new rule's
   project-wide effect: 141 of 155 merged variants (91%) are now
   classified `blocked`, including a handful of single-observation
   deviations on the control lines.
8. **[Control lines 15 & 14](08_control_lines_15_14/README.md)**
   *(revised; approved since — round 2 regenerated its two figures only
   to drop hours 25/26, round 3 merged them into one)* — delta chart,
   line 14's two directions pooled, blockade windows recomputed under
   the new rule (320 slots, up from 112). The first pass's significant
   line 14 finding does not clearly survive this revision. Round 3:
   both lines' curves now share one figure (`control_lines_delta.png`,
   section-A palette) — numbers unchanged (diffed, byte-identical).
   **Round 4:** verified byte-identical again after line 14's
   reclassification — blockade windows here are built only from lines
   17/19/22, never line 14.
9. **[Lines 9 & 97 during blockades](09_lines_9_97/README.md)**
   *(revised three times)* — both directions pooled, updated 320-slot
   windows. Route-switching effects got much stronger (p≈0 for both
   lines); line 9 additionally shows a newly-significant Saturday
   travel-time delay (+11.7 min). Round 2 added
   `line_9_blockade_delta.png` / `line_97_blockade_delta.png`: line 9 is
   both route- and time-affected during others' blockades; line 97's own
   detour is a net time *cost* specifically in the 14:00–17:00 window
   despite saving time overall. Round 3: fixed a legend overlapping the
   data in both figures (section H). **Round 4:** verified unaffected —
   line 14 never appears in this phase.

## What changed numerically, first pass → this revision

| Metric | First pass | This revision |
|---|---|---|
| Line 22 overall blocked share (docs/06) | 0.2% | **11.7%** |
| Non-reference variants classified `blocked` (project-wide) | 51 / 165 (31%) | 141 / 155 (91%) |
| Control lines' blocked share | exactly 0% | 0.3–0.8% (still noise-level) |
| Phase 08/09 blockade window count | 112 slots | 320 slots |
| Line 14 direction_A blockade effect (docs/08) | +2.3–2.4 min, p<0.05 (both tests) | Weekday +0.8 min, tests disagree (MWU p=0.07, t p=0.006) |
| Line 9 Saturday travel-time effect (docs/09) | inconclusive (n=4, underpowered) | **+11.7 min, p=0.010** (n=5 vs 7) |
| Line 9/97 route-switching significance (docs/09) | p=0.016–0.006 | p≈0 (both lines, both strata) |

**Read together, these changes tell a consistent story:** the new
absolute stop-count rule is more complete (it stops missing line 22's
real closure) but far less selective (it also picks up one-off noise on
every line, including the controls) — trading window precision for
window completeness. That trade-off strengthens some findings (line 9's
Saturday delay, both lines' route-switching) and weakens others (line
14's control-line effect), rather than uniformly improving or degrading
the analysis. This is documented explicitly in each affected phase
rather than presented as a clean improvement.

## What changed numerically, this revision → round 2

Round 2's two new exclusions (line 19B variant 5, line 97B variant 2)
are small and mostly targeted: line 19B's excluded variant was already
classified `regular`, so it changes nothing except display and a tiny
denominator shift; line 97B's excluded variant *was* `blocked`, so it's
the only source of numeric drift below. Phase 08 (both control lines'
windows and stats) is confirmed **byte-identical** to round 1 after
rerunning — the new exclusions don't touch lines 17/19/22.

| Metric | Round 1 | Round 2 |
|---|---|---|
| Line 97 overall blocked share (docs/06) | 5.0% | 4.7% |
| Line 97 phase 05 n blocked / overall delta | 108 / −8.0 min | 100 / −8.2 min |
| Line 97 phase 09 (a) Weekday route share | 5.7% vs 1.0% | 5.4% vs 0.7% |
| Line 97 phase 09 (a) Combined route share | 15.2% vs 1.7% | 14.9% vs 1.3% |
| Phase 08 blockade windows / control-line stats | 320 slots | **320 slots, unchanged** |

## What changed numerically, round 2 → round 3

Unlike rounds 1–2, round 3 made **no changes to `variant_merges.json`**
— every numeric shift below comes from phase 05's new `count>5`
significance floor (scoped to that phase only; `variant_type_v2` itself,
and therefore phases 06/08/09, is unaffected). Phase 08's stats are
confirmed byte-identical (diffed again after the round-3 rerun).

| Metric | Round 2 | Round 3 |
|---|---|---|
| Phase 05: lines 14/15 present at all | Yes (n=13, n=4 blocked blocks — noise) | **No — removed entirely** |
| Phase 05 line 9 n blocked / delta | 116 / −15.8 min | 93 / −15.9 min |
| Phase 05 line 17 n blocked / delta | 121 / −10.4 min | 93 / −11.4 min |
| Phase 05 line 19 n blocked / delta | 203 / −8.7 min | 183 / −8.7 min |
| Phase 05 line 22 n blocked / delta | 236 / −4.0 min | 210 / −3.1 min |
| Phase 05 line 97 n blocked / delta | 100 / −8.2 min | 61 / −8.0 min |
| Phase 06/08/09 numbers | — | **Unchanged** (no variant-merge edits this round) |

## What changed numerically, round 3 → round 4

Only `variant_type_v2`'s line-14 classification changed
(`pipeline/variant_merges.py`); `govData/variant_merges.json` is
untouched, so lines 9/17/19/22/97 and line 15 are numerically identical
to round 3.

| Metric | Round 3 | Round 4 |
|---|---|---|
| Line 14 overall blockade share (docs/06) | 0.8% | **0.0%** |
| Line 14 Saturday blockade share (docs/06) | 3.1% (n=65) | **0.0%** (n=65) |
| Phase 05/08/09 numbers (all lines) | — | **Unchanged** (verified byte-identical/re-derived) |
| Line 22 Saturday summary row (docs/06) | Both directions pooled, 51.2% | **Direction_A only**, "22 (dir A)" — see [line_22](06_blockade_frequency/line_22/README.md) |
| Line 22 overall/per-line-panel share (docs/06) | 11.7% / 51.2% | **Unchanged** (both directions still pooled outside the Saturday summary) |

**Sources:** `prompts/revision_round_prompt.md`,
`prompts/revision_round_2_prompt.md`, `prompts/revision_round_3_prompt.md`,
`prompts/revision_round_4_prompt.md`,
`govData/variant_merges.json`, `pipeline/variant_merges.py`,
`pipeline/pooled_analysis.py`, `pipeline/config.py`.
