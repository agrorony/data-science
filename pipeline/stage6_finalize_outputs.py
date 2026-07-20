"""Stage 6 -- finalize the 3 consolidated output files.

Merges stage4's per-group route-variant tables with stage5's
confirmed/heuristic variant_type labels into the 3 consolidated files
(one per artifact type, spanning all 7 lines -- not one file per line):

  - govData/df_cleaned.csv          (row/stop level)
  - govData/variant_summary.csv     (variant level)
  - govData/clean_filtered_data.csv (row level, display-filtered subset)

Every row keeps both route_id and route_name (line), plus direction_group,
route_variant_id, is_reference, variant_type, and whether variant_type is
confirmed or still resting on stage5's heuristic default.
"""

from __future__ import annotations

import pandas as pd

from pipeline import config

REFERENCE_VARIANT_TYPE = "regular"  # the reference route (route_variant_id 0-equivalent) is never a detour


def load_variant_type_lookup(decisions_path=None) -> pd.DataFrame:
    decisions_path = decisions_path or config.VARIANT_TYPE_DECISIONS_PATH
    decisions = pd.read_csv(decisions_path)
    unconfirmed = decisions[~decisions["confirmed"]]
    if not unconfirmed.empty:
        print(
            f"WARNING: {len(unconfirmed)}/{len(decisions)} variant_type rows in "
            f"{decisions_path} are still unconfirmed (using stage5's heuristic "
            "label as-is). Review that file before treating variant_type as final."
        )
    return decisions[["route_name", "direction_group", "route_variant_id", "cluster_id", "confirmed_type", "confirmed"]]


def attach_variant_type(df: pd.DataFrame, lookup: pd.DataFrame) -> pd.DataFrame:
    merged = df.merge(
        lookup, on=["route_name", "direction_group", "route_variant_id"], how="left"
    )
    is_ref_col = "is_reference" if "is_reference" in merged.columns else None
    if is_ref_col:
        merged["confirmed_type"] = merged["confirmed_type"].where(
            ~merged[is_ref_col], REFERENCE_VARIANT_TYPE
        )
        merged["confirmed"] = merged["confirmed"].where(~merged[is_ref_col], True)
    merged = merged.rename(columns={"confirmed_type": "variant_type", "confirmed": "variant_type_confirmed"})
    return merged


def run() -> None:
    lookup = load_variant_type_lookup()

    df_cleaned = pd.read_csv(config.STAGING_DF_CLEANED_PATH)
    variant_summary = pd.read_csv(config.STAGING_VARIANT_SUMMARY_PATH)
    clean_filtered = pd.read_csv(config.STAGING_CLEAN_FILTERED_PATH)

    df_cleaned_final = attach_variant_type(df_cleaned, lookup)
    variant_summary_final = attach_variant_type(variant_summary, lookup)
    clean_filtered_final = attach_variant_type(clean_filtered, lookup)

    df_cleaned_final.to_csv(config.DF_CLEANED_PATH, index=False, encoding="utf-8-sig")
    variant_summary_final.to_csv(config.VARIANT_SUMMARY_PATH, index=False, encoding="utf-8-sig")
    clean_filtered_final.to_csv(config.CLEAN_FILTERED_DATA_PATH, index=False, encoding="utf-8-sig")

    print(f"Saved -> {config.DF_CLEANED_PATH} ({len(df_cleaned_final):,} rows)")
    print(f"Saved -> {config.VARIANT_SUMMARY_PATH} ({len(variant_summary_final):,} variants)")
    print(f"Saved -> {config.CLEAN_FILTERED_DATA_PATH} ({len(clean_filtered_final):,} rows)")
    print()
    print("variant_type breakdown (variant_summary.csv, non-reference rows):")
    non_ref = variant_summary_final[~variant_summary_final["is_reference"]]
    print(non_ref["variant_type"].value_counts().to_string())


if __name__ == "__main__":
    run()
