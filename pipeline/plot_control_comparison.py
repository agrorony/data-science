"""Phase 08 -- indirect impact of Aza-corridor closures on control lines 14/15.

**Revision round (sections C, G):** rebuilt on the merged/excluded
variant set and the new absolute >15-stop blocked rule
(`pipeline.variant_merges`, section B) instead of stage5's original
fraction-based `variant_type` column -- this removes the need for the
old line-22-direction_A special case (its real closure variant now
clears the new rule on its own). Both directions of line 14 are now
pooled into a single distribution (section C; line 15 already has no
direction split). Only the delta chart is kept per control line (top
panel of the original two-panel figure) -- the boxplot/distribution
comparison and the per-direction hourly-pattern files have been
removed (section G).

A (month, day_of_week, scheduled_departure_time) slot counts as a
confirmed Aza-corridor blockade window if lines 17, 19, or 22 (either
direction) has `variant_type_v2 == "blocked"` for that exact slot.

For each control line, every baseline block (`variant_type_v2 ==
"reference"`, `n_observations >= config.LOW_CONFIDENCE_THRESHOLD`)
whose (day_of_week, hour) matches a flagged window is tagged "blockade"
if its own month is one of the flagged months for that (day_of_week,
hour) pair, or "matched_normal" if it shares the same (day_of_week,
hour) but comes from a non-flagged month. Blocks whose (day_of_week,
hour) never appears among the flagged windows at all are dropped.

Not part of the regular stage0-10 pipeline run -- built for
docs/08_control_lines_15_14/README.md.
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from pipeline import config, variant_merges as vm, pooled_analysis as pa

OUT_DIR = config.REPO_ROOT / "docs" / "08_control_lines_15_14"
MIN_N_FOR_TEST = 3
SOURCE_LINES = [17, 19, 22]


def build_blockade_windows(effective_df: pd.DataFrame) -> pd.DataFrame:
    """Every (month, day_of_week, scheduled_departure_time) slot where
    lines 17/19/22 (either direction) have a `blocked` merged variant,
    per the new section-B rule. Returns one row per distinct slot,
    tagged with a coarse `category` (Saturday / Weekday)."""
    scope = effective_df[effective_df["route_name"].isin(SOURCE_LINES)]
    blocks = scope.drop_duplicates(
        subset=["route_name", "direction_group", "route_variant_id", "month", "day_of_week", "scheduled_departure_time"]
    )
    blocked = blocks[blocks["variant_type_v2"] == "blocked"]
    windows = blocked[["month", "day_of_week", "scheduled_departure_time"]].drop_duplicates().reset_index(drop=True)
    windows["category"] = np.where(windows["day_of_week"] == 7, "Saturday", "Weekday")
    return windows


def load_baseline_blocks(effective_df: pd.DataFrame, route_name: int, min_n: int) -> pd.DataFrame:
    """Control line's own end-to-end travel time per (month,
    day_of_week, hour) block, both directions pooled, restricted to the
    merged baseline variant and n_observations >= min_n (CLAUDE.md
    issue #6)."""
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


def compare_groups(tagged: pd.DataFrame, label: str) -> list[dict]:
    rows = []
    for category in ["Saturday", "Weekday", "Combined"]:
        sub = tagged if category == "Combined" else tagged[tagged["category"] == category]
        blk = sub.loc[sub["group"] == "blockade", "mean_cumulative_travel_time_min"]
        norm = sub.loc[sub["group"] == "matched_normal", "mean_cumulative_travel_time_min"]
        row = {"label": label, "category": category, "n_blockade": len(blk), "n_normal": len(norm)}
        if len(blk) >= MIN_N_FOR_TEST and len(norm) >= MIN_N_FOR_TEST:
            u = stats.mannwhitneyu(blk, norm, alternative="two-sided")
            t = stats.ttest_ind(blk, norm, equal_var=False)
            row.update(
                {
                    "median_blockade": blk.median(),
                    "median_normal": norm.median(),
                    "delta_median_min": blk.median() - norm.median(),
                    "mwu_p": u.pvalue,
                    "ttest_p": t.pvalue,
                }
            )
        else:
            row.update({"median_blockade": blk.median() if len(blk) else np.nan, "median_normal": norm.median() if len(norm) else np.nan, "delta_median_min": np.nan, "mwu_p": np.nan, "ttest_p": np.nan})
        rows.append(row)
    return rows


def plot_hourly_delta(tagged: pd.DataFrame, out_path, title: str, stats_rows: list[dict]) -> None:
    """Delta-chart-only version (section G): just the top panel of the
    original two-panel figure -- per-hour gap, dashed zero line, grey
    shading over Saturday-only window hours."""
    agg = (
        tagged.groupby(["hour_display", "group"])["mean_cumulative_travel_time_min"]
        .median()
        .unstack()
    )
    sat_hours = sorted(tagged.loc[tagged["category"] == "Saturday", "hour_display"].unique())

    fig, ax = plt.subplots(figsize=(10, 5.5))

    if "blockade" in agg.columns and "matched_normal" in agg.columns:
        delta = (agg["blockade"] - agg["matched_normal"]).dropna().sort_index()
        ax.plot(delta.index, delta.values, color="#d62728", linewidth=2.5, marker="o", markersize=5, label="Blockade window minus matched normal")
    ax.axhline(0, color="black", linewidth=1, linestyle="--", alpha=0.6)

    band_labeled = False
    for hr in sat_hours:
        ax.axvspan(hr - 0.4, hr + 0.4, color="grey", alpha=0.18, zorder=0, label="Saturday-only window hour" if not band_labeled else "")
        band_labeled = True

    ax.set_xlabel("Hour of day (25/26 shown as 01:00/02:00 next day)")
    ax.set_ylabel("Extra travel time in blockade window (min)")
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    combined = next(r for r in stats_rows if r["category"] == "Combined")
    p_str = f"{combined['mwu_p']:.3f}" if not np.isnan(combined["mwu_p"]) else "n/a (insufficient n)"
    caption = (
        f"How to read: per-hour median-travel-time gap between confirmed Aza-corridor blockade-window months "
        f"(lines 17/19/22, either direction, new >15-stop blocked rule) and matched normal months at the same "
        f"day-of-week/hour, both directions of this control line pooled. Combined (all flagged hours pooled): "
        f"n={combined['n_blockade']} blockade blocks vs n={combined['n_normal']} matched-normal blocks, "
        f"Mann-Whitney U p={p_str}."
    )
    fig.text(0.5, -0.05, caption, ha="center", fontsize=8, wrap=True)
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def run() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df_cleaned = pd.read_csv(config.DF_CLEANED_PATH, low_memory=False)
    variant_summary = pd.read_csv(config.VARIANT_SUMMARY_PATH)
    effective_df, _ = vm.build_effective_df_cleaned(df_cleaned, variant_summary)

    windows = build_blockade_windows(effective_df)
    print(f"Blockade windows (new rule, lines 17/19/22 pooled): {len(windows)} distinct slots "
          f"({(windows['category'] == 'Saturday').sum()} Saturday, {(windows['category'] == 'Weekday').sum()} Weekday)")

    targets = [("Line 15", 15), ("Line 14", 14)]

    stats_rows: list[dict] = []
    for label, route_name in targets:
        blocks = load_baseline_blocks(effective_df, route_name, config.LOW_CONFIDENCE_THRESHOLD)
        tagged = tag_windows(blocks, windows)
        label_stats = compare_groups(tagged, label)
        stats_rows.extend(label_stats)

        title = f"{label}: Travel-Time Delta, Confirmed Blockade Window vs Matched Normal (Both Directions Pooled)"
        out_path = OUT_DIR / f"{label.lower().replace(' ', '_')}_hourly_pattern.png"
        plot_hourly_delta(tagged, out_path, title, label_stats)
        print(f"Saved -> {out_path}")

    stats_df = pd.DataFrame(stats_rows)
    stats_csv = OUT_DIR / "control_comparison_stats.csv"
    stats_df.to_csv(stats_csv, index=False)
    print(f"Saved -> {stats_csv}")
    print(stats_df.to_string(index=False))

    windows_csv = OUT_DIR / "blockade_windows_used.csv"
    windows.to_csv(windows_csv, index=False)
    print(f"Saved -> {windows_csv}")


if __name__ == "__main__":
    run()
