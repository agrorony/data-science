# Final Report — Working Draft
(Content drafted so far. Sections/figure numbers are placeholders — will be renumbered once assembled in Word.)

---

## Introduction

We analyze the Israeli Ministry of Transport's *"Arrival to Station by Day and Hour"* dataset ([data.gov.il](https://data.gov.il/he/datasets/ministry_of_transport/arrivaltostationdayandhours/e3673768-3dc2-4e62-b0ea-cf763c07a037)), which records average bus arrival behavior for scheduled service across Israel. We focus on seven bus lines running through Jerusalem's Rechavia corridor (lines 9, 14, 15, 17, 19, 22, 97), yielding 603,662 records after cleaning.

Each record is *not* a single bus ride. It is the average travel behavior of all rides that shared the same (route, month, day of week, scheduled departure hour, stop) combination, together with `n_observations` — how many individual rides that average is built from. A full trip is therefore not one row but a **block** of consecutive rows, one per stop, ordered by `stop_sequence`, each carrying the cumulative travel time and distance from the trip's first stop. Table 1 shows one such block.

**Table 1.** Line 19, direction A (route_id 10802) — Wednesday, 05:00 departure, September (first 8 of 39 stops)

| stop_sequence | stop_name | n_observations | cumulative_time (min) | cumulative_distance (m) |
|---|---|---|---|---|
| 1 | כניסה ראשית/הדסה עין כרם | 6 | 0.39 | 0 |
| 2 | מרכז הסטודנט/הדסה עין כרם | 6 | 0.83 | 457 |
| 3 | צומת אורה | 6 | 3.08 | 1,973 |
| 4 | הכפר השוודי/סולד | 6 | 5.20 | 2,901 |
| 5 | מרכז פיליפ ליאון/סולד | 6 | 6.27 | 3,219 |
| 6 | המפלצת/טהון | 6 | 7.13 | 3,525 |
| 7 | טהון/גולומב | 6 | 8.37 | 3,866 |
| 8 | פארק פישמן/גולומב | 6 | 9.18 | 4,246 |

This block structure is what the rest of the analysis is built on: comparing which stops appear, and in what order, across all blocks sharing the same (route, month, day, hour) lets us tell a normal trip from one that skipped stops — a **variant** — which is how the street closures on Aza St. were first detected (Section 2.2).

**Project goal:** use the data to analyze the travel patterns of bus lines serving Jerusalem's Rechavia neighborhood.

**The big question:** given the recurring street closures near the neighborhood, how can a resident know the most reliable way to leave Rechavia by bus? We break this into four sub-questions, addressed in Section 3: (1) when and how often do the closures occur, and on which lines; (2) does the detour actually take longer, or does it compensate for the added distance; (3) do the closures spill over onto nearby lines that don't run on the closed street at all; and (4) how do lines that share part of the corridor, but not the exact closed segment, respond?

---

## 2. Exploratory analysis

### 2.1 Data cleaning

The raw export, filtered to the seven target lines (16 underlying `route_id`s), contains 708,642 records. Inspecting these revealed a structural problem: 158,151 records (22.3%) share the exact same key — route, month, day of week, hour, and stop — with at least one other record, forming 53,170 duplicate groups. This is consistent with the government export itself being assembled from roughly three overlapping data batches covering the same period, not a data-entry error: 89% of the duplicate groups contained exactly 3 rows (a suspiciously consistent size for random mistakes), and 98% of those groups were pure copies — identical on every field except ride count — exactly what repeated exports of the same real trip would produce. The same pattern was already seen, at a different scale, in an earlier version of this pipeline that concatenated four raw files.

We resolved each duplicate group by majority vote: for every group, we kept the stop that a majority of its duplicate rows agreed on, then — among rows agreeing with that stop — kept the one with the highest `n_observations` (the most individual rides behind it). Only about 2% of duplicate groups actually disagreed on which stop was recorded; for the rest, the duplicate copies were identical apart from observation count, so any reasonable rule resolves them the same way. This left **603,662 final records**, none of which were dropped for any reason other than being a losing duplicate.

Two more issues were flagged, not removed: records built from fewer than 8 rides (6.3% of the data) are marked `low_confidence` rather than dropped, since excluding them would silently erase real low-traffic time slots (e.g. late night); and hours coded 25/26 (meaning 01:00/02:00 the next day, on a 26-hour clock) are remapped to 1/2 for display only, so figures stay readable without losing data.

### 2.2 Route structure and variants — how we found the closures

Every bus line runs in one of two directions (direction A / direction B, except line 15, which is a single loop route with no direction split — see the route mapping table in Section 2.2's appendix). Within one line and direction, we grouped all blocks (Section "Introduction", Table 1) sharing the same month, day of week, and departure hour, and compared their stop sequences.

Most blocks for a given line and direction follow the exact same sequence of stops — we call this the **reference route** (the sequence shown in Table 1 for line 19). A minority of blocks follow a different sequence: some stops are missing, usually a *consecutive run* of them, while the stops before and after that gap match the reference route exactly. We call each distinct alternative sequence a **variant**, and rank variants by how many blocks use them. Variants that appeared fewer than 5 times across the whole dataset were treated as one-off reporting noise and excluded, rather than as real, repeated route changes.

Table 2 shows exactly this kind of gap for line 19, direction A: compared with the reference route in Table 1, this variant skips stop_sequence 17–22 — six consecutive stops, three of which sit on Aza St. (עזה/הרב ברלין, עזה/רד"ק, עזה/בלפור). This is a real block, in the same row format as Table 1 — nothing removed for display, this is simply what the data contains: `stop_sequence` jumps straight from 16 to 23.

**Table 2.** Line 19, direction A (route_id 10802) — Saturday, 19:00 departure, January (a detour block; same reference route as Table 1, rows 16 and 23 shown)

| stop_sequence | stop_name | n_observations | cumulative_time (min) | cumulative_distance (m) |
|---|---|---|---|---|
| 16 | הרצוג/טשרניחובסקי | 7 | 21.11 | 8,249 |
| 23 | אוסישקין/בצלאל | 7 | 25.94 | 8,453 |

In Table 1's reference sequence, the same two stops are `stop_sequence` 16 and 23 as well — but with six rows in between (17–22, listed above) that simply don't exist in this block. Nothing was deleted for the table; this is what the raw data looks like for a trip that skipped Aza St.

To see this pattern across *all* variants of a line at once, rather than one gap at a time, we built a stop-presence heatmap: stops along the x-axis (in reference order), each variant as a row, colored green where the variant visits that stop and white where it doesn't, with rows ordered by how often each variant occurs. This grid makes a shared gap across several of a line's frequent variants immediately visible as a vertical white band — which is how the Aza St. segment was first identified as a recurring, structural gap rather than a one-off (Figure 1; one panel per line, e.g. `docs/03_variants/line_19/variants_raw.png`).

Because the year covered by this dataset (2024) included repeated political protests in the area, and Aza St. runs past the Prime Minister's residence, this gap has a concrete real-world explanation: police repeatedly closed the street to traffic, and buses were rerouted around it. This finding is what redirected the project from general travel-pattern exploration toward the specific closure-impact questions in Section 3.

A later refinement (documented in `docs/03_variants/`) merged a handful of variants that differed only trivially (e.g. skipping just one terminal stop) and excluded a few more that turned out to be unrelated one-off issues — this cleaned up the variant counts used in Sections 2.3 onward but did not change the Aza St. finding itself.

### 2.3 Baseline travel-time comparison across lines

Once a line's baseline route is fixed (Section 2.2), we can compare travel time across the seven lines on equal footing: mean end-to-end trip duration for the baseline variant only, pooling both directions of each line into one distribution.

Figure 2 ranks the seven lines by this mean, longest to shortest. Table 3 adds each line's baseline route length, confirming that travel time tracks distance closely (r = 0.92, r² = 0.84, across the 7 lines): line 9 covers the longest route (20.0 km) and takes the longest time (~90 min), line 97 the shortest of both (10.0 km, ~44 min). Implied average speed ranges from 13.4 km/h (line 9) to 17.4 km/h (line 19). The one real exception is line 15: shorter than both lines 17 and 19 (15.9 km vs. 16.6/16.1 km) yet slower than either (65.5 min vs. 59.7/55.5 min) — its implied speed (14.5 km/h) is the lowest of the non-line-9 group, so route length alone doesn't fully explain line 15's duration.

**Table 3.** Baseline route length, mean travel time, and implied average speed, by line

| Line | Route length (km) | Mean travel time (min) | Implied speed (km/h) |
|---|---|---|---|
| 9 | 20.0 | 89.7 | 13.4 |
| 22 | 17.9 | 74.3 | 14.5 |
| 15 | 15.9 | 65.5 | 14.5 |
| 17 | 16.6 | 59.7 | 16.7 |
| 19 | 16.1 | 55.5 | 17.4 |
| 14 | 12.8 | 48.7 | 15.7 |
| 97 | 10.0 | 43.6 | 13.8 |

The black error bars in Figure 2 are the standard error of the mean (SEM = std/√n). These are small (0.20–0.40 min) purely because of sample size — every line has n > 940 baseline blocks — so the mean itself is estimated precisely for all seven lines. The reported standard deviations, by contrast, range 9.1–14.6 min. It's worth being precise about what that variation is: each data point behind it is not a single ride but a time-slot average (one route/direction/month/day-of-week/hour combination), so this spread reflects structural variation across the day and week, not random noise between two buses on the same route at the same hour.

Figure 3 shows that structure directly: all seven lines follow the same diurnal shape — travel time rises through the morning, peaks around 14:00–15:00, and falls off toward evening. Line 9, for example, averages ~67 min at 06:00 versus ~109 min at its 14:00 peak — a 40+ minute swing that is largely responsible for its overall std. A variance decomposition confirms this: departure hour alone accounts for 70% of the variance in line 9's baseline travel time (η² = 0.70), and hour + day-of-week + month together account for 95% — confirming this dispersion is systematic, not noise.

Because the lines differ so much in overall length, absolute std is a misleading way to compare their *relative* volatility. Normalizing by the mean (coefficient of variation, CV = std/mean) tells a flatter story: line 9 has the largest absolute std (14.6 min) but a mid-range CV (16.3%), while the shorter lines 14, 15, and 97 all sit around 21% CV — proportionally at least as variable, if not more, than line 9. In other words, the shorter lines are no less exposed to traffic-driven timing swings; they just have less total travel time for the same swing to be spread across.

Lines mostly differ in overall level (a roughly constant vertical gap between line 9's curve and line 97's, for example), not in *when* during the day they are slowest — so the network-wide worst time to travel is the same early-afternoon window regardless of which of these lines you take.

This baseline (no detour) picture is the yardstick the rest of the report measures against: any travel-time effect attributed to a street closure in Section 3 is a deviation from these already-known hourly and per-line patterns, not a first look at how long these lines normally take.

**Figure 2.** Baseline trip duration by line, longest to shortest, mean ± SEM (both directions pooled; std reported per bar). `docs/04_baselines/travel_time_all_lines.png`

**Figure 3.** Baseline travel time by departure hour, all seven lines (±1 SEM shading). `docs/04_baselines/baseline_travel_time_by_hour.png`

### 2.4 How often do lines actually detour?

Section 2.2 showed how one detour is detected within a single line. Zooming out to the whole network: across the full year, how often does each line run a non-baseline ("blocked") variant instead of its usual route?

**Table 5.** Share of trips on a non-baseline variant, by line, overall and on Saturdays

| Line | Overall blocked share | Saturday blocked share | n (Saturday blocks) |
|---|---|---|---|
| 17 | 12.2% | 80.5% | 82 |
| 22 (direction A) | 9.9% | 69.0% | 42 |
| 19 | 8.9% | 75.7% | 74 |
| 9 | 7.0% | 84.1% | 82 |
| 97 | 4.7% | 66.4% | 110 |
| 15 (control) | 0.3% | 0.0% | 56 |
| 14 (control) | 0.0% | 0.0% | 65 |

Every line that shares the Aza St. corridor (9, 17, 19, 22, 97) shows the same shape: a modest overall share (5–12%) that jumps to a large majority of trips on Saturdays specifically (66–84%). The two control lines sit far below all five, at 0.3% and 0.0% — a useful sanity check, since they don't run through the corridor at all: their near-zero share confirms the detection method is picking up something real and geographically specific on the five affected lines, not noise spread evenly across the network.

One nuance is worth flagging directly, since it looks like a contradiction at first: on two Saturdays (April, June) where most affected lines sit near 100% blocked, line 22 — and sometimes line 19 — shows a markedly lower share (25–75%) at the exact same hours. Checking each line's individual trip records rules out a scheduling difference: all lines ran the same hour slots, just some of line 22's trips stayed on the normal route instead of detouring. This is genuine differential exposure, not an artifact — line 22's longer route only partially overlaps the closed segment, so a closure evidently doesn't force 100% of its scheduled trips onto a detour the way it does for line 17.

**Figure 5.** Non-baseline variant share by month and day of week, all seven lines, shared colorbar. `docs/06_blockade_frequency/blockade_all_lines.png`

---

## 3. Specific question, methods, conclusions

### 3.1 When during the year do closures happen?

**Question:** is there a clear, well-supported pattern for when Aza St. closures occur, or are they scattered unpredictably?

**Method:** every (month, day-of-week) combination was scanned for cells where at least 3 lines independently show a blocked share above 10%, then each flagged cell was confirmed at the hour level: an hour only counts as confirmed if at least 3 of that cell's affected lines are each individually well-supported (n≥8 observations) and "pure" (every trip in that exact slot agrees on which variant it ran) — a strict bar chosen specifically to avoid rounding a merely red-looking cell up to "confirmed."

**Findings:** 21 (month, day-of-week) cells clear this bar across the year. Eleven are Saturdays — every month with data except December — each confirmed for a consistent evening window, roughly 19:00 through midnight. Ten are weekdays: three correspond to specific, separately verified events (a wide Wednesday event in November, 10:00–22:00; a narrower Wednesday event in December, 13:00–18:00; and two distinct single-hour events on a Monday in October, 08:00 and 13:00, that turned out to have two unrelated causes rather than being one spread-out closure), and seven are newly confirmed weekday cells in April, May, and June — May Monday in particular is large and well supported (up to 26 observations per line). As a sanity check, the two control lines never clear the 10% bar in any single cell across the whole year, which is expected given their near-zero overall share.

**Conclusion (part 1 of the big question):** closures are concentrated on Saturday evenings essentially year-round, plus a smaller number of specific weekday windows clustered in spring (April–June) and one sustained event each in autumn and early winter.

**Figure 6.** Confirmed blockade hours by month and day of week, full year. `docs/13_full_year_calendar/confirmed_hours_calendar.png`

### 3.2 Does detouring cost or save time?

**Question:** when a bus detours around a closure instead of running its normal route, does the rider lose time overall, or does the alternate path compensate?

**Method:** for each of the five affected lines, we compared the median travel time of its dominant detour variant against its own baseline variant, by departure hour, both directions pooled.

**Findings:** every one of the five lines' detour is faster overall than its baseline — savings from −8.0 min (line 97) to −15.9 min (line 9), statistically supported for every line individually (95% CI excludes 0, p≤0.005 in all five). The underlying route distance explains why: every detour is measurably *shorter* than the baseline route it replaces (by 6.5–17.7%), not longer — these "detours" behave more like a short-turn or express variant than a slow forced diversion.

This overall pattern hides one exception worth flagging up front, since Section 3.4 returns to it: line 97's detour is only faster *on average*. Broken down by hour, it costs riders up to +14 minutes specifically between roughly 14:00 and 17:00, even though the same detour saves time at every other hour of the day.

**Conclusion (part 2):** taking the detour is, on balance, the better choice on every affected line — but "on balance" is doing real work for line 97 specifically in the mid-afternoon.

**Figure 7.** Median travel-time delta (detour minus baseline) by hour, all five affected lines. `docs/05_skip_comparison/delta_all_lines.png`

### 3.3 Do closures ripple onto lines that don't run through Aza St.? — control lines 14 & 15

**Question:** lines 14 and 15 don't pass through the Aza St. corridor at all. Do the closures there slow them down anyway, indirectly — e.g. via displaced traffic elsewhere in the city?

**Method:** we first defined a *confirmed blockade window*: any (month, day-of-week, hour) slot where at least one of lines 17, 19, or 22 (direction A only — see note below) ran a genuinely blocked variant that hour (missing more than 15 stops from its normal route). This gave **208 such slots** across the year (36 on Saturdays, 172 on weekdays).

*Methods note: line 22's direction B needed a separate fix first.* Line 22 runs a longer overall route than the other affected lines, and a handful of its direction-B trips happened to also miss more than 15 stops for reasons unrelated to the Aza St. closure — one-stop schedule swaps elsewhere on the route, not detours. Counting those as "blockade windows" would have overstated how often a closure was really happening. Excluding direction B (verified separately, not a real corridor detour) drops the weekday window count from an earlier, contaminated 284 to the corrected 172; Saturday windows are unaffected, since direction B never drove a Saturday-only window.

For each control line (14, both directions pooled; 15, its single loop route), every one of its own baseline trips was labeled *blockade* if its own (month, day, hour) matched one of the 208 confirmed slots, or *matched normal* if it ran at the same day-of-week and hour but in a month that wasn't flagged for that slot — comparing like against like (same time of week), not blockade months against all other months indiscriminately. We compared the two groups' travel-time distributions with a Mann-Whitney U test (primary, since travel times are right-skewed) and Welch's t-test (secondary), separately for Saturdays and weekdays.

**Findings:**

**Table 4.** Control line travel time, confirmed blockade windows vs. matched normal weeks

| Line | Stratum | n blockade | n normal | Median blockade (min) | Median normal (min) | Δ (min) | Mann-Whitney p | Welch t p |
|---|---|---|---|---|---|---|---|---|
| 15 | Saturday | 33 | 12 | 52.9 | 52.0 | +0.9 | 0.376 | 0.353 |
| 15 | Weekday | 153 | 746 | 64.8 | 66.6 | −1.8 | 0.941 | 0.543 |
| 14 | Saturday | 40 | 7 | 37.8 | 36.6 | +1.2 | 0.317 | 0.256 |
| 14 | Weekday | 198 | 1,108 | 48.0 | 47.1 | +0.9 | 0.156 | 0.064 |

Neither control line shows a significant effect in any stratum, and — unlike an earlier pass through this analysis — the two tests now agree with each other everywhere, including on line 14's weekday stratum (Mann-Whitney p=0.156, Welch p=0.064; both "not significant," though Welch is borderline).

**Stronger, properly-stratified check:** because Saturday and weekday trips differ systematically (different traffic, different schedules), simply pooling them risks distorting the comparison. A day/hour-stratified permutation test — which shuffles blockade/normal labels only *within* matching (day-of-week, hour) groups, so it stays valid even with both strata combined — gives one clean answer per line: line 15's travel time is **−1.2 min [95% CI −3.4, +1.0], p=0.973**; line 14's is **−0.4 min [95% CI −1.9, +1.2], p=0.998**. Both confidence intervals comfortably include zero, both effect sizes are negligible (Cliff's δ = −0.08 and −0.06), and both p-values are about as far from significant as a p-value can be.

Figure 4 shows the hour-by-hour version of the same comparison. Both lines swing several minutes above and below zero at different, largely uncoordinated hours (line 15 peaks near +4.4 min around 08:00; line 14 peaks near +9.2 min around 16:00) rather than moving together — this is consistent with the null result above: what looks like a pattern hour to hour is noise around a near-zero average, not a shared response to the closures.

**Conclusion:** we do not find evidence that the Aza St. closures spill over onto lines that don't run through that corridor. Both the per-stratum tests and the more rigorous day/hour-stratified permutation test agree on this for both lines. For a rider deciding whether closures make lines 14 or 15 unreliable, the answer from this data is: no — travel time on those two lines during a confirmed closure is statistically indistinguishable from a normal day at the same hour.

**Figure 4.** Hourly travel-time delta (blockade window minus matched normal), lines 14 and 15, Saturday-only hours shaded. `docs/08_control_lines_15_14/control_lines_delta.png`

### 3.4 Lines 9 & 97: same area, different segment — reroute, delay, or both?

**Question:** lines 9 and 97 pass through the general Aza St. area but not the exact segment shared by 17/19/22. During a confirmed closure, do they change route, run late, or neither?

**Method:** using the same confirmed blockade windows as Section 3.3, two separate questions were asked for each line: (a) *route* — does the line's own share of non-baseline trips rise during blockade windows compared with matched normal hours (chi-square/Fisher's exact test)? (b) *time* — restricted to trips that stayed on the line's own baseline route, does travel time change (Mann-Whitney U)?

**Findings — line 9:** strongly route-affected in both strata (Saturday: 92.1% vs. 52.9% non-baseline, p=0.001; weekday: 31.0% vs. 0.7%, p≈0) — line 9 reroutes far more often once the corridor is closed. It is also time-affected, but only on Saturdays: baseline trips run **11.7 minutes slower** during confirmed blockade windows (75.6 vs. 63.9 min, p=0.010) — the single largest confirmed delay found anywhere in this project. There is no measurable weekday time effect.

**Findings — line 97:** equally strongly route-affected (Saturday: 85.3% vs. 46.2%, p=0.0003; weekday: 9.2% vs. 0.8%, p≈0). Unlike line 9, its own baseline-route travel time shows no delay — if anything, a small, statistically supported speed-up (−1.2 min, p=0.005) during blockade windows, plausibly because traffic that normally shares its route is displaced elsewhere. But as Section 3.2 noted, line 97's own detour is not uniformly fast: it costs up to +14 minutes specifically between 14:00 and 17:00, so which variant a rider happens to catch, and at what hour, matters more for line 97 than for line 9.

**Conclusion (part 3):** both lines reroute heavily during a closure rather than absorbing it in place — but only line 9 riders experience a confirmed, sizeable delay, and only on Saturdays. Line 97 riders are largely protected on time overall, except for a specific mid-afternoon window where their own detour becomes the slow option.

**Figure 8.** Own detour cost vs. cost of staying on the baseline route during others' blockades, by hour, line 97. `docs/09_lines_9_97/line_97_blockade_delta.png`

### Bringing the four sub-questions together

Returning to the project's central question — how can a resident know the most reliable way to leave Rechavia by bus, given recurring closures — the four findings above combine into a single practical answer. Closures are concentrated on Saturday evenings nearly year-round, plus a handful of specific spring weekday windows (3.1). During a confirmed closure, lines 17, 19, 22, 9, and 97 all reroute rather than sit in the closure, and that reroute is faster than their normal route on average (3.2), so simply staying on one of these lines through a closure window is, on balance, not a bad choice. The exceptions are narrow but concrete: line 9 riders face a real ~12-minute delay specifically on Saturdays (3.4), and line 97's detour briefly reverses into a time cost between 14:00 and 17:00 (3.2, 3.4) — both worth avoiding at those specific times if an alternative exists. Lines 14 and 15, which don't run through the corridor at all, show no measurable slowdown at any time during a confirmed closure (3.3) — they are the one genuinely unaffected option, though also the two lines least useful for actually leaving the neighborhood via this corridor in the first place.

---

## 4. Follow-up ideas

A few directions this project didn't have time to pursue, in rough order of how directly they extend the current analysis. The stop code marking line 97's direction split (`5912`) is unresolved in every available stop-name table in this dataset; a proper GTFS or stations re-export would let line 97's figures use a real stop name instead of a raw code. The same closure-impact method — confirmed windows, baseline-vs-detour delta, control-line spillover test — is not specific to Aza St. or to Jerusalem, and re-running it on a different corridor or city would test whether the pattern found here (fast detours, narrow but real delay windows, no measurable spillover to unrelated lines) generalizes or was specific to this particular street and this particular set of closures. This dataset also has no ridership or crowding information, only scheduled travel time; combining it with boarding counts would turn "line 9 loses 12 minutes on Saturdays" into an estimate of total rider-minutes lost, a more directly useful number for transit planning than a per-trip delay. Finally, since the detection method here works retrospectively on a full year of data, a live version — watching for a sudden shift in which variant a line is running, hour by hour — could plausibly flag a new closure within the same day it starts, rather than requiring a full data export to confirm it after the fact.

---

*(Draft complete through Section 4. Remaining before submission: final figure selection to fit the 10-page budget, formatting pass — font/margins/line spacing/figure numbering renumbered in order — and trimming prose where sections run long. See `FINAL_REPORT_OUTLINE.md` for the page budget and task split.)*
