"""Figure 2 (merged) -- compact stop-presence comparison, 4 representative lines.

One panel per line (19, 9, 97, 15), single row, each showing its most
informative direction: whichever of direction_A/direction_B has the larger
(clearer) dominant detour gap for 19/9/97, and line 15's single "main"
route (no direction split, no significant detour -- shown as a contrast
case: what a non-divergent line's grid looks like).

Reuses variant_summary.csv and stage10_route_deviation_heatmaps's stop-name
lookup / presence-grid computation (build_group_heatmap, rtl) for the
actual data -- this script only restructures layout, plotting, and which
rows/columns get shown.

Output: docs/03_variants/fig2_stop_presence.png
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
import pandas as pd

from pipeline import config, stage4_route_variants, style  # noqa: F401 (style applies rcParams)
from pipeline.stage10_route_deviation_heatmaps import build_group_heatmap, rtl, HEBREW_FONT

RAW_COUNT_THRESHOLD = 5  # matches plot_variants_revised.py's own significance bar
OUT_PATH = config.REPO_ROOT / "docs" / "03_variants" / "fig2_stop_presence.png"
SELECTED_LINES = [19, 9, 97, 15]  # fixed order (subset of pipeline.style.LINE_ORDER)


def top_detour_n_missing(sig_group: pd.DataFrame) -> int:
    detours = sig_group[(~sig_group["is_reference"]) & (sig_group["n_missing"] >= 1)]
    if detours.empty:
        return -1
    return int(detours.sort_values("count", ascending=False).iloc[0]["n_missing"])


def choose_direction(sig: pd.DataFrame, line: int) -> str:
    """Whichever direction has the single dominant detour with the larger
    (clearer) stop-count gap; default to direction_A on a tie. Lines with
    only one direction group (e.g. line 15's "main") just use that."""
    directions = sorted(sig.loc[sig["route_name"] == line, "direction_group"].unique())
    if len(directions) == 1:
        return directions[0]
    gaps = {d: top_detour_n_missing(sig[(sig["route_name"] == line) & (sig["direction_group"] == d)]) for d in directions}
    return "direction_B" if gaps.get("direction_B", -1) > gaps.get("direction_A", -1) else "direction_A"


def cell_rows(sig_group: pd.DataFrame) -> pd.DataFrame:
    """Reference row + the single dominant (highest-count) variant that
    actually skips a stop, if one exists; reference-only otherwise."""
    ref = sig_group[sig_group["is_reference"]]
    detours = sig_group[(~sig_group["is_reference"]) & (sig_group["n_missing"] >= 1)]
    if detours.empty:
        return ref
    top_detour = detours.sort_values("count", ascending=False).iloc[[0]]
    return pd.concat([ref, top_detour])


def label_step(n_stops: int) -> int:
    """Every stop when there are few; every 2nd-4th otherwise -- 4 wide
    panels (instead of the earlier 10-panel grid) leave enough width per
    panel for this to stay legible."""
    if n_stops <= 15:
        return 1
    if n_stops <= 30:
        return 2
    if n_stops <= 45:
        return 3
    return 4


def draw_cell(ax, heatmap_data, row_labels: list[str], station_labels: list[str], title: str) -> None:
    cmap = ListedColormap(["#f7f7f7", "#1D9E75"])
    ax.imshow(heatmap_data, cmap=cmap, vmin=0, vmax=1, aspect="auto")

    n_stops = len(station_labels)
    step = label_step(n_stops)
    positions = list(range(0, n_stops, step))
    ax.set_xticks(positions)
    ax.set_xticklabels(
        [rtl(station_labels[i]) for i in positions],
        rotation=90, ha="center", fontsize=7.5, fontfamily=HEBREW_FONT,
    )
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=8)
    ax.set_title(title, fontsize=10, fontweight="semibold")
    ax.tick_params(length=0)


def run() -> None:
    variant_summary = pd.read_csv(config.VARIANT_SUMMARY_PATH)
    stop_code_to_name = stage4_route_variants.load_stop_code_to_name()
    sig = variant_summary[(variant_summary["is_reference"]) | (variant_summary["count"] > RAW_COUNT_THRESHOLD)]

    panels = []
    for line in SELECTED_LINES:
        direction = choose_direction(sig, line)
        group = sig[(sig["route_name"] == line) & (sig["direction_group"] == direction)]
        rows = cell_rows(group)
        n_missing = int(rows.loc[~rows["is_reference"], "n_missing"].max()) if (~rows["is_reference"]).any() else 0
        panels.append((line, direction, rows, n_missing))
        dir_label = "single reference route (no direction split)" if direction == "main" else f"direction {direction[-1]}"
        print(f"Line {line}: {dir_label}, {'reference-only' if n_missing == 0 else f'-{n_missing} stops'}")

    fig, axes = plt.subplots(1, len(panels), figsize=(13, 5.2))

    for ax, (line, direction, rows, n_missing) in zip(axes, panels):
        heatmap_data, _, station_labels = build_group_heatmap(rows, stop_code_to_name)
        row_labels = [
            "Reference" if r.is_reference else f"Detour (-{r.n_missing} stops)"
            for r in rows.itertuples()
        ]
        title = f"Line {line}" if direction == "main" else f"Line {line} · direction {direction[-1]}"
        draw_cell(ax, heatmap_data, row_labels, station_labels, title)

    legend = [Patch(color="#1D9E75", label="Present"), Patch(facecolor="#f7f7f7", edgecolor="#999999", label="Missing")]
    fig.legend(handles=legend, loc="upper center", bbox_to_anchor=(0.5, 0.97), fontsize=9, ncol=2)

    fig.suptitle("Route Deviations: Dominant Detour vs. Reference Route", fontsize=13, fontweight="bold", y=1.0)
    fig.tight_layout(rect=[0, 0.02, 1, 0.90])
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PATH, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved -> {OUT_PATH}")


if __name__ == "__main__":
    run()
