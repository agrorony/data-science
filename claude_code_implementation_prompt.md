# Implementation prompt for Claude Code — apply the chosen visual language

Use this after picking a direction from Claude Design. Fill in the `[[...]]` placeholders with the specifics of the chosen direction (fonts, background color, gridline style, etc.) before running.

---

I've finalized the visual direction for our data science final project (chosen: "Minimal Academic", 1a). Apply it consistently — but **only to the figures that actually go in the final report**, not the whole pipeline.

**Scope — restyle only these 8 figures, nothing else.** `FINAL_REPORT_DRAFT.md` is the single source of truth for what's in scope: it's the current, trimmed draft after our advanced-stage cleanup (phases 07/10/11 were archived to `archive/docs/`, not deleted, and are out of scope; several `docs/` numbers were also corrected on 26 Jul — don't touch anything under `archive/`). The 8 figures it references, and the exact script that generates each one:

| Figure | Path referenced in the draft | Generating script |
|---|---|---|
| 1 | `docs/03_variants/line_19/variants_raw.png` | `pipeline/plot_variants_revised.py` |
| 2 | `docs/04_baselines/travel_time_all_lines.png` | `pipeline/plot_travel_time_all_lines.py` |
| 3 | `docs/04_baselines/baseline_travel_time_by_hour.png` | `pipeline/plot_travel_time_all_lines.py` (same script, second figure) |
| 4 | `docs/08_control_lines_15_14/control_lines_delta.png` | `pipeline/plot_control_comparison.py` |
| 5 | `docs/06_blockade_frequency/blockade_all_lines.png` | `pipeline/plot_blockade_frequency.py` |
| 6 | `docs/13_full_year_calendar/confirmed_hours_calendar.png` | `pipeline/analyze_full_year_calendar.py` |
| 7 | `docs/05_skip_comparison/delta_all_lines.png` | `pipeline/plot_baseline_vs_blocked_delta.py` |
| 8 | `docs/09_lines_9_97/line_97_blockade_delta.png` | `pipeline/plot_line9_97_blockade_impact.py` |

Watch out for near-duplicate scripts that are **not** in scope: `pipeline/plot_skip_comparison.py` produces `rony/figures/skip_comparison_<line>_<group>.png` (per-line detail, superseded by figure 7's cross-line summary — do not touch it), and the ~120 other PNGs under `rony/figures/` and the archived `docs/07`, `docs/10`, `docs/11` folders are earlier-stage/exploratory work, not final-report figures — leave them as-is. Before touching any script, confirm its output path matches one of the 8 rows above; if a script produces both an in-scope and an out-of-scope figure (none currently do, but check), restyle only the in-scope one.

If a figure gets swapped later (the outline notes a couple of "pick 2 of 3" choices), re-check `FINAL_REPORT_DRAFT.md`/`FINAL_REPORT_OUTLINE.md` for the current figure list rather than assuming this table is still accurate.

**Do not change:** the fixed per-line color mapping already in `pipeline/config.py` (`LINE_COLORS`): 17=#b30000, 19=#e34a33, 22=#fc8d59 (shared corridor), 9=#54278f, 97=#9e9ac8 (non-shared corridor), 14=#045a8d, 15=#74a9cf (control lines). Every chart type (bars, lines, heatmap, map legend) must use these colors in this fixed left-to-right/top-to-bottom order: 17, 19, 22, 9, 97, 14, 15.

**What to do:**

1. Create a shared `pipeline/style.py` that is imported and applied (call it once, at the top of `run_pipeline.py` and at the top of every standalone `plot_*.py`) before any figure is built:

```python
import matplotlib.pyplot as plt

LINE_COLORS = {
    17: "#b30000", 19: "#e34a33", 22: "#fc8d59",   # shared corridor
    9:  "#54278f", 97: "#9e9ac8",                    # non-shared corridor
    14: "#045a8d", 15: "#74a9cf",                    # control lines
}

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Source Sans 3", "Arial", "DejaVu Sans"],
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.titleweight": "semibold",
    "axes.labelsize": 10,
    "axes.labelcolor": "#4a4a4a",
    "axes.edgecolor": "#e2e2e2",
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "axes.facecolor": "white",
    "figure.facecolor": "white",
    "grid.color": "#eeeeee",
    "grid.linewidth": 0.8,
    "xtick.color": "#8a8a8a",
    "ytick.color": "#8a8a8a",
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.frameon": False,
    "legend.fontsize": 9,
    "legend.loc": "best",
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})
```

   `LINE_COLORS` here should just re-export/import the existing dict already in `pipeline/config.py` — don't duplicate it, keep `config.py` as the single source of truth and have `style.py` only own the rcParams block.

2. Refactor only the 6 scripts listed in the scope table above (`plot_variants_revised.py`, `plot_travel_time_all_lines.py`, `plot_control_comparison.py`, `plot_blockade_frequency.py`, `analyze_full_year_calendar.py`, `plot_baseline_vs_blocked_delta.py`, `plot_line9_97_blockade_impact.py`) to import `pipeline.style` and drop their current hardcoded ad-hoc colors (e.g. wherever a script hardcodes a one-off hex for a non-line-specific series — replace with a neutral color from the style, e.g. the accent `#045a8d` or a gray, and reserve `LINE_COLORS` strictly for series that represent a specific bus line). Leave every other `plot_*.py` / `stage*.py` script untouched. Enforce the fixed line order (17, 19, 22, 9, 97, 14, 15) wherever multiple lines appear in one in-scope chart, including legends.

3. Apply these chart conventions everywhere, not just rcParams:
   - No vertical gridlines, no full border box (top/right spines already hidden by rcParams — don't override per-script).
   - Legend: no frame, placed to minimize overlap with data.
   - Matplotlib chart title itself stays in English and terse (the Hebrew report caption carries the actual finding — see point 5).
   - Any Hebrew stop/street name inside a chart: set explicitly in "Noto Sans Hebrew" (fall back to whatever Hebrew-capable font is installed in the sandbox — check and flag if Noto Sans Hebrew isn't available), rotated 90° on the x-axis when labels are dense (this is the existing `rtl()` pattern in `stage10_route_deviation_heatmaps.py` — keep that helper, just fix the font).

4. Re-run only the 6 in-scope scripts individually (not the full `pipeline/run_pipeline.py` orchestrator — that would also touch archived/superseded stages and every other figure) so the 8 PNGs listed in the scope table regenerate with the new style. Confirm each output file's modification time actually updated and its path still matches the scope table exactly.

5. Figure titles/captions (written in Hebrew in the report body, not in the chart image) must follow this fixed structure — flag any existing caption in the draft that only describes axes instead of stating a finding, e.g. replace something like "איור 3. עיכוב חציוני לפי קו" with "איור 3. בקווים החולקים מסלול משותף העיכוב החציוני גבוה פי 2–3 מקווי הביקורת":
   - **Figure [n]. [sentence stating the main finding]**
   - short technical description: what's shown, breakdown, time range
   - italic "How to read: [units/markers/colors note if needed]"

6. **Verify before finishing:** confirm exactly 8 PNGs changed (`git status` / `git diff --stat` on `docs/`, scoped to the 8 paths above — nothing under `archive/`, `rony/figures/`, or any other `docs/*` subfolder should show as modified); spot-check 3–4 of the regenerated figures to confirm rcParams actually applied (white background, no vertical gridlines, no top/right spines, unframed legend) and Hebrew labels still render correctly and in the right font; confirm line order/colors are identical and consistently ordered across every regenerated figure.

Flag anything ambiguous rather than guessing (e.g. if a script has a chart element — like a colorbar or annotation style — the spec doesn't explicitly cover, or if a figure path in the draft doesn't match what a script actually produces).
