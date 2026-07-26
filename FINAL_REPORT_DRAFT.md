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

To see this pattern across *all* variants of a line at once, rather than one gap at a time, we built a stop-presence heatmap: stops along the x-axis (in reference order), each variant as a row, colored green where the variant visits that stop and white where it doesn't, with rows ordered by how often each variant occurs. This grid makes a shared gap across several of a line's frequent variants immediately visible as a vertical white band — which is how the Aza St. segment was first identified as a recurring, structural gap rather than a one-off. (Figure — one panel per line, e.g. `docs/03_variants/line_19/variants_raw.png`.)

Because the year covered by this dataset (2024) included repeated political protests in the area, and Aza St. runs past the Prime Minister's residence, this gap has a concrete real-world explanation: police repeatedly closed the street to traffic, and buses were rerouted around it. This finding is what redirected the project from general travel-pattern exploration toward the specific closure-impact questions in Section 3.

A later refinement (documented in `docs/03_variants/`) merged a handful of variants that differed only trivially (e.g. skipping just one terminal stop) and excluded a few more that turned out to be unrelated one-off issues — this cleaned up the variant counts used in Sections 2.3 onward but did not change the Aza St. finding itself.

---

*(Sections 2.3–2.4, Section 3, Section 4 to be drafted next — see `FINAL_REPORT_OUTLINE.md` for what goes where.)*
