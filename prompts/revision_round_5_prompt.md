# Prompt for Claude Code — revision round 5: rebuild the Saturday-evening timeline

Copy everything below into Claude Code, run from the repo root.

---

Rework the top panel of `docs/06_blockade_frequency/line_22/saturday_timeline_and_cost_22B.png`. The current version colors each (line-direction × hour) cell by a **majority vote across all Saturdays in the data** — this hides how many Saturdays each cell is based on and how strong the pattern is, and the figure never states how it was built. Keep the bottom panel (22B's pass-through cost) unchanged. All global rules from previous prompts apply (English, palette, captions, no hours 25/26).

## 1. Replace binary cells with a share gradient

- Cell value = **% of Saturdays on which that line-direction ran a detour (blocked) variant at that hour**, computed from the effective variant set (`variant_type_v2`, post-merge/exclusion; line 14 rules and 22B handling per previous rounds).
- Color: house-style Reds colormap, 0–100% scale, labeled colorbar ("Share of Saturdays on a detour variant").
- **Annotate every cell with its evidence base**: the fraction as `k/n` (e.g. `8/11` = detoured on 8 of the 11 Saturdays with data for that slot). Use white text on dark cells, black on light, matching the house heatmap style.
- Rows stay 17A, 17B, 19A, 19B, 22A, 22B; columns are Saturday evening hours 19:00–24:00.

## 2. Distinguish "not operating" from "0% blocked"

- A slot with **no data at all** (the line never operated that Saturday hour) must be visually distinct from a slot that operated and was 0% blocked: render no-data cells with a **hatched gray pattern** (e.g. `///`) and include it in the legend as "No service / no data".
- If a cell has data for only some Saturdays, that's fine — the `k/n` annotation already conveys it; do not hatch partial cells.

## 3. State exactly how the figure is built, on the figure

- Subtitle (directly under the title, smaller font): one sentence with the exact cell definition, including the month range and Saturday count, e.g.: *"Each cell: share of the N Saturdays (months Jan–Dec 2025) with data for that slot on which the line ran a detour variant; k/n printed in each cell."* Fill N and the month range from the actual data.
- The bottom caption (`fig.text`) keeps its current content but drop any wording that described the old majority-vote scheme.
- Update the accompanying `docs/06_blockade_frequency/line_22/README.md` section for this figure to match the new construction.

## Verification

- Open the regenerated PNG and check: gradient + colorbar present, every cell annotated k/n, hatched no-data cells distinct from 0% cells, subtitle states the definition with real numbers, bottom panel untouched.
- Sanity checks against known results: 22B's row should read low shares through 19:00–23:00 while 17A/17B/19A/19B/22A read high shares early evening; totals should be consistent with the Saturday shares in `disagreement_deep_dive.md` (e.g. 22A ≈ 69%, 22B ≈ 32% before its exclusions context). If they contradict, stop and investigate before saving.
- Report the k/n table (rows × hours) as a small CSV next to the figure (`saturday_timeline_data.csv`) so the numbers are auditable.
