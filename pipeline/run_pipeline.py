"""Orchestrator for the bus-transit data pipeline.

Runs stage0 (optional, --rebuild-merged) through stage10.
Halts automatically after stage3 if govData/route_id_decisions.json is
incomplete (see stage3_investigate_route_ids.py) -- stage4 onward needs a
confirmed 'treatment' for every multi-route_id line first.

Also warns (without halting) if govData/variant_type_decisions.csv still
has unconfirmed rows when stage6 runs -- see stage5_variant_classification.py
for the agent/human review step that produces that file.

Stage0 (rebuilding govData/ride_data_merged.csv from the raw government
source, see stage0_rebuild_merged.py) is opt-in via --rebuild-merged: it
reads an 85M+ row external file outside the repo and is slow, so it's
skipped by default (the orchestrator otherwise assumes
govData/ride_data_merged.csv already exists and is current).
"""

from __future__ import annotations

import argparse
import sys

from pipeline import (
    config,
    style,  # noqa: F401
    stage0_rebuild_merged,
    stage1_validate_coverage,
    stage2_rename_and_tag,
    stage3_investigate_route_ids,
    stage4_route_variants,
    stage5_variant_classification,
    stage6_finalize_outputs,
    stage7_eda_summary,
    stage8_detour_clusters,
    stage9_control_comparison,
    stage10_route_deviation_heatmaps,
)

def _header(label: str) -> None:
    print("=" * 60)
    print(label)
    print("=" * 60)


def run_stage0_rebuild_merged() -> None:
    _header("Stage 0: rebuild ride_data_merged.csv from raw source (majority-vote dedup)")
    stage0_rebuild_merged.run()


def run_stage1_validate_coverage() -> None:
    _header("Stage 1: validate route_id coverage")
    stage1_validate_coverage.run()


def run_stage2_rename_and_tag() -> None:
    _header("Stage 2: rename columns + tag route_name")
    stage2_rename_and_tag.run()


def run_stage3_investigate_route_ids() -> None:
    _header("Stage 3: investigate multi-route_id lines [BLOCKING CHECKPOINT]")
    stage3_investigate_route_ids.run()


def run_stage4_route_variants() -> None:
    _header("Stage 4: route-sequence variant detection")
    stage4_route_variants.run()


def run_stage5_variant_classification() -> None:
    _header("Stage 5: variant classification [REVIEW CHECKPOINT]")
    stage5_variant_classification.run()


def run_stage6_finalize_outputs() -> None:
    _header("Stage 6: finalize consolidated outputs")
    stage6_finalize_outputs.run()


def run_stage7_eda_summary() -> None:
    _header("Stage 7: EDA summary (coverage, count_common, travel-time anomalies)")
    stage7_eda_summary.run()


def run_stage8_detour_clusters() -> None:
    _header("Stage 8: per-cluster detour frequency figures")
    stage8_detour_clusters.run()


def run_stage9_control_comparison() -> None:
    _header("Stage 9: control-vs-protest line comparison")
    stage9_control_comparison.run()


def run_stage10_route_deviation_heatmaps() -> None:
    _header("Stage 10: route deviation heatmaps")
    stage10_route_deviation_heatmaps.run()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--rebuild-merged", action="store_true",
        help="Run stage0 first: rebuild govData/ride_data_merged.csv from the raw source file.",
    )
    args = parser.parse_args()

    if args.rebuild_merged:
        run_stage0_rebuild_merged()

    if not config.RIDE_DATA_MERGED_PATH.exists():
        raise FileNotFoundError(
            f"{config.RIDE_DATA_MERGED_PATH} does not exist. Rerun with "
            "--rebuild-merged, or place it manually first."
        )

    run_stage1_validate_coverage()
    run_stage2_rename_and_tag()
    run_stage3_investigate_route_ids()

    if not stage3_investigate_route_ids.decisions_complete():
        print()
        print("HALTING: govData/route_id_decisions.json is incomplete.")
        print(
            "Review govData/route_id_comparison_report.csv and fill in a "
            "'treatment' (pool / keep_separate / direction_pair) for each "
            f"line in {config.MULTI_ROUTE_ID_LINES} before rerunning."
        )
        sys.exit(1)

    run_stage4_route_variants()
    run_stage5_variant_classification()
    print()
    print(
        "NOTE: govData/variant_type_decisions.csv was (re)written by stage5 "
        "with heuristic defaults and confirmed=False. Review it (candidate "
        "clusters are in govData/candidate_variant_labels.csv) before trusting "
        "variant_type in the final outputs -- stage6 will warn but not halt."
    )
    run_stage6_finalize_outputs()
    run_stage7_eda_summary()
    run_stage8_detour_clusters()
    run_stage9_control_comparison()
    run_stage10_route_deviation_heatmaps()

    print()
    print("Pipeline complete.")


if __name__ == "__main__":
    main()
