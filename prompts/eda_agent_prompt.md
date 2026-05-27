# EDA Agent — Bus Transit Data

You are a data science assistant working on a final project for an Introduction to Data Science course.
Read CLAUDE.md first for full project context, data schema, and known issues before doing anything.

Your job is to produce a single well-structured Jupyter notebook: `rony/eda_exploration.ipynb`.
Write each section as you complete it. Use markdown cells for section headers and findings.
All plots must be saved as PNG files inside `rony/figures/` in addition to being shown inline.

---

## Step 0 — Setup

Install any missing packages with pip (use --quiet --break-system-packages).
Import: pandas, numpy, matplotlib, seaborn, warnings.
Set seaborn style to "whitegrid". Suppress warnings.

---

## Step 1 — Load and Deduplicate

1. Load `govData/ride_data_merged.csv`.
2. Report the raw shape.
3. Identify and count duplicate rows on: `(route_id, month, DayOfWeek, HourSourceTime, StopSequence_Rishui)`.
4. Keep the row with the **higher** `count_common` for each duplicate group (use sort + drop_duplicates).
5. Report the cleaned shape and how many rows were dropped.
6. Filter to the 4 main routes: `[5499, 10802, 37936, 10398]`. Report how many rows remain per route.
7. Add a boolean column `low_confidence` = True where `count_common < 8`.
8. Add a column `hour_display`: convert HourSourceTime 25→1, 26→2, all others stay as-is.
9. Add a column `day_label`: map DayOfWeek 1→"Sun", 2→"Mon", 3→"Tue", 4→"Wed", 5→"Thu", 6→"Fri", 7→"Sat".

Write a markdown cell summarising the key findings from this step.

---

## Step 2 — Coverage Analysis

For each route, excluding `low_confidence` rows:

1. For each (route, DayOfWeek), find the set of active hours (hours that have at least one row).
2. Define the route's expected range on that day as [min_hour, max_hour].
3. Identify coverage gaps: integers in that range with no data.
4. Build a summary DataFrame with columns:
   `route_id | day_label | active_hours_count | hour_range | gap_hours | gap_count`
5. Print this table.

Then produce **Plot 1**: a heatmap grid (one subplot per route, 2×2) showing number of records per (day × hour). X-axis = hour_display, Y-axis = day_label ordered Sun→Sat. Use a sequential colormap. Title each subplot with the route_id. Save as `rony/figures/heatmap_coverage.png`.

Write a markdown cell noting which routes have the most gaps and on which days.

---

## Step 3 — count_common Distribution and Low-Confidence Check

1. For each route, show a boxplot of `count_common` by `day_label` (include all rows, mark low_confidence rows in a different color if possible).
2. Print: per route, what % of (route × day × hour) combinations are below the count_common=8 threshold.
3. Check whether `count_common` is consistent across stops within the same (route, month, DayOfWeek, HourSourceTime) group — i.e. does it vary along the route?
   - Compute per group: min and max count_common across stops.
   - Report how many groups have min ≠ max, and show the top 5 most variable groups as a table.
   - Write a markdown interpretation: is this a data quality issue or evidence of partial routes?

Save boxplot as `rony/figures/count_common_boxplot.png`.

---

## Step 4 — Travel Time Anomaly Detection

Use only non-low-confidence rows. For each route, work with the **last stop** per (route, month, DayOfWeek, HourSourceTime) group — this represents total journey time.

1. Compute per-route, per-DayOfWeek: mean and std of total travel time across all hours.
2. Compute a z-score for each (route, DayOfWeek, HourSourceTime): z = (travel_time - mean) / std.
3. Flag rows where |z| > 2 as anomalies.
4. Print a table of all anomalies: route_id, day_label, hour_display, total_travel_time, z_score. Sort by |z_score| descending.
5. Identify stop-level anomaly stops: where `timeCumSum_std / timeCumSum_mean > 0.3`. Report per route: which stop numbers have the highest relative variance, and what are the top 3 "bottleneck" stops per route.

Produce **Plot 2**: for each route, a line plot of median total travel time (y-axis) by hour_display (x-axis), with separate lines per day_label. Highlight anomaly points with a red marker. Save as `rony/figures/travel_time_by_hour.png`.

Write a markdown cell: which hours show the clearest congestion signal? Which routes are most variable?

---

## Step 5 — Summary Table

Produce a final summary DataFrame combining the above results:

| route_id | day_label | active_hours | hour_range | gap_count | median_count_common | anomaly_hours | low_conf_pct |
|---|---|---|---|---|---|---|---|

- `anomaly_hours`: comma-separated list of hours flagged in Step 4.
- `low_conf_pct`: % of rows for this route+day with count_common < 8.

Print the full table and save it as `rony/eda_summary_table.csv`.

---

## Step 6 — Conclusions

Write a markdown cell (no code needed) that answers:
1. Which route has the best data quality (highest count_common, fewest gaps)?
2. Which route/day/hour combinations should be treated with caution in any downstream model?
3. What are the 2–3 most interesting anomalies found?
4. What would you recommend as the minimum count_common threshold for modeling, and why?

---

## Final Check

Before finishing:
- Confirm all 6 figures/files exist: `eda_exploration.ipynb`, `eda_summary_table.csv`, `figures/heatmap_coverage.png`, `figures/count_common_boxplot.png`, `figures/travel_time_by_hour.png`.
- Run all cells from top to bottom and confirm no errors.
- If any cell errors, fix it before declaring done.
