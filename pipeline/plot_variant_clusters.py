"""After-clustering variant heatmaps for docs/03_variants.

Same green/white stop-presence grid as stage10_route_deviation_heatmaps
(the "before clustering" reproduction of avishagi's original
visualization), but rows are grouped and colour-coded by stage5's
cluster_id, so the effect of clustering is visible by flipping between
the stage10 figure (before) and this one (after).

One PNG per (line, direction_group) that has >=1 display-set variant:
rony/figures/variant_clusters_<line>_<group>.png
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap, to_rgb
from matplotlib.patches import Patch

from pipeline import config, stage4_route_variants
from pipeline.stage10_route_deviation_heatmaps import rtl

CLUSTER_PALETTE = ["#4C72B0", "#DD8452", "#8172B2", "#C44E52", "#937860", "#64B5CD"]
REFERENCE_COLOR = "#1D9E75"
REGULAR_COLOR = "#BBBBBB"


def _row_sort_key(row: pd.Series) -> tuple:
    if row["is_reference"]:
        return (0, "", -row["count"])
    if pd.notna(row["cluster_id"]):
        return (1, row["cluster_id"], -row["count"])
    return (2, "", -row["count"])


def build_clustered_heatmap(display_sub: pd.DataFrame, stop_code_to_name: dict[int, str]):
    display_sub = display_sub.copy()
    display_sub["_sort"] = display_sub.apply(_row_sort_key, axis=1)
    display_sub = display_sub.sort_values("_sort")

    longest = display_sub.loc[display_sub["n_stops"].idxmax()]
    all_codes = longest["route_sequence_str"].split("-")
    station_labels = stage4_route_variants.get_stop_names([int(c) for c in all_codes], stop_code_to_name)

    heatmap_data, labels_y, row_colors = [], [], []
    cluster_color_map: dict[str, str] = {}
    palette_cycle = list(CLUSTER_PALETTE)

    for _, row in display_sub.iterrows():
        codes = set(row["route_sequence_str"].split("-"))
        heatmap_data.append([1 if c in codes else 0 for c in all_codes])

        if row["is_reference"]:
            color, tag = REFERENCE_COLOR, "REFERENCE | "
        elif pd.notna(row["cluster_id"]):
            cid = row["cluster_id"]
            if cid not in cluster_color_map:
                cluster_color_map[cid] = palette_cycle[len(cluster_color_map) % len(palette_cycle)]
            color, tag = cluster_color_map[cid], f"{cid} | "
        else:
            color, tag = REGULAR_COLOR, "ungrouped | "

        row_colors.append(color)
        labels_y.append(f"variant {row['route_variant_id']} | {tag}n={row['count']} | {row['n_stops']} stops")

    return np.array(heatmap_data), labels_y, station_labels, row_colors, cluster_color_map


def plot_clustered_heatmap(heatmap_data, labels_y, station_labels, row_colors, cluster_color_map, line, group, path) -> None:
    cmap = ListedColormap(["#f7f7f7", "#1D9E75"])
    columns = [rtl(s) for s in station_labels]
    fig_height = max(4, 0.35 * len(labels_y) + 2)

    fig, (ax_colors, ax_heat) = plt.subplots(
        1, 2, figsize=(16.6, fig_height),
        gridspec_kw={"width_ratios": [0.025, 1], "wspace": 0.02},
    )

    color_arr = np.array([to_rgb(c) for c in row_colors]).reshape(-1, 1, 3)
    ax_colors.imshow(color_arr, aspect="auto")
    ax_colors.set_xticks([])
    ax_colors.set_yticks([])

    import seaborn as sns
    sns.heatmap(
        heatmap_data, cmap=cmap, vmin=0, vmax=1, cbar=False,
        xticklabels=columns, yticklabels=labels_y,
        linecolor="lightgrey", linewidths=0.3, ax=ax_heat,
    )
    ax_heat.set_xticklabels(ax_heat.get_xticklabels(), rotation=45, ha="right", fontsize=7)
    ax_heat.set_yticklabels(ax_heat.get_yticklabels(), fontsize=8)
    ax_heat.set_title(f"Route variants grouped by detour cluster -- line {line} / {group} (after clustering)")
    ax_heat.set_xlabel("Stations (longest observed route order)")
    ax_heat.set_ylabel("")

    legend = [Patch(color="#1D9E75", label="Stop present"), Patch(color="#f7f7f7", label="Stop missing")]
    legend.append(Patch(color=REFERENCE_COLOR, label="Reference variant (row colour band)"))
    for cid, color in cluster_color_map.items():
        legend.append(Patch(color=color, label=f"{cid} (row colour band)"))
    legend.append(Patch(color=REGULAR_COLOR, label="Ungrouped / regular variant (row colour band)"))
    ax_heat.legend(handles=legend, loc="upper right", bbox_to_anchor=(1.32, 1), fontsize=7)

    fig.text(
        0.5, -0.08,
        "How to read: each row is one observed stop sequence (variant); the left colour strip shows which "
        "detour cluster stage5 assigned it to (same colour = same likely closure/detour location); green cells "
        "are stops the variant visits, white cells are stops it skips relative to the longest observed route.",
        ha="center", va="top", fontsize=8, wrap=True,
    )

    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def run() -> None:
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    variant_summary = pd.read_csv(config.VARIANT_SUMMARY_PATH)
    stop_code_to_name = stage4_route_variants.load_stop_code_to_name()

    for (line, group), sub in variant_summary.groupby(["route_name", "direction_group"]):
        display_sub = sub[sub["in_display_set"]]
        if display_sub.empty:
            print(f"line {line} / {group}: nothing passed the display filter, skipped.")
            continue

        heatmap_data, labels_y, station_labels, row_colors, cluster_color_map = build_clustered_heatmap(
            display_sub, stop_code_to_name
        )
        path = config.FIGURES_DIR / f"variant_clusters_{line}_{group}.png"
        plot_clustered_heatmap(heatmap_data, labels_y, station_labels, row_colors, cluster_color_map, line, group, path)
        print(f"Saved -> {path} ({len(labels_y)} variants, {len(cluster_color_map)} clusters)")


if __name__ == "__main__":
    run()
