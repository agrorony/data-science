# 03 — Line 9: Raw and Merged Variants

**Revision note:** clustering has been removed from this phase entirely
(stage5's cluster grouping is no longer part of the story). This report
now covers: the raw stop-presence grid filtered to variants observed
more than 5 times (`n>5`), and a second grid after applying a manual
merge/exclude table (`govData/variant_merges.json`,
`pipeline/variant_merges.py`). See
[docs/02_route_mapping](../../02_route_mapping/README.md) for direction
labels.

## direction_A

- **Raw** (`variants_raw_direction_A.png`): 4 variants clear `n>5`
  (reference `n=491` + 3 alternates).
- **Merges applied:** `0+1` → new reference (`n=870`, 67 stops, using
  variant 0's sequence — the more frequent of the two); `2+3+4+5` → one
  merged variant (`n=44`, 64 stops, using variant 2's sequence).
- **Exclusions:** none.
- **Merged** (`variants_merged_direction_A.png`): 2 variants clear
  `n>5` after merging (down from 4 raw) — the reference and the single
  merged detour variant. 16 further singleton variants (`n≤2` each)
  remain unmerged and don't clear the display threshold in either grid.

## direction_B

- **Raw** (`variants_raw_direction_B.png`): 5 variants clear `n>5`.
- **Merges applied:** `0+1+3` → new reference (`n=776`, 63 stops,
  variant 0's sequence); `2+4` → one merged variant (`n=54`, 56 stops,
  variant 2's sequence).
- **Exclusions:** none.
- **Merged** (`variants_merged_direction_B.png`): 2 variants clear
  `n>5` (down from 5 raw).

**Sources:** `govData/variant_summary.csv`, `govData/variant_merges.json`,
`pipeline/variant_merges.py`, `pipeline/plot_variants_revised.py`.
