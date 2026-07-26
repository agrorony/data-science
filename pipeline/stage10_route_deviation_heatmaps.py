"""Stage 10 -- route deviation heatmaps (per line/direction group).

Reproduces the final visualization in
avishagi/bus_route_initial_filtering.ipynb (create_heatmap_data_v5 +
plot_routes_heatmap_v3): a green/white grid showing, for each route
variant that passed the display filter, which of the longest observed
route's stops it actually visits.

Uses the same combined filter already computed in stage4
(filter_for_display -> the `in_display_set` column in
govData/variant_summary.csv): stop-count within range of the reference
route AND (observed more than the min-count threshold OR skips a stop
the user flagged as critical for that line). The reference variant is
always included as the top row.

Generalized from the original (one line at a time, 4 lines total) to all
7 lines / 13 direction groups. One PNG per (line, direction_group):
rony/figures/route_deviation_heatmap_<line>_<group>.png
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

from pipeline import config, stage4_route_variants


def is_hebrew(text: str) -> bool:
    return any("֐" <= ch <= "׿" for ch in text)


def rtl(text: str) -> str:
    """Reverse genuine Hebrew for correct display; leave ASCII (e.g.
    'Unknown(1787)' fallbacks for stops missing from the name mapping) as-is."""
    return text[::-1] if is_hebrew(text) else text


# "Noto Sans Hebrew" is not installed in this environment (checked via
# matplotlib.font_manager); "David" is the best available Hebrew-capable
# fallback on this machine and renders the ASCII "Unknown(<code>)" labels
# fine too.
HEBREW_FONT = "David"
DENSE_LABEL_THRESHOLD = 15  # above this many stops, rotate 90 deg instead of 45


def build_group_heatmap(display_sub: pd.DataFrame, stop_code_to_name: dict[int, str]):
    display_sub = display_sub.sort_values(["is_reference", "count"], ascending=[False, False])

    longest = display_sub.loc[display_sub["n_stops"].idxmax()]
    all_codes = longest["route_sequence_str"].split("-")
    station_labels = stage4_route_variants.get_stop_names(
        [int(c) for c in all_codes], stop_code_to_name
    )

    heatmap_data = []
    labels_y = []
    for _, row in display_sub.iterrows():
        codes = set(row["route_sequence_str"].split("-"))
        heatmap_data.append([1 if c in codes else 0 for c in all_codes])
        tag = "REFERENCE | " if row["is_reference"] else ""
        labels_y.append(f"variant {row['route_variant_id']} | {tag}n={row['count']} | {row['n_stops']} stops")

    return np.array(heatmap_data), labels_y, station_labels


def heatmap_row_height(labels_y) -> float:
    """Height (inches) a single-panel figure/subplot row needs to fit
    `labels_y` rows of the green/white grid, floor at 4in."""
    return max(4, 0.35 * len(labels_y) + 2)


def draw_group_heatmap(ax, heatmap_data, labels_y, station_labels, title) -> None:
    """Draw the green/white stop-presence grid into an existing Axes,
    without creating or saving a figure -- lets callers compose multiple
    groups into one multi-panel figure (see plot_variants_revised.py)."""
    cmap = ListedColormap(["#f7f7f7", "#1D9E75"])
    columns = [rtl(s) for s in station_labels]

    sns.heatmap(
        heatmap_data, cmap=cmap, vmin=0, vmax=1, cbar=False,
        xticklabels=columns, yticklabels=labels_y,
        linecolor="lightgrey", linewidths=0.3, ax=ax,
    )
    dense = len(columns) > DENSE_LABEL_THRESHOLD
    rotation = 90 if dense else 45
    ax.set_xticklabels(
        ax.get_xticklabels(), rotation=rotation, ha="center" if dense else "right",
        fontsize=7, fontfamily=HEBREW_FONT,
    )
    ax.set_yticklabels(ax.get_yticklabels(), fontsize=8)
    ax.set_title(title)
    ax.set_xlabel("Stations (longest observed route order)")
    ax.set_ylabel("Route variants (sorted by occurrence count)")

    legend = [Patch(color="#1D9E75", label="Present"), Patch(color="#f7f7f7", label="Missing")]
    ax.legend(handles=legend, loc="upper right", bbox_to_anchor=(1.15, 1))


def plot_group_heatmap(heatmap_data, labels_y, station_labels, line, group, path) -> None:
    fig, ax = plt.subplots(figsize=(16, heatmap_row_height(labels_y)))
    draw_group_heatmap(ax, heatmap_data, labels_y, station_labels, f"Route deviations from reference -- line {line} / {group}")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
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

        heatmap_data, labels_y, station_labels = build_group_heatmap(display_sub, stop_code_to_name)
        path = config.FIGURES_DIR / f"route_deviation_heatmap_{line}_{group}.png"
        plot_group_heatmap(heatmap_data, labels_y, station_labels, line, group, path)
        print(f"Saved -> {path} ({len(labels_y)} variants, {len(station_labels)} stations)")


if __name__ == "__main__":
    run()
