"""Phase 09 -- do lines 9 and 97 behave differently during the confirmed
Aza-corridor closure windows established for lines 17/19/22?

**Revision round (sections C, H): rebuilt on the merged/excluded
variant set and the new absolute >15-stop blocked rule**
(`pipeline.variant_merges`, section B) instead of stage5's
fraction-based `variant_type` column, **both directions of each line
pooled into one distribution** (section C, no more per-direction
panels), and **reusing the updated 320-slot blockade window table from
docs/08** (`docs/08_control_lines_15_14/blockade_windows_used.csv`,
itself rebuilt in this revision round -- see docs/08's README for why
the window count grew from 112 to 320).

Lines 9 and 97 physically pass through/near the Aza St. corridor and
have their own real detour activity there (docs/03_variants/line_9,
docs/03_variants/line_97), but their variant clusters don't match the
exact stop set lines 17/19/22 lose. This module asks, for each of line
9 and line 97 (both directions pooled), during the confirmed blockade
windows:

(a) Route affected? -- does the line's own `variant_type_v2`
    non-baseline ("blocked") share differ between blockade-window
    blocks and matched-normal blocks? 2x2 proportion test (Fisher's
    exact when any expected cell < 5, chi-square with Yates correction
    otherwise), stratified Saturday / Weekday / Combined.

(b) Time affected on baseline? -- restricted to the line's own merged
    baseline variant (`variant_type_v2 == "reference"`), does
    end-to-end travel time differ between blockade-window and
    matched-normal blocks? Mann-Whitney U primary, Welch's t-test as a
    robustness check, `n_observations >= config.LOW_CONFIDENCE_THRESHOLD`,
    same three strata.

Not part of the regular stage0-10 pipeline run -- built for
docs/09_lines_9_97/README.md. Run with `python -m
pipeline.plot_line9_97_blockade_impact` from the repo root.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
from scipy import stats

from pipeline import config, variant_merges as vm, pooled_analysis as pa
from pipeline import plot_baseline_vs_blocked_delta as pbd

OUT_DIR = config.REPO_ROOT / "docs" / "09_lines_9_97"
WINDOWS_CSV = config.REPO_ROOT / "docs" / "08_control_lines_15_14" / "blockade_windows_used.csv"
MIN_N_FOR_TEST = 3
CATEGORIES = ["Saturday", "Weekday", "Combined"]


def load_windows() -> pd.DataFrame:
    """The updated blockade window table built in docs/08 from lines
    17/19/22's confirmed closures under the new >15-stop rule. Reused
    verbatim here so phases 08 and 09 never drift apart."""
    return pd.read_csv(WINDOWS_CSV)


def _distinct_blocks(df: pd.DataFrame, route_name: int) -> pd.DataFrame:
    """Both directions of `route_name` pooled (section C)."""
    scope = df[df["route_name"] == route_name]
    return scope.drop_duplicates(
        subset=["direction_group", "route_variant_id", "month", "day_of_week", "scheduled_departure_time"]
    ).copy()


def tag_windows(blocks: pd.DataFrame, windows: pd.DataFrame) -> pd.DataFrame:
    months_by_key = windows.groupby(["day_of_week", "scheduled_departure_time"])["month"].apply(set)
    category_by_key = windows.groupby(["day_of_week", "scheduled_departure_time"])["category"].first()

    keys = list(zip(blocks["day_of_week"], blocks["scheduled_departure_time"]))
    groups: list[str | None] = []
    categories: list[str | None] = []
    for key, month in zip(keys, blocks["month"]):
        if key not in months_by_key.index:
            groups.append(None)
            categories.append(None)
            continue
        flagged_months = months_by_key[key]
        groups.append("blockade" if month in flagged_months else "matched_normal")
        categories.append(category_by_key[key])

    out = blocks.copy()
    out["group"] = groups
    out["category"] = categories
    return out[out["group"].notna()]


# ---------------------------------------------------------------------------
# (a) Route affected: variant-share comparison
# ---------------------------------------------------------------------------


def _proportion_test(a: int, b: int, c: int, d: int) -> tuple[str, float]:
    table = np.array([[a, b], [c, d]])
    if table.sum() == 0 or table[0].sum() == 0 or table[1].sum() == 0 or table[:, 0].sum() == 0 or table[:, 1].sum() == 0:
        return "n/a", np.nan
    _, _, _, expected = stats.chi2_contingency(table, correction=True)
    if expected.min() < 5:
        _, p = stats.fisher_exact(table)
        return "Fisher exact", p
    _, p, _, _ = stats.chi2_contingency(table, correction=True)
    return "Chi-square (Yates)", p


def variant_share_comparison(tagged: pd.DataFrame, label: str) -> list[dict]:
    rows = []
    for category in CATEGORIES:
        sub = tagged if category == "Combined" else tagged[tagged["category"] == category]
        blk = sub[sub["group"] == "blockade"]
        norm = sub[sub["group"] == "matched_normal"]
        a = int((blk["variant_type_v2"] == "blocked").sum())
        n_blk = len(blk)
        c = int((norm["variant_type_v2"] == "blocked").sum())
        n_norm = len(norm)
        test_name, p = _proportion_test(a, n_blk - a, c, n_norm - c)
        rows.append(
            {
                "label": label, "category": category,
                "n_blockade": n_blk, "n_non_baseline_blockade": a, "share_blockade": a / n_blk if n_blk else np.nan,
                "n_normal": n_norm, "n_non_baseline_normal": c, "share_normal": c / n_norm if n_norm else np.nan,
                "test": test_name, "p_value": p,
            }
        )
    return rows


# ---------------------------------------------------------------------------
# (b) Time affected: travel-time comparison (baseline variant only)
# ---------------------------------------------------------------------------


def load_baseline_blocks(effective_df: pd.DataFrame, route_name: int, min_n: int) -> pd.DataFrame:
    """End-to-end travel time per (direction, month, day_of_week, hour)
    block, both directions pooled, restricted to the line's own merged
    baseline variant and n_observations >= min_n (CLAUDE.md issue #6)."""
    scope = effective_df[
        (effective_df["route_name"] == route_name)
        & (effective_df["variant_type_v2"] == "reference")
        & (effective_df["n_observations"] >= min_n)
    ]
    last_stop = (
        scope.sort_values("stop_sequence")
        .groupby(["direction_group", "route_variant_id", "month", "day_of_week", "scheduled_departure_time"])
        .tail(1)
        .copy()
    )
    last_stop["hour_display"] = last_stop["scheduled_departure_time"].replace({25: 1, 26: 2})
    return last_stop


def compare_travel_time(tagged: pd.DataFrame, label: str) -> list[dict]:
    rows = []
    for category in CATEGORIES:
        sub = tagged if category == "Combined" else tagged[tagged["category"] == category]
        blk = sub.loc[sub["group"] == "blockade", "mean_cumulative_travel_time_min"]
        norm = sub.loc[sub["group"] == "matched_normal", "mean_cumulative_travel_time_min"]
        row = {"label": label, "category": category, "n_blockade": len(blk), "n_normal": len(norm)}
        if len(blk) >= MIN_N_FOR_TEST and len(norm) >= MIN_N_FOR_TEST:
            u = stats.mannwhitneyu(blk, norm, alternative="two-sided")
            t = stats.ttest_ind(blk, norm, equal_var=False)
            row.update({"median_blockade": blk.median(), "median_normal": norm.median(), "delta_median_min": blk.median() - norm.median(), "mwu_p": u.pvalue, "ttest_p": t.pvalue})
        else:
            row.update({"median_blockade": blk.median() if len(blk) else np.nan, "median_normal": norm.median() if len(norm) else np.nan, "delta_median_min": np.nan, "mwu_p": np.nan, "ttest_p": np.nan})
        rows.append(row)
    return rows


def _stars(p: float) -> str:
    if p is None or np.isnan(p):
        return ""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"


# ---------------------------------------------------------------------------
# Figures (single pooled panel per line -- section C removes the
# per-direction grid, but the plotting functions still accept a list of
# labels so they degrade gracefully to one column/row)
# ---------------------------------------------------------------------------


def plot_variant_share(share_rows: list[dict], line_label: str, out_path) -> None:
    fig, ax = plt.subplots(figsize=(6.5, 5))

    cats = [r["category"] for r in share_rows]
    x = np.arange(len(cats))
    width = 0.35
    blk_shares = [100 * r["share_blockade"] if not np.isnan(r["share_blockade"]) else 0 for r in share_rows]
    norm_shares = [100 * r["share_normal"] if not np.isnan(r["share_normal"]) else 0 for r in share_rows]

    bars_blk = ax.bar(x - width / 2, blk_shares, width, color="#d62728", alpha=0.75, label="Blockade window")
    bars_norm = ax.bar(x + width / 2, norm_shares, width, color="#1f77b4", alpha=0.75, label="Matched normal")

    for bar, r in zip(bars_blk, share_rows):
        ax.annotate(f"n={r['n_blockade']}", xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=8)
    for bar, r in zip(bars_norm, share_rows):
        ax.annotate(f"n={r['n_normal']}", xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=8)

    for i, r in enumerate(share_rows):
        p = r["p_value"]
        label_txt = f"p={p:.3f} {_stars(p)}" if not np.isnan(p) else "n/a"
        ax.text(i, max(blk_shares[i], norm_shares[i]) + 6, label_txt, ha="center", fontsize=8, style="italic")

    ax.set_xticks(x)
    ax.set_xticklabels(cats)
    ax.set_title(f"{line_label} (both directions pooled)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Non-baseline (blocked) share of blocks (%)")
    ax.set_ylim(0, max(max(blk_shares, default=0), max(norm_shares, default=0)) + 20)
    ax.grid(True, alpha=0.3, axis="y")
    ax.legend(fontsize=8)

    caption = (
        f"How to read: percentage of {line_label} blocks (any hour-slot, any variant, both directions pooled) "
        f"whose merged variant is 'blocked' under the new >15-stop rule, compared between confirmed Aza-corridor "
        f"blockade-window hours and matched-normal hours (same day-of-week/scheduled hour, non-flagged month). "
        f"n = total blocks in each group; p-value from Fisher's exact or chi-square (Yates-corrected) test."
    )
    fig.suptitle(f"{line_label}: Own Route-Variant (Detour) Share, Blockade Window vs Matched Normal", fontsize=12, y=1.08)
    fig.text(0.5, -0.06, caption, ha="center", fontsize=8, style="italic", wrap=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_travel_time(tagged: pd.DataFrame, stats_rows: list[dict], line_label: str, out_path) -> None:
    fig, axes = plt.subplots(1, len(CATEGORIES), figsize=(13, 4.6), sharey=False)

    for j, category in enumerate(CATEGORIES):
        ax = axes[j]
        sub = tagged if category == "Combined" else tagged[tagged["category"] == category]
        blk = sub.loc[sub["group"] == "blockade", "mean_cumulative_travel_time_min"]
        norm = sub.loc[sub["group"] == "matched_normal", "mean_cumulative_travel_time_min"]

        data = [blk.values, norm.values]
        bp = ax.boxplot(data, tick_labels=["Blockade\nwindow", "Matched\nnormal"], patch_artist=True, widths=0.55, showfliers=True)
        bp["boxes"][0].set_facecolor("#d62728")
        bp["boxes"][0].set_alpha(0.65)
        if len(bp["boxes"]) > 1:
            bp["boxes"][1].set_facecolor("#1f77b4")
            bp["boxes"][1].set_alpha(0.65)

        row = next(r for r in stats_rows if r["category"] == category)
        if len(blk) >= MIN_N_FOR_TEST and len(norm) >= MIN_N_FOR_TEST:
            ax.set_title(f"n={len(blk)} vs n={len(norm)}\nMWU p={row['mwu_p']:.3f} {_stars(row['mwu_p'])}", fontsize=9)
        else:
            ax.set_title(f"n={len(blk)} vs n={len(norm)} (insufficient for testing)", fontsize=9)

        if j == 0:
            ax.set_ylabel(f"{line_label}\nTravel time (min)", fontsize=9)
        ax.annotate(category, xy=(0.5, 1.15), xycoords="axes fraction", ha="center", fontsize=11, fontweight="bold")
        ax.grid(True, alpha=0.3, axis="y")
        ax.tick_params(axis="x", labelsize=8)

    legend_handles = [
        Patch(facecolor="#d62728", alpha=0.65, label="Blockade window (Aza-corridor closure confirmed on 17/19/22)"),
        Patch(facecolor="#1f77b4", alpha=0.65, label="Matched normal (same day-of-week/hour, non-flagged month)"),
    ]
    fig.legend(handles=legend_handles, loc="lower center", ncol=2, fontsize=9, bbox_to_anchor=(0.5, -0.05))

    caption = (
        f"How to read: each panel compares {line_label}'s own end-to-end travel-time distribution (merged baseline "
        f"variant only, both directions pooled, n_observations >= {config.LOW_CONFIDENCE_THRESHOLD}) in confirmed "
        f"blockade-window hours vs matched normal hours; Mann-Whitney U tests whether the two distributions differ."
    )
    fig.suptitle(f"{line_label}: Travel-Time Distribution, Blockade Window vs Matched Normal Window", fontsize=13, y=1.08)
    fig.text(0.5, -0.1, caption, ha="center", fontsize=9, style="italic", wrap=True)
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Section D (revision round 2) -- own detour vs. absorbing others' blockade
# ---------------------------------------------------------------------------


def own_blocked_slots(effective_df: pd.DataFrame, route_name: int) -> set:
    """(month, day_of_week, scheduled_departure_time) slots where this
    line itself (any direction/variant) ran a blocked variant."""
    scope = effective_df[
        (effective_df["route_name"] == route_name) & (effective_df["variant_type_v2"] == "blocked")
    ]
    return set(zip(scope["month"], scope["day_of_week"], scope["scheduled_departure_time"]))


def exclude_own_blocked_slots(windows: pd.DataFrame, own_slots: set) -> pd.DataFrame:
    keys = list(zip(windows["month"], windows["day_of_week"], windows["scheduled_departure_time"]))
    keep = [k not in own_slots for k in keys]
    return windows[keep].reset_index(drop=True)


def plot_own_vs_absorbed_delta(line_label: str, route_name: int, effective_df: pd.DataFrame, windows: pd.DataFrame, out_path) -> dict:
    """Section D -- two curves per line: red = own detour (blocked variant
    minus baseline, hours the line itself ran the blocked variant); blue =
    staying on its own baseline route during confirmed lines 17/19/22
    blockade windows where this line itself was NOT blocked (absorbing the
    traffic instead of detouring)."""
    endpoints = pa.block_endpoints(effective_df)
    baseline_ep = pa.baseline_endpoints(endpoints, route_name=route_name)
    blocked_ep = pa.blocked_endpoints(endpoints, route_name=route_name)

    red_delta = pd.Series(dtype=float)
    red_thin_hours: list = []
    if not blocked_ep.empty and not baseline_ep.empty:
        red_delta, red_thin_hours, _ = pbd.compute_delta(baseline_ep, blocked_ep)

    own_slots = own_blocked_slots(effective_df, route_name)
    absorb_windows = exclude_own_blocked_slots(windows, own_slots)
    baseline_ep_dropped = pa.drop_late_night_hours(baseline_ep)
    tagged = tag_windows(baseline_ep_dropped, absorb_windows)

    blue_delta = pd.Series(dtype=float)
    blue_thin_hours: list = []
    n_absorb_blockade = n_absorb_normal = 0
    absorb_overall_delta = None
    if not tagged.empty:
        agg = tagged.groupby(["scheduled_departure_time", "group"])["end_time_min"].median().unstack()
        n_by_group = tagged.groupby(["scheduled_departure_time", "group"])["end_time_min"].size().unstack()
        if "blockade" in agg.columns and "matched_normal" in agg.columns:
            blue_delta = (agg["blockade"] - agg["matched_normal"]).dropna().sort_index()
            blue_n = n_by_group.get("blockade", pd.Series(dtype=int))
            blue_thin_hours = [h for h in blue_delta.index if blue_n.get(h, 0) < pbd.THIN_THRESHOLD]
        n_absorb_blockade = int((tagged["group"] == "blockade").sum())
        n_absorb_normal = int((tagged["group"] == "matched_normal").sum())
        if n_absorb_blockade and n_absorb_normal:
            absorb_overall_delta = round(
                tagged.loc[tagged["group"] == "blockade", "end_time_min"].median()
                - tagged.loc[tagged["group"] == "matched_normal", "end_time_min"].median(),
                1,
            )

    fig, ax = plt.subplots(figsize=(10, 5.5))

    band_labeled_red = False
    for hr in red_thin_hours:
        ax.axvspan(hr - 0.4, hr + 0.4, color="#d62728", alpha=0.10, zorder=0, label="Thin data, own detour (<8 blocks)" if not band_labeled_red else "")
        band_labeled_red = True
    band_labeled_blue = False
    for hr in blue_thin_hours:
        ax.axvspan(hr - 0.4, hr + 0.4, color="#1f77b4", alpha=0.10, zorder=0, label="Thin data, absorbing (<8 blocks)" if not band_labeled_blue else "")
        band_labeled_blue = True

    if not red_delta.empty:
        ax.plot(red_delta.index, red_delta.values, color="#d62728", linewidth=2.2, marker="o", markersize=5, label="Own detour: blocked variant minus baseline")
    if not blue_delta.empty:
        ax.plot(blue_delta.index, blue_delta.values, color="#1f77b4", linewidth=2.2, marker="s", markersize=5, label="Staying on route during others' blockade: blockade window minus matched normal")

    ax.axhline(0, color="black", linewidth=1, linestyle="--", alpha=0.6)
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Extra travel time (min)")
    ax.set_title(f"{line_label}: Own Detour vs. Staying on Route During Others' Blockades", fontsize=12, fontweight="bold")
    ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0)
    ax.grid(True, alpha=0.3)

    n_own_blocked, n_own_baseline = len(blocked_ep), len(baseline_ep)
    own_overall_delta = (
        round(blocked_ep["end_time_min"].median() - baseline_ep["end_time_min"].median(), 1)
        if n_own_blocked and n_own_baseline else None
    )

    caption = (
        f"How to read: red = {line_label}'s own blocked/special variant minus its own baseline variant, both "
        f"directions pooled, in hours {line_label} itself ran the blocked variant (n={n_own_blocked} blocked vs "
        f"n={n_own_baseline} baseline blocks). Blue = {line_label}'s own baseline-variant travel time in confirmed "
        f"lines 17/19/22 blockade windows minus matched-normal hours, restricted to windows where {line_label} "
        f"itself stayed on its baseline route (n={n_absorb_blockade} blockade vs n={n_absorb_normal} matched-normal "
        f"blocks). Positive = slower than usual; shaded bands mark hours with fewer than {pbd.THIN_THRESHOLD} "
        f"observations in that curve's own category."
    )
    fig.text(0.5, -0.08, caption, ha="center", va="top", fontsize=8, wrap=True)
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)

    return {
        "route_name": route_name,
        "n_own_blocked": n_own_blocked, "n_own_baseline": n_own_baseline, "own_overall_delta_min": own_overall_delta,
        "n_absorb_blockade": n_absorb_blockade, "n_absorb_normal": n_absorb_normal, "absorb_overall_delta_min": absorb_overall_delta,
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df_cleaned = pd.read_csv(config.DF_CLEANED_PATH, low_memory=False)
    variant_summary = pd.read_csv(config.VARIANT_SUMMARY_PATH)
    effective_df, _ = vm.build_effective_df_cleaned(df_cleaned, variant_summary)
    windows = load_windows()

    lines = [("Line 9", 9), ("Line 97", 97)]

    all_share_rows: list[dict] = []
    all_time_rows: list[dict] = []

    for line_label, route_name in lines:
        # (a) route affected -- all distinct blocks, any variant, both directions pooled
        all_blocks = _distinct_blocks(effective_df, route_name)
        tagged_all = tag_windows(all_blocks, windows)
        share_rows = variant_share_comparison(tagged_all, line_label)
        all_share_rows.extend(share_rows)

        share_path = OUT_DIR / f"{line_label.lower().replace(' ', '_')}_variant_share_comparison.png"
        plot_variant_share(share_rows, line_label, share_path)
        print(f"Saved -> {share_path}")

        # (b) time affected -- baseline-only blocks, both directions pooled
        baseline_blocks = load_baseline_blocks(effective_df, route_name, config.LOW_CONFIDENCE_THRESHOLD)
        tagged_baseline = tag_windows(baseline_blocks, windows)
        time_rows = compare_travel_time(tagged_baseline, line_label)
        all_time_rows.extend(time_rows)

        time_path = OUT_DIR / f"{line_label.lower().replace(' ', '_')}_travel_time_comparison.png"
        plot_travel_time(tagged_baseline, time_rows, line_label, time_path)
        print(f"Saved -> {time_path}")

    # (D) revision round 2 -- own detour vs. absorbing others' blockade
    delta_rows: list[dict] = []
    for line_label, route_name in lines:
        delta_path = OUT_DIR / f"line_{route_name}_blockade_delta.png"
        row = plot_own_vs_absorbed_delta(line_label, route_name, effective_df, windows, delta_path)
        delta_rows.append(row)
        print(f"Saved -> {delta_path}  ({row})")

    share_stats_df = pd.DataFrame(all_share_rows)
    share_csv = OUT_DIR / "variant_share_stats.csv"
    share_stats_df.to_csv(share_csv, index=False)
    print(f"Saved -> {share_csv}")
    print(share_stats_df.to_string(index=False))

    time_stats_df_all = pd.DataFrame(all_time_rows)
    time_csv = OUT_DIR / "travel_time_stats.csv"
    time_stats_df_all.to_csv(time_csv, index=False)
    print(f"Saved -> {time_csv}")
    print(time_stats_df_all.to_string(index=False))


if __name__ == "__main__":
    run()
