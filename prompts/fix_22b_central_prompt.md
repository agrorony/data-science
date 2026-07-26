# Prompt for Claude Code — centralize the 22B decision (stop the "blocked 22B" regressions)

Copy everything below into Claude Code, run from the repo root.

---

## The bug

The project decision (see `docs/06_blockade_frequency/disagreement_deep_dive.md`): **line 22 direction_B has no corridor blockades** — its non-baseline variants skip 0 blockade-footprint stops and are not blockade responses; 22B must never be counted as blocked anywhere.

This decision was implemented inconsistently. Line 14's analogous decision lives **centrally** in `pipeline/variant_merges.py` (`_classify` forces line 14 non-reference variants to `"noise"`, so every consumer of `variant_type_v2` inherits it). The 22B decision was instead patched **per script** (special cases in `pipeline/plot_blockade_frequency.py`, `pipeline/compute_stats_backing.py`, `pipeline/analyze_deep_dive_windows.py`, `pipeline/plot_missing_fraction_comparison.py`). Result: every new analysis that reads `variant_type_v2` reintroduces 22B as blocked — this just happened again in `docs/11_deep_dive_candidate_windows/`.

## The fix

1. **Centralize:** in `pipeline/variant_merges.py`'s `_classify`, force line 22 + direction_B non-reference variants to a non-blocked label — use `"non_corridor"` (not `"noise"`; the reason differs from line 14's and the label should say so). Add a comment mirroring the line-14 one, citing the deep-dive report. Line 22 direction_A is untouched.
2. **Remove the per-script special cases** in the four files above (and any others `grep` finds for 22B/direction_B handling) — they are now redundant; leaving them invites divergence. Where a script's special case did something *other* than reclassification (e.g. the Saturday summary labeling "22 (dir A)"), keep the labeling but make it read from the central classification.
3. **Add a regression guard:** a small assertion helper in `variant_merges.py` (e.g. `assert_no_false_blockades(effective_df)`) verifying that no line-14 and no 22B slot is ever `variant_type_v2 == "blocked"`; call it in `build_effective_df_cleaned` so any future analysis fails loudly instead of silently regressing.
4. **Regenerate every downstream output** that reads `variant_type_v2`: phases 05, 06 (all heatmaps + Saturday summary + timeline), 08 (blockade windows definition), 09, and the newer 10/11/12 folders (candidate windows, deep dive, statistics). Where phase 11's conclusions were based on 22B "blockades", re-run that analysis and rewrite its README accordingly.
5. **Document:** one paragraph in `docs/README.md` (or the cleaning decision log) stating the central rule: line 14 → `noise`, 22B → `non_corridor`, with links to the two investigation reports — so the decision has exactly one home.

## Frequency-figure audit (mandatory, not optional)

After the central fix, **audit every figure in `docs/` that shows blockade/variant frequencies and could contain 22B data**, one by one — do not rely on the regeneration list alone. For each figure: determine how line 22's value was computed (pooled A+B? A only? B included as blocked?), fix if wrong, regenerate.

- **Phase 06 is the prime suspect — check it first.** The per-line month×day heatmap for line 22 (`line_22/blockade_frequency_22.png`) and the all-lines subplot grid (`blockade_all_lines.png`) almost certainly pool both directions, meaning their percentages include 22B slots (previously as blocked — wrong; after the fix as never-blocked — which *dilutes* direction A's share, also wrong). Per the round-4 decision, line 22's blockade shares must be computed from **direction_A only**.
- Also audit: `blockade_saturday_summary.png`, the phase 06 disagreement figures (`disagreement_windows.png/csv`), the 22B timeline figure (its top panel legitimately *shows* 22B as a row — that is correct and stays), phase 08's blockade-window definition (windows must derive from 17/19/22A only), phase 09's blockade-window comparisons, and everything in `docs/10_candidate_windows/`, `docs/11_deep_dive_candidate_windows/`, `docs/12_statistics/`.
- Produce an audit table in the final summary: figure | how line 22 was computed before | verdict (correct / fixed) | action taken.

**Marking rule:** every figure whose line-22 values are computed excluding direction B must say so **on the figure itself** — label the row/bar/curve "22 (dir A)" where applicable, and add a fixed footnote line to the caption: *"Line 22 computed from direction A only; direction B excluded (non-corridor variants — see docs/06_blockade_frequency/disagreement_deep_dive.md)."* Apply the same wording everywhere for consistency. Figures that legitimately display 22B as its own row/curve (e.g. the Saturday timeline) do not get the footnote — they get their existing per-figure explanation.

## Verification

- After regeneration, run a global check: no figure, CSV, or README under `docs/` reports a nonzero blocked share for line 14 or for 22B, and no line-22 frequency anywhere is diluted by direction-B slots. `grep` the regenerated CSVs to prove it and print the check results.
- Visually open each audited figure and confirm the "22 (dir A)" label and footnote are present where required.
- Confirm the four de-special-cased scripts produce byte-identical (or explained-diff) outputs vs before, except where 22B blockades were wrongly present.
- List every file changed and any conclusion in phases 10–12 that changed as a result.
