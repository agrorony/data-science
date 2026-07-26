# 05 — Line 14: Baseline vs. Blocked/Special Variant (Control)

Method and headline finding: [docs/05_skip_comparison](../README.md).

**Revision round 3 (section B2): line 14 no longer appears in this
phase.** Its entire "blocked" bucket (11 merged variants, max count=4)
was singleton/near-singleton recording noise — near-full-length routes
missing just 1–6 stops out of 40, not real detours (see
[docs/07's addendum](../../07_blockade_investigation/README.md) on why
control lines had a nonzero "blocked" count at all under the new
>15-stop rule, and the main phase 05 README for the count>5 fix that
removes this noise from the phase's statistics). With zero blocks
clearing the significance floor, line 14 has no delta figure here.

**Revision round 4:** confirmed by direct investigation to be
stop-recording dropouts, not detours (see
[docs/06_blockade_frequency/line_14/blocked_slots_investigation.md](../../06_blockade_frequency/line_14/blocked_slots_investigation.md)).
`variant_type_v2` now classifies these variants `"noise"` at the source
instead of `"blocked"`, so line 14's absence here no longer depends on
this phase's own `count>5` floor — no numeric change.

**Answer:** no meaningful special-variant behavior exists for line 14 —
the apparent one in the first two revision rounds was entirely an
artifact of an over-permissive blocked-variant rule, not a real finding.

**Sources:** `govData/df_cleaned.csv`, `pipeline/plot_baseline_vs_blocked_delta.py`.
