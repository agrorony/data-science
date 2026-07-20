# Work Report — Sunday, July 19, 2026

Six commits were pushed yesterday (4 by Rony, 2 by Avishag). The big picture: the project moved from scattered per-person notebooks to a **unified, staged pipeline** (`pipeline/`) covering all 7 lines, and the merged dataset was rebuilt with a corrected dedup method.

## Timeline of commits

| Time | Author | Commit |
|---|---|---|
| 12:47 | Rony | `b5d0775` — dataset rebuild, validation script, new figures & variant notebook |
| 12:48 | Rony | `b940dd9` — backup of previous `ride_data_merged.csv` |
| 15:02 | Rony | `f95c71e` — new `pipeline/` package (stages 0–10) + generated outputs |
| 15:03 | Avishag | `ded0022` — updated notebooks, new GTFS pre-work notebook, cleanup of per-line CSVs |
| (+2 merges) | | |

## 1. Dataset rebuild (Rony, morning)

- `rebuild_ride_data_merged.py` rewritten (157 lines): rebuilds `govData/ride_data_merged.csv` from the raw government source with a **block-aware, majority-vote dedup**, replacing the old per-row "keep highest count_common" rule. The old rule was arbitrary for the ~2% of duplicate groups where copies disagree on StopCode.
- Two timestamped backups of the old merged file saved in `govData/`.
- New `validate_target_routes.py` + `govData/target_route_ids.json` — preflight check that all route_ids for the 7 target lines exist in the merged file.

## 2. New `pipeline/` package (Rony, afternoon)

An orchestrated pipeline (`pipeline/run_pipeline.py`) replacing the notebook-based workflow, generalized from 4 hardcoded routes to all 7 lines / 13 (line, direction) groups:

- **Stage 0** — rebuild merged CSV with majority-vote dedup (opt-in, slow).
- **Stage 1** — validate route_id coverage.
- **Stage 2** — rename columns + tag rows with line name (replaces `change_colmn_name.ipynb`); single `renamed_ride_data.csv` for all lines.
- **Stage 3** — *blocking checkpoint*: pairwise comparison of multi-route_id lines (stop overlap, direction, month coverage) → `route_id_decisions.json`. Pipeline halts here until every decision is confirmed.
- **Stage 4** — route-sequence variant detection per line/direction group (generalizes `bus_route_initial_filtering.ipynb`).
- **Stage 5** — *review checkpoint*: classify variants as regular / blocked / ambiguous with a per-line-scaled heuristic, and cluster blocked variants by which stops are missing (so lines with two closure locations, e.g. line 97, get two clusters).
- **Stage 6** — merge into 3 consolidated outputs: `df_cleaned.csv`, `variant_summary.csv`, `clean_filtered_data.csv` (all lines in each, route_id always kept).
- **Stage 7** — general EDA: coverage, count/confidence, travel-time anomalies (baseline uses regular variants only, so detours don't mask anomalies).
- **Stage 8** — detour-frequency figures per detour *cluster* (month×day heatmap + hour bar chart), not one blended number per line.
- **Stage 9** — control-vs-protest line comparison using only geographically verified pairs in `config.CONTROL_PAIRS`.
- **Stage 10** — route-deviation heatmaps (green/white stop-visit grids), reproducing Avishag's visualization.

Generated outputs committed: the 3 consolidated CSVs, `route_id_comparison_report.csv`, decision files, and ~25 figures under `rony/figures/` (detour frequency per line, deviation heatmaps per direction, control comparison 19 vs 15, travel-time-by-hour, etc.).

## 3. Rony's analysis artifacts (morning commit)

- `rony/variant_analysis.ipynb` (new, ~1,700 lines) — protest/blockade analysis: blockade event calendar, protest frequency by hour, line 15 as control, segment-impact figures.
- `rony/FIGURE_REVISION_PROMPT.md` — spec for revising figures.
- `report 2.docx` added at repo root.

## 4. Avishag's work

- **New** `avishagi/pre_work_project1.ipynb` (~880 lines) — GTFS ground-truth work: reads the official GTFS zip (routes/trips/stop_times/stops), inspects line definitions, and updates `govData/jerusalem_stops.csv` (+290 lines).
- Updated `bus_route_initial_filtering.ipynb`.
- **Cleanup**: deleted the old per-line files (`clean_filtered_data_17/19/22.csv`, `variant_summary_17/19/22.csv`) — superseded by the consolidated stage-6 outputs — and removed a temporary zip from git history.

## Current state / open items

- Pipeline halts after **stage 3** until `govData/route_id_decisions.json` is fully confirmed; stage 5's `variant_type_decisions.csv` also expects human review before stage 6 finalizes labels.
- Old notebooks (`change_colmn_name`, parts of `bus_route_initial_filtering`, `variant_analysis`) are now superseded by pipeline stages — future work should go through `pipeline/run_pipeline.py`.
- Two large CSV backups are committed to git; consider gitignoring them.
