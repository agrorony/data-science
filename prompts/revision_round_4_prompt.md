# Prompt for Claude Code — revision round 4 on the `docs/` presentation outputs

Copy everything below into Claude Code, run from the repo root.

---

Fourth correction round. All global rules from previous prompts still apply (English, legend + caption, house style, per-line palette from `pipeline/config.py`, no hours 25/26, directions pooled from phase 04 onward). Background findings for this round: `docs/06_blockade_frequency/disagreement_deep_dive.md` and `docs/06_blockade_frequency/line_14/blocked_slots_investigation.md` — read both before starting.

## A. New figure — line 22B: "something happens time-wise" (combined timeline + cost)

One figure, two panels, in `docs/06_blockade_frequency/line_22/`:

1. **Top panel — Saturday-evening timeline:** for each of 17A, 17B, 19A, 19B, 22A, 22B (rows), the Saturday hour slots 19:00–24:00 as colored cells: blocked / regular / not operating. Shows that all groups detour through the evening while 22B keeps running its regular route. Distinct colors with a legend, palette-consistent line labels.
2. **Bottom panel — 22B pass-through cost:** 22B's reference-route end-to-end travel time during Saturday slots when 17/19 were blocked vs other Saturday slots (mean/median bars or points with n annotated: n=21 vs n=5; note the small control group in the caption). The ~4.5 min gap from the deep-dive should reproduce.

Caption ties the two: 22B doesn't detour — it drives through the blockade hours and pays a small time cost. Save as `saturday_timeline_and_cost_22B.png`.

## B. Saturday summary heatmap — exclude 22B from the computation

Regenerate `docs/06_blockade_frequency/blockade_saturday_summary.png` (and any other figure aggregating line 22 across directions) so that **line 22's values are computed from direction_A only — 22B does not enter the calculation at all** (per the deep-dive: its share is inflated by non-corridor variants and its corridor behavior differs). Label the row "22 (dir A)" and state the exclusion in the caption. Keep the group ordering [17, 19, 22] [9, 97] [14, 15].

## C. Line 14 is never blocked — project-wide

Decision (data-backed, see `line_14/blocked_slots_investigation.md`): line 14's 14 "blocked" slots are single-trip stop-recording dropouts, not detours.

1. **Reclassify:** in the effective classification (`pipeline/variant_merges.py` / `variant_type_v2` logic), force all line-14 non-reference variants to a non-blocked category (e.g. `noise`). Line 14's blockade share must be exactly 0% everywhere.
2. **Audit every figure and statistic in `docs/`** for line 14 appearing as a blocked/detouring line, and regenerate whatever this touches. At minimum check: phase 05 (remove `line_14/` outputs and 14's curve from any multi-line delta figure — a control line has no legitimate "blocked vs baseline" comparison), phase 06 (14's per-line heatmap shows 0% everywhere; combined all-lines figure and Saturday summary updated), phase 04 (unaffected but verify), phases 08–09 (14 is a control there — verify it's treated purely as control and its 14 noise slots don't leak into any blockade-window definition).
3. **Document:** short addendum in `docs/06_blockade_frequency/line_14/README.md` linking the investigation and listing exactly which figures changed.

## Process

1. Order: C1 (reclassification) → B and C2 (regeneration/audit) → A.
2. Update `docs/README.md` index.
3. Verify every regenerated figure visually (palette, legends, captions, no 25/26, line 14 at 0% everywhere).
4. Finish with a list of every file changed and the numeric before/after for line 14 and the Saturday summary.
