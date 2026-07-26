# Deep dive: why lines disagree on blockade frequency

*Analysis of all disagreement windows, without the 0.9/0.7 thresholds. Data: effective (merged, post-exclusion) variant set, `variant_type_v2` (>15-stop rule).*

**Status: fixed centrally, `fix_22b_central_prompt.md`.** This document's
own candidate figure #4 below (recompute 22B's share counting only
corridor-footprint variants as "blocked") is exactly what
`pipeline.variant_merges.LINE_22_NON_CORRIDOR_DIRECTION` now does: line 22
direction_B's non-reference variants are forced to `"non_corridor"`
project-wide, so its share reads 0% everywhere, not just in one recomputed
figure. The numbers on this page (32%, 69%, the 10-stop footprint, etc.)
describe the state of the data **as investigated at the time** and remain
an accurate record of the diagnosis; they are not live numbers and are no
longer recomputed elsewhere in the project the way they were before this
fix (see [line_22/README.md](line_22/README.md) and
[docs/06_blockade_frequency/README.md](README.md) for current figures).

## The disagreement, quantified

Relaxing the thresholds to "any window where the max share ≥30% and the gap between lines ≥25pp" yields **15 disagreement windows** (vs the handful found before). In **14 of 15, line 22 is the low outlier** — usually at 0% while 17 and 19 are at 40–100%. Splitting by direction pins it down entirely:

| Saturday blocked share | direction_A | direction_B |
|---|---|---|
| Line 17 | 82% | 80% |
| Line 19 | 67% | 83% |
| Line 22 | 69% | **32%** |

**The entire disagreement is line 22, direction B.**

## Hypothesis 1 — 22B never skips the Aza corridor: CONFIRMED

Defining the "blockade footprint" as the 10 stops skipped by 17's and 19's main blocked variants:

- 22 direction_A's reference route contains 3 footprint stops, and its main non-baseline variant (n=96) skips exactly those 3 → a genuine corridor detour. Its 69% Saturday share is real.
- 22 direction_B's reference route contains only **2** footprint stops, and its top variants (n=112, n=29) skip **0** of them — they are 1-stop swaps elsewhere on the route, not corridor detours. So 22B (a) physically barely touches the blocked segment in this direction, and (b) its 32% "blocked" share is inflated by trivial variants that are not blockade responses at all.

## Hypothesis 2 — regular rides happen later than blocked rides: CONFIRMED (except 22B)

On Saturdays, for 17A, 19B, and 22A: blocked slots span 19:00–23:00 (median 21:00) while regular slots exist only at 22:00–24:00 (median 23:00) — regular service resumes *after* the blockade. **22B is the exception:** its regular rides run through the whole evening 19:00–23:00. During Saturday slots when 17/19 were blocked, 22B ran its normal route 21 times, a variant 12 times, and was absent 3 times. It genuinely keeps driving through the blockade hours.

## Hypothesis 3 — 22B blockade-window data is fabricated: REFUTED

All 38 of 22B's Saturday blocks have distinct stop-level travel-time vectors (0 identical pairs), only 0.5% of rows have std = 0, and n_observations is a plausible 7–10. The data is real.

## Bonus finding

When 22B passes through during 17/19 blockade slots on its reference route, it is **~4.5 min slower** (mean 56.8 vs 52.3 min; n=21 vs 5 — small control group, treat as suggestive). It passes, but pays.

## Bottom line

The 100%-vs-other disagreements are not a data problem. Line 22 direction B travels the corridor in a direction/segment the blockade doesn't force a detour on, keeps operating through blockade hours slightly slower, and its nominal "blocked" share is inflated by non-corridor 1-stop variants.

## Candidate figures (pick what you want)

1. **Stop-overlap map** — the 3 reference routes vs the 10-stop blockade footprint, showing 22B touches only 2 stops (visual proof of H1).
2. **Saturday-evening timeline** — per line/direction: hour slots 19:00–24:00 colored blocked/regular/absent, showing everyone detours 19–23 while 22B keeps driving (H2).
3. **22B pass-through cost** — its reference-route travel time during 17/19 blockade slots vs other Saturday slots (the +4.5 min finding).
4. **Corrected share heatmap** — 22B's share recomputed counting only corridor-footprint variants as "blocked" (would drop from 32% to ~0%, making the story consistent).
