"""Stage 4 -- per-line/direction route-sequence variant detection.

Refactor of avishagi/bus_route_initial_filtering.ipynb's function library,
generalized to:
  - run over all 7 lines from config.py instead of 4 hardcoded file paths
  - group route_ids into direction_groups per govData/route_id_decisions.json
    (a "pool" of route_ids sharing one variant-space) instead of assuming
    one route_id per line
  - always keep route_id (and the new route_name/direction_group columns)
    in the output rather than splitting per line into separate files

Produces 3 STAGING files (route_id/route_name/variant_type-tagged, but
without a final variant_type label yet -- that's added by stage5+stage6):
  - govData/_staging_df_cleaned.csv        (row/stop level)
  - govData/_staging_variant_summary.csv   (variant level, incl. n_missing
    for every variant -- this feeds stage5's classification heuristic)
  - govData/_staging_clean_filtered_data.csv (row level, restricted to
    variants judged "long enough to matter" for display purposes)

Requires govData/route_id_decisions.json to be complete for every
multi-route_id line (see stage3_investigate_route_ids.decisions_complete).
"""

from __future__ import annotations

from collections import Counter

import pandas as pd

from pipeline import config, stage3_investigate_route_ids

BLOCK_KEYS = ["route_id", "month", "day_of_week", "scheduled_departure_time"]
STOP_CODE_FIXES = {2008: 1525}
MIN_COUNT = 5


def load_stop_code_to_name(path=None) -> dict[int, str]:
    path = path or config.JERUSALEM_STOPS_PATH
    stops_df = pd.read_csv(path)
    mapping = dict(zip(stops_df["stop_code"], stops_df["stop_name"]))
    mapping[2008] = "צומת פת/הרב הרצוג"  # manual fix, carried over from avishagi's pipeline
    return mapping


def get_stop_names(codes: list[int], stop_code_to_name: dict[int, str]) -> list[str]:
    return [stop_code_to_name.get(int(c), f"Unknown({c})") for c in codes]


def clean_duplicate_stops(df_sorted: pd.DataFrame, stop_code_fixes: dict[int, int]) -> pd.DataFrame:
    df_clean = df_sorted.drop_duplicates(subset=BLOCK_KEYS + ["stop_sequence"], keep="first").copy()
    for wrong_code, correct_code in stop_code_fixes.items():
        mask = df_clean["stop_code"] == wrong_code
        df_clean.loc[mask, "stop_code"] = correct_code
    return df_clean


def extract_route_sequences(df_sorted: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    block_sequences = (
        df_sorted.sort_values("stop_sequence")
        .groupby(BLOCK_KEYS, sort=False)["stop_code"]
        .apply(lambda s: "-".join(str(c) for c in s.tolist()))
    )
    counts = Counter(block_sequences.tolist())
    route_counts = pd.DataFrame(
        [{"route_sequence_str": seq, "count": n} for seq, n in counts.items()]
    )
    route_counts["n_stops"] = route_counts["route_sequence_str"].apply(lambda s: len(s.split("-")))
    route_counts = route_counts.sort_values("count", ascending=False).reset_index(drop=True)
    route_counts["route_variant_id"] = range(len(route_counts))
    return block_sequences, route_counts


def assign_variant_ids(df_sorted: pd.DataFrame, block_sequences: pd.Series, route_counts: pd.DataFrame) -> pd.DataFrame:
    seq_to_variant = dict(zip(route_counts["route_sequence_str"], route_counts["route_variant_id"]))
    block_variant = block_sequences.map(seq_to_variant).rename("route_variant_id").reset_index()
    df_cleaned = df_sorted.merge(block_variant, on=BLOCK_KEYS, how="left")
    df_cleaned["route_variant_id"] = df_cleaned["route_variant_id"].astype("Int64")
    return df_cleaned


def compare_to_reference(route_counts: pd.DataFrame, stop_code_to_name: dict[int, str]) -> pd.DataFrame:
    reference_row = route_counts.iloc[0]
    reference_codes = reference_row["route_sequence_str"].split("-")
    reference_set = set(reference_codes)

    rows = []
    for _, row in route_counts.iterrows():
        current_codes = row["route_sequence_str"].split("-")
        current_set = set(current_codes)
        missing = [c for c in reference_codes if c not in current_set]
        added = [c for c in current_codes if c not in reference_set]
        rows.append(
            {
                "route_variant_id": row["route_variant_id"],
                "count": row["count"],
                "n_stops": row["n_stops"],
                "route_sequence_str": row["route_sequence_str"],
                "is_reference": row["route_variant_id"] == reference_row["route_variant_id"],
                "n_missing": len(missing),
                "n_added": len(added),
                "missing_stop_codes": missing,
                "missing_stop_names": get_stop_names([int(c) for c in missing], stop_code_to_name),
                "added_stop_codes": added,
            }
        )
    return pd.DataFrame(rows)


def filter_for_display(comparison_df: pd.DataFrame, critical_stops: list[int]) -> set:
    """Return the set of route_variant_ids worth keeping for display/heatmap
    purposes: long enough relative to the reference route, frequent enough,
    or skipping a stop the user has flagged as critical for this line."""
    ref_n_stops = comparison_df.loc[comparison_df["is_reference"], "n_stops"].iloc[0]
    min_stops = max(10, round(ref_n_stops * 0.4))
    max_stops = ref_n_stops + 10
    critical_set = set(str(s) for s in critical_stops)

    def skips_critical(missing_codes: list[str]) -> bool:
        return bool(critical_set & set(missing_codes))

    mask_len = comparison_df["n_stops"].between(min_stops, max_stops)
    mask_count = comparison_df["count"] >= MIN_COUNT
    mask_critical = comparison_df["missing_stop_codes"].apply(skips_critical)
    mask_final = comparison_df["is_reference"] | (mask_len & (mask_count | mask_critical))
    return set(comparison_df.loc[mask_final, "route_variant_id"])


def process_group(
    df_all: pd.DataFrame,
    line: str,
    group_name: str,
    route_ids: list[int],
    critical_stops: list[int],
    stop_code_to_name: dict[int, str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sub = df_all[df_all["route_id"].isin(route_ids)].drop_duplicates()
    if sub.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    df_sorted = sub.sort_values(BLOCK_KEYS + ["stop_sequence"])
    df_sorted = clean_duplicate_stops(df_sorted, STOP_CODE_FIXES)

    block_sequences, route_counts = extract_route_sequences(df_sorted)
    df_cleaned = assign_variant_ids(df_sorted, block_sequences, route_counts)

    comparison_df = compare_to_reference(route_counts, stop_code_to_name)
    display_ids = filter_for_display(comparison_df, critical_stops)

    df_cleaned = df_cleaned.copy()
    df_cleaned.insert(0, "direction_group", group_name)  # route_name already present (from stage2)

    comparison_df.insert(0, "direction_group", group_name)
    comparison_df.insert(0, "route_name", line)

    comparison_df["in_display_set"] = comparison_df["route_variant_id"].isin(display_ids)
    clean_filtered = df_cleaned[df_cleaned["route_variant_id"].isin(display_ids)]

    return df_cleaned, comparison_df, clean_filtered


def run() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not stage3_investigate_route_ids.decisions_complete():
        raise RuntimeError(
            f"{config.ROUTE_ID_DECISIONS_PATH} is incomplete. Run stage3 and "
            "fill in a 'treatment' for every multi-route_id line before "
            "running stage4."
        )

    df_all = pd.read_csv(config.RENAMED_RIDE_DATA_PATH)
    stop_code_to_name = load_stop_code_to_name()
    groups = config.load_route_id_groups()

    df_cleaned_parts, variant_summary_parts, clean_filtered_parts = [], [], []

    for line, line_groups in groups.items():
        critical_stops = config.CRITICAL_STOPS.get(str(line), [])
        for group_name, route_ids in line_groups.items():
            df_cleaned, comparison_df, clean_filtered = process_group(
                df_all, line, group_name, route_ids, critical_stops, stop_code_to_name
            )
            if df_cleaned.empty:
                print(f"WARNING: line {line} group {group_name} (route_ids {route_ids}) has no rows -- skipped.")
                continue
            df_cleaned_parts.append(df_cleaned)
            variant_summary_parts.append(comparison_df)
            clean_filtered_parts.append(clean_filtered)
            n_variants = comparison_df["route_variant_id"].nunique()
            n_display = comparison_df["in_display_set"].sum()
            print(
                f"line {line} / {group_name} (route_ids {route_ids}): "
                f"{len(df_cleaned):,} rows, {n_variants} variants, {n_display} kept for display"
            )

    df_cleaned_all = pd.concat(df_cleaned_parts, ignore_index=True)
    variant_summary_all = pd.concat(variant_summary_parts, ignore_index=True)
    clean_filtered_all = pd.concat(clean_filtered_parts, ignore_index=True)

    df_cleaned_all.to_csv(config.STAGING_DF_CLEANED_PATH, index=False, encoding="utf-8-sig")
    variant_summary_all.to_csv(config.STAGING_VARIANT_SUMMARY_PATH, index=False, encoding="utf-8-sig")
    clean_filtered_all.to_csv(config.STAGING_CLEAN_FILTERED_PATH, index=False, encoding="utf-8-sig")

    print()
    print(f"Saved -> {config.STAGING_DF_CLEANED_PATH} ({len(df_cleaned_all):,} rows)")
    print(f"Saved -> {config.STAGING_VARIANT_SUMMARY_PATH} ({len(variant_summary_all):,} variants)")
    print(f"Saved -> {config.STAGING_CLEAN_FILTERED_PATH} ({len(clean_filtered_all):,} rows)")

    return df_cleaned_all, variant_summary_all, clean_filtered_all


if __name__ == "__main__":
    run()
