"""Revision round C -- shared helpers for pooling both directions of a
line into one distribution, used by phases 04, 05, 08, 09.

All four phases need the same basic building block: one row per real
observed (route_name, direction_group, route_variant_id, month,
day_of_week, scheduled_departure_time) block, with its end-to-end
travel time/distance (the block's own last-stop cumulative value) and
n_observations -- built from the merged/excluded variant set in
pipeline.variant_merges, not the raw df_cleaned.csv. "Pooled" simply
means grouping by route_name alone instead of (route_name,
direction_group) wherever a phase's stats/figures don't need the
direction-specific stop sequence itself.
"""

from __future__ import annotations

import pandas as pd

from pipeline import config

LOW_CONFIDENCE_THRESHOLD = config.LOW_CONFIDENCE_THRESHOLD
BLOCK_KEYS = ["route_name", "direction_group", "route_variant_id", "month", "day_of_week", "scheduled_departure_time"]


def block_endpoints(effective_df: pd.DataFrame, min_observations: int = LOW_CONFIDENCE_THRESHOLD) -> pd.DataFrame:
    """One row per block: end-to-end travel time/distance (at the
    block's own max stop_sequence) plus its variant_type_v2 and
    is_reference flag. `n_observations` filters out low-confidence rows
    (CLAUDE.md issue #6) before any aggregation."""
    df = effective_df[effective_df["n_observations"] >= min_observations]

    idx = df.groupby(BLOCK_KEYS)["stop_sequence"].idxmax()
    endpoints = df.loc[idx].copy()
    endpoints = endpoints.rename(
        columns={
            "mean_cumulative_travel_time_min": "end_time_min",
            "mean_cumulative_distance_m": "end_dist_m",
        }
    )
    return endpoints[
        BLOCK_KEYS + ["end_time_min", "end_dist_m", "n_observations", "variant_type_v2"]
    ].reset_index(drop=True)


def baseline_endpoints(endpoints: pd.DataFrame, route_name=None) -> pd.DataFrame:
    """Blocks on the reference (merged baseline) variant only, both
    directions included -- "pooled" is just the caller not grouping by
    direction_group afterward."""
    out = endpoints[endpoints["variant_type_v2"] == "reference"]
    if route_name is not None:
        out = out[out["route_name"] == route_name]
    return out


def blocked_endpoints(endpoints: pd.DataFrame, route_name=None) -> pd.DataFrame:
    out = endpoints[endpoints["variant_type_v2"] == "blocked"]
    if route_name is not None:
        out = out[out["route_name"] == route_name]
    return out
