# 03 — Line 14: Raw and Merged Variants (Control)

**Revision note:** clustering removed from this phase; see
[docs/03_variants](../README.md) for what changed project-wide.

Line 14 is a control line. Neither direction has any merge/exclude
entries in `govData/variant_merges.json` — there was nothing worth
merging.

- **direction_A:** raw (`n>5`) = 1 variant (the reference, `n=846`).
  Merged = same, 1 variant. 8 singleton (`n=1`) variants exist in the
  full data but never clear the display threshold.
- **direction_B:** raw (`n>5`) = 1 variant (the reference, `n=992`).
  Merged = same, 1 variant. 3 singleton variants exist but don't clear
  the threshold.

Unchanged from the pre-revision phase 03 conclusion: line 14's
near-total single-variant stability is what makes it usable as a
control in [docs/08_control_lines_15_14](../../08_control_lines_15_14/README.md).

**Sources:** `govData/variant_summary.csv`, `govData/variant_merges.json`,
`pipeline/plot_variants_revised.py`.
