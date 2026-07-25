"""Central configuration for the bus-transit pipeline.

Every stage script imports from here instead of hardcoding route scope,
paths, or column names. The route scope is derived from
`govData/target_route_ids.json` so adding/removing lines only requires
editing that one file.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GOV_DATA_DIR = REPO_ROOT / "govData"
RONY_DIR = REPO_ROOT / "rony"
FIGURES_DIR = RONY_DIR / "figures"

TARGET_ROUTE_IDS_PATH = GOV_DATA_DIR / "target_route_ids.json"

# Raw government export (large, pipe-delimited, lives outside the repo).
# Used only by stage0_rebuild_merged.py.
RAW_SOURCE_PATH = Path(r"C:\Users\ronys\Downloads\e3673768-3dc2-4e62-b0ea-cf763c07a037(3).csv")
STAGE0_DEDUP_AUDIT_PATH = GOV_DATA_DIR / "stage0_dedup_audit.csv"

RIDE_DATA_MERGED_PATH = GOV_DATA_DIR / "ride_data_merged.csv"
RENAMED_RIDE_DATA_PATH = GOV_DATA_DIR / "renamed_ride_data.csv"

ROUTE_ID_COMPARISON_REPORT_PATH = GOV_DATA_DIR / "route_id_comparison_report.csv"
ROUTE_ID_DECISIONS_PATH = GOV_DATA_DIR / "route_id_decisions.json"

CANDIDATE_VARIANT_LABELS_PATH = GOV_DATA_DIR / "candidate_variant_labels.csv"
VARIANT_TYPE_DECISIONS_PATH = GOV_DATA_DIR / "variant_type_decisions.csv"

DF_CLEANED_PATH = GOV_DATA_DIR / "df_cleaned.csv"
VARIANT_SUMMARY_PATH = GOV_DATA_DIR / "variant_summary.csv"
CLEAN_FILTERED_DATA_PATH = GOV_DATA_DIR / "clean_filtered_data.csv"

EDA_SUMMARY_TABLE_PATH = RONY_DIR / "eda_summary_table.csv"

# Stage4 intermediate output (pre variant_type labeling -- finalized by
# stage6 into the 3 consolidated files below).
STAGING_DF_CLEANED_PATH = GOV_DATA_DIR / "_staging_df_cleaned.csv"
STAGING_VARIANT_SUMMARY_PATH = GOV_DATA_DIR / "_staging_variant_summary.csv"
STAGING_CLEAN_FILTERED_PATH = GOV_DATA_DIR / "_staging_clean_filtered_data.csv"

# Stop-metadata files currently in play (see CLAUDE.md "Known Data Issues").
# jerusalem_stops.csv is the most complete; stop_code_to_name_mapping.csv and
# stations.csv are used by specific notebooks. Kept as separate constants
# rather than picking one, since new lines' stops may only be resolvable in
# one of them.
JERUSALEM_STOPS_PATH = GOV_DATA_DIR / "jerusalem_stops.csv"
STOP_CODE_TO_NAME_MAPPING_PATH = GOV_DATA_DIR / "stop_code_to_name_mapping.csv"
STATIONS_PATH = GOV_DATA_DIR / "stations.csv"

LOW_CONFIDENCE_THRESHOLD = 8

# Raw -> readable column names (from avishagi/change_colmn_name.ipynb).
RENAME_COLUMNS = {
    "_id": "record_id",
    "month": "month",
    "route_id": "route_id",
    "DayOfWeek": "day_of_week",
    "HourSourceTime": "scheduled_departure_time",
    "StopSequence_Rishui": "stop_sequence",
    "StopCode": "stop_code",
    "count_common": "n_observations",
    "timeCumSum_mean": "mean_cumulative_travel_time_min",
    "timeCumSum_std": "std_cumulative_travel_time_min",
    "distCumSum_mean": "mean_cumulative_distance_m",
    "distCumSum_std": "std_cumulative_distance_m",
}

# Stops that matter when deciding whether a route variant is a meaningful
# detour vs. routine noise (see filter_routes_for_heatmap in
# avishagi/bus_route_analysis_functions_4.ipynb). Only known for the original
# protest lines today. Lines 15, 9, 97, 14 have no entry yet -- this is
# domain knowledge (which stops matter geographically) that only a human
# familiar with these routes can supply. Do not guess values here.
CRITICAL_STOPS: dict[str, list[int]] = {
    "17": [1054, 1575, 1484, 1079, 1080, 1544, 1546],
    "19": [1054, 1575, 1484, 1079, 1080, 1544, 1546],
    "22": [1054, 1575, 1484, 1079, 3857],
    # "15": [],   # TODO: fill in once known
    # "9":  [],   # TODO: fill in once known
    # "97": [],   # TODO: fill in once known (reportedly 2 separate blockage locations)
    # "14": [],   # TODO: fill in once known
}

# Which lines serve as a traffic-only "control" for which "protest" line,
# used by stage9_control_comparison.py. Pairing requires geographic
# knowledge (shared road segments) that can't be derived from the data
# alone -- only fill in pairs you've actually verified. Lines with no entry
# are skipped by stage9 rather than guessed.
CONTROL_PAIRS: dict[str, str] = {
    "17": "15",
    "19": "15",
    "22": "15",
    # "9":  None,  # TODO: identify a control line once geography is known
    # "97": None,  # TODO: identify a control line once geography is known
    # "14": None,  # TODO: identify a control line once geography is known
}


def load_route_id_groups(
    decisions_path: Path = ROUTE_ID_DECISIONS_PATH,
    targets: dict[str, list[int]] | None = None,
) -> dict[str, dict[str, list[int]]]:
    """Return {line: {group_name: [route_id, ...]}} for every line.

    For multi-route_id lines, reads `direction_groups` from
    route_id_decisions.json (see stage3_investigate_route_ids.py). Lines
    with a single route_id (no decision needed) get one trivial group.
    Raises if a multi-route_id line's decision is missing/incomplete --
    callers should have already checked via
    stage3_investigate_route_ids.decisions_complete().
    """
    targets = targets or load_target_route_ids()
    decisions = json.loads(decisions_path.read_text(encoding="utf-8")) if decisions_path.exists() else {}

    groups: dict[str, dict[str, list[int]]] = {}
    for line, route_ids in targets.items():
        if len(route_ids) == 1:
            groups[line] = {"main": route_ids}
            continue

        entry = decisions.get(line)
        if not entry or not entry.get("treatment"):
            raise ValueError(
                f"Line {line} has {len(route_ids)} route_ids but no confirmed "
                f"decision in {decisions_path}. Run stage3_investigate_route_ids "
                "and fill in the decisions file first."
            )
        direction_groups = entry.get("direction_groups")
        if direction_groups:
            groups[line] = {name: list(ids) for name, ids in direction_groups.items()}
        else:
            # e.g. "pool" or "keep_separate" without explicit sub-groups:
            # treat every route_id as its own group.
            groups[line] = {str(rid): [rid] for rid in route_ids}
    return groups


def load_target_route_ids(path: Path = TARGET_ROUTE_IDS_PATH) -> dict[str, list[int]]:
    """Return {line_name: [route_id, ...]} straight from target_route_ids.json."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {str(line): [int(r) for r in route_ids] for line, route_ids in raw.items()}


def build_route_id_to_line(targets: dict[str, list[int]] | None = None) -> dict[int, str]:
    """Return {route_id: line_name}, flattened from target_route_ids.json.

    This replaces every hardcoded 4-route mapping found in the notebooks
    (MAIN_ROUTES, ROUTE_NAMES, chosen_route_ids_by_line, ...).
    """
    targets = targets or load_target_route_ids()
    route_id_to_line: dict[int, str] = {}
    for line, route_ids in targets.items():
        for route_id in route_ids:
            route_id_to_line[route_id] = line
    return route_id_to_line


# Revision round 3, section A -- one fixed color per line, used in every
# figure where more than one line appears (phases 04, 05, 06 row labels, 08).
# Families: 17/19/22 = shared-corridor "protest" lines (reds), 9/97 = Aza St.
# non-shared protest lines (purples), 14/15 = controls (blues/teal). The
# reds/purples match round 2's plot_baseline_vs_blocked_delta.CROSS_LINE_COLORS
# verbatim so already-published figures don't shift.
LINE_COLORS: dict[int, str] = {
    17: "#b30000", 19: "#e34a33", 22: "#fc8d59",
    9: "#54278f", 97: "#9e9ac8",
    14: "#045a8d", 15: "#74a9cf",
}

LINES: list[str] = sorted(load_target_route_ids().keys(), key=lambda x: (len(x), x))
ROUTE_ID_TO_LINE: dict[int, str] = build_route_id_to_line()
MULTI_ROUTE_ID_LINES: list[str] = [
    line
    for line, route_ids in load_target_route_ids().items()
    if len(route_ids) > 1
]
