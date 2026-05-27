# Data Science Final Project — Bus Transit EDA

## Project Goal
Exploratory data analysis of Israeli public bus transit data, as part of an Introduction to Data Science course final project.
The primary goal of this phase is to understand data quality and identify anomalies before modeling.

## Data Files

### Main analysis file
`govData/ride_data_merged.csv` — ~225K rows, aggregated by route × month × day × hour × stop.

| Column | Description |
|---|---|
| `_id` | Row ID |
| `month` | Month (1–12) |
| `route_id` | Route identifier |
| `DayOfWeek` | 1=Sunday … 6=Friday, 7=Saturday |
| `HourSourceTime` | Departure hour (5–26; hours 25–26 = 01:00–02:00 next day) |
| `StopSequence_Rishui` | Stop number along route (1 = first stop) |
| `StopCode` | Stop identifier |
| `count_common` | Number of actual rides that contributed to this aggregate row |
| `timeCumSum_mean` | Mean cumulative travel time (minutes) from start to this stop |
| `timeCumSum_std` | Std dev of cumulative travel time |
| `distCumSum_mean` | Mean cumulative distance (meters) from start to this stop |
| `distCumSum_std` | Std dev of cumulative distance |

### Supporting files
- `govData/stations.csv` — stop metadata (name, location)
- `output_sample/rides.csv` — raw SIRI/GTFS ride records (last 7 days sample)
- `output_sample/ride_stops.csv` — raw stop-level records

## Known Data Issues
1. **Duplicate rows**: ~77,869 rows are duplicated on (route_id, month, DayOfWeek, HourSourceTime, StopSequence_Rishui). Must deduplicate before any analysis.
2. **Noise routes**: 99 route_ids exist but only 4 are meaningful. Filter to: `[5499, 10802, 37936, 10398]`.
3. **Direction**: 3 routes are single-direction; route 10398 is circular (no direction concept).
4. **Late-night hours**: HourSourceTime 25 and 26 represent 01:00 and 02:00 of the following day. For display, convert to 1 and 2.
5. **Saturday sparsity**: DayOfWeek=7 has ~8K rows vs ~40K on weekdays — low statistical power.
6. **count_common floor**: Minimum is 4, median is 12. Rows with count_common < 8 (bottom 25th percentile) should be flagged as low-confidence.

## Key Definitions
- **Active hour**: a (route, day, hour) combination that has at least one row with count_common ≥ 8 after deduplication.
- **Coverage gap**: an hour that falls within a route's active range on a given day but has no rows at all.
- **Travel time anomaly**: a (route, day, hour) where the total travel time (timeCumSum_mean at max StopSequence) deviates more than 2 standard deviations from that route's mean for that day-of-week.
- **Stop-level anomaly**: a stop within a route where timeCumSum_std / timeCumSum_mean > 0.3 (high relative variance).
