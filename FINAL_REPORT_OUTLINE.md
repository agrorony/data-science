# Final Report — Structure & Task Split
Course 71253, final report due **1 Aug 2026** (today: 23 Jul — 9 days left).
Format: Word or PDF, **≤10 pages including figures**, font ≥11, line spacing ≥1.15, margins ≥1", figures numbered + titled with their main message, no code, informative variable names.

This maps the course's required sections onto the work already done in `docs/01`–`docs/09`, and proposes a page budget, figure picks, and a split between the two of you. Source doc for all content below: `docs/README.md` and the numbered phase folders.

---

## 1. Introduction to the data — ~1 page

Content:
- Dataset: Israeli Ministry of Transport "Arrival to station, day and hours" ([data.gov.il](https://data.gov.il/he/datasets/ministry_of_transport/arrivaltostationdayandhours/e3673768-3dc2-4e62-b0ea-cf763c07a037)).
- Scope: 7 Jerusalem bus lines (9, 14, 15, 17, 19, 22, 97), 16 underlying `route_id`s, final cleaned table `df_cleaned.csv` — 603,662 rows.
- What a record means: average travel behavior (cumulative time/distance) for all rides matching one (route, month, day-of-week, departure hour, stop) combination, plus `n_observations` (rides behind the average).
- One-paragraph summary of the main cleaning issue (the ~22% duplicate-key rows from overlapping export batches, resolved by majority-vote dedup) — full detail belongs in section 2, not here.

Source: `docs/01_data_cleaning/README.md`, `docs/02_route_mapping/README.md`.
No figure strictly required here — keep it text-only to save space for section 2.

---

## 2. Exploratory analysis — ~3.5 pages (this is the "significant portion")

Four sub-parts, each 2-4 sentences of narrative, not the full decision-log detail from `docs/`:

1. **Data cleaning** — the duplicate-export problem, majority-vote resolution, `low_confidence` flag (n<8), late-night hour remap. (from `docs/01`)
2. **Route structure & variants** — every line has multiple stop-sequence "variants"; how they were detected and consolidated (manual merge table). One figure: a variants grid for a representative line. (from `docs/02`, `docs/03`)
3. **Baseline travel-time patterns** — how the 7 lines compare on trip duration once reduced to their most common route. Figure: `docs/04_baselines/travel_time_all_lines.png` (all 7 lines ranked, error bars). (from `docs/04`)
4. **How often lines deviate from baseline** — cross-line view of how often each line runs a non-standard ("blocked") variant. Figure: `docs/06_blockade_frequency/blockade_all_lines.png`. (from `docs/06`)

**Figures for this section (pick 2 of the 3 candidates below to stay on budget):**
- `docs/03_variants/line_22/variants_merged.png` (or another single line) — shows what a variant grid looks like.
- `docs/04_baselines/travel_time_all_lines.png` — headline cross-line figure.
- `docs/06_blockade_frequency/blockade_all_lines.png` — sets up the question section.

---

## 3. Specific question, methods, conclusions — ~4.5 pages

**Project goal:** use the data to analyze the travel patterns of bus lines serving Jerusalem's Rechavia neighborhood.

**The big question:** *given the recurring street closures near the neighborhood, how can a resident know the most reliable way to leave Rechavia by bus?*

Split into 4 sub-questions, each its own short subsection (state question → method in prose → 1 figure → conclusion), following the course's recommended subsection format:

| # | Question | Method (from) | Figure |
|---|---|---|---|
| Q1 | When during the year do blockades happen, and how consistent is the pattern? | `docs/13_full_year_calendar` | `confirmed_hours_calendar.png` |
| Q2 | When a line's bus detours around a blockade, is the detour actually slower than the normal route? | `docs/05_skip_comparison` | `delta_all_lines.png` |
| Q3 | Do blockades ripple onto lines that don't even run through the blocked street? (control lines 14 & 15) | `docs/08_control_lines_15_14` | one control-line hourly-pattern figure |
| Q4 | Lines 9 & 97 share the corridor but not the exact blocked segment — do they reroute, run late, or both? | `docs/09_lines_9_97` | `line_9_blockade_delta.png` or `line_97_blockade_delta.png` |

Each conclusion should state the finding in plain language with the number attached, e.g. "line 9 is delayed by 11.7 minutes on Saturdays during blockade windows (p=0.010)" — the actual verified numbers are already in the `docs/08` and `docs/09` READMEs, just need shortening into report prose (drop the two-round revision history — the report only needs the final, current numbers).

---

## 4. Follow-up ideas — ~0.5–1 page

Candidates already implied by open items in `docs/`:
- Resolve the unmapped `stop_code 5912` (line 97 direction split) with a proper GTFS/stations re-export.
- Extend the blockade-impact method to other corridors/cities to test whether the ripple pattern generalizes.
- Bring in ridership/crowding data (not in this dataset) to estimate passenger-minutes lost, not just bus-minutes.
- A live/predictive version: flag a likely blockade in near-real-time from a sudden variant-share shift.

---

## Page budget check
Intro (1) + EDA (3.5) + Question section (4.5) + Follow-up (0.5) + title/refs ≈ **9.5 pages**. Tight — expect to trim EDA prose, not figures, if over.

---

## Suggested task split

Based on who already owns each phase's underlying analysis (fastest to write, least re-derivation):

- **Avishagi (you):** Section 1 (Introduction) + Section 2 parts 1–2 (data cleaning, route/variant structure) — this is your existing work in `avishagi/` and `docs/01–03`.
- **Rony:** Section 2 parts 3–4 (baselines, blockade frequency) + all of Section 3 (the question section) — this is his pipeline/subagent work in `docs/04–09`.
- **Together:** Section 4 (follow-up ideas), final figure selection/trim to page budget, formatting pass (font/margins/spacing/figure numbering), and reusing the same figures for the 10-minute presentation.

Alternative split if you'd rather divide by *section* instead of *phase ownership*: one of you writes Intro+EDA end-to-end, the other writes the Question+Conclusions section — simpler to coordinate but means whoever didn't build `docs/04–09` has to learn that analysis from scratch to write it well. The phase-based split above avoids that.

## Suggested timeline
- **Jul 23–24:** agree on this outline + exact figure picks.
- **Jul 25–27:** draft assigned sections independently (write in a shared doc, English, no code).
- **Jul 28–29:** merge, cut to 10 pages, check every formatting rule.
- **Jul 30:** final proofread; adapt kept figures for the presentation.
- **Jul 31:** buffer before the Aug 1 deadline.
