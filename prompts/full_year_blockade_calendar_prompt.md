# Prompt for Claude Code — full-year blockade scan (relaxed threshold) + confirmed-hours calendar

Copy everything below into Claude Code, run from the repo root.

---

Read `CLAUDE.md` for background but note it is stale relative to the real project state — trust `docs/` and `pipeline/` instead. Read, in full: `docs/10_candidate_windows/README.md`, `docs/11_deep_dive_candidate_windows/README.md`, and `docs/06_blockade_frequency/disagreement_deep_dive.md`. This prompt **redoes and broadens** the phase-10/11 scan under a simpler, more permissive rule (phase 10's rule required "no line saturating + ≥3 lines elevated ≥15pp above an own-baseline of 0%," which excluded already-known cases and some real ones with thin margins). Use only the effective/merged classification (`pipeline.variant_merges.build_effective_df_cleaned`, `variant_type_v2` — never raw `variant_type`), applied to `govData/df_cleaned.csv`. Never use raw ride-level files. All global rules from the project's other `prompts/*.md` files apply (no code snippets in reports, cite sources, plain two-level verdict language, state n everywhere).

## Part A — Rescan, relaxed rule (this replaces phase 10's filter, does not just add to it)

For every (month, day_of_week) cell across the full year, all 7 lines:

- Compute blocked-share exactly as `pipeline/plot_blockade_frequency.py`'s `fraction_pivot` does (hours/directions pooled per line, per month, per day-of-week), same as phases 06/10.
- **New rule — flag any cell where at least 3 lines independently show blocked-share > 10%.** No saturation exclusion, no baseline-relative comparison, no exclusion of already-explained cases (Saturday near-100% cells, line 22B) — include everything that clears the bar. For each flagged cell, report every line's share and n; if a cell's story is already fully documented (e.g. it's one of the known Saturday closures, or overlaps line 22B's known pattern), say so explicitly and link to the existing doc (`docs/06_blockade_frequency/disagreement_deep_dive.md`, `docs/06_blockade_frequency/line_14/blocked_slots_investigation.md`) rather than re-deriving it — but still include it in the output list; don't drop it.
- Flag (don't silently drop) any cell where the n behind a reported share is under 8 (project's low-confidence floor, CLAUDE.md issue #6) — keep it in the list, labeled low-confidence, rather than excluding it as phase 10 did for the winter Saturdays.
- Render the same heatmap style as phases 06/10 (Reds colormap, 0-1 scale, % annotated, `pipeline.config.LINE_COLORS` for line labels) for all 7 lines, full year — save images.
- Output a single ranked table of every flagged (month, day_of_week) cell: lines involved, share + n per line, and a one-line flag for "already documented elsewhere" vs. "not previously examined at hour level."

Do not do any hour-level work in this part — that's Part B, and it runs on every cell this part flags (no manual approval gate this time — the point of relaxing the rule is to get one complete, systematic pass; skip the two-pass review-before-deep-dive step used in phases 10/11).

## Part B — Hour-level deep dive → confirmed-hours calendar

For **every** cell flagged in Part A, replicate the method already validated in `docs/06_blockade_frequency/disagreement_deep_dive.md` and `docs/11_deep_dive_candidate_windows/README.md`:

- Pull every (hour, direction) slot for every elevated line in that cell; tabulate `variant_type_v2` per slot; check footprint overlap against the existing corridor/Aza-St. footprints (recompute from `govData/variant_summary.csv`'s `missing_stop_codes`, same method as phase 11 — do not redefine a new footprint if an existing one already covers the relevant stops).
- **Confidence rule for what counts as "confirmed":** an hour is marked confirmed only if (a) `n >= 8` for that slot, and (b) the slot is variant-*pure* — i.e. within that exact (line, direction, month, day_of_week, hour) group, only one `route_variant_id` appears in the effective/merged data (this is the same purity check already run in this chat's discussion: project-wide, only 1 of 905 blocked-containing slots mixes a blocked and a reference variant — cite that finding rather than re-deriving the global rate, but re-verify it specifically for each cell's own slots). If a slot is impure or under-n, mark that specific hour "inconclusive," not confirmed — don't round up.
- **n-anomaly check (report only strong deviations):** for each confirmed hour, compare its `n` to the same (line, direction)'s `n` at an adjacent reference-variant hour on the same (month, day_of_week) (the nearest hour before/after the blocked window running the reference variant). Report this comparison **only if the ratio is ≥2x or ≤0.5x** in either direction — stay silent (don't print a line) for anything milder; this is meant to surface real coverage gaps or fabrication-style artifacts (per the check already run for line 22B/December in this project), not routine hour-to-hour traffic variation.
- Build the per-cell timeline figure (same style as `disagreement_windows.png` / phase 11's `timeline_*.png`).

## Output — the calendar

Produce **one summary grid**: month (rows) × day-of-week (columns), 7 such grids or one faceted figure per relevant line-group (your call on layout, but keep it readable) — each cell that reached "confirmed" status in Part B is labeled with its confirmed hour range (e.g. "confirmed, 13–17h") instead of a raw percentage; cells that were flagged in Part A but didn't produce a clean confirmed-hour result are labeled "inconclusive" with a one-phrase reason (low n / impure slots / already-explained artifact — cite the doc). This is the deliverable rony will use to decide what to present. Do not just re-print the phase-06/10 percentage heatmaps here — the whole point of this pass is to convert "share %" into a plain "was there a confirmed blockage, and when" answer per cell.

## Outputs / files

- New folder `docs/13_full_year_calendar/` (next available phase number — 12 is already taken by statistics) with a `README.md` in the same style as the other numbered phases.
- The relaxed-rule heatmaps (Part A), the ranked flagged-cell table, per-cell timeline figures (Part B), the n-anomaly report (only the ≥2x/≤0.5x cases, each with the two n values and hours compared), and the final calendar grid(s).
- Update `docs/README.md`'s phase index with the new `13_` entry.

## Verification before finishing

- Recompute every share/n directly from `govData/df_cleaned.csv` via `build_effective_df_cleaned` in this pass — do not carry over any number from docs/10 or docs/11 without recomputing it.
- Confirm the three already-deep-dived cells from phase 11 (Nov/Wed, Dec/Wed, Oct/Mon) reappear in Part A's relaxed list and that Part B's confirmed-hours for them match phase 11's findings (Nov ~10–18h, Dec 13–17h for the real direction_A signal specifically — not conflated with direction_B's artifact, Oct ~12–14h) — if they don't match, stop and reconcile before publishing the calendar.
- Confirm control lines 14/15 never reach "confirmed" status anywhere on the calendar (sanity check, same as phases 10/11).
- Spot-check at least 2 of the already-known Saturday cells to confirm they correctly land as "confirmed" with a sensible hour range, citing the existing docs rather than re-deriving the explanation.
