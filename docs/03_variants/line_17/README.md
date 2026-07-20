# 03 — Line 17: Raw and Merged Variants

**Revision note:** clustering removed from this phase; see
[docs/03_variants](../README.md) for what changed project-wide. See
[docs/02_route_mapping](../../02_route_mapping/README.md) for direction
labels.

## direction_A

- **Raw** (`variants_raw_direction_A.png`): 4 variants clear `n>5`.
- **Merges applied:** `0+1` → new reference (`n=487`, 47 stops,
  variant 0's sequence); `2+3` → one merged variant (`n=41`, 41 stops,
  variant 2's sequence).
- **Exclusions:** none.
- **Merged** (`variants_merged_direction_A.png`): 2 variants clear
  `n>5` (down from 4 raw).

## direction_B

- **Raw** (`variants_raw_direction_B.png`): 4 variants clear `n>5`.
- **Merges applied:** `1+2+3` → one merged variant (`n=76`, 46 stops,
  variant 1's sequence). Reference (variant 0, `n=618`) is not part of
  any merge and stays as-is.
- **Exclusions:** none.
- **Merged** (`variants_merged_direction_B.png`): 2 variants clear
  `n>5` (down from 4 raw).

**Sources:** `govData/variant_summary.csv`, `govData/variant_merges.json`,
`pipeline/variant_merges.py`, `pipeline/plot_variants_revised.py`.
