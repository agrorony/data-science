# 03 — Line 19: Raw and Merged Variants

**Revision note:** clustering removed from this phase; see
[docs/03_variants](../README.md) for what changed project-wide. See
[docs/02_route_mapping](../../02_route_mapping/README.md) for direction
labels.

## direction_A

- **Raw** (`variants_raw_direction_A.png`): 4 variants clear `n>5`.
- **Merges applied:** `0+2+4` → new reference (`n=1,205`, 42 stops,
  variant 0's sequence — variants 2 and 4 are absorbed into the
  baseline count); `1+3` → one merged variant (`n=91`, 36 stops,
  variant 1's sequence).
- **Exclusions:** none.
- **Merged** (`variants_merged_direction_A.png`): 2 variants clear
  `n>5` (down from 4 raw).

## direction_B

- **Raw** (`variants_raw_direction_B.png`): 6 variants clear `n>5`.
- **Merges applied:** `1+2` → one merged variant (`n=114`, 34 stops,
  variant 1's sequence). Reference (variant 0, `n=1,194`) unmerged.
- **Exclusions:** variants 3 and 4 (`n=17` and `n=12` in the raw data)
  are dropped from all analysis entirely, per the revision spec — not
  merged, not counted anywhere downstream.
- **Merged** (`variants_merged_direction_B.png`): 3 variants clear
  `n>5` (down from 6 raw, after the exclusions). One further merged
  variant (`n=12`, only 12 stops — a severely truncated trip) survives
  in the full data as the **only non-reference variant in this entire
  project classified `regular` under the new >15-stop rule** (section
  B) — every other line/direction's non-reference variants have enough
  stops to count as `blocked`.

**Sources:** `govData/variant_summary.csv`, `govData/variant_merges.json`,
`pipeline/variant_merges.py`, `pipeline/plot_variants_revised.py`.
