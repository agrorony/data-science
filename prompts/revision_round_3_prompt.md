# Prompt for Claude Code — revision round 3 on the `docs/` presentation outputs

Copy everything below into Claude Code, run from the repo root.

---

Third correction round, after `prompts/revision_round_2_prompt.md` was executed. All global rules from previous prompts still apply (English, legend + caption on every figure, house style for heatmaps, no hours 25/26 anywhere, directions pooled from phase 04 onward).

## A. Global — one color per line, defined once

Define a **fixed color per line** in one place (e.g. `LINE_COLORS` in `pipeline/config.py`) and use it in **every figure where more than one line appears** (phases 04, 05, 06 combined figures, 08, 09). Keep the family logic already in use: lines 17/19/22 = distinct shades of red, lines 9/97 = distinct shades of purple, lines 14/15 = distinct shades of a third family (e.g. blue/teal). Regenerate every multi-line figure so colors match this palette exactly, and make legends consistent ("Line 19" etc.). Document the palette in `docs/README.md`.

## B. Phase 05 — verify data source + explain lines 14/15 appearing

1. **Audit the phase 05 computation:** confirm the delta figures and statistics are built from the **cleaned, merged, post-exclusion variant set** (the output of the phase 03 merge/exclusion structure), NOT from raw variants. If any figure was computed from raw data, fix and regenerate.
2. **Investigate why lines 14 and 15 appear in phase 05 at all**, given they are essentially never blocked. Determine the cause (e.g. leftover raw variants, trivial skip-variants that should have been merged into baseline, a bug in the blocked rule ">15 stops") and report it in `docs/05_skip_comparison/README.md` with numbers. If their "special variants" are artifacts — remove them from phase 05 outputs; if they are real but rare, say so explicitly and justify keeping or dropping them.

## C. Phase 06 — analyze the 100%-vs-other disagreement windows

Add an analysis (README section + supporting figure) of the windows where **most lines show 100% blockade share while other lines show a different value**. For those specific (month, day) cells: compare the lines' **regular (baseline) rides** — which hour-slots each line actually operated, how many trips per hour, and whether the disagreeing line simply ran extra hours outside the blockade or genuinely passed through. This extends the phase 07 schedule-difference finding with concrete per-window evidence. Keep it in `docs/06_blockade_frequency/` (the phase 07 folder stays untouched).

## D. Phase 06 — Saturday summary heatmap row order

In the Saturday summary heatmap (`blockade_saturday_summary.png`), order the rows by group: **17, 19, 22, then 9, 97, then 14, 15** — with a subtle visual separator (horizontal line or extra spacing) between the three groups. Group labels on the side are welcome (e.g. "shared blocked segment", "Aza St. non-shared", "controls").

## E. Phase 04 — deeper baseline statistics

1. **Standard error instead of standard deviation:** in the all-lines barplot (`travel_time_all_lines.png`) and in the README tables, replace std error bars with **standard error of the mean (SEM)**; report n per line. Keep std available in the README table as a column (it still tells the chaos story), but the error bars show SEM.
2. **New figure — baseline travel time by hour:** for each line, the baseline variant's end-to-end travel time per departure hour (directions pooled). One combined figure, one curve per line, using the section-A palette, with SEM shading or error bars per point. Save as `docs/04_baselines/baseline_travel_time_by_hour.png`. Per-line versions optional if the combined one gets crowded.

## F. Line 97 detour distance figure

Line 97 is an outlier in how much blockades delay it. Add a figure comparing its **cumulative distance along the detour (blocked) variant vs the regular baseline route** — cumulative distance (km) on the y-axis over the stop sequence, two curves (baseline vs detour, clearly labeled), so the extra distance of the detour is visible. Annotate the end-to-end distance difference. Place in `docs/05_skip_comparison/line_97/` (or `docs/09_lines_9_97/` if the data sits more naturally there — pick one and link from both READMEs). If the same view is cheap to produce for the other blocked lines, add them for context in a small-multiples panel — 97 must be the highlighted headline panel.

## G. Phase 08 — lines 14 & 15 in one figure

Combine the two control-line delta charts into **a single figure**: both lines' blockade-window-minus-matched-normal delta curves on shared axes (section-A palette), one legend, shared zero line and shading conventions. Replace the two separate files.

## H. Phase 09 — fix legend placement

In the `line_9_blockade_delta.png` and `line_97_blockade_delta.png` figures, the legend currently sits on top of the curves. Move it to an empty area or outside the axes (`bbox_to_anchor`), and verify visually that it no longer overlaps any data.

## Process

1. Order: A (palette) first, then B–H in any dependency-sensible order; regenerate all multi-line figures under the palette.
2. Update `docs/README.md` (index + palette documentation).
3. Verify every regenerated figure visually (open the PNG): palette correct, legend not overlapping, captions present, no hours 25/26.
4. Finish with a summary: the cause found in B2, the findings of C, and any numeric changes.
