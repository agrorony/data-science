

We are preparing the final course presentation. Produce (a) English md reports documenting our work processes and decisions, and (b) presentation-quality figures. Work through the 9 phases below **in order** — later phases depend on earlier ones.

## Output structure

Create a `docs/` tree, one numbered folder per phase. Each folder contains a `README.md` (the report) and its figures. Where a phase produces many artifacts per line, add `line_<N>/` subfolders so navigation stays easy:

```
docs/
  01_data_cleaning/
  02_route_mapping/
  03_variants/line_<N>/
  04_baselines/line_<N>/
  05_skip_comparison/line_<N>/
  06_blockade_frequency/line_<N>/
  07_blockade_investigation/
  08_control_lines_15_14/
  09_lines_9_97/
```

## Global rules

- **All reports in English.** Stop names may stay in Hebrew.
- **Every figure must have a legend (or labeled colorbar) and a caption** (a `fig.text` sentence explaining what the reader sees and how to read it). No raw column names on axes. Hours 25/26 shown as 01:00/02:00.
- **House style for all frequency/blockade heatmaps** — match `rony/figures/variant_frequency_heatmap.png` exactly: Reds colormap, % annotation in every cell, labeled colorbar, month on x, day-of-week on y, clean bold panel titles. Use its typography as the baseline for all other figures too.
- **Direction labels:** keep `direction_A`/`direction_B` in figures and reports, but phase 02 produces a key table (direction → terminal stops); every report that mentions directions links to that key.
- Prefer reusing/extending `pipeline/` stage code; put new reusable plotting in `pipeline/`. Reports document decisions and findings — no code snippets in reports.

## Phases

### 01 — Data cleaning documentation
Report with two parts: (1) a narrative walkthrough following the data from the raw government download to `govData/df_cleaned.csv`, explaining each transformation and why; (2) a compact decision-log appendix table: every cleaning decision (structural ~3x export overlap, majority-vote block dedup replacing per-row max-count_common, count_common<8 low-confidence flag, hours 25/26, Saturday sparsity, StopCode disagreements...), each with rationale, alternatives considered, and before/after row counts. Sources: `pipeline/stage0_rebuild_merged.py`, `pipeline/STAGE0_DEDUP_NOTES.md`, `rebuild_ride_data_merged.py`, CLAUDE.md "Known Data Issues", git history from 2026-07-19.

### 02 — route_id ↔ commercial line mapping
Report mapping every `route_id` in the data to its commercial line number (9, 14, 15, 17, 19, 22, 97), its direction_group, and its terminal stop names (from `govData/jerusalem_stops.csv` / stations data). Include: the full key table (line | route_id(s) | direction_A/B | first stop → last stop, Hebrew names), how the direction split was determined (see `pipeline/stage3_investigate_route_ids.py` and `govData/route_id_decisions.json`), and any unresolved route_ids. This key is referenced by all later phases.

### 03 — Variants: before and after clustering (per line)
Two separate figure sets per (line, direction):
- **Before clustering:** reproduce the final visualization of `avishagi/bus_route_initial_filtering.ipynb` (`create_heatmap_data_v5` + `plot_routes_heatmap_v3`, as wrapped by `run_full_pipeline` at the end of the notebook) — the green/white stop-presence grid of raw variants, exactly that look. This is the pre-clustering state, as it existed before the 2026-07-19 pipeline work.
- **After clustering:** a separate figure showing the same variants grouped by their stage5 cluster (one color per cluster, or grid rows ordered/bracketed by cluster), so the effect of clustering is visible by flipping between the two figures.
Per-line README: variant counts before/after, what clustering merged, and any judgment calls.

### 04 — Baseline (most common) variant per line/direction
For each (line, direction): identify the most common variant (the baseline/reference). One multi-panel figure per direction: cumulative travel time AND cumulative distance along the stop sequence (two stacked panels or twin axes, stop names on x), plus a panel of trip frequency by day of week. One README per line summarizing both directions: baseline variant id, n, stop count, end-to-end time/distance, weekday pattern.

### 05 — Baseline vs stop-skipping variants
For each (line, direction), compare the baseline against variants that skip stops: name exactly which stops each variant skips (Hebrew names, via the phase 02 key), and quantify the travel-time difference vs the baseline — total and per affected segment. Answer explicitly in the README: does skipping save time (short-turn/express behavior) or does it coincide with *longer* rides (indicating a blockage/detour)? Per-line subfolders.

### 06 — Blockade/variant frequency characterization (house style)
For each line: one figure with a panel **both per each line 2 directions, and per line** — month×day heatmap of the share of hour-slots using a non-baseline (blocked) variant, in the exact house style of `rony/figures/variant_frequency_heatmap.png` (% annotated, Reds, colorbar). Per-line README noting the visible pattern (e.g. Saturdays, specific months) per direction.

### 07 — Investigation: explain the contradictions (SUBAGENT)
Spawn a research subagent for this phase. The current figure shows e.g. **July Saturdays: line 19 at 100% blocked-variant share vs line 22 at 67% in the same period** — lines that supposedly share the blocked segment. The subagent must find the actual cause and verify it against the data, not just hypothesize. Candidate explanations to test: data added in the 2026-07-19 rebuild changed the shares; different schedules (different hour-slots operated per line on Saturdays — a line running fewer hour-slots can hit 100% more easily); different variant-classification sensitivity per line; genuinely different routing. The subagent writes `docs/07_blockade_investigation/README.md`: the contradiction, hypotheses tested, evidence for each (with numbers), and the verified conclusion. Then regenerate the phase 06 figures if the investigation changes how shares should be computed, and add an explanation figure if it helps (house style).

### 08 — Indirect impact on control lines 15 & 14 (SUBAGENT)
Spawn an analysis subagent. Lines 15 and 14 are controls that should experience **no route change**. Using blockade windows established with certainty from phase 06/07 (e.g. ≥75% blocked share on lines 17/19/22), test the *indirect* effect of blockades on alternative corridors: compare the control line's total travel-time **distribution** during blockade windows vs matched normal windows (same day-of-week and hour) — boxplots/violin plus a significance note and n per group. **Method anchor:** replicate and extend how this was done before the 2026-07-19 work, on line 15 only — see `rony/variant_analysis.ipynb` and `rony/figures/route15_control_analysis.png` — now applied to both 15 and 14 with the distribution comparison. Subagent writes the README (method, windows used, findings); then produce the figures in the pre-2026-07-19 visual style of `route15_control_analysis.png` (matplotlib line/panel style, gray shading for flagged windows, proper legends).

### 09 — Lines 9 & 97 behavior during blockades (SUBAGENT)
Spawn an analysis subagent. Lines 9 and 97 also pass through Aza St. but do not share the exact blocked segment with 17/19/22. During the certain-blockade windows from phase 08: (a) do 9/97 themselves switch to non-baseline variants (route affected)? (b) does their travel time change even when they stay on their baseline variant? Two-part figure per line (variant-share comparison + travel-time comparison, same matched-window method as phase 08 for comparability) plus a README with the verified conclusion: route affected, time affected, both, or neither.

## Process requirements

- After phases 07–09, pause and present the subagents' findings summary before finalizing figures.
- Verify every figure visually (open the PNG) against the Global rules before moving on.
- Keep a top-level `docs/README.md` index linking all 9 folders with one-line summaries — this becomes the navigation page for building the presentation.
