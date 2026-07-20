# 03 — Line 15: Raw and Merged Variants (Control)

**Revision note:** clustering removed from this phase; see
[docs/03_variants](../README.md) for what changed project-wide.

Line 15 has no direction split (single `route_id`, loop route — see
[docs/02_route_mapping](../../02_route_mapping/README.md)). No
merge/exclude entries for line 15 — nothing worth merging.

- **main:** raw (`n>5`) = 1 variant (the reference, `n=1,201`). Merged =
  same, 1 variant. One other variant exists (`n=4`) but doesn't clear
  the threshold in either grid.

Unchanged from the pre-revision phase 03 conclusion: line 15's
near-total single-variant stability is what makes it usable as a
control.

**Sources:** `govData/variant_summary.csv`, `govData/variant_merges.json`,
`pipeline/plot_variants_revised.py`.
