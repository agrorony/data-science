# Work Report — July 20–26, 2026

Follow-up to `work_report_2026-07-19.md`. This week the project moved from "pipeline exists" to "presentation-ready documentation": the full `docs/` tree (9 phases) was built and then refined through four prompt-driven revision rounds, plus two data investigations that changed analysis decisions.

## Timeline

| Date | What happened |
|---|---|
| Jul 20 | Work report for Jul 19 committed; legacy rebuild/validation scripts removed; Avishag updated `chosen_route_ids_by_line` to list-based route IDs |
| Jul 20–22 | **Initial `docs/` build** (`presentation_prep_prompt.md`): all 9 phase folders created — cleaning docs, route_id↔line mapping, variant maps, baselines, skip comparison, blockade heatmaps, plus subagent investigations (07–09) |
| Jul 23 | **Revision round 2 executed** (commits `94ebf14`, `90e5593`): per-direction figures replaced by per-line subplot figures, exclusions applied, hours 25/26 removed; first presentation draft `מצגת1.pptx` added |
| Jul 25 | **Revision rounds 3+4 executed** (commit `6215a17`, 66 files): palette, SEM, deep-dive fixes — details below |
| Jul 25–26 | **Two chat investigations** (22B disagreement, line 14 noise) → two analysis reports + round-4 corrections |

## The revision rounds (what changed in `docs/`)

**Round 1** (baseline corrections): clustering dropped in favor of a **manual variant-merge table** (encoded in `pipeline/variant_merges.py` + `govData/variant_merges.json`); raw maps limited to variants with n>5; the 10%-missing-fraction "blocked" rule replaced by **"any non-baseline variant with >15 stops = blocked"** (`variant_type_v2`) — this made line 22's detours finally count; directions pooled from phase 04 onward; all-lines travel-time barplot added; phase 05 restyled to delta charts; phase 08 reduced to delta-only.

**Round 2**: two more variant exclusions (19B v5, 97B v2); phase 03 maps consolidated to one figure per line (direction A over B as subplots — `variants_raw.png` / `variants_merged.png`); cross-line delta figure (`delta_all_lines.png`, reds for 17/19/22, purples for 9/97); all-lines blockade heatmap grid + Saturday summary heatmap; two-curve blockade-delta figures for lines 9/97; hours 25/26 banned from all figures.

**Round 3**: global **per-line color palette** in `pipeline/config.py` enforced across all multi-line figures; phase 04 error bars switched from std to **SEM** + new `baseline_travel_time_by_hour.png`; phase 05 data-source audit; line 97 **detour-distance figure** (`detour_distance.png`, `detour_distance_all_lines.png`); phases 08 controls merged into one figure (`control_lines_delta.png`); Saturday heatmap rows grouped [17 19 22][9 97][14 15]; legend overlaps fixed.

**Round 4** (executed Jul 25): line 22B and line 14 corrections following the investigations below — new `saturday_timeline_and_cost_22B.png`, Saturday summary recomputed without 22B, line 14 reclassified as never-blocked project-wide, `disagreement_windows.csv/png` artifacts added.

## Investigations & findings (the analytical core of the week)

**1. Cumulative-distance dip (lines 97/17).** The detour curves showed *decreasing* cumulative distance. Verified in-data: distance is the vehicle's position projected onto the licensed route shape, which regresses during off-shape detours (time increases while "distance" drops). Conclusion: detour distances must be rebuilt from stop coordinates, not the projected field.

**2. Blockade disagreement deep dive** (`docs/06_blockade_frequency/disagreement_deep_dive.md`). Relaxing the 0.9/0.7 thresholds exposed 15 disagreement windows — 14 of them driven by **line 22 direction B** (Saturday blocked share 32% vs 67–83% for all other groups). Verified: 22B's route touches only 2 of the 10 blockade-footprint stops and its variants skip none of them (H1 ✓); all other groups' regular Saturday rides exist only after 23:00 while 22B drives through 19:00–23:00 (H2 ✓ except 22B); no data fabrication — all 38 Saturday blocks distinct (H3 ✗). Bonus: 22B is ~4.5 min slower when passing through during others' blockades (n=21 vs 5). **Decision: 22B excluded from blockade-share calculations; line 22 represented by direction A.**

**3. Line 14 "blockades"** (`docs/06_blockade_frequency/line_14/blocked_slots_investigation.md`). Its 14 flagged slots (0.8%) are ten n=1 and one n=4 variants that skip 1–6 stops, add zero stops, share zero stops with the blockade footprint, occur mostly weekday midday (8/14 on Tuesdays), with no travel-time effect — stop-recording dropouts, not detours. Root cause: the n>5 filter applied only to maps, never to statistics. **Decision: line 14 is never-blocked project-wide (pure control).**

## Current state

- `docs/` is complete and internally consistent through round 4; `docs/README.md` indexes all phases and the palette.
- Prompt history preserved in `prompts/` (5 files: initial + rounds 1–4).
- First presentation draft `מצגת1.pptx` exists at repo root.

## Open items

- **Large uncommitted diff** (~60 files): most `govData/*.csv` and notebooks show as modified (likely a pipeline rerun and/or line-ending churn) — needs review and a commit or discard; a stray `.git/index.lock` warning appeared during inspection.
- **Untracked:** `line_97_findings.png` (repo root — move into `docs/` or delete), `lectures/`, `.claude/`.
- Line-14 report offers 3 optional figures — none generated yet (awaiting choice).
- The 22B pass-through cost finding rests on n=5 control slots — flag as suggestive in the presentation.
