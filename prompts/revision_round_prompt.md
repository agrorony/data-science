# Prompt for Claude Code — revision round on the `docs/` presentation outputs

Copy everything below into Claude Code, run from the repo root.

---

The first pass over `docs/` (phases 01–09, see `prompts/presentation_prep_prompt.md`) is done and reviewed. This round applies corrections. **Phases 01 and 02 are approved — do not touch them.** All global rules from the original prompt still apply (English reports, legend + caption on every figure, house style for heatmaps).

The changes below alter the variant definitions themselves (merges, exclusions, a new blocked rule), so after fixing phase 03 you must **propagate downstream**: recompute phases 04–09 with the new variant set.

## A. Phase 03 — drop clustering, add manual variant merges

1. **Remove clustering entirely.** Delete the `after_clustering_*.png` figures and all cluster references in the phase 03 READMEs. Stage5 clustering is no longer part of the story.
2. **Pre-merge map:** the stop-presence grid (`before_clustering` style, keep the exact avishagi green/white look) must show **only variants observed more than 5 times** (n > 5). Rename to `variants_raw_direction_<X>.png`.
3. **Manual merges — applied AFTER the raw map is produced.** Some variants differ only trivially (e.g. skipping the terminal stop) and must be united into one variant. Variant IDs below refer to the numbering in the current `docs/03_variants/line_<N>/before_clustering_direction_<X>.png` figures (variants sorted by occurrence, 0 = reference):

| Line | Direction | Merge into one variant | Exclude from ALL analysis |
|------|-----------|------------------------|---------------------------|
| 9    | A         | 0+1, 2+3+4+5           | — |
| 9    | B         | 0+1+3, 2+4             | — |
| 17   | A         | 0+1, 2+3               | — |
| 17   | B         | 1+2+3                  | — |
| 19   | A         | 0+2+4, 1+3             | — |
| 19   | B         | 1+2                    | variants 3, 4 |
| 22   | A         | none                   | — |
| 22   | B         | none                   | — |
| 97   | A         | 1+2                    | variants 3, 4 |
| 97   | B         | 3+1, 0+4               | variant 5 |

   - "Merge" = the united group becomes a single variant; its n is the sum; when a merge group contains the reference (variant 0), the merged variant IS the baseline. Use the most frequent member's stop sequence as the merged variant's representative sequence.
   - "Exclude" = dropped entirely: not in the merged variant set, not in any statistic in phases 04–09.
   - Encode this table as data (e.g. `pipeline/variant_merges.py` or a json in `govData/`), not hardcoded in a notebook.
4. **Post-merge map:** a second grid figure per (line, direction), `variants_merged_direction_<X>.png`, showing the merged variant set. README documents: raw variant count (n>5), merges applied, exclusions, final variant count.

## B. New blocked-variant rule (replaces the 10% missing-fraction rule)

Phase 07 found that line 22's blocked variant was never counted: its direction is long, so the detour misses <10% of stops and `MINOR_MISSING_FRACTION = 0.10` in `pipeline/stage5_variant_classification.py` classified it "regular". Replace the rule: **after the section-A merges and exclusions, ANY non-baseline variant whose path has more than 15 stops counts as a blocked/detour variant.** No fraction thresholds. Document the rule change and its effect (which variants changed classification, per line) in `docs/07_blockade_investigation/README.md` as an addendum.

## C. Directions are combined from phase 04 onward

Phases 04, 05, 08, 09 no longer split by direction: **pool all end-to-end trips from both directions** of a line into one distribution. (Phase 03 keeps per-direction figures; phase 06 see section E.)

## D. Phase 04 — combined travel-time barplot

Add the phase's headline figure: **one barplot spanning all 7 lines** — mean end-to-end travel time per line (both directions pooled), with error bars from the averaged std, showing how chaotic each line's duration is. Sort bars sensibly, annotate values, caption explains that tall error bars = unpredictable line. Rework the per-line figures/READMEs to pooled-direction stats. Save as `docs/04_baselines/travel_time_all_lines.png`.

## E. Phase 06 — one combined figure per line

Keep only the both-directions-combined month×day heatmap per line (house style). Delete the per-direction panels. Recompute shares with the new blocked rule from section B — line 22's map should now show its blockades.

## F. Phase 05 — delta-style figures, confirmed variants only

Replace the current phase 05 figures with the **delta style** — anchor: the top panel of `docs/08_control_lines_15_14/line_15_hourly_pattern.png`: per-hour line chart of the travel-time gap, here **baseline variant vs blocked/special variant** of the same line (directions pooled), dashed zero line, shaded hours where data is thin. One figure per line. **Only confirmed/approved variants** (the post-merge, post-exclusion set from section A) may enter the statistics. README still answers: does the special route cost or save time, and by how much per hour.

## G. Phase 08 — delta graph only

Keep **only the delta chart** (the top-panel style: blockade-window minus matched-normal travel time by hour, zero line, shading): one per control line (15 and 14, directions pooled). Delete the boxplot/distribution figures, the absolute-travel-time panels, and the per-direction hourly-pattern files. Recompute with the section-B blockade windows (they may change now that line 22's blockades are counted). Keep the stats CSVs.

## H. Phase 09 — recompute with new definitions

Rerun the lines 9/97 analysis (variant share + travel time during blockade windows) with the merged/excluded variant set, the new blocked rule, pooled directions, and the updated blockade windows from G. Figure style may stay as-is.

## Process

1. Order: A → B → then C–H (downstream recomputation).
2. Update `docs/README.md` index to reflect removed/renamed figures.
3. Verify every regenerated figure visually against the global rules (legend, caption, no raw column names) before moving on.
4. Finish with a short summary of what changed numerically vs the first pass (e.g. line 22 blockade share before/after, phase 08 windows count).
