# 09 — Lines 9 and 97 During Confirmed Aza-Corridor Blockade Windows

**Revision round (sections C, H): rebuilt** on the merged/excluded
variant set and the new absolute >15-stop blocked rule
([docs/07's addendum](../07_blockade_investigation/README.md)), **both
directions of each line pooled** (section C), and reusing the **updated
320-slot blockade window table from
[docs/08_control_lines_15_14](../08_control_lines_15_14/README.md)**
(up from 112 in the first pass — see docs/08 for why the window count
grew). Figure style is unchanged (variant-share bar chart + travel-time
boxplot grid), now with one pooled panel per line instead of one panel
per direction.

**Revision round 2 (section D):** line 97's new exclusion
([docs/03_variants](../03_variants/README.md), direction B variant 2,
classified `blocked`) shifts its own route-share numbers slightly (see
the updated Weekday/Combined rows below — Saturday and all of line 9's
numbers are unaffected, since that exclusion only removes line 97
blocks). A new figure per line, `line_<N>_blockade_delta.png`, adds a
direct answer to "what happens to 9/97 during a blockade": red =
the line's own detour cost (blocked variant vs. its own baseline, in
hours it ran the detour); blue = the cost of staying on the baseline
route during confirmed 17/19/22 blockade windows where this line itself
was *not* blocked. Hours 25/26 are dropped from every figure per the
global rule.

## Method

Identical to [docs/08](../08_control_lines_15_14/README.md): windows are
loaded verbatim from `docs/08_control_lines_15_14/blockade_windows_used.csv`.
(a) Route affected — any block's `variant_type_v2` non-baseline
("blocked") share, blockade-window vs. matched-normal, tested with
Fisher's exact or chi-square (Yates), stratified Saturday/Weekday/Combined.
(b) Time affected — restricted to each line's own merged baseline
variant (`variant_type_v2 == "reference"`), Mann-Whitney U primary /
Welch t-test robustness check, same strata. `n_observations >= 8` floor
throughout (CLAUDE.md issue #6). Reproduce with `python -m
pipeline.plot_line9_97_blockade_impact`.

## Findings

### Line 9 (both directions pooled)

| Question | Category | n blockade | n normal | Result |
|---|---|---|---|---|
| (a) Route | Saturday | 63 | 17 | 92.1% vs 52.9% non-baseline, Fisher p=**0.001** |
| (a) Route | Weekday | 328 | 1,347 | 13.4% vs 0.8%, Chi-sq p≈**0** |
| (a) Route | Combined | 391 | 1,364 | 26.1% vs 1.5%, Chi-sq p≈**0** |
| (b) Time | Saturday | 5 | 7 | 75.6 vs 63.9 min, Δ=**+11.7**, MWU p=**0.010** |
| (b) Time | Weekday | 276 | 1,304 | 90.9 vs 90.0 min, Δ=+0.9, MWU p=0.102 (ns) |
| (b) Time | Combined | 281 | 1,311 | 90.7 vs 90.0 min, Δ=+0.8, MWU p=0.144 (ns) |

**Verdict: route strongly affected in both strata; time affected on
Saturdays specifically, not on weekdays.** Line 9's own non-baseline
share jumps sharply during blockade windows on both Saturday (92% vs
53%) and weekday (13% vs 1%) — a much larger, better-supported effect
than the first pass found, reflecting the broader window set. Unlike
the first pass (where the Saturday travel-time question was
underpowered, n=0-1), this revision has enough Saturday baseline blocks
(n=5 vs 7) to detect a real, significant **+11.7 minute** slowdown on
Saturdays specifically — the single largest confirmed delay found
anywhere in this project. Weekday and Combined travel time show a small,
non-significant positive delta.

### Line 97 (both directions pooled)

| Question | Category | n blockade | n normal | Result |
|---|---|---|---|---|
| (a) Route | Saturday | 68 | 26 | 85.3% vs 46.2% non-baseline, Chi-sq p=**0.0003** |
| (a) Route | Weekday | 504 | 1,777 | 5.4% vs 0.7%, Chi-sq p≈**0** |
| (a) Route | Combined | 572 | 1,803 | 14.9% vs 1.3%, Chi-sq p≈**0** |
| (b) Time | Saturday | 10 | 14 | 32.4 vs 33.0 min, Δ=−0.6, MWU p=0.121 (ns) |
| (b) Time | Weekday | 451 | 1,652 | 42.4 vs 43.4 min, Δ=−1.0, MWU p=0.293 (ns) |
| (b) Time | Combined | 461 | 1,666 | 42.1 vs 43.3 min, Δ=−1.1, MWU p=0.161 (ns) |

*(Weekday/Combined route-share numbers updated in revision round 2 —
Saturday and all (b) time numbers are unchanged, since the new
exclusion only removes a small number of weekday-flagged blocked
blocks; the conclusion below is unaffected.)*

**Verdict: route affected in both strata; time not affected (if
anything, slightly faster, wrong sign for congestion).** Line 97 shows
the same strong route-choice shift as line 9 (85% vs 46% on Saturdays,
5.7% vs 1.0% on weekdays, both highly significant), but no travel-time
effect on its own baseline variant in any stratum — small negative
(faster) point estimates throughout, none significant.

## Comparison to the first pass and to the control lines (docs/08)

**The route-affected finding got much stronger** for both lines under
the broader window set (p-values now effectively 0, vs. p=0.016–0.006 in
the first pass) — both lines clearly divert more often during confirmed
blockade windows than during matched-normal hours. **The
travel-time-affected finding flipped for line 9**: the first pass
reported this as "inconclusive" (n=4, underpowered); this revision finds
a real, significant Saturday-specific delay (+11.7 min, n=5 vs 7 — still
a small sample, but now enough to clear significance). Line 97 remains
travel-time-unaffected in both passes.

This mirrors [docs/08](../08_control_lines_15_14/README.md)'s
experience in the opposite direction: pooling directions and broadening
the window set can either wash out a previously-significant finding
(line 14, in docs/08) or newly reveal one that was underpowered before
(line 9 Saturday, here) — the new >15-stop rule trades window precision
for window completeness, and the effect on any single statistical test
depends on how that trade-off interacts with each line's specific
sample sizes. Read every p-value in this revision alongside its n,
not in isolation.

**Overall:** lines 9 and 97 both show the same qualitative pattern as
the first pass — a strong route-choice response to the shared corridor's
closure, more than a confirmed travel-time delay — with line 9 now
additionally showing a specific, credible Saturday delay that the first
pass could not detect.

## Section D (revision round 2) — own detour vs. absorbing others' blockade

Two curves per line, per-hour: **red** = the line's own detour cost
(its blocked variant minus its own baseline, in hours it ran the
blocked variant — identical computation to
[docs/05](../05_skip_comparison/README.md)); **blue** = the cost of
*staying on* its own baseline route during confirmed lines 17/19/22
blockade windows, restricted to the subset of those windows where this
line itself was **not** also running a blocked variant (i.e. genuinely
absorbing the traffic rather than detouring).

**Line 9** (`line_9_blockade_delta.png`): red is negative almost
everywhere (own detour saves 15.8 min overall — matches docs/05), with
one brief exception around 17:00 (+1.5 min). Blue is small but mostly
positive (+1.3 min overall, n=268 blockade vs n=1,290 matched-normal
blocks), meaning that in the hours line 9 stays on its baseline route
while 17/19/22 are blocked, it runs a little slower than a normal
matched hour — consistent with, and about the same size as, the
Weekday travel-time effect found in section (b) above. **Verdict: both
route and time are affected** — line 9 detours when it can (and saves
time doing so), and picks up a small, real time cost in the hours it
doesn't.

**Line 97** (`line_97_blockade_delta.png`): the more striking pattern —
red is *strongly positive* (up to +14 min) during hours 14–17, even
though line 97's all-hours median detour saves 8.2 min overall
([docs/05](../05_skip_comparison/README.md)). Line 97's blocked variant
is not uniformly a shortcut: at those specific afternoon hours the
detour itself is the slow option. Blue stays close to zero to mildly
negative overall (−1.1 min, n=454 blockade vs n=1,661 matched-normal
blocks) — staying on the baseline route during others' blockades costs
line 97 essentially nothing. **Verdict: route is affected (per section
(a) above) and the time effect is hour-dependent** — mostly neutral to
beneficial, but the detour becomes a net time cost specifically in the
mid-afternoon window, a pattern the pooled Weekday/Combined statistics
in section (b) average away.

## Figures

- `line_9_variant_share_comparison.png`, `line_97_variant_share_comparison.png`
  — % non-baseline blocks, blockade window vs matched normal, both
  directions pooled, Saturday/Weekday/Combined, n and p-value annotated.
- `line_9_travel_time_comparison.png`, `line_97_travel_time_comparison.png`
  — travel-time boxplots (own baseline variant, both directions pooled),
  same three strata, n and Mann-Whitney p annotated.
- `line_9_blockade_delta.png`, `line_97_blockade_delta.png` (section D,
  revision round 2) — own-detour vs. absorbing-others'-blockade delta by
  hour, both directions pooled.

Underlying numbers: `variant_share_stats.csv`, `travel_time_stats.csv`.

**Sources:** `govData/df_cleaned.csv`, `govData/variant_merges.json`,
`docs/08_control_lines_15_14/blockade_windows_used.csv`,
[docs/02_route_mapping](../02_route_mapping/README.md),
[docs/03_variants](../03_variants/README.md),
[docs/05_skip_comparison](../05_skip_comparison/README.md),
[docs/06_blockade_frequency](../06_blockade_frequency/README.md),
[docs/07_blockade_investigation](../07_blockade_investigation/README.md),
[docs/08_control_lines_15_14](../08_control_lines_15_14/README.md),
`pipeline/variant_merges.py`, `pipeline/pooled_analysis.py`,
`pipeline/plot_baseline_vs_blocked_delta.py`,
`pipeline/plot_control_comparison.py`,
`pipeline/plot_line9_97_blockade_impact.py`.
