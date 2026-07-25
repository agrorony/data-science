"""Revision round A/B -- manual variant merges/exclusions and the new
absolute-stop-count blocked rule, replacing stage5's clustering and
fraction-based classification.

`govData/variant_merges.json` encodes, per (line, direction_group), which
raw `route_variant_id`s (stage4 numbering, 0 = reference, sorted by
occurrence) get merged into one variant and which get dropped entirely.
This module turns that config into:

  - a per-(line, direction, raw_id) -> merged_id-or-None (excluded) map
  - an "effective" variant_summary: one row per merged variant, with
    `count` = sum of its members' counts, and `n_stops` /
    `route_sequence_str` taken from its most-frequent member (the
    "representative"). The merged-in id is the representative's own raw
    id, so no new id scheme is introduced.
  - `variant_type_v2`: "reference" for the merged variant containing raw
    id 0 (or plain id 0 if never merged), else "blocked" if the merged
    variant's `n_stops > BLOCKED_STOP_THRESHOLD`, else "regular". No
    fraction thresholds and no ambiguous/clustering step -- see
    docs/07_blockade_investigation/README.md's addendum for why.
  - `apply_to_df_cleaned`: drops excluded rows from a df_cleaned-shaped
    frame and relabels `route_variant_id` to the merged id, so every
    downstream phase (04-09) can treat the output exactly like the
    original df_cleaned.csv.
"""

from __future__ import annotations

import json

import pandas as pd

from pipeline import config

VARIANT_MERGES_PATH = config.GOV_DATA_DIR / "variant_merges.json"
BLOCKED_STOP_THRESHOLD = 15

# Revision round 4, section C -- line 14's route shares 0 stops with the
# 17/19 blockade footprint, and every one of its non-reference merged
# variants is a near-singleton (n=1, one n=4) that skips 1-6 stops and adds
# none: a stop-recording dropout signature, not a detour (see
# docs/06_blockade_frequency/line_14/blocked_slots_investigation.md). Force
# these to "noise" instead of "blocked" so line 14's blockade share is 0%
# everywhere project-wide (phases 05/06/08/09 all read variant_type_v2 and
# need no line-14 special case of their own).
LINE_14_NO_BLOCKED = 14


def load_merge_config(path=None) -> dict:
    path = path or VARIANT_MERGES_PATH
    return json.loads(path.read_text(encoding="utf-8"))


def _group_key(line, group) -> tuple[str, str]:
    return (str(line), str(group))


def build_id_maps(merge_config: dict, variant_summary: pd.DataFrame) -> dict[tuple, dict[int, int | None]]:
    """Return {(line, direction_group): {raw_id: merged_id_or_None}}."""
    counts = variant_summary.set_index(["route_name", "direction_group", "route_variant_id"])["count"]

    id_maps: dict[tuple, dict[int, int | None]] = {}
    for line_str, groups in merge_config.items():
        for group, spec in groups.items():
            key = _group_key(line_str, group)
            id_map: dict[int, int | None] = {}

            for raw_id in spec["exclude"]:
                id_map[raw_id] = None

            for merge_group in spec["merges"]:
                counted = [(rid, counts.get((int(line_str), group, rid), 0)) for rid in merge_group]
                representative = max(counted, key=lambda x: x[1])[0]
                for rid, _ in counted:
                    id_map[rid] = representative

            id_maps[key] = id_map
    return id_maps


def build_effective_variant_summary(variant_summary: pd.DataFrame, merge_config: dict | None = None) -> pd.DataFrame:
    merge_config = merge_config or load_merge_config()
    id_maps = build_id_maps(merge_config, variant_summary)

    rows = []
    for (line, group), sub in variant_summary.groupby(["route_name", "direction_group"]):
        key = _group_key(line, group)
        id_map = id_maps.get(key, {})

        sub = sub.copy()
        sub["merged_id"] = sub["route_variant_id"].map(lambda rid: id_map.get(rid, rid))
        sub = sub[sub["merged_id"].notna()]

        for merged_id, grp in sub.groupby("merged_id"):
            representative = grp.loc[grp["count"].idxmax()]
            is_reference = bool((grp["route_variant_id"] == 0).any())
            rows.append(
                {
                    "route_name": line,
                    "direction_group": group,
                    "route_variant_id": int(merged_id),
                    "count": int(grp["count"].sum()),
                    "n_stops": int(representative["n_stops"]),
                    "route_sequence_str": representative["route_sequence_str"],
                    "is_reference": is_reference,
                    "n_raw_members": len(grp),
                    "member_raw_ids": sorted(grp["route_variant_id"].tolist()),
                }
            )

    def _classify(r):
        if r["is_reference"]:
            return "reference"
        if int(r["route_name"]) == LINE_14_NO_BLOCKED:
            return "noise"
        return "blocked" if r["n_stops"] > BLOCKED_STOP_THRESHOLD else "regular"

    out = pd.DataFrame(rows)
    out["variant_type_v2"] = out.apply(_classify, axis=1)
    return out.sort_values(["route_name", "direction_group", "route_variant_id"]).reset_index(drop=True)


def apply_merges(df: pd.DataFrame, raw_variant_summary: pd.DataFrame, merge_config: dict | None = None) -> pd.DataFrame:
    """Drop excluded rows from `df` (any df_cleaned-shaped frame keyed by
    route_name/direction_group/route_variant_id) and relabel
    route_variant_id to the merged id."""
    merge_config = merge_config or load_merge_config()
    id_maps = build_id_maps(merge_config, raw_variant_summary)

    def remap(row_line, row_group, row_id):
        id_map = id_maps.get(_group_key(row_line, row_group), {})
        return id_map.get(row_id, row_id)

    df = df.copy()
    keys = list(zip(df["route_name"], df["direction_group"], df["route_variant_id"]))
    merged_ids = [remap(*k) for k in keys]
    df["route_variant_id"] = merged_ids
    df = df[df["route_variant_id"].notna()].copy()
    df["route_variant_id"] = df["route_variant_id"].astype(int)
    return df


def attach_variant_type_v2(df: pd.DataFrame, effective_summary: pd.DataFrame) -> pd.DataFrame:
    lookup = effective_summary.set_index(["route_name", "direction_group", "route_variant_id"])["variant_type_v2"]
    df = df.copy()
    df["variant_type_v2"] = list(
        zip(df["route_name"], df["direction_group"], df["route_variant_id"])
    )
    df["variant_type_v2"] = df["variant_type_v2"].map(lambda k: lookup.get(k, "regular"))
    return df


def build_effective_df_cleaned(df_cleaned: pd.DataFrame | None = None, variant_summary: pd.DataFrame | None = None):
    """One-stop helper for phases 04-09: returns (effective_df, effective_summary)
    where effective_df is df_cleaned.csv with merges/exclusions applied and
    variant_type_v2 attached, and effective_summary is the merged variant
    table (see build_effective_variant_summary)."""
    df_cleaned = df_cleaned if df_cleaned is not None else pd.read_csv(config.DF_CLEANED_PATH, low_memory=False)
    variant_summary = variant_summary if variant_summary is not None else pd.read_csv(config.VARIANT_SUMMARY_PATH)

    merge_config = load_merge_config()
    effective_summary = build_effective_variant_summary(variant_summary, merge_config)
    effective_df = apply_merges(df_cleaned, variant_summary, merge_config)
    effective_df = attach_variant_type_v2(effective_df, effective_summary)
    return effective_df, effective_summary
