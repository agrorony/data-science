# 03 — Raw and Merged Variants

**Revision note: clustering has been removed from this phase entirely.**
The stage5 detour-cluster grouping used in the first pass is no longer
part of the project's story. This phase now shows, per (line,
direction): the raw stop-presence grid (`avishagi/bus_route_initial_filtering.ipynb`'s
green/white look, unchanged) filtered to variants observed more than 5
times (`n>5`, replacing stage4's `filter_for_display` heuristic), and a
second grid after applying a manual merge/exclude table.

**Revision round 2:** two more variants are excluded outright (line 19
direction B's variant 5, line 97 direction B's variant 2 — both
blockades irrelevant to the rest of the analysis), and the figures are
now **one PNG per line** (`variants_raw.png`, `variants_merged.png`),
with each direction as a vertical subplot and the line number as the
suptitle — replacing the previous one-PNG-per-(line, direction) layout.
Line 15 (single direction) gets a one-panel figure with the same title
style.

**Merge/exclude table** (`govData/variant_merges.json`, applied by
`pipeline/variant_merges.py`): some raw variants differ only trivially
(e.g. skipping a terminal stop) and are united into one variant (count
summed, the most-frequent member's stop sequence kept as representative);
a few variants are dropped from all analysis entirely. Lines 14 and 15
(the two control lines) have no merges or exclusions — there was nothing
worth merging.

| Line | Direction | Merged into one | Excluded |
|---|---|---|---|
| 9 | A | 0+1, 2+3+4+5 | — |
| 9 | B | 0+1+3, 2+4 | — |
| 17 | A | 0+1, 2+3 | — |
| 17 | B | 1+2+3 | — |
| 19 | A | 0+2+4, 1+3 | — |
| 19 | B | 1+2 | 3, 4, **5** |
| 22 | A | none | — |
| 22 | B | none | — |
| 97 | A | 1+2 | 3, 4 |
| 97 | B | 3+1, 0+4 | 5, **2** |

(New exclusions bolded.) Sanity check after applying: the merged map for
line 19 direction B and line 97 direction B each now show **2 rows**
instead of the previous 3 — verified both programmatically
(`variant_type_v2` printed for each surviving row) and visually in
`line_19/variants_merged.png` / `line_97/variants_merged.png`. Line 19B's
excluded variant 5 was already classified `regular` (not `blocked`)
under the >15-stop rule, so its removal has no effect on any blockade
statistic — only on the display and on the small handful of blocks
counted in phase 06's denominator. Line 97B's excluded variant 2 *was*
classified `blocked`, so its removal changes line 97's own blocked-share
and delta figures downstream (see [docs/06](../06_blockade_frequency/README.md),
[docs/09](../09_lines_9_97/README.md)).

This same merged/excluded variant set is now the single source of truth
for phases 04–09 (see `pipeline/variant_merges.build_effective_df_cleaned`),
replacing the original `df_cleaned.csv`'s raw `route_variant_id` values.

Per-line detail: [line_9](line_9/README.md), [line_14](line_14/README.md),
[line_15](line_15/README.md), [line_17](line_17/README.md),
[line_19](line_19/README.md), [line_22](line_22/README.md),
[line_97](line_97/README.md).

**Sources:** `govData/variant_summary.csv`, `govData/variant_merges.json`,
`pipeline/variant_merges.py`, `pipeline/plot_variants_revised.py`,
`pipeline/stage10_route_deviation_heatmaps.py`.
