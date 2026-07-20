"""Phase 05 -- baseline vs. stop-skipping variant comparison.

For every displayed non-reference variant that skips >=1 stop relative
to its line/direction's baseline (reference) variant, computes a
day-of-week/hour-matched comparison against the baseline:

  - total end-to-end travel-time delta (variant - baseline), minutes,
    averaged over the (day_of_week, scheduled_departure_time) slots the
    variant actually occurred in, each matched against the baseline's
    own average at that *same* day/hour (not the baseline's overall
    average across all hours).
  - the "segment delta": same day/hour-matched comparison, but restricted
    to the travel time across just the skipped block (between the two
    boundary stops the variant and baseline share immediately around the
    gap), isolating the local effect of skipping from the trip's overall
    length.

Matching on (day_of_week, hour) rather than the exact (month, day, hour)
block is necessary because each raw block belongs to exactly one variant
(stage4 assigns one stop-sequence per block) -- the reference and a
skip-variant never share the literal same block, so the closest
apples-to-apples control is "how does the reference behave at this same
weekday/hour, averaged across whichever months it ran then." This is the
same matched-window logic phases 08-09 use for control-line comparisons.

Writes govData/skip_comparison.csv, consumed by plot_skip_comparison.py
and the phase 05 reports.
"""

from __future__ import annotations

import ast

import pandas as pd

from pipeline import config, stage4_route_variants


def _parse_list(value):
    if isinstance(value, list):
        return value
    if pd.isna(value):
        return []
    return ast.literal_eval(value)


def find_boundary_stops(ref_codes: list[str], missing_codes: list[str]) -> list[tuple[str, str]]:
    """Return (before, after) stop_code pairs bounding each contiguous
    missing block in the reference sequence."""
    missing_set = set(missing_codes)
    blocks = []
    i = 0
    while i < len(ref_codes):
        if ref_codes[i] in missing_set:
            j = i
            while j < len(ref_codes) and ref_codes[j] in missing_set:
                j += 1
            before = ref_codes[i - 1] if i > 0 else None
            after = ref_codes[j] if j < len(ref_codes) else None
            if before is not None and after is not None:
                blocks.append((before, after))
            i = j
        else:
            i += 1
    return blocks


def day_hour_stop_time_map(sub: pd.DataFrame) -> dict[tuple[int, int], dict[int, float]]:
    """{(day_of_week, hour): {stop_code: mean cumulative travel time}}."""
    out: dict[tuple[int, int], dict[int, float]] = {}
    for (day, hour), grp in sub.groupby(["day_of_week", "scheduled_departure_time"]):
        out[(day, hour)] = grp.groupby("stop_code")["mean_cumulative_travel_time_min"].mean().to_dict()
    return out


def run() -> pd.DataFrame:
    df_cleaned = pd.read_csv(config.DF_CLEANED_PATH, low_memory=False)
    variant_summary = pd.read_csv(config.VARIANT_SUMMARY_PATH)
    variant_summary["missing_stop_codes"] = variant_summary["missing_stop_codes"].apply(_parse_list)
    variant_summary["missing_stop_names"] = variant_summary["missing_stop_names"].apply(_parse_list)

    rows = []
    for (line, group), sub_vs in variant_summary.groupby(["route_name", "direction_group"]):
        ref = sub_vs[sub_vs["is_reference"]]
        if ref.empty:
            continue
        ref = ref.iloc[0]
        ref_codes = ref["route_sequence_str"].split("-")
        ref_sub = df_cleaned[
            (df_cleaned["route_name"] == line)
            & (df_cleaned["direction_group"] == group)
            & (df_cleaned["route_variant_id"] == ref["route_variant_id"])
        ]
        ref_maps = day_hour_stop_time_map(ref_sub)

        candidates = sub_vs[
            (~sub_vs["is_reference"]) & (sub_vs["in_display_set"]) & (sub_vs["n_missing"] > 0)
        ]
        for _, var in candidates.iterrows():
            var_sub = df_cleaned[
                (df_cleaned["route_name"] == line)
                & (df_cleaned["direction_group"] == group)
                & (df_cleaned["route_variant_id"] == var["route_variant_id"])
            ]
            if var_sub.empty:
                continue
            var_maps = day_hour_stop_time_map(var_sub)
            blocks = find_boundary_stops(ref_codes, var["missing_stop_codes"])

            total_deltas, seg_deltas = [], []
            n_matched = 0
            for (day, hour), var_stop_times in var_maps.items():
                ref_stop_times = ref_maps.get((day, hour))
                if ref_stop_times is None:
                    continue
                n_matched += 1
                var_total = max(var_stop_times.values())
                ref_total = max(ref_stop_times.values())
                total_deltas.append(var_total - ref_total)

                for before, after in blocks:
                    before_i, after_i = int(before), int(after)
                    if {before_i, after_i} <= var_stop_times.keys() and {before_i, after_i} <= ref_stop_times.keys():
                        var_seg = var_stop_times[after_i] - var_stop_times[before_i]
                        ref_seg = ref_stop_times[after_i] - ref_stop_times[before_i]
                        seg_deltas.append(var_seg - ref_seg)

            if n_matched == 0:
                continue

            rows.append(
                {
                    "route_name": line,
                    "direction_group": group,
                    "route_variant_id": var["route_variant_id"],
                    "count": var["count"],
                    "n_missing": var["n_missing"],
                    "missing_stop_names": var["missing_stop_names"],
                    "variant_type": var["variant_type"],
                    "cluster_id": var["cluster_id"],
                    "n_day_hour_slots": len(var_maps),
                    "n_matched_to_baseline": n_matched,
                    "total_time_delta_min": round(sum(total_deltas) / len(total_deltas), 1) if total_deltas else None,
                    "n_missing_blocks": len(blocks),
                    "segment_time_delta_min": round(sum(seg_deltas) / len(seg_deltas), 1) if seg_deltas else None,
                    "n_segment_matches": len(seg_deltas),
                }
            )

    out = pd.DataFrame(rows).sort_values(["route_name", "direction_group", "count"], ascending=[True, True, False])
    out.to_csv(config.GOV_DATA_DIR / "skip_comparison.csv", index=False, encoding="utf-8-sig")
    print(f"Saved -> {config.GOV_DATA_DIR / 'skip_comparison.csv'} ({len(out)} variants)")
    return out


if __name__ == "__main__":
    run()
