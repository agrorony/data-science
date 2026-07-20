# Prompt for Claude Code — make all pipeline figures self-explanatory

Copy everything below into Claude Code, run from the repo root.

---

All figures produced by the pipeline (stages 7, 8, 9, 10 — saved under `rony/figures/`) are unreadable to someone who didn't write the code: missing legends/colorbars, unlabeled axes, unexplained terms, and at least one degenerate plot. Fix the **plotting code in `pipeline/`** (not the PNGs), then regenerate all figures.

Course context: these figures go into a final report where every figure must have a title stating its main message, and variable names on graphs must be informative (not raw column names). Assume the reader is a course grader who has never seen this codebase.

## Global requirements (apply to every figure)

1. **Every heatmap gets a colorbar** with a label stating exactly what the color encodes and its units/range (e.g. "Fraction of trips using a detour variant (0–1)", "Number of confident data rows").
2. **Every axis gets a human-readable label** — never raw column names. Hours 25/26 must display as 01:00/02:00.
3. **Every figure gets a caption/subtitle sentence** (use `fig.text` or a wrapped subtitle) explaining in plain language what the reader is looking at and how to read it, including definitions of project jargon the first time it appears in that figure: "detour cluster", "reference variant", "direction group", "confident row (count_common ≥ 8)", "blocked variant".
4. **Titles state the message, not the mechanics.** Bad: "line 19 / direction_A / cluster_1: detour fraction by month x day". Good: "Line 19 southbound: detours concentrate on Saturdays and in May".
5. Legends for any plot with more than one series/color category. Consistent color scheme across figures for the same concept.
6. Readable font sizes (tick labels ≥ 8pt after saving; rotate or thin dense stop-name labels).

## Known specific problems (verify and fix each)

- **`stage8_detour_clusters.py` → `detour_frequency_*.png`**: month×day heatmaps have no colorbar; unclear if color = fraction or count. Hour bar charts have no y-axis label ("number of detoured (month,day) blocks"? state it). Panels for clusters with a single occurrence render as one meaningless full-width bar (e.g. line 19 cluster_2: one bar spanning x=0.6–1.4) — for sparse clusters either annotate "only N occurrences" or skip the hour panel with a text note instead of plotting garbage. Also explain in the caption what a cluster is (a group of variants missing the same stops ≈ one closure location).
- **`stage7_eda_summary.py` → `heatmap_coverage.png`**: 13 subplots, no colorbar anywhere. Add a shared colorbar labeled with what's counted; state in the caption that dark purple = no data and that Saturday sparsity is expected. Consider a shared color scale across subplots so panels are comparable — if scales differ per panel, say so explicitly.
- **`stage9_control_comparison.py` → `control_comparison_19_vs_15.png`**: currently a single orange rectangle over a continuous 23.6–24.4 x-axis — this is a bug (bar chart with one data point on a continuous axis). Use a categorical x-axis of hours, show the delta per hour with a zero reference line, label y as "Change in control line's travel time during protest hours (minutes)", and annotate n (how many (month,day,hour) blocks are behind each bar). If there is only one qualifying block, print that in the figure instead of an empty-looking chart.
- **`stage10_route_deviation_heatmaps.py` → `route_deviation_heatmap_*.png`**: has a Present/Missing legend already, but explain "REFERENCE" and "n=" in the caption, make stop-name labels legible (larger font, maybe every other label), and state that rows are variants sorted by frequency.

## Process

1. Read each stage's plotting code before changing it; keep the computation logic untouched — change presentation only.
2. Regenerate all figures by running the relevant stages (stage 8, 7, 9, 10) via `pipeline/run_pipeline.py` or by invoking the stage modules directly. Do not hand-edit PNGs.
3. After regenerating, open each PNG and verify against the global requirements above; iterate until every figure passes.
4. List at the end any figure whose data (not presentation) looks wrong, so we can investigate separately.
