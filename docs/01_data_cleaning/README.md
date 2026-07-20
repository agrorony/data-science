# 01 — Data Cleaning: From Raw Government Export to `df_cleaned.csv`

## Part 1: Narrative walkthrough

### Starting point: the raw government export

The source is the Israeli Ministry of Transport dataset ["Arrival to
station, day and hours"](https://data.gov.il/he/datasets/ministry_of_transport/arrivaltostationdayandhours/e3673768-3dc2-4e62-b0ea-cf763c07a037),
a large pipe-delimited CSV. Each row aggregates the average travel
behavior of all rides that matched one (route, month, day-of-week,
departure hour, stop) combination, along with `count_common` — how many
individual rides that average is built from.

The project targets 7 commercial bus lines (9, 14, 15, 17, 19, 22, 97),
which together span 16 underlying `route_id` values (a line can have more
than one `route_id`, e.g. a separate id per direction). An earlier phase
of the project worked with only 4 hardcoded routes; that scope was
expanded to the full 7-line target list documented in `CLAUDE.md`
("Known Data Issues" #2) and in `govData/target_route_ids.json`.

### Stage 0 — rebuild the merged file with a corrected dedup (`pipeline/stage0_rebuild_merged.py`)

Filtering the raw export down to the 16 target `route_id`s leaves
**708,642 rows**. Inspecting those rows surfaced a structural problem:
many rows share the exact same key
`(route_id, month, DayOfWeek, HourSourceTime, StopSequence_Rishui)` —
**158,151 rows (22.3%)**, forming 53,170 duplicate-key groups, 89% of
which contain exactly 3 rows. This is consistent with the raw government
export itself containing ~3 overlapping data batches covering the same
period — the same underlying phenomenon `CLAUDE.md` originally documented
for the old `ride_data1–4.csv` concatenation (issue #1), just recurring at
larger scale once the route scope grew to 16 `route_id`s.

An earlier script at the repo root, `rebuild_ride_data_merged.py`,
resolved each duplicate key by keeping whichever row had the highest
`count_common`, without checking whether the duplicate copies actually
agreed on which stop (`StopCode`) the row described. `stage0_rebuild_merged.py`
replaces it with a block-aware, majority-vote resolution (full methodology
in `pipeline/STAGE0_DEDUP_NOTES.md`):

1. For each duplicate key, take the `StopCode` with a clear majority
   across the group's rows.
2. If there's no clear majority (a genuine tie), fall back to the
   highest-`count_common` row among the tied `StopCode`s, and flag the
   key as `ambiguous=True` in the audit report rather than silently
   guessing.
3. Among rows agreeing with the winning `StopCode`, keep the single row
   with the highest `count_common` — so a winning row's travel-time and
   distance figures come from one internally-consistent real observation,
   rather than being averaged or mixed across different source rows.

Only **1,065 of the 53,170 groups (2.0%)** actually disagree on
`StopCode` at all — the rest are pure redundant copies where only
`count_common` differs, so any reasonable dedup rule handles them
identically. Within the 1,065 disagreeing groups, 1,017 (95.5%) resolve
by a clean majority (e.g. 2-of-3 copies agreeing). The remaining 48
groups (all concentrated in route 5502/line 22 and 11107–11108/line 9,
month 1, hour 12) have no majority — a 2-vs-2 split traced to a
one-position stop-numbering shift near the start of the trip in one of
two overlapping export copies, which re-synchronizes by stop 11. These 48
groups are resolved with the same highest-`count_common` fallback and
explicitly flagged in `govData/stage0_dedup_audit.csv` (48 of 603,662
output rows, ~0.008%).

Output: **`govData/ride_data_merged.csv`, 603,662 rows** (550,491
already-unique rows + 53,170 winning rows, one per duplicate group). Two
timestamped backups of the pre-rebuild file were kept in `govData/` for
traceability.

### Stage 2 — rename columns and tag lines (`pipeline/stage2_rename_and_tag.py`)

Raw column names (`HourSourceTime`, `StopSequence_Rishui`, `count_common`
...) aren't self-explanatory for a course report. Stage 2 renames every
column to a readable form (e.g. `HourSourceTime` → `scheduled_departure_time`,
`count_common` → `n_observations`) and adds a `route_name` column mapping
every `route_id` to its commercial line, using the single source-of-truth
mapping in `target_route_ids.json`. This replaces Avishagi's original
per-file, 4-route-only renaming notebook. No rows are dropped — 603,662
rows in, 603,662 out — and the output covers all 7 lines in one file
(`route_id` is always kept, never used to split into per-line files).

### Stage 6 — attach variant-type labels and finalize (`pipeline/stage6_finalize_outputs.py`)

After route-sequence variants are detected and classified (Stages 3–5,
documented in `docs/02_route_mapping/` and `docs/03_variants/`), Stage 6
merges the `variant_type` / `direction_group` / `is_reference` labels
back onto the row-level data to produce the final
**`govData/df_cleaned.csv` — 603,662 rows**, same count as the Stage 0
output. This confirms Stage 6 only enriches rows with metadata; it does
not filter. (A second, smaller output, `clean_filtered_data.csv`,
597,042 rows, is a display-filtered subset used by later phases — not
part of this cleaning walkthrough.)

Two flags are attached for downstream analyses to use, but neither
removes rows at this stage: `low_confidence` (`n_observations < 8`) and
`hour_display` (`scheduled_departure_time` with 25/26 remapped to 1/2 for
readability). See the decision log below.

---

## Part 2: Decision-log appendix

| # | Decision | Rationale | Alternatives considered | Row count effect |
|---|---|---|---|---|
| 1 | Expand route scope from the original 4 hardcoded routes to the full 7-line / 16-`route_id` target list | Matches the instructor-aligned target line list in `CLAUDE.md` (#2); the 4-route pilot under-covered the project's actual scope | Keep the legacy 4-route scope | Defines the raw universe at 708,642 rows (vs. a smaller pilot universe previously) |
| 2 | Diagnose the ~3x structural export overlap | Raw export batches cover overlapping periods, producing rows that share the same `(route, month, day, hour, stop)` key | None — this is a data artifact to be characterized, not a design choice | 708,642 rows in scope → 158,151 (22.3%) share a key with ≥1 other row, in 53,170 groups |
| 3 | Resolve duplicate keys by block-aware majority vote on `StopCode`, replacing the old per-row "keep highest `count_common`" rule | The old rule ignored whether duplicate copies agreed on which stop the row described — arbitrary (a coin-flip when `count_common` was tied) for the ~2% of groups that disagree, risking grafting the wrong stop into an otherwise-correct sequence | (a) Keep the old max-`count_common` rule — rejected, arbitrary for disagreeing groups; (b) blend/average fields across disagreeing rows — rejected, breaks internal consistency between a row's own `timeCumSum`/`distCumSum` values | 708,642 rows → 603,662 rows (550,491 unique-key + 53,170 group winners) |
| 4 | Flag (rather than silently resolve) the 48 groups with no clear `StopCode` majority | Traced to a one-position stop-numbering shift near the trip start in one overlapping export copy (re-syncs by stop 11) — not reconstructable from `count_common` alone | Attempt to algorithmically reconstruct the "correct" shifted alignment — rejected as unverifiable from available fields | 48 of 603,662 rows (~0.008%) flagged `ambiguous=True` in `stage0_dedup_audit.csv`; no rows dropped |
| 5 | Flag rows with `n_observations` (`count_common`) < 8 as `low_confidence` rather than dropping them | Floor is 4, median is 12 (`CLAUDE.md` #6) — low-count rows are noisier averages, not invalid ones | Drop low-count rows outright — rejected, would silently erase legitimate low-traffic hour slots (e.g. late night) that are themselves informative | No rows removed; adds a boolean column consumed by later EDA (`pipeline/stage7_eda_summary.py`) |
| 6 | Remap `scheduled_departure_time` 25/26 → display as 01:00/02:00 | These represent the following day's 1am/2am on a 26-hour clock (`CLAUDE.md` #4); showing "25:00" on a chart axis is unreadable | Drop late-night rows entirely — rejected, real ridership; keep raw 25/26 labels — rejected, fails the course's "informative axis labels" rule | Cosmetic remap only (`hour_display` column); no rows dropped |
| 7 | Treat Saturday sparsity (`DayOfWeek=7`) as a caution flag, not an exclusion | Saturday has far fewer rows than weekdays (`CLAUDE.md` #5) — low statistical power, but real and relevant service | Exclude Saturdays from analysis — rejected, Saturday patterns are part of the "best time to take this bus" question | No rows removed; downstream figures/tests should widen confidence intervals or note low-n for Saturday |
| 8 | Rename raw columns to readable names and tag every row with `route_name` in one unified file | Raw names (`HourSourceTime`, `StopSequence_Rishui`...) fail the course's informative-labels rule; a single file keeps `route_id`/`route_name` as columns instead of splitting per line, simplifying cross-line comparison | Keep raw names + a separate data dictionary — rejected, doesn't satisfy the report's axis-labeling rule; per-line file split (the original per-notebook approach) — rejected, made cross-line comparison and pipeline reuse harder | 603,662 rows → 603,662 rows (pure rename + tag, no filtering) |

### Row-count summary

| Stage | File | Rows |
|---|---|---|
| Raw export, filtered to 16 target `route_id`s | (in-memory, Stage 0 input) | 708,642 |
| After Stage 0 majority-vote dedup | `govData/ride_data_merged.csv` | 603,662 |
| After Stage 2 rename + line tagging | `govData/renamed_ride_data.csv` | 603,662 |
| After Stage 6 variant-type enrichment (final) | `govData/df_cleaned.csv` | 603,662 |
| Display-filtered subset (later phases only) | `govData/clean_filtered_data.csv` | 597,042 |

**Sources:** `pipeline/stage0_rebuild_merged.py`, `pipeline/STAGE0_DEDUP_NOTES.md`,
`pipeline/stage2_rename_and_tag.py`, `pipeline/stage6_finalize_outputs.py`,
`pipeline/config.py`, `govData/stage0_dedup_audit.csv`, `CLAUDE.md`
("Known Data Issues"), `work_report_2026-07-19.md`, git history
2026-07-19 (commits `b5d0775`, `b940dd9`, `f95c71e`).
