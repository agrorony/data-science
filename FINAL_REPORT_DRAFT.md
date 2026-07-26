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

---

## 3. Specific question, methods, conclusions

*(Section 3.1 — blockade frequency/timing — and 3.2 — detour cost — depend on Rony's ongoing work on the blockade-frequency phases (Section 2.4/docs 06, 13) and will be drafted once that's finalized. Note: docs/07 was archived and replaced by docs/13's confirmed-hours output as the answer to "when do blockades happen" — see docs/README.md. Jumping ahead to 3.3, which is done.)*

### 3.3 Do closures ripple onto lines that don't run through Aza St.? — control lines 14 & 15

**Question:** lines 14 and 15 don't pass through the Aza St. corridor at all. Do the closures there slow them down anyway, indirectly — e.g. via displaced traffic elsewhere in the city?

**Method:** we first defined a *confirmed blockade window*: any (month, day-of-week, hour) slot where at least one of lines 17, 19, or 22 (either direction) ran a genuinely blocked variant that hour (missing more than 15 stops from its normal route). This gave 320 such slots across the year (36 on Saturdays, 284 on weekdays).

For each control line (14, both directions pooled; 15, its single loop route), every one of its own baseline trips was labeled *blockade* if its own (month, day, hour) matched one of those 320 flagged slots, or *matched normal* if it ran at the same day-of-week and hour but in a month that wasn't flagged for that slot — comparing like against like (same time of week), not blockade months against all other months indiscriminately. We compared the two groups' travel-time distributions with a Mann-Whitney U test (primary, since travel times are right-skewed) and Welch's t-test (secondary), separately for Saturdays and weekdays.

**Findings:**

**Table 4.** Control line travel time, confirmed blockade windows vs. matched normal weeks

| Line | Stratum | n blockade | n normal | Median blockade (min) | Median normal (min) | Δ (min) | Mann-Whitney p | Welch t p |
|---|---|---|---|---|---|---|---|---|
| 15 | Saturday | 33 | 12 | 52.9 | 52.0 | +0.9 | 0.376 | 0.353 |
| 15 | Weekday | 265 | 854 | 66.2 | 67.5 | −1.3 | 0.884 | 0.715 |
| 14 | Saturday | 40 | 7 | 37.8 | 36.6 | +1.2 | 0.317 | 0.256 |
| 14 | Weekday | 376 | 1,298 | 48.5 | 47.7 | +0.8 | 0.071 | **0.006** |

Neither control line shows a clearly significant effect. Line 15 shows essentially no difference in either stratum. Line 14's weekday stratum shows a small effect in the expected direction (+0.8 min slower during blockade windows), but the two tests disagree: Mann-Whitney is only borderline (p=0.071) while Welch's t-test is significant (p=0.006).

Figure 4 shows the same comparison hour by hour instead of pooled into one number. Both control lines run 2–9 minutes slower than their own normal pattern specifically between roughly 13:00 and 17:00, during confirmed blockade windows. But the two lines' curves track each other closely across the *entire* day — nearly identical shape and magnitude, not just in that window — which points away from an Aza-corridor-specific effect and toward something both lines would share regardless of that one closure: ordinary citywide midday/afternoon traffic that happens to also be heavier on the days the closures were active.

**Conclusion:** we do not find clear, consistent evidence that the Aza St. closures spill over onto lines that don't run through that corridor. There is a directional hint — line 14 runs a little slower during blockade windows in the afternoon — but it only clears one of two statistical tests, and line 15 shows nothing at all. For a rider deciding whether closures make lines 14 or 15 unreliable, the honest answer from this data is: not detectably — any slowdown they'd experience in that window is better explained by ordinary midday congestion than by the Aza St. closure itself.

**Figure 4.** Hourly travel-time delta (blockade window minus matched normal), lines 14 and 15, Saturday-only hours shaded. `docs/08_control_lines_15_14/control_lines_delta.png`

---

*(Section 2.4, Sections 3.1–3.2, 3.4, and Section 4 still to be drafted — see `FINAL_REPORT_OUTLINE.md` for what goes where.)*
