# 03 — Line 97: Raw and Merged Variants

**Revision note:** clustering removed from this phase; see
[docs/03_variants](../README.md) for what changed project-wide. See
[docs/02_route_mapping](../../02_route_mapping/README.md) for direction
labels.

## direction_A

- **Raw** (`variants_raw_direction_A.png`): 4 variants clear `n>5`.
- **Merges applied:** `1+2` → one merged variant (`n=37`, 26 stops,
  variant 1's sequence). Reference (variant 0, `n=1,133`) unmerged.
- **Exclusions:** variants 3 and 4 dropped entirely (`n=7` and `n=4` in
  the raw data).
- **Merged** (`variants_merged_direction_A.png`): 2 variants clear
  `n>5` (down from 4 raw, after exclusions).

## direction_B

- **Raw** (`variants_raw_direction_B.png`): 6 variants clear `n>5`.
- **Merges applied:** `3+1` → one merged variant (`n=27`, 32 stops,
  variant 1's sequence, the more frequent of the two); `0+4` → new
  reference (`n=1,158`, 34 stops, variant 0's sequence).
- **Exclusions:** variant 5 dropped entirely (`n=7` in the raw data).
- **Merged** (`variants_merged_direction_B.png`): 3 variants clear
  `n>5` (down from 6 raw, after the exclusion).

**Note carried over from the pre-revision phase 03 write-up:** the
pre-2026-07-19-style clustering step used to surface line 97's second,
Malha-area closure signature as a distinct cluster
(`97_direction_B_cluster_2`). That distinction no longer exists in this
revision — clustering has been removed project-wide, and this phase's
merge table doesn't reconstruct it as a separate merged variant. Readers
interested in that secondary closure should still consult
`govData/candidate_variant_labels.csv` (the pre-revision cluster
assignment) directly; it isn't represented in the current phase 03
figures or merged variant set.

**Sources:** `govData/variant_summary.csv`, `govData/variant_merges.json`,
`pipeline/variant_merges.py`, `pipeline/plot_variants_revised.py`.
