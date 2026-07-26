# 05 — Baseline vs. Blocked/Special Variant (Delta Style)

**Revision round (section F): the phase 05 figures have been replaced
entirely.** Instead of per-variant stop-skip bar charts, each line now
gets one delta-style line chart (anchor: the top panel of
[docs/08_control_lines_15_14](../08_control_lines_15_14/README.md)'s
`line_15_hourly_pattern.png`): for each hour of day, (median travel time
on the line's blocked/special variant) minus (median travel time on its
baseline variant), both directions pooled (section C), using only the
confirmed post-merge/post-exclude variant set from
[docs/03_variants](../03_variants/README.md) and the new >15-stop
blocked rule (section B). Grey bands mark hours with fewer than 8
blocked-variant observations (thin data).

**Revision round 2:** hours 25/26 (01:00/02:00 next day) are dropped
from every figure's data entirely (global rule — previously shown as
01:00/02:00, now just not plotted). Line 97's new exclusion
([docs/03_variants](../03_variants/README.md), direction B variant 2)
removes 8 blocked blocks from line 97's stats (n_blocked 108→100 vs.
the first revision round). A combined figure, `delta_all_lines.png`,
plots lines 17/19/22 (reds) and 9/97 (purples) on shared axes so all
five non-control lines' hourly detour patterns can be compared
directly. Colors now come from the single project-wide palette in
`pipeline/config.LINE_COLORS` (`docs/README.md`).

**Revision round 3 (sections A, B, F):**

- **B1 (data-source audit):** confirmed correct — `run()` calls
  `vm.build_effective_df_cleaned(df_cleaned, variant_summary)` (the
  merged, post-exclusion variant set) before computing anything, exactly
  like every other revised phase. No bug; this phase was never built
  from raw variants.
- **B2 (why control lines 14/15 appeared at all — found and fixed):**
  every line, control or not, has a long tail of `count<=5`,
  near-full-length "blocked" merged variants (missing just 1–11 stops
  out of a 30–67-stop route) — near-certainly one-off recording noise,
  not real detours. Protest lines also have one or two *dominant* real
  detour variants (count in the dozens to hundreds), so the noise was a
  minor contaminant there. **Lines 14 and 15 have no dominant variant at
  all** — 100% of their "blocked" blocks were this singleton/near-singleton
  noise (line 14's largest "blocked" variant: count=4; line 15's only
  one: count=4). Fix, scoped to this phase only (`variant_type_v2`
  itself is untouched everywhere else): a merged variant is now only
  eligible to count as "blocked" here if its `count >
  MIN_BLOCKED_VARIANT_COUNT` (5) — reusing `plot_variants_revised`'s own
  `RAW_COUNT_THRESHOLD` convention for "real enough to matter." Effect:
  **lines 14 and 15 now have zero blocked blocks and no longer appear in
  this phase at all** (their old, noise-driven figures are removed);
  the five real protest lines lose only their small noise contribution
  (n_blocked drops by 8–39 blocks each, deltas shift by ≤1 min) — see the
  updated table below. **Round 4:** line 14's noise variants are now
  classified `"noise"` at the source
  ([docs/06_blockade_frequency/line_14](../06_blockade_frequency/line_14/README.md))
  rather than relying on this phase's `count>5` floor to hide them;
  line 15's are unchanged and still rely on the floor. No numeric
  change here.
- **F — line 97 detour-distance figure:** `line_97/detour_distance.png`
  compares cumulative distance (km) along line 97's baseline route vs.
  its dominant detour variant. Counterintuitively, **the detour is
  *shorter*, not longer** (7.94 km vs. 9.64 km, −17.7%) — so line 97's
  large blockade delay at certain hours ([docs/09](../09_lines_9_97/README.md))
  is congestion/signal time on the detour, not extra distance. A
  companion `detour_distance_all_lines.png` shows the same comparison
  for lines 9/17/19/22 for context (all also end up *shorter*, except
  line 22 which is ~flat, +0.9%).

## Headline finding: every remaining line's blocked/special variant is faster overall

| Line | n baseline | n blocked | Overall median delta (min) | Verdict |
|---|---|---|---|---|
| 9 | 1,605 | 93 | **−15.9** | saves time |
| 17 | 944 | 93 | **−11.4** | saves time |
| 19 | 2,191 | 183 | **−8.7** | saves time |
| 22 | 1,879 | 210 | **−3.1** | saves time |
| 97 | 2,145 | 61 | **−8.0** | saves time |

(Lines 14 and 15 no longer appear — see B2 above. `n blocked` in this
table is after the `count>5` significance floor, not the raw
`variant_type_v2` count used elsewhere in the project.)

Every remaining line's blocked/special variant is measurably *faster*
than its baseline overall, consistent with earlier rounds: the routes
classified as "detours" in this dataset behave like short-turn/express
service or avoid a congested corridor, not like a slower forced detour.
Line 22 — now correctly showing a substantial blocked share
([docs/06_blockade_frequency](../06_blockade_frequency/README.md)) —
also shows the smallest time saving (−3.1 min), plausibly because its
blocked variant only skips a small slice of a much longer route (and,
per F above, is barely longer in distance at all).

**`delta_all_lines.png`:** the combined view shows this "saves time"
pattern is not uniform across hours — several lines' curves cross above
zero at specific hours even though their all-hours median is negative
(see e.g. line 97's midday peak, discussed in
[docs/09](../09_lines_9_97/README.md) where the same variant behaves
very differently from line 9's).

Per-line detail: [line_9](line_9/README.md), [line_17](line_17/README.md),
[line_19](line_19/README.md), [line_22](line_22/README.md),
[line_97](line_97/README.md) (line 97 also has
[detour_distance.png](line_97/README.md), section F). Lines 14 and 15
no longer have per-line pages in this phase (B2).

**Figures:** per-line `line_<N>/baseline_vs_blocked_delta.png`, the
combined `delta_all_lines.png` (section B, round 2), line 97's
`detour_distance.png` plus the cross-line `detour_distance_all_lines.png`
(section F, round 3).

**Sources:** `govData/df_cleaned.csv`, `govData/variant_merges.json`,
`pipeline/variant_merges.py`, `pipeline/pooled_analysis.py`,
`pipeline/config.py`, `pipeline/plot_baseline_vs_blocked_delta.py`.
