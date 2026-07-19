"""Stage 8 -- per-line, per-cluster detour frequency figures.

Generalizes rony/variant_analysis.ipynb's protest-frequency heatmap from
"one blended fraction per line" to one frequency profile per detected
detour cluster (see stage5_variant_classification.py), so a line with
multiple distinct closure locations (e.g. line 97) gets a separate
figure/panel per location instead of averaging them together.

For each (route_name, direction_group, cluster_id) with variant_type ==
"blocked", computes the fraction of (month, day, hour) blocks that used a
variant in that cluster, and plots a month x day heatmap plus an
hour-of-day bar chart. Saved as one figure per line under rony/figures/,
named detour_frequency_<line>.png (all of a line's clusters/directions as
subplots in one file, since that's how the report will reference them).
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from pipeline import config

DAY_LABELS = {1: "Sun", 2: "Mon", 3: "Tue", 4: "Wed", 5: "Thu", 6: "Fri", 7: "Sat"}


def load_data() -> pd.DataFrame:
    df = pd.read_csv(config.VARIANT_SUMMARY_PATH)
    cleaned = pd.read_csv(
        config.DF_CLEANED_PATH,
        usecols=["route_name", "direction_group", "route_variant_id", "month", "day_of_week", "scheduled_departure_time"],
    )
    cleaned = cleaned.drop_duplicates()
    cleaned["hour_display"] = cleaned["scheduled_departure_time"].replace({25: 1, 26: 2})
    cleaned["day_label"] = cleaned["day_of_week"].map(DAY_LABELS)
    return df, cleaned


def cluster_frequency(variant_summary: pd.DataFrame, blocks: pd.DataFrame, line, group, cluster_id) -> pd.DataFrame:
    variant_ids = variant_summary[
        (variant_summary["route_name"] == line)
        & (variant_summary["direction_group"] == group)
        & (variant_summary["cluster_id"] == cluster_id)
    ]["route_variant_id"]

    scope = blocks[(blocks["route_name"] == line) & (blocks["direction_group"] == group)]
    total_blocks = scope.groupby(["month", "day_label"]).size()

    cluster_blocks = scope.merge(
        pd.DataFrame({"route_variant_id": variant_ids}), on="route_variant_id"
    )
    cluster_counts = cluster_blocks.groupby(["month", "day_label"]).size()

    freq = (cluster_counts / total_blocks).fillna(0).rename("fraction").reset_index()
    return freq, cluster_blocks


def run() -> None:
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    variant_summary, blocks = load_data()

    clusters = (
        variant_summary[variant_summary["variant_type"] == "blocked"]
        .dropna(subset=["cluster_id"])[["route_name", "direction_group", "cluster_id"]]
        .drop_duplicates()
    )

    if clusters.empty:
        print("No 'blocked' clusters found -- nothing to plot for stage8.")
        return

    for line, line_clusters in clusters.groupby("route_name"):
        n = len(line_clusters)
        fig, axes = plt.subplots(n, 2, figsize=(11, 3.2 * n), squeeze=False)

        for i, (_, row) in enumerate(line_clusters.iterrows()):
            group, cluster_id = row["direction_group"], row["cluster_id"]
            freq, cluster_blocks = cluster_frequency(variant_summary, blocks, line, group, cluster_id)

            day_order = list(DAY_LABELS.values())
            pivot = freq.pivot(index="day_label", columns="month", values="fraction").reindex(day_order)
            im = axes[i, 0].imshow(pivot.values, aspect="auto", cmap="Reds", vmin=0, vmax=1)
            axes[i, 0].set_yticks(range(len(pivot.index)))
            axes[i, 0].set_yticklabels(pivot.index)
            axes[i, 0].set_xticks(range(len(pivot.columns)))
            axes[i, 0].set_xticklabels(pivot.columns)
            axes[i, 0].set_title(f"line {line} / {group} / {cluster_id}: detour fraction by month x day", fontsize=8)

            by_hour = cluster_blocks.groupby("hour_display").size()
            axes[i, 1].bar(by_hour.index, by_hour.values, color="firebrick")
            axes[i, 1].set_title(f"line {line} / {group} / {cluster_id}: occurrences by hour", fontsize=8)

        fig.suptitle(f"Line {line} -- detour cluster frequency (generalizes the old single 'protest fraction' per line)")
        fig.tight_layout(rect=[0, 0, 1, 0.95])
        out_path = config.FIGURES_DIR / f"detour_frequency_{line}.png"
        fig.savefig(out_path, dpi=120)
        plt.close(fig)
        print(f"Saved -> {out_path} ({n} cluster panel(s))")


if __name__ == "__main__":
    run()
