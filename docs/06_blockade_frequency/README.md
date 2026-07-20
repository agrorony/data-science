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

## Cross-line summary (overall non-baseline share, both directions pooled)

| Line | Overall share | Saturday share | n (Saturday blocks) |
|---|---|---|---|
| 9 | 7.0% | 84.1% | 82 |
| 14 (control) | 0.8% | 3.1% | 65 |
| 15 (control) | 0.3% | 0.0% | 56 |
| 17 | 12.2% | 80.5% | 82 |
| 19 | 8.9% | 75.7% | 74 |
| 22 | **11.7%** | 51.2% | 80 |
| 97 | 5.0% | 66.4% | 110 |

**Line 22 is fixed.** In the first pass, line 22's overall share (0.2%)
sat at control-line level — [docs/07_blockade_investigation](../07_blockade_investigation/README.md)
diagnosed this as a genuine classification bug (its real closure fell
just under the old 10%-of-route-length cutoff). Under the new rule,
line 22 now shows **11.7%** — squarely with lines 9/17/19/97, and its
May-weekday cells now clearly show the same closure pattern as line 19
(see `blockade_frequency_22.png`: May Sat=100%, Sep Sat=100%, Tue/May=62%).

**Control lines are no longer exactly 0%.** As documented in
[docs/07's addendum](../07_blockade_investigation/README.md), the new
rule occasionally labels a rare, single-observation route deviation on
lines 14/15 as "blocked" simply because it has >15 stops, with no way to
distinguish that from a real detour except low frequency. Their shares
(0.8% and 0.3%) remain far below every non-control line, so they still
function as controls in practice, but this is a real, honest side-effect
of dropping the fraction threshold — not a data artifact to explain
away.

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

**Sources:** `govData/df_cleaned.csv`, `govData/variant_merges.json`,
`pipeline/variant_merges.py`, `pipeline/plot_blockade_frequency.py`.
