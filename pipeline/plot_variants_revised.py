"""Revision round A -- phase 03 replacement: drop clustering entirely,
show only variants observed more than 5 times (n>5), then a second grid
after applying the manual merges/exclusions in
govData/variant_merges.json.

Same green/white stop-presence grid look as
stage10_route_deviation_heatmaps.py (which reproduces
avishagi/bus_route_initial_filtering.ipynb exactly) -- only the variant
*selection* rule changes (n>5 instead of stage4's filter_for_display
heuristic), not the visual style.

**Revision round 2, section A.2:** one figure per line, not per
(line, direction) -- vertical subplots, direction_A on top / direction_B
below, suptitle = the line name. Single-direction lines (15) get a
one-panel figure with the same title style.

Output: docs/03_variants/line_<line>/variants_raw.png and
docs/03_variants/line_<line>/variants_merged.png
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from pipeline import config, stage4_route_variants, variant_merges as vm
from pipeline.stage10_route_deviation_heatmaps import build_group_heatmap, draw_group_heatmap, heatmap_row_height

RAW_COUNT_THRESHOLD = 5
OUT_DIR = config.REPO_ROOT / "docs" / "03_variants"


def _display_rows(sub: pd.DataFrame) -> pd.DataFrame:
    return sub[(sub["is_reference"]) | (sub["count"] > RAW_COUNT_THRESHOLD)]


def plot_line_figure(line, group_frames: list[tuple[str, pd.DataFrame]], stop_code_to_name: dict, label_suffix: str, path) -> None:
    """group_frames: [(direction_group, display_sub), ...] in display
    order, already filtered to the n>5-or-reference display set. Skips
    empty groups; skips the whole figure if nothing survives."""
    panels = []
    for group_name, sub in group_frames:
        if sub.empty:
            print(f"line {line} / {group_name}: nothing clears n>{RAW_COUNT_THRESHOLD}, skipped ({label_suffix}).")
            continue
        heatmap_data, labels_y, station_labels = build_group_heatmap(sub, stop_code_to_name)
        panels.append((group_name, heatmap_data, labels_y, station_labels))

    if not panels:
        print(f"line {line}: no panels survive for {label_suffix}, figure skipped.")
        return

    heights = [heatmap_row_height(labels_y) for _, _, labels_y, _ in panels]
    fig, axes = plt.subplots(
        len(panels), 1, figsize=(16, sum(heights) + 0.6),
        gridspec_kw={"height_ratios": heights},
        squeeze=False,
    )
    for ax_row, (group_name, heatmap_data, labels_y, station_labels) in zip(axes[:, 0], panels):
        draw_group_heatmap(ax_row, heatmap_data, labels_y, station_labels, f"{group_name} ({label_suffix})")

    fig.suptitle(f"Line {line}", fontsize=16, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(path, dpi=120)
    plt.close(fig)
    print(f"Saved -> {path} ({len(panels)} panel(s): {[p[0] for p in panels]})")


def run() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    variant_summary = pd.read_csv(config.VARIANT_SUMMARY_PATH)
    stop_code_to_name = stage4_route_variants.load_stop_code_to_name()

    effective_summary = vm.build_effective_variant_summary(variant_summary)

    for line in sorted(variant_summary["route_name"].unique(), key=lambda x: (len(str(x)), str(x))):
        line_dir = OUT_DIR / f"line_{line}"
        line_dir.mkdir(parents=True, exist_ok=True)

        raw_line = variant_summary[variant_summary["route_name"] == line]
        raw_groups = sorted(raw_line["direction_group"].unique())
        raw_frames = [(g, _display_rows(raw_line[raw_line["direction_group"] == g])) for g in raw_groups]
        plot_line_figure(line, raw_frames, stop_code_to_name, f"raw, n>{RAW_COUNT_THRESHOLD}", line_dir / "variants_raw.png")

        merged_line = effective_summary[effective_summary["route_name"] == line]
        merged_groups = sorted(merged_line["direction_group"].unique())
        merged_frames = [(g, _display_rows(merged_line[merged_line["direction_group"] == g])) for g in merged_groups]
        plot_line_figure(line, merged_frames, stop_code_to_name, "merged", line_dir / "variants_merged.png")


if __name__ == "__main__":
    run()
