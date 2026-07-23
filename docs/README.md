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
4. **[Baseline variants](04_baselines/README.md)** *(revised, approved
   since — untouched in round 2)* — stats pool both directions of a
   line; headline figure (`travel_time_all_lines.png`) ranks all 7 lines
   by mean end-to-end baseline travel time with error bars showing
   trip-duration variability.
5. **[Baseline vs. blocked/special variant](05_skip_comparison/README.md)**
   *(revised, then revised again)* — delta-style per-hour line charts
   (baseline vs. blocked variant, directions pooled); every non-control
   line's blocked variant is faster than baseline overall. Round 2 adds
   `delta_all_lines.png`, all five non-control lines' hourly detour
   deltas on shared axes.
6. **[Blockade/variant frequency](06_blockade_frequency/README.md)**
   *(revised, then revised again)* — one combined (both-directions)
   heatmap per line under the new >15-stop rule. Line 22's share jumps
   from 0.2% to 11.7%, correctly landing alongside lines 9/17/19/97.
   Round 2 adds `blockade_all_lines.png` (all 7 lines, shared colorbar)
   and `blockade_saturday_summary.png` (Saturday share, lines × months).
7. **[Blockade investigation](07_blockade_investigation/README.md)**
   *(original investigation unchanged; addendum added; approved since —
   untouched in round 2)* — the addendum documents the new rule's
   project-wide effect: 141 of 155 merged variants (91%) are now
   classified `blocked`, including a handful of single-observation
   deviations on the control lines.
8. **[Control lines 15 & 14](08_control_lines_15_14/README.md)**
   *(revised; approved since — round 2 regenerated its two figures only
   to drop hours 25/26, numbers unchanged)* — delta chart only, line
   14's two directions pooled, blockade windows recomputed under the
   new rule (320 slots, up from 112). The first pass's significant line
   14 finding does not clearly survive this revision — the two
   statistical tests disagree.
9. **[Lines 9 & 97 during blockades](09_lines_9_97/README.md)**
   *(revised, then revised again)* — both directions pooled, updated
   320-slot windows. Route-switching effects got much stronger (p≈0 for
   both lines); line 9 additionally shows a newly-significant Saturday
   travel-time delay (+11.7 min) that was underpowered in the first
   pass. Round 2 adds `line_9_blockade_delta.png` /
   `line_97_blockade_delta.png`: line 9 is both route- and
   time-affected during others' blockades (detours when possible, small
   real delay when it doesn't); line 97's own detour is a net time
   *cost* specifically in the 14:00–17:00 window despite saving time
   overall.

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

**Sources:** `prompts/revision_round_prompt.md`,
`prompts/revision_round_2_prompt.md`, `govData/variant_merges.json`,
`pipeline/variant_merges.py`, `pipeline/pooled_analysis.py`.
