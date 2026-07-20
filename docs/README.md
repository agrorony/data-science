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

1. **[Data cleaning](01_data_cleaning/README.md)** *(unchanged)* — how
   the raw government export becomes `govData/df_cleaned.csv`.
2. **[Route mapping](02_route_mapping/README.md)** *(unchanged)* — the
   key table every later phase links to: `route_id` → commercial line →
   `direction_A`/`direction_B` → terminal stops.
3. **[Raw and merged variants](03_variants/README.md)** *(revised)* —
   clustering removed; raw stop-presence grids now show only variants
   observed >5 times, followed by a manual merge/exclude table
   (`govData/variant_merges.json`) that consolidates trivially-different
   variants and drops a handful entirely. This merged/excluded variant
   set is now the source of truth for every later phase.
4. **[Baseline variants](04_baselines/README.md)** *(revised)* — stats
   now pool both directions of a line; new headline figure
   (`travel_time_all_lines.png`) ranks all 7 lines by mean end-to-end
   baseline travel time with error bars showing trip-duration
   variability.
5. **[Baseline vs. blocked/special variant](05_skip_comparison/README.md)**
   *(revised)* — replaced entirely with delta-style per-hour line
   charts (baseline vs. blocked variant, directions pooled). Every
   non-control line's blocked variant is faster than baseline overall.
6. **[Blockade/variant frequency](06_blockade_frequency/README.md)**
   *(revised)* — one combined (both-directions) heatmap per line under
   the new >15-stop rule. Line 22's share jumps from 0.2% to 11.7%,
   correctly landing alongside lines 9/17/19/97.
7. **[Blockade investigation](07_blockade_investigation/README.md)**
   *(original investigation unchanged; addendum added)* — the addendum
   documents the new rule's project-wide effect: 141 of 155 merged
   variants (91%) are now classified `blocked`, including a handful of
   single-observation deviations on the control lines.
8. **[Control lines 15 & 14](08_control_lines_15_14/README.md)**
   *(revised)* — delta chart only, line 14's two directions pooled,
   blockade windows recomputed under the new rule (320 slots, up from
   112). The first pass's significant line 14 finding does not clearly
   survive this revision — the two statistical tests disagree.
9. **[Lines 9 & 97 during blockades](09_lines_9_97/README.md)**
   *(revised)* — both directions pooled, updated 320-slot windows.
   Route-switching effects got much stronger (p≈0 for both lines); line
   9 additionally shows a newly-significant Saturday travel-time delay
   (+11.7 min) that was underpowered in the first pass.

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

**Sources:** `prompts/revision_round_prompt.md`, `govData/variant_merges.json`,
`pipeline/variant_merges.py`, `pipeline/pooled_analysis.py`.
