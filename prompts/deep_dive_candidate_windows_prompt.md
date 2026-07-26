# Prompt for Claude Code — hour-level deep dive on candidate windows + line 22 December check

Copy everything below into Claude Code, run from the repo root.

---

Read `CLAUDE.md` for background but note it is stale relative to the real project state — trust `docs/` and `pipeline/` instead. Read `docs/10_candidate_windows/README.md` in full (the scan that produced this task's inputs) and `docs/06_blockade_frequency/disagreement_deep_dive.md` (the methodology to replicate — it did an hour-level deep dive on two Saturday cells; this prompt extends the same approach to three new, different cells plus one targeted anomaly check). Use only the effective/merged classification (`pipeline.variant_merges.build_effective_df_cleaned` on `govData/df_cleaned.csv`, `variant_type_v2`) — never raw `variant_type` or raw ride files. All global rules from the project's other `prompts/*.md` files apply (no code snippets in reports, cite sources, plain-language verdicts, state n everywhere).

## Part A — Hour-level deep dive on three approved candidate windows

`docs/10_candidate_windows/README.md` flagged (month, day_of_week) cells where several lines show a similar, moderate, non-saturating blocked-share at once — a different pattern from the already-explained April/June Saturday "majority vs. outlier" case. Three cells are approved for deep dive:

1. **November, Wednesday** (17: 67% n=21, 9: 55% n=29, 19: 51% n=43, 22: 37% n=35, 97: 35% n=37) — top priority, crosses both the corridor group (17/19/22) and the Aza St. group (9/97).
2. **December, Wednesday** (22: 61% n=38, 19: 20% n=41, 17: 19% n=21, 9: 16% n=32) — see Part B for a required sub-investigation specific to line 22 here.
3. **October, Monday** (17: 55% n=11, 19: 50% n=42, 22: 32% n=34, 9: 17% n=23) — note line 17's n=11 is thin; flag this explicitly in the writeup rather than silently treating it as equal-confidence to the others.

For each of the three cells, replicate `disagreement_deep_dive.md`'s method:

- Pull every (hour, direction) slot in `df_cleaned.csv` (effective/merged) for every line elevated in that cell, on that (month, day_of_week).
- Tabulate `variant_type_v2` per slot (reference/regular/blocked/noise) and build a timeline figure in the same style as `disagreement_windows.png` (hour on one axis, line/direction rows, colored by variant type).
- Check stop-overlap against the known blockade footprints already defined in `docs/06_blockade_frequency` / `docs/07_blockade_investigation` (the 10-stop corridor footprint for 17/19/22, and separately whatever footprint applies to the Aza St. group for 9/97 — locate this from `docs/09_lines_9_97` if not already explicit). Do not invent a new footprint if an existing one already covers the relevant stops.
- Check timing spread (do blocked and regular slots cluster at different hours, like the Saturday "regular resumes after 23:00" pattern, or are they interleaved?).
- Report n per slot; do not over-read any slot with n<8 (project's own low-confidence floor per CLAUDE.md issue #6).
- Verdict per cell, using exactly this two-level language: "real coordinated event" (with the specific mechanism, e.g. shared corridor closure at those hours) vs. "not novel / already-explained pattern" vs. "inconclusive — low n / conflicting signal" — no overclaiming.

## Part B — Required: explain line 22's December pattern before trusting it

`docs/10_candidate_windows/README.md` flagged that line 22 sits at **almost exactly 50% blocked-share on every weekday in December (Sun–Thu), each with n=38** — Wednesday (60.5%) barely stands out from the rest. A share pinned near a round 50% across multiple independent days, with an identical n=38 each day, is a specific red flag for a construction artifact (direction mixing, a merge/exclusion applied inconsistently, or a duplicate-row issue) rather than a genuine, real detour pattern — this project has already found exactly this kind of bug once before (line 22 direction B's inflated Saturday share, `disagreement_deep_dive.md`; and CLAUDE.md's original documented duplicate-row issue, ~34% of rows, in the raw merged file — confirm whether `df_cleaned.csv` is fully clean of that or could still carry residual duplicates).

Before treating December's line 22 pattern as a real finding, check, in this order:

1. **Direction split.** Line 22 has no merges/exclusions in `variant_merges.json` for either direction (`docs/03_variants`: "22 | A | none | —", "22 | B | none | —"). Split December's blocked-share by direction A vs. B separately. If one direction is driving all of it (like the original 22B issue), say so explicitly and identify which.
2. **Is n=38 real or duplicated.** Check whether the same n=38 across five different days is coincidence, or whether rows are being double-counted (re-verify no residual duplicate rows survive into `df_cleaned.csv` the way CLAUDE.md documented for the raw merged file — cross-check `_id` or an equivalent row-identity field for exact duplicates within the December/line-22 slice).
3. **Which variant is being counted as "blocked."** Identify the specific variant(s) responsible for line 22's December "blocked" label and check, the same way the 22B investigation did: how many footprint stops does line 22's reference route touch in December, and does this variant actually skip them, or is it (like 22B's original 1-stop swaps) a trivial deviation being over-classified as "blocked" under the >15-stop rule?
4. **Fabrication/duplication check**, same test as `disagreement_deep_dive.md` Hypothesis 3: are December's line-22 "blocked" rows distinct at the stop-level travel-time vector (no identical pairs), and what fraction have std=0? If a large share of rows are near-identical, that points to a merge/duplication bug, not real service.
5. **Bottom-line verdict**: is December's ~50% line-22 pattern (a) a genuine, month-wide partial closure affecting line 22 specifically, (b) a direction-mixing artifact like the original 22B bug, or (c) a data-duplication/classification artifact? State which, with the evidence from steps 1–4.

## Outputs

- New folder `docs/11_deep_dive_candidate_windows/` with a top-level `README.md` (style matching `docs/06_blockade_frequency/README.md`): one section per Part-A cell with its timeline figure, verdict, and n caveats; a distinct, clearly-labeled section for the Part-B line-22-December investigation with its own verdict.
- Per-cell timeline figures (`timeline_<month>_<day>.png`) in the same visual style as `disagreement_windows.png`.
- If Part B finds a real classification/merge bug, do **not** silently fix `variant_merges.json` — report the finding and the recommended fix, and stop for rony's review before changing any merge/exclusion table (this table is a manually-curated, previously-audited source of truth; changes need sign-off, same as prior rounds in `work_report_2026-07-20_to_26.md`).
- Update `docs/README.md`'s phase index with the new `11_` entry.

## Verification before finishing

- Cross-check that every reported share/n in the new README matches what you can recompute directly from `df_cleaned.csv` via `build_effective_df_cleaned` — do not carry over any number without recomputing it in this pass.
- If Part B's direction split or duplicate check turns up something that changes December's line-22 share materially, flag that explicitly as a finding for rony rather than quietly adjusting the number.
- Sanity check against the control lines: confirm lines 14/15 show nothing resembling this pattern in December (they shouldn't, per `docs/10`'s existing sanity check) — if they do, treat that as a sign the anomaly-check logic itself has a bug, not a real finding, and investigate before reporting.
