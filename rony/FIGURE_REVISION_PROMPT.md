# Figure Revision Tasks — variant_analysis.ipynb

## Context

This is a data science final project analyzing Israeli public bus transit data,
focusing on how protest-related road blockades affect bus travel times.
The main notebook is `rony/variant_analysis.ipynb`. It loads cleaned data from
`govData/df_cleaned_{route}.csv` (routes 15, 17, 19, 22) and variant summaries
from `govData/variant_summary_{route}.csv`. Figures are saved to `rony/figures/`.

Column names in the cleaned data use Avishagi's renamed convention:
- `route_name` — 15 / 17 / 19 / 22
- `month`, `day_of_week` (1=Sun … 7=Sat)
- `scheduled_departure_time` (hours 5–26; 25=01:00, 26=02:00 next day)
- `hour_display` — derived: replace {25→1, 26→2}
- `stop_sequence`, `stop_code`
- `route_variant_id` (0 = reference/normal route)
- `n_observations`, `mean_cumulative_travel_time_min`
- `is_reference_variant`, `is_protest_variant` (derived booleans)

Lines 17, 19, 22 are the "protest routes" (subject to detours during blockades).
Line 15 is the traffic-only control (shares road segments with protest routes
but has no detour variant — it just slows down when traffic increases).

**Work in `rony/variant_analysis.ipynb`. Run all cells end-to-end before finishing.**

---

## PART A — Investigations (print findings; do NOT make the final decision)

### A1 — Friday late-night rows (Figure 3 issue)

Jerusalem has no public transit on Friday nights (Shabbat begins Friday evening).
Yet the coverage heatmap shows records for `day_of_week=6` (Friday) at hours 0–4
(i.e., `hour_display` in {1, 2} after the 25→1 / 26→2 replacement, or original
`scheduled_departure_time` in {25, 26}).

Task:
1. Filter the combined dataframe to `day_of_week == 6` AND
   `scheduled_departure_time >= 25` (i.e., hours mapped to 01:00–02:00).
2. Print: how many rows, which route_names, which months, and the
   n_observations distribution for those rows.
3. Print the two options clearly:
   - **Option A — Reassign**: move these rows to Thursday night
     (set `day_of_week = 5`, `hour_display` stays as 1 or 2).
   - **Option B — Drop**: remove these rows from the dataset entirely.
4. State the tradeoff for each option and stop. Do not implement either option.

---

### A2 — protest_frequency_by_hour audit (Figure 6 issue)

The current figure shows very different hour-coverage patterns between Lines 17
and 19, which may be an artifact rather than a real difference.

Task:
1. For each protest route (17, 19, 22), print:
   - How many distinct `route_variant_id` values exist in the raw data
     (before the `is_protest_variant` filter).
   - Which of those variant IDs are classified as protest variants and why
     (based on the `variant_summary_{route}.csv` `n_missing` criterion).
   - For each protest variant ID, how many rows it has and which hours it covers.
2. For each route, check whether the hours that appear "missing" in the
   protest_frequency_by_hour figure correspond to hours where:
   - There are protest-variant rows but all have `n_observations < 8`, OR
   - There are simply no protest-variant rows at all.
3. Print a clear conclusion: are the inter-route differences in the figure
   explained by low observation counts, by different variant IDs being included,
   or by something else?
4. Do not regenerate the figure yet.

---

### A3 — Missing months for Line 17

Task:
1. For each of the four routes, print a table of which months (1–12) appear
   in `df_cleaned_{route}.csv` and how many rows each month has.
2. Identify which months are absent for Line 17 but present for Lines 19 and 22.
3. Check whether those months exist in the raw source files (look in `govData/`)
   or are truly absent from the data entirely.
4. Print a one-paragraph summary of what you found.

---

## PART B — Figure Changes

### B1 — Figure 1: blockade_event_calendar.png  (MODIFY)

Current title: "Blockade Events — Specific (Month × Day × Hour) Slots on Detour Route"

Changes:
1. **Title**: Change to:
   "Blockade Schedule: When Did Detour Routes Operate?"
2. **Caption**: Add `fig.text(0.5, -0.04, caption, ...)` below the subplots
   with the text:
   "Each marker is a (day-of-week, month, hour) slot where over 50% of recorded
   trips used the detour route. X-axis = month, Y-axis = hour of day,
   marker shape and color = day of week."
   Use `ha='center'`, `fontsize=10`, `style='italic'`.
3. **Multi-day marker**: For each subplot (route), after plotting all the dots,
   compute for every (month, hour_display) coordinate the count of distinct
   days-of-week that have a blockade event (protest_share >= 0.5).
   For coordinates where this count > 3, overlay a large semi-transparent grey
   circle (`marker='o'`, `s=300`, `color='grey'`, `alpha=0.25`, `zorder=0`)
   centered on that coordinate. Do not label these circles or add them to the
   legend — they are purely a background visual cue.

---

### B2 — Figure 2: count_common_boxplot.png  (REPLACE)

Drop the boxplot figure entirely. Create a new figure saved as
`figures/hourly_trip_frequency.png`.

New figure — 3 subplots side by side:
- **Subplot 1 — Weekdays (Sun–Thu)**: `day_of_week` in {1,2,3,4,5}
- **Subplot 2 — Friday**: `day_of_week == 6`
- **Subplot 3 — Saturday**: `day_of_week == 7`

For each subplot, draw one line per route (15, 17, 19, 22) showing:
- X = `hour_display`
- Y = count of distinct (route_name, month, day_of_week, hour_display)
  groups that have at least one row with `n_observations >= 8`

Use `ROUTE_COLORS` for line colors. Add a legend. Label axes:
- X: "Hour of day"
- Y: "Active hour-slots (n_obs ≥ 8)"

Overall title: "Hourly Trip Frequency by Day Type"

---

### B3 — Figure 3: heatmap_coverage.png  (DO NOT TOUCH)

Do not regenerate or modify this figure.
The investigation in A1 is the action item for this figure.

---

### B4 — Figure 4: line15_at_blockade_events.png  (REBUILD)

Drop the existing figure and its generating cells completely.
Create a new figure saved as `figures/line15_segment_impact.png`.

**Step 1 — Find the relevant stops for Line 15.**

Load `govData/stations.csv`. Print all stop rows whose name contains
any of: "בן צבי", "בצלאל", "טשרניחובסקי", "פיכמן".
Then cross-reference with `df_cleaned_15.csv` to find which of those stop codes
actually appear in Line 15's data and what their `stop_sequence` values are.
Print the result. Identify:
- `seq_start` = stop_sequence of the "שדרות בן צבי / בצלאל" stop
- `seq_end`   = stop_sequence of the "טשרניחובסקי / פיכמן" stop

If the stop name matching is ambiguous, print all candidates and pick the
stop_sequence pair that gives the shortest unambiguous segment.

**Step 2 — Compute segment travel time for Line 15.**

For the reference variant of Line 15 (`route_variant_id == 0`,
`n_observations >= 8`), compute the segment travel time as:
  `tt_seg = mean_cumulative_travel_time_min at seq_end
           - mean_cumulative_travel_time_min at seq_start`

Group to one value per (month, day_of_week, hour_display):
use the mean of tt_seg across all stop-sequence rows in that group.

**Step 3 — Cluster blockade events.**

From `high_events` (protest_share >= 0.5, protest routes 17/19/22), extract
all unique (day_of_week, hour_display) pairs. Assign each to a cluster using
this scheme:
- Morning weekday:   day_of_week in {1–5}, hour_display in 5–9
- Midday weekday:    day_of_week in {1–5}, hour_display in 10–14
- Afternoon weekday: day_of_week in {1–5}, hour_display in 15–18
- Evening weekday:   day_of_week in {1–5}, hour_display in 19–24
- Saturday:          day_of_week == 7  (any hour)
- Friday:            day_of_week == 6  (any hour)

Print how many blockade events fall into each cluster.
Drop clusters with fewer than 3 events.

**Step 4 — Compute per-cluster baseline and delta.**

For each cluster:
1. Identify the set of months that had at least one blockade event for that
   cluster's (day_of_week, hour_display) combinations → call these `blockade_months`.
2. Baseline = mean segment TT for Line 15 on the same (day_of_week, hour_display)
   combinations, restricted to months NOT in `blockade_months`.
3. Delta = mean segment TT during `blockade_months` minus the baseline.
4. Also compute the standard deviation of the delta across individual
   (month, day_of_week, hour_display) observations for error bars.

**Step 5 — Plot.**

A single bar chart (or grouped dot plot):
- X = cluster label (e.g., "Morning Wkday", "Sat", etc.)
- Y = delta in minutes (positive = longer during blockade months)
- Add error bars (±1 std)
- Add a horizontal red dashed line at y=0
- Annotate each bar with the number of blockade events in that cluster (n=…)

Title: "Line 15 Segment Slowdown During Blockade Months"
Subtitle: "Segment: Ben Tzvi/Betzalel → Tchernichovsky/Fichman"
Y-axis label: "Extra travel time vs. baseline (minutes)"

---

### B5 — Figure 5: monthly_blockade_vs_control.png  (DELETE)

Delete `figures/monthly_blockade_vs_control.png`.
Remove the generating cell from the notebook.

---

### B6 — Figure 6: protest_frequency_by_hour.png  (HOLD)

Do not regenerate. The A2 investigation must be completed first.
After printing the A2 findings, add a markdown cell in the notebook stating
what the investigation found and whether the figure needs to be redrawn.

---

### B7 — Figure 7: route15_control_analysis.png  (MODIFY — top panel only)

The two-panel figure already exists and is structurally correct.
One change to the **top panel** only (extra minutes on detour vs. reference):

After drawing the lines, identify hours where the Line 15 baseline is
**unreliable** — defined as: the (max - min) of Line 15 total travel time
across all months and days at that hour exceeds 30 minutes.

Compute this from `tt_all` where `route_name == 15` and `is_reference == True`,
grouping by `hour_display` and taking `max - min` of `total_travel_time`.

At each unreliable hour, add a vertical grey shaded band:
`ax_top.axvspan(hour - 0.4, hour + 0.4, color='grey', alpha=0.15, zorder=0)`

Add a legend entry for the shaded band: "High baseline variance (Line 15 range > 30 min)".

---

### B8 — Figure 8: travel_time_by_hour.png  (DELETE)

Delete `figures/travel_time_by_hour.png`.
Remove the generating cell from the notebook.

---

### B9 — Figure 9: travel_time_comparison.png  (DELETE)

Delete `figures/travel_time_comparison.png`.
Remove the generating cell from the notebook.

---

### B10 — Figure 10: variant_frequency_heatmap.png  (MODIFY — shared scale)

The current code sets `vmax` independently per subplot, making the color
encoding incomparable across lines.

Fix: before the plotting loop, compute:
```python
global_vmax = max(
    freq_df[freq_df['route_name'] == r]['protest_fraction'].max()
    for r in PROTEST_ROUTES
)
global_vmax = max(global_vmax, 0.01)
```
Then pass `vmin=0, vmax=global_vmax` to every `sns.heatmap(...)` call in the loop.

---

## PART C — Final checklist

At the end of the notebook, print a summary cell listing:
- Which figures were regenerated (with filename)
- Which figures were deleted
- Which investigations are complete and summarized
- Which decisions are pending (i.e., A1 Option A vs B, and A2 figure redesign)
