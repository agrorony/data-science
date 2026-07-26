# Implementation prompt for Claude Code — apply the chosen visual language

Use this after picking a direction from Claude Design. Fill in the `[[...]]` placeholders with the specifics of the chosen direction (fonts, background color, gridline style, etc.) before running.

---

I've settled on a visual direction for our data science final project's report and figures. Apply it consistently across the codebase — don't just restyle one chart.

**Chosen style spec:**
- Font family (body/report): [[e.g. "Calibri" / "Georgia"]]
- Font family (chart text — must render Hebrew RTL labels correctly): [[e.g. "Arial" / "DejaVu Sans"]]
- Chart background: [[e.g. white / light gray #f7f7f7]]
- Gridlines: [[e.g. light horizontal only, alpha 0.25]]
- Legend style/placement: [[e.g. top-right, no border, small font]]
- Report accent color / heading color: [[hex]]
- Figure caption convention: [[e.g. bold "Figure N —" prefix + one-sentence takeaway]]

**Do not change:** the fixed per-line color mapping already in `pipeline/config.py` (`LINE_COLORS`): 17=#b30000, 19=#e34a33, 22=#fc8d59, 9=#54278f, 97=#9e9ac8, 14=#045a8d, 15=#74a9cf.

**What to do:**

1. Add a single shared style module (e.g. `pipeline/style.py`) that defines matplotlib rcParams (fonts, background, gridlines, legend) per the spec above, plus any shared helper for figure titles/footnotes ("how to read" text). This becomes the one place that controls chart look.

2. Refactor every `pipeline/plot_*.py` script (there are ~10: `plot_baselines.py`, `plot_travel_time_all_lines.py`, `plot_blockade_frequency.py`, `plot_skip_comparison.py`, `plot_control_comparison.py`, `plot_line9_97_blockade_impact.py`, `stage10_route_deviation_heatmaps.py`, etc.) to import and apply this shared style instead of their current hardcoded ad-hoc colors (e.g. `plot_baselines.py` currently hardcodes `#1D9E75`, `#4C72B0`, `#DD8452` for non-line-specific series — replace with the shared style's palette, keeping `LINE_COLORS` only for series that represent a specific bus line).

3. Re-run the figure-generating stages (`python -m pipeline.run_pipeline` or the individual `plot_*` scripts — check `pipeline/run_pipeline.py` for the right invocation) so every PNG under `rony/figures/` and `docs/*/` regenerates with the new style.

4. Update the Word report template/draft (use the `docx` skill) to match: heading styles and accent color per the spec, while keeping the course's hard requirements from `CLAUDE.md` — font ≥11pt, line spacing ≥1.15, margins ≥1 inch, every figure numbered and referenced as "(Figure N)", no code snippets in the report.

5. **Verify before finishing:** spot-check 3–4 regenerated figures (one bar chart, one line chart, one heatmap, the route map) to confirm the new style actually applied and Hebrew labels still render correctly; confirm the pipeline runs end-to-end without errors; confirm the docx still meets the formatting rules above.

Flag anything ambiguous rather than guessing (e.g. if a script has a chart element the style spec doesn't cover).
