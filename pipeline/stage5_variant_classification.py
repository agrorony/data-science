"""Stage 5 -- REVIEW CHECKPOINT: regular vs. blocked variant classification.

For every non-reference route variant produced by stage4, this stage:
  1. Computes a heuristic candidate label (regular / blocked / ambiguous)
     based on what fraction of the reference route's stops are missing,
     scaled per line rather than a fixed absolute count (the old
     3<=n_missing<=15 heuristic doesn't generalize across lines whose
     reference route length ranges from 12 to 67 stops).
  2. Clusters "blocked"/"ambiguous" candidates within each
     (route_name, direction_group) by overlap of *which* stops are
     missing, so a line with two distinct closure locations (e.g. line 97,
     per user report) surfaces as two separate clusters instead of one
     blended "protest fraction".

Writes:
  - govData/candidate_variant_labels.csv : per-variant evidence, for review
  - govData/variant_type_decisions.csv   : pre-filled with the heuristic
    label and confirmed=False; a human or reviewing agent edits
    `confirmed_type`/`confirmed` before stage6 finalizes anything.

This checkpoint is NOT blocking to prepare (the decisions file is always
written, pre-filled with sane defaults) but stage6 will loudly flag any
row still `confirmed=False` as using an unconfirmed heuristic label.
"""

from __future__ import annotations

import ast

import pandas as pd

from pipeline import config

MINOR_MISSING_FRACTION = 0.10  # below this: "regular" (routine stop-matching noise)
MAJOR_MISSING_FRACTION = 0.50  # above this: "ambiguous" (could be a long detour or a truncated/broken trip)
CLUSTER_JACCARD_THRESHOLD = 0.2


def _parse_list(value) -> list:
    if isinstance(value, list):
        return value
    if pd.isna(value):
        return []
    return ast.literal_eval(value)


class UnionFind:
    def __init__(self, items):
        self.parent = {i: i for i in items}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def heuristic_label(n_missing: int, ref_n_stops: int) -> str:
    if n_missing == 0:
        return "regular"
    fraction = n_missing / ref_n_stops
    if fraction < MINOR_MISSING_FRACTION:
        return "regular"
    if fraction > MAJOR_MISSING_FRACTION:
        return "ambiguous"
    return "blocked"


def cluster_group(sub: pd.DataFrame) -> dict:
    """Cluster blocked/ambiguous variants within one (line, direction_group)
    by missing-stop-set overlap. Returns {route_variant_id: cluster_label}."""
    candidates = sub[sub["heuristic_label"].isin(["blocked", "ambiguous"])]
    variant_ids = candidates["route_variant_id"].tolist()
    stop_sets = {
        vid: set(codes)
        for vid, codes in zip(candidates["route_variant_id"], candidates["missing_stop_codes"])
    }

    uf = UnionFind(variant_ids)
    for i, a in enumerate(variant_ids):
        for b in variant_ids[i + 1 :]:
            set_a, set_b = stop_sets[a], stop_sets[b]
            union_size = len(set_a | set_b)
            jaccard = len(set_a & set_b) / union_size if union_size else 0.0
            if jaccard >= CLUSTER_JACCARD_THRESHOLD:
                uf.union(a, b)

    roots = {vid: uf.find(vid) for vid in variant_ids}
    root_to_label = {}
    next_cluster_num = 1
    for vid in variant_ids:
        root = roots[vid]
        if root not in root_to_label:
            root_to_label[root] = f"cluster_{next_cluster_num}"
            next_cluster_num += 1
    return {vid: root_to_label[roots[vid]] for vid in variant_ids}


def run(variant_summary_path=None, labels_path=None, decisions_path=None) -> pd.DataFrame:
    variant_summary_path = variant_summary_path or config.STAGING_VARIANT_SUMMARY_PATH
    labels_path = labels_path or config.CANDIDATE_VARIANT_LABELS_PATH
    decisions_path = decisions_path or config.VARIANT_TYPE_DECISIONS_PATH

    df = pd.read_csv(variant_summary_path)
    df["missing_stop_codes"] = df["missing_stop_codes"].apply(_parse_list)
    df["missing_stop_names"] = df["missing_stop_names"].apply(_parse_list)

    non_ref = df[~df["is_reference"]].copy()
    ref_n_stops = df[df["is_reference"]].set_index(["route_name", "direction_group"])["n_stops"]
    non_ref["ref_n_stops"] = non_ref.apply(
        lambda r: ref_n_stops.loc[(r["route_name"], r["direction_group"])], axis=1
    )
    non_ref["missing_fraction"] = (non_ref["n_missing"] / non_ref["ref_n_stops"]).round(3)
    non_ref["heuristic_label"] = non_ref.apply(
        lambda r: heuristic_label(r["n_missing"], r["ref_n_stops"]), axis=1
    )

    non_ref["cluster_id"] = None
    for (line, group), sub in non_ref.groupby(["route_name", "direction_group"]):
        cluster_map = cluster_group(sub)
        for vid, label in cluster_map.items():
            mask = (
                (non_ref["route_name"] == line)
                & (non_ref["direction_group"] == group)
                & (non_ref["route_variant_id"] == vid)
            )
            non_ref.loc[mask, "cluster_id"] = f"{line}_{group}_{label}"

    labels_cols = [
        "route_name",
        "direction_group",
        "route_variant_id",
        "count",
        "n_stops",
        "ref_n_stops",
        "n_missing",
        "missing_fraction",
        "missing_stop_names",
        "heuristic_label",
        "cluster_id",
        "in_display_set",
    ]
    labels_df = non_ref[labels_cols].sort_values(
        ["route_name", "direction_group", "cluster_id", "count"], ascending=[True, True, True, False]
    )
    labels_df.to_csv(labels_path, index=False, encoding="utf-8-sig")

    decisions_df = non_ref[
        ["route_name", "direction_group", "route_variant_id", "cluster_id", "heuristic_label"]
    ].copy()
    decisions_df["confirmed_type"] = decisions_df["heuristic_label"]
    decisions_df["confirmed"] = False
    decisions_df["notes"] = ""
    decisions_df.to_csv(decisions_path, index=False, encoding="utf-8-sig")

    print(f"Saved -> {labels_path} ({len(labels_df)} non-reference variants)")
    print(f"Saved -> {decisions_path} (pre-filled, confirmed=False -- review before stage6)")
    print()
    print("Heuristic label counts:")
    print(non_ref["heuristic_label"].value_counts().to_string())
    print()
    n_clusters = non_ref["cluster_id"].dropna().nunique()
    print(f"{n_clusters} distinct detour clusters found across all lines.")
    multi_cluster_lines = (
        non_ref.dropna(subset=["cluster_id"])
        .groupby(["route_name", "direction_group"])["cluster_id"]
        .nunique()
    )
    multi_cluster_lines = multi_cluster_lines[multi_cluster_lines > 1]
    if not multi_cluster_lines.empty:
        print("Lines/directions with more than one distinct detour cluster:")
        print(multi_cluster_lines.to_string())

    return non_ref


if __name__ == "__main__":
    run()
