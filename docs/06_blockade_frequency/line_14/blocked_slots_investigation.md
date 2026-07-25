# Line 14: what the "blockade" marks in phase 06 actually are

*Investigation of every slot phase 06 reports as blocked for line 14. Data: effective (merged) variant set, `variant_type_v2`.*

## What was checked

All 14 hour-slots (out of ~1,850 line-14 blocks, 0.8%) marked "blocked", their 11 underlying variants, the stops they skip, their timing, and their travel times vs the reference route at the same day-of-week/hour.

## What the data shows

**Line 14 cannot detour around the blockade: its route shares 0 stops with the 17/19 blockade footprint** (the 10 stops skipped by those lines' real detours). Whatever its "blocked" marks are, they are not Aza-corridor responses.

**The marked variants are recording dropouts, not route changes.** All 11 are near-singletons (ten have n=1, one has n=4). They skip 1–6 stops clustered in the same zones of the route (sequence ~7–14 in direction A, ~24–30 in direction B) and — decisively — **add zero new stops**. A real detour adds streets; a bus that simply didn't register at a stop (no passengers, missed stop-detection) produces exactly this signature.

**Timing has no blockade pattern.** The 14 slots scatter across weekdays and hours (8 of 14 on *Tuesdays*, hours 05:00–22:00, only 2 on Saturday) — nothing like the Saturday-19:00–23:00 concentration of the real blockades.

**Travel time is unaffected.** Deltas vs the reference median at the same day/hour range from −8.1 to +12.5 min, mean ≈ +1.8 min, mixed signs — ordinary traffic variance, no systematic slowdown.

## Why they were counted at all

The ">15 stops = blocked" rule labels **every** non-reference variant as blocked, and the n>5 filter was applied only to the *maps*, not to the statistics — so these n=1 dropouts silently entered the phase 06 frequencies.

## Conclusion

Line 14's phase-06 "blockades" are classification noise from single-trip stop-recording dropouts. The decision to treat line 14 as never-blocked project-wide is supported by the data.

## Figure options (pick 0–3)

1. **Dropout signature grid** — stop-presence grid of the 11 flagged variants (green/white, house layout) side by side with line 17's real detour variant: 14's rows show scattered 1–6 missing stops and no added stops; 17's shows a contiguous corridor gap. Visual proof these aren't detours.
2. **Timing scatter** — day-of-week × hour scatter of the 14 flagged slots over a background of 17/19's real blocked slots: 14's marks land on weekday midday, the real blockades on Saturday evening.
3. **Delta bars** — one bar per flagged slot: travel time vs matched reference median, mixed signs around zero, vs the consistently positive deltas of real blockades (line 17 reference bars alongside).
