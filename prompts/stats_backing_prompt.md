# Prompt for Claude Code — statistical backing: permutation tests + bootstrap CIs

Copy everything below into Claude Code, run from the repo root.

---

Add nonparametric statistical backing (permutation tests + bootstrap confidence intervals) to every key comparison in `docs/`. No new modeling (no regression/DiD) — the goal is to attach honest p-values, confidence intervals, and effect sizes to the numbers we already report. All global rules from previous prompts apply.

## Method (one implementation, reused everywhere)

Write one reusable module, e.g. `pipeline/stats_tests.py`:

- **Permutation test** for a difference between two groups of blocks: shuffle group labels 10,000 times, two-sided p = share of shuffles with |difference| ≥ observed. Where the comparison was constructed as matched (same day-of-week/hour), permute **within those strata**, not globally — the test must respect the matching that built the comparison. Test the difference in means; also report the difference in medians.
- **Bootstrap CI**: 10,000 resamples with replacement within each group, percentile 95% CI on the difference in means (and medians).
- **Effect size**: Cliff's delta with standard qualitative bands (negligible/small/medium/large).
- Fixed random seed (document it); report exact n per group everywhere.
- Unit of observation = one block (one line/direction, month, day-of-week, hour). State this explicitly in the reports: rides within a block are already averaged, so n counts blocks, not rides.

## Comparisons to run

1. **Phase 05 — detour cost per line**: for each of 17, 19, 22 (direction A only), 9, 97: blocked-variant vs baseline end-to-end travel time (the delta the figures already show, pooled over hours). Permutation p, bootstrap CI, Cliff's delta.
2. **Phase 08 — control lines**: for 15 and 14 separately: travel time during blockade windows vs matched normal slots (stratified permutation within day/hour). This replaces the single Mann-Whitney note with p + CI + effect size. Do NOT add a signed-rank or any second hypothesis test — one test per comparison. Additionally compute a **breadth statistic**: of the hours shown in the delta chart, in how many is the per-hour delta positive (e.g. "positive in 14 of 17 hours"); this is descriptive only, no p-value.
3. **22B pass-through cost** (`docs/06_blockade_frequency/line_22/`): the 21-vs-5 Saturday-slot comparison. Expect a wide CI — that is the point; report it as-is.
4. **Phase 09 — lines 9/97**: (a) travel-time delta of the regular variant during others'-blockade windows vs matched normal (per line); (b) variant-share comparison during vs outside blockade windows (permutation on the binary blocked indicator per slot).

## Outputs

- `docs/10_statistics/README.md`: a short methods section in plain language (what a permutation test and bootstrap CI are, why they suit small samples, the stratification rule, the block-as-unit caveat, seed), followed by **one results table**: comparison | n₁/n₂ | Δmean [95% CI] | Δmedian | permutation p | Cliff's δ | verdict. No code in the report.
- `docs/10_statistics/results.csv` with the same table machine-readable.
- **Annotate the existing figures**: add "Δ = X min [CI], p = Y (permutation)" to the caption of each figure whose comparison was tested (phase 05 deltas, phase 08 control figure, 22B cost panel, phase 09 delta figures). For the phase 08 figure, the caption also gets the breadth sentence ("delta positive in k of n hours" per line). Regenerate those figures; do not change anything else about them.
- Update each affected phase README with one sentence citing the result and linking to `docs/10_statistics/`.

## Interpretation rules for the README

- CI excluding 0 and p < 0.05 → "statistically supported"; otherwise → "suggestive, not conclusive" — use exactly this two-level language, no overclaiming.
- Where n is small (22B: n=5 control), say so next to the verdict.
- Add a one-line note that no multiple-comparisons correction was applied across the ~8 tests, and that results near p=0.05 should be read accordingly (or apply Benjamini-Hochberg and report both — implementer's choice, but say which).

## Verification

- Sanity: the permutation p for a comparison with an obviously huge gap (e.g. line 19's detour cost) should be very small; the 22B 21-vs-5 comparison should yield a wide CI. If either comes out otherwise, stop and debug before writing results.
- Cross-check Δmean values in `results.csv` against the deltas already printed in the existing READMEs/figures — they must match; if not, find out which computation diverged and reconcile before publishing.
- Update `docs/README.md` index with the new `10_statistics/` entry.
