# Stage 0 dedup methodology

This documents the deduplication logic in `stage0_rebuild_merged.py`, which
rebuilds `govData/ride_data_merged.csv` from the raw government source
file. Written for the course report's methodology section.

## The problem

The raw source file contains a structural overlap: many trip records
appear more than once under the exact same key
`(route_id, month, DayOfWeek, HourSourceTime, StopSequence_Rishui)`. Of
708,642 rows across the project's 16 target `route_id`s:

- 550,491 rows (77.7%) have a unique key — no duplication, kept as-is.
- 158,151 rows (22.3%) share a key with at least one other row, forming
  53,170 duplicate-key groups.
- 89% of those groups have exactly 3 rows sharing the key — consistent
  with the raw export containing roughly 3 overlapping data batches
  covering the same period (the same underlying issue CLAUDE.md already
  documented for the old `ride_data1–4.csv` concatenation, just recurring
  inside the single unified government export used for this rebuild).

An earlier version of this script (`rebuild_ride_data_merged.py`, kept at
the repo root) resolved duplicate keys by keeping whichever row had the
highest `count_common`, without checking whether the duplicate rows
actually agreed on `StopCode`. For groups where they don't agree, that
tiebreak is arbitrary — particularly when `count_common` is *tied* across
the disagreeing rows, in which case the "highest count_common" rule
reduces to whichever row happened to appear first in the file.

## How much this actually matters

Of the 53,170 duplicate-key groups, only **1,065 (2.0%)** have more than
one distinct `StopCode` value within the group — the rest are pure
redundant copies (identical `StopCode`, only `count_common` differs
between the overlapping exports) and dedup correctly regardless of which
row is kept.

Within those 1,065 disagreeing groups:

- **1,017 groups (95.5%)** have a clear majority: 3 rows sharing the key,
  2 agreeing on one `StopCode` and 1 outlier. Example: route 5502, month 1,
  day 1, hour 5, stop_sequence 42 — 2 of 3 copies say `StopCode=6028`, 1
  says `6286`, `count_common` tied at 4 across all three. These are
  resolved by majority vote (2 of 3 wins), not by an arbitrary
  count_common tiebreak.
- **48 groups (4.5%)** have no clear majority (an even 2-vs-2 split across
  4 rows). All 48 are concentrated in one narrow slice: route_id 5502
  (line 22) and 11107/11108 (line 9), `month=1`, `HourSourceTime=12`,
  across several `DayOfWeek` values, at `StopSequence_Rishui` positions
  1–10 only. Inspecting the full block for one of these
  (route 11108, month 1, day 1, hour 12) shows the two disagreeing
  `StopCode` values at position *N* in one copy match the value at
  position *N+1* in the other copy — i.e. a **one-position numbering
  shift** between two overlapping export copies for the first ~10 stops
  of that trip, which re-synchronizes by position 11 (both copies agree
  from there through the end of the route). This looks like a data
  artifact in the raw export (an extra/missing stop record near the start
  of the trip in one of the two overlapping copies), not a genuine
  alternate route. Reconstructing the "correct" shifted alignment isn't
  possible from `count_common` alone, so these 48 groups are resolved
  with the same majority-vote fallback (highest `count_common` among the
  tied `StopCode`s) and are explicitly flagged (`ambiguous=True`) in
  `govData/stage0_dedup_audit.csv` for anyone who wants to inspect or
  exclude them. They affect 48 of 603,661 output rows (~0.008%).

## The resolution rule

For each duplicate key:

1. Take the most common (`mode`) `StopCode` across the group's rows.
2. If there's a clear majority, use it.
3. If there's no clear majority (a tie for the top spot), fall back to the
   highest-`count_common` row among the tied `StopCode`s, and record the
   key in the audit report as `ambiguous=True`.
4. Among the rows agreeing with the winning `StopCode`, keep the single
   row with the highest `count_common` (rather than mixing fields from
   different rows) — this keeps `timeCumSum_mean/std` and
   `distCumSum_mean` internally consistent, coming from one real
   observed row.

The full audit trail (every key with any `StopCode` disagreement, whether
majority-resolved or flagged ambiguous) is written to
`govData/stage0_dedup_audit.csv`.
