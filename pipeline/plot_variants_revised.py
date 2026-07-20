"""Revision round A -- phase 03 replacement: drop clustering entirely,
show only variants observed more than 5 times (n>5), then a second grid
after applying the manual merges/exclusions in
govData/variant_merges.json.

Same green/white stop-presence grid look as
stage10_route_deviation_heatmaps.py (which reproduces
avishagi/bus_route_initial_filtering.ipynb exactly) -- only the variant
*selection* rule changes (n>5 instead of stage4's filter_for_display
heuristic), not the visual style.

Output: rony/figures/variants_raw_<line>_<group>.png and
rony/figures/variants_merged_<line>_<group>.png
"""

from __future__ import annotations

import pandas as pd

from pipeline import config, stage4_route_variants, variant_merges as vm
from pipeline.stage10_route_deviation_heatmaps import build_group_heatmap, plot_group_heatmap

RAW_COUNT_THRESHOLD = 5


def run() -> None:
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    variant_summary = pd.read_csv(config.VARIANT_SUMMARY_PATH)
    stop_code_to_name = stage4_route_variants.load_stop_code_to_name()

    effective_summary = vm.build_effective_variant_summary(variant_summary)

    for (line, group), sub in variant_summary.groupby(["route_name", "direction_group"]):
        raw_sub = sub[(sub["is_reference"]) | (sub["count"] > RAW_COUNT_THRESHOLD)]
        if raw_sub.empty:
            print(f"line {line} / {group}: nothing clears n>{RAW_COUNT_THRESHOLD}, skipped (raw).")
            continue
        heatmap_data, labels_y, station_labels = build_group_heatmap(raw_sub, stop_code_to_name)
        path = config.FIGURES_DIR / f"variants_raw_{line}_{group}.png"
        plot_group_heatmap(heatmap_data, labels_y, station_labels, line, f"{group} (raw, n>{RAW_COUNT_THRESHOLD})", path)
        print(f"Saved -> {path} ({len(labels_y)} variants)")

    for (line, group), sub in effective_summary.groupby(["route_name", "direction_group"]):
        merged_sub = sub[(sub["is_reference"]) | (sub["count"] > RAW_COUNT_THRESHOLD)]
        if merged_sub.empty:
            print(f"line {line} / {group}: nothing clears n>{RAW_COUNT_THRESHOLD}, skipped (merged).")
            continue
        heatmap_data, labels_y, station_labels = build_group_heatmap(merged_sub, stop_code_to_name)
        path = config.FIGURES_DIR / f"variants_merged_{line}_{group}.png"
        plot_group_heatmap(heatmap_data, labels_y, station_labels, line, f"{group} (merged)", path)
        print(f"Saved -> {path} ({len(labels_y)} variants)")


if __name__ == "__main__":
    run()
