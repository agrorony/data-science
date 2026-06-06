# Data Science Final Project — Israeli Bus Transit EDA
## Course: 71253 — Introduction to Data Science

---

## Language
Always respond in English, regardless of the language used in the prompt.

---

## Course Requirements (from instructor PDF)

**Team:** 2 students. Working alone or in groups larger than 2 is not permitted.

**Deliverables & deadlines:**
| Due date | Task |
|---|---|
| 5 May | Progress report I (submitted) |
| 9 June | Progress report II |
| TBD | 10-minute presentation |
| 1 Aug | Final report (penalty: -2 pts/day late, max 7 days) |

**Progress report II** (due 9 June): concise description of the specific questions to address and the methods to use. Up to 2 pages including figures.

**Final report** (due 1 Aug): Word or PDF, max 10 pages including figures. Must include:
- Introduction to the data (with link to source)
- Exploratory analysis (should be a *significant* portion of the report)
- Specific questions addressed, methods used, and conclusions
- Ideas for follow-up studies

**Formatting rules for the final report:**
- Font size ≥ 11, line spacing ≥ 1.15, margins ≥ 1 inch
- Number all figures; reference them in text as "(Figure N)"
- Each figure must have a title stating its main message
- Variable names on graphs must be informative (not raw column names)
- Do NOT include code snippets in the report

**Important professor note:** The instructor recommends focusing on "big" questions (e.g. "When is the best time to take this bus line?") rather than narrow statistical ones (e.g. "what is the correlation between X and Y?"). The exploratory analysis before focusing on a specific question should be a significant part of both the project and the final report.

**Data source:** Israeli government open data — https://data.gov.il/dataset/

---

## Project Goal
Exploratory data analysis of Israeli public bus transit data. The primary goal of the current phase is to understand data quality and identify anomalies before modeling.

---

## Data Files

### Main analysis file
`govData/ride_data_merged.csv` — ~225K rows (before deduplication), aggregated by route × month × day-of-week × hour × stop.

Each row represents the **average travel behavior** across all rides that matched a specific (route, month, day-of-week, departure hour, stop) combination.

| Column | Description |
|---|---|
| `_id` | Row ID |
| `month` | Month (1–12) |
| `route_id` | Route identifier |
| `DayOfWeek` | 1=Sunday, 2=Mon, 3=Tue, 4=Wed, 5=Thu, 6=Friday, 7=Saturday |
| `HourSourceTime` | Departure hour (5–26; hours 25–26 = 01:00–02:00 next day) |
| `StopSequence_Rishui` | Stop number along route (1 = first stop) |
| `StopCode` | Stop identifier |
| `count_common` | Number of actual rides that contributed to this aggregate row |
| `timeCumSum_mean` | Mean cumulative travel time (minutes) from route start to this stop |
| `timeCumSum_std` | Std dev of cumulative travel time |
| `distCumSum_mean` | Mean cumulative distance (meters) from route start to this stop |
| `distCumSum_std` | Std dev of cumulative distance |

### Supporting files
- `govData/stations.csv` — stop metadata (name, location)
- `output_sample/rides.csv` — raw SIRI/GTFS ride records (last 7 days sample)
- `output_sample/ride_stops.csv` — raw stop-level records

---

## Known Data Issues
1. **Duplicate rows (~34% of data):** ~77,869 rows share the same (route_id, month, DayOfWeek, HourSourceTime, StopSequence_Rishui) but have different `count_common` values. This appears to result from overlapping data across the source files `ride_data1–4.csv`. **Must deduplicate before any analysis** — keep the row with the higher `count_common`.
2. **Noise routes:** 99 route_ids exist but only 4 are meaningful. Filter to: `[5499, 10802, 37936, 10398]`.
3. **Direction:** 3 of the 4 routes are single-direction; route 10398 is circular (no direction concept). There is no explicit direction column in the merged file.
4. **Late-night hours:** HourSourceTime 25 and 26 represent 01:00 and 02:00 of the following day. Convert to 1 and 2 for display.
5. **Saturday sparsity:** DayOfWeek=7 has ~8K rows vs ~40K on weekdays — low statistical power, treat with caution.
6. **count_common floor:** Minimum is 4, median is 12. Rows with count_common < 8 should be flagged as low-confidence.
7. **count_common consistency along stops:** After deduplication, only 3 out of 1,130 groups show any variation in count_common across stops within the same (route, month, day, hour). This is a minor issue, not a systematic one.

---

## Key Definitions
- **Active hour:** a (route, day, hour) combination that has at least one row with count_common ≥ 8 after deduplication.
- **Coverage gap:** an hour that falls within a route's active range on a given day but has no rows at all.
- **Travel time anomaly:** a (route, day, hour) where total travel time (timeCumSum_mean at max StopSequence) deviates more than 2 standard deviations from that route's mean for that day-of-week.
- **Stop-level anomaly / bottleneck:** a stop where timeCumSum_std / timeCumSum_mean > 0.3 (high relative variance — suggests congestion or irregularity at that stop).

---

## Work Done So Far

### Rony — `rony/data_exploration.ipynb`
Initial diagnostic notebook. Covers:
- Loaded `ride_data_merged.csv` and identified the ~77,869 duplicate rows (same route/month/day/hour/stop, different count_common).
- Confirmed that after deduplication, count_common is consistent across stops in the same group in almost all cases (only 3 exceptions out of 1,130 groups for route 5499).
- Analyzed how common duplicate rows are at the day level and at the day+hour+stop level.

### Avishagi — `avishagi/`
Three notebooks and a reusable Python module focused on route sequence analysis:

- **`change_colmn_name.ipynb`** — Renamed columns across all ride_data files to more readable names (e.g. `HourSourceTime` → `scheduled_departure_time`, `StopSequence_Rishui` → `stop_sequence`), added a `route_name` column, and saved as `renamed_*.csv` files in `govData/`.
- **`map_bus_routes.ipynb`** — Extracted the full stop sequence for each (route, month, day, hour) group to detect variant routes. Identified the most common stop sequence per route, filtered it out, and analyzed rare/deviant sequences (buses that skipped stops or took a different path). Visualized the distribution of route variants by stop count.
- **`bus_route_analysis_functions.ipynb` + `bus_route_analysis.py`** — Refactored the above analysis into reusable, documented functions (`load_and_clean_data`, `extract_route_sequences`, `filter_by_stop_count`, etc.) so the pipeline can be run on any of the ride_data files.

**Note:** Avishagi's notebooks use the renamed column names (`scheduled_departure_time`, `stop_sequence`, etc.). Rony's notebooks use the original column names. When combining work, map accordingly.
