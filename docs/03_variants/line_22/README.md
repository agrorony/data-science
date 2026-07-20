# 03 — Line 22: Raw and Merged Variants

**Revision note:** clustering removed from this phase; see
[docs/03_variants](../README.md) for what changed project-wide. See
[docs/02_route_mapping](../../02_route_mapping/README.md) for direction
labels.

No merge/exclude entries for either direction of line 22 — the merge
table leaves it untouched (`"merges": [], "exclude": []]` in both
directions).

## direction_A

- **Raw** (`variants_raw_direction_A.png`): 2 variants clear `n>5`
  (reference `n=1,023`, plus variant 1, `n=96`, 51 stops).
- **Merged** (`variants_merged_direction_A.png`): identical to raw — no
  merges to apply.
- Variant 1 (`n=96`) is the same variant [docs/07_blockade_investigation](../../07_blockade_investigation/README.md)
  identified as line 22's real Aza-corridor closure, previously
  mislabeled `regular` by the old fraction-based rule. Under the new
  >15-stop rule (section B), it is now correctly labeled `blocked`
  (51 > 15) with no merge needed to fix it — see the phase 07 addendum.

## direction_B

- **Raw** (`variants_raw_direction_B.png`): 3 variants clear `n>5`.
- **Merged** (`variants_merged_direction_B.png`): identical to raw — no
  merges to apply.

**Sources:** `govData/variant_summary.csv`, `govData/variant_merges.json`,
`pipeline/plot_variants_revised.py`.
