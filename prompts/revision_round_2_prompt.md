# Prompt for Claude Code — revision round 2 on the `docs/` presentation outputs

Copy everything below into Claude Code, run from the repo root.

---

Second correction round after `prompts/revision_round_prompt.md` was executed. **Phases 01, 02, 04, 07, 08 are approved — do not touch them** (except the global hour rule below where it requires regenerating a figure). All global rules from the previous prompts still apply (English, legend + caption on every figure, house style for heatmaps).

## Global — hours 25/26

New rule replacing the old "show 25/26 as 01:00/02:00": **hours 25 and 26 must not appear in any figure at all.** Drop those rows from plotted data, remove the 1/2 ticks, and delete any caption/axis text mentioning them. Apply to every figure you touch in this round; also regenerate any existing figure whose axes or captions currently mention 25/26 or 01:00/02:00 (this is the only permitted edit to otherwise-approved phases).

## A. Phase 03 — two more exclusions + subplot layout

1. **Exclude from the going-forward variant set** (they are blockades irrelevant to the rest of the analysis):
   - Line 19, direction B: variant 5
   - Line 97, direction B: variant 2

   Variant IDs as numbered in the current `docs/03_variants` figures. Sanity check after applying: the merged map for each of these two (line, direction) groups should show **2 rows instead of the current 3**. If that's not what you get, stop and re-verify the ID mapping before proceeding. Add both to the exclusion data structure from the previous round (`pipeline/variant_merges.py` / the json), and propagate: these variants must not appear in any phase 04–09 statistic. Recompute affected downstream outputs (phase 05, 06, 09 at minimum) and note numeric changes in the READMEs.
2. **Figure layout:** rework the phase 03 maps so each line gets **one figure with vertical subplots**: column 1 row 1 = direction A, row 2 = direction B, and the figure's main suptitle is the line name (e.g. "Line 19"). Line 15 (single direction) gets a one-panel figure with the same title style. Apply to both the raw (n>5) maps and the merged maps — i.e. per line: `variants_raw.png` and `variants_merged.png`, each containing both directions.

## B. Phase 05 — add a cross-line delta figure

Keep the existing per-line delta figures and **add one combined figure**: per-hour travel-time delta of the blocked variant vs the regular (baseline) ride, one curve per line, for lines **17, 19, 22, 9, 97** on shared axes. Color scheme: lines 17/19/22 in distinct shades of **red**, lines 9/97 in distinct shades of **purple**. Dashed zero line, legend with line numbers, caption explaining that curves above zero = the detour costs time. Save as `docs/05_skip_comparison/delta_all_lines.png`.

## C. Phase 06 — combined all-lines heatmap figure

Keep the per-line figures and **add one figure containing all 7 lines' month×day blockade-share heatmaps as subplots** (house style), with a **single shared colorbar** and a common 0–100% scale so panels are directly comparable. Arrange subplots in a readable grid (e.g. 4×2), suptitle stating the message. Save as `docs/06_blockade_frequency/blockade_all_lines.png`.

**Optional extra (user-approved idea):** since blockades concentrate on Saturdays, also produce a compact summary heatmap — rows = lines, columns = months, cell value = Saturday blockade share (%) — one small panel that compares all lines at a glance. Save as `blockade_saturday_summary.png` if produced.

## D. Phase 09 — the "what happens to 9/97 during others' blockades" delta figure

For each of lines 9 and 97 **separately**, one delta figure (travel time, per hour, directions pooled, style anchored to the phase 08 delta chart) with two curves:

- **Red curve — own detour:** the line's blocked-variant travel time minus its baseline-variant travel time (delta vs the regular ride), in the hours where the line itself ran the blocked variant.
- **Blue curve — staying on route during others' blockade:** the line's **regular (baseline) variant** travel-time delta vs matched normal hours (same day-of-week/hour), computed **only in windows where lines 17/19/22 were blocked but this line was not**.

Together the two curves show what happens to 9/97 during a blockade: either they detour (red) or they keep their route and absorb the traffic (blue). Dashed zero line, legend naming both conditions exactly, caption with n per curve; shade hours with thin data. Save as `docs/09_lines_9_97/line_9_blockade_delta.png` and `line_97_blockade_delta.png`. Update the README with the conclusion these figures support (route affected / time affected / both / neither).

## Process

1. Order: Global hour rule + A (exclusions) first, then B, C, D recomputed with the updated variant set.
2. Update `docs/README.md` index for new/renamed figures.
3. Verify every new/regenerated figure visually (open the PNG): legend present, caption present, no hour 25/26 anywhere, colors as specified.
4. Finish with a numeric change summary vs the previous round (e.g. line 19B / 97B blockade shares after the exclusions).
