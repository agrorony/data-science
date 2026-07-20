"""Phase 04 -- baseline (reference) variant figures, one per (line, direction).

**Revision round:** the reference variant is now the *merged* baseline
from `pipeline.variant_merges` (post section-A merges/exclusions), not
the raw stage4 reference -- e.g. line 19 direction_A's baseline now
folds in raw variants 0, 2 and 4 (n=1,205 combined). See
docs/03_variants for the merge table.

For each line/direction_group, builds a 3-panel figure:
  1. cumulative travel time along the stop sequence
  2. cumulative distance along the stop sequence
  3. total observed rides (n_observations) by day of week

Hours 25/26 are not involved here (this is stop-sequence, not
hour-of-day), but day-of-week is displayed with weekday names, not raw
integers (Global rules: no raw column names/codes on axes).

Output: rony/figures/baseline_<line>_<group>.png
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from pipeline import config, stage4_route_variants, variant_merges as vm
from pipeline.stage10_route_deviation_heatmaps import rtl

DAY_NAMES = {1: "Sun", 2: "Mon", 3: "Tue", 4: "Wed", 5: "Thu", 6: "Fri", 7: "Sat"}


def get_baseline_rows(df_cleaned: pd.DataFrame, variant_summary: pd.DataFrame, line: str, group: str):
    ref_row = variant_summary[
        (variant_summary["route_name"] == line)
        & (variant_summary["direction_group"] == group)
        & (variant_summary["is_reference"])
    ]
    if ref_row.empty:
        return None, None
    ref_id = int(ref_row.iloc[0]["route_variant_id"])
    sub = df_cleaned[
        (df_cleaned["route_name"] == line)
        & (df_cleaned["direction_group"] == group)
        & (df_cleaned["route_variant_id"] == ref_id)
    ]
    return sub, ref_row.iloc[0]


def plot_baseline(sub: pd.DataFrame, ref_row: pd.Series, line: str, group: str, stop_code_to_name: dict, path) -> None:
    by_stop = (
        sub.groupby("stop_sequence")
        .agg(
            stop_code=("stop_code", "first"),
            mean_time=("mean_cumulative_travel_time_min", "mean"),
            mean_dist=("mean_cumulative_distance_m", "mean"),
        )
        .sort_index()
    )
    stop_labels = [rtl(n) for n in stage4_route_variants.get_stop_names(by_stop["stop_code"].tolist(), stop_code_to_name)]

    by_day = sub.groupby("day_of_week")["n_observations"].sum().reindex(range(1, 8), fill_value=0)
    day_labels = [DAY_NAMES[d] for d in by_day.index]

    fig, axes = plt.subplots(
        4, 1, figsize=(15, 13),
        gridspec_kw={"height_ratios": [1, 1.3, 0.05, 0.8], "hspace": 0.55},
    )
    ax_time, ax_dist, ax_spacer, ax_day = axes
    ax_spacer.axis("off")
    ax_time.plot(range(len(by_stop)), by_stop["mean_time"], marker="o", color="#1D9E75", linewidth=1.5)
    ax_time.set_ylabel("Cumulative travel time (min)")
    ax_time.set_title(f"Baseline variant -- line {line} / {group}: cumulative travel time along the route")
    ax_time.set_xticks(range(len(by_stop)))
    ax_time.tick_params(labelbottom=False)
    ax_time.grid(alpha=0.3)

    ax_dist.plot(range(len(by_stop)), by_stop["mean_dist"], marker="o", color="#4C72B0", linewidth=1.5)
    ax_dist.set_ylabel("Cumulative distance (m)")
    ax_dist.set_title("Cumulative distance along the route (x-axis: stops, in route order)")
    ax_dist.set_xticks(range(len(by_stop)))
    ax_dist.set_xticklabels(stop_labels, rotation=60, ha="right", fontsize=6)
    ax_dist.grid(alpha=0.3)

    bars = ax_day.bar(day_labels, by_day.values, color="#DD8452")
    ax_day.set_ylabel("Total observed rides\n(n_observations, baseline variant only)")
    ax_day.set_title("Baseline-variant trip volume by day of week")
    ax_day.grid(alpha=0.3, axis="y")
    for b, v in zip(bars, by_day.values):
        if v > 0:
            ax_day.text(b.get_x() + b.get_width() / 2, v, f"{int(v):,}", ha="center", va="bottom", fontsize=8)

    ref_id = int(ref_row["route_variant_id"])
    n_stops = int(ref_row["n_stops"])
    n_blocks = int(ref_row["count"])
    end_time = by_stop["mean_time"].iloc[-1]
    end_dist = by_stop["mean_dist"].iloc[-1]
    fig.text(
        0.5, -0.01,
        f"How to read: variant {ref_id} is the most frequently observed stop sequence for this line/direction "
        f"({n_blocks:,} schedule blocks, {n_stops} stops) -- top two panels show how travel time and distance "
        f"accumulate stop-by-stop (end-to-end: {end_time:.1f} min, {end_dist:,.0f} m); bottom panel shows how many "
        "rides on this baseline variant were observed on each day of week.",
        ha="center", va="top", fontsize=8, wrap=True,
    )

    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def run() -> None:
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    df_cleaned = pd.read_csv(config.DF_CLEANED_PATH, low_memory=False)
    variant_summary = pd.read_csv(config.VARIANT_SUMMARY_PATH)
    effective_df, effective_summary = vm.build_effective_df_cleaned(df_cleaned, variant_summary)
    stop_code_to_name = stage4_route_variants.load_stop_code_to_name()

    for (line, group), _ in effective_summary.groupby(["route_name", "direction_group"]):
        sub, ref_row = get_baseline_rows(effective_df, effective_summary, line, group)
        if sub is None or sub.empty:
            print(f"line {line} / {group}: no baseline rows, skipped.")
            continue
        path = config.FIGURES_DIR / f"baseline_{line}_{group}.png"
        plot_baseline(sub, ref_row, str(line), group, stop_code_to_name, path)
        print(f"Saved -> {path}")


if __name__ == "__main__":
    run()
