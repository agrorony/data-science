"""Phase 11 -- hour-level deep dive on the three approved candidate windows
from docs/10_candidate_windows/README.md, plus a required sub-investigation
of line 22's December pattern (Part B) before it can be trusted as a
finding. Extends docs/06_blockade_frequency/disagreement_deep_dive.md's
method (per-slot variant_type_v2 tabulation, footprint stop-overlap, timing
spread) to three new cells that were NOT part of that earlier deep dive.

Uses only the effective/merged classification
(`pipeline.variant_merges.build_effective_df_cleaned` on
`govData/df_cleaned.csv`, `variant_type_v2`) -- never raw `variant_type`.

Outputs (docs/11_deep_dive_candidate_windows/):
  - timeline_<cell>.png            per Part-A cell, per-(line,direction,hour)
                                    variant-type grid (house style, like
                                    disagreement_windows.png)
  - slot_table_<cell>.csv          every (line, direction, hour) slot's
                                    variant_type_v2, n_observations, merged
                                    route_variant_id used in that cell
  - footprints.csv                 the two blockade footprints (corridor
                                    17/19, Aza St. 9/97) derived directly
                                    from govData/variant_summary.csv's
                                    missing_stop_codes for this pass
  - line22_december_direction_split.csv
  - line22_december_duplicate_check.csv
  - line22_december_variant_check.csv
  - line22_december_fabrication_check.csv
  - control_sanity_december.csv
  - README.md (written separately, using the numbers this script prints)
"""

from __future__ import annotations

import ast
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

from pipeline import config, variant_merges as vm

DAY_LABELS = {1: "Sun", 2: "Mon", 3: "Tue", 4: "Wed", 5: "Thu", 6: "Fri", 7: "Sat"}
DAY_NUM = {v: k for k, v in DAY_LABELS.items()}
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

OUT_DIR = config.REPO_ROOT / "docs" / "11_deep_dive_candidate_windows"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MIN_N_RELIABLE = config.LOW_CONFIDENCE_THRESHOLD  # 8, CLAUDE.md issue #6

BLOCK_KEYS = ["route_name", "direction_group", "route_variant_id", "month", "day_of_week", "scheduled_departure_time"]

CORRIDOR_LINE_DIRS = [(17, "direction_A"), (17, "direction_B"), (19, "direction_A"), (19, "direction_B")]
AZA_LINE_DIRS = [(9, "direction_A"), (9, "direction_B"), (97, "direction_A"), (97, "direction_B")]

CELLS = [
    {"key": "november_wednesday", "month": 11, "day_label": "Wed", "lines": [17, 9, 19, 22, 97],
     "title": "November, Wednesday"},
    {"key": "december_wednesday", "month": 12, "day_label": "Wed", "lines": [22, 19, 17, 9],
     "title": "December, Wednesday"},
    {"key": "october_monday", "month": 10, "day_label": "Mon", "lines": [17, 19, 22, 9],
     "title": "October, Monday"},
]


def load_data():
    df_cleaned = pd.read_csv(config.DF_CLEANED_PATH, low_memory=False)
    variant_summary = pd.read_csv(config.VARIANT_SUMMARY_PATH)
    effective_df, effective_summary = vm.build_effective_df_cleaned(df_cleaned, variant_summary)
    return effective_df, effective_summary, variant_summary


def block_table(effective_df: pd.DataFrame) -> pd.DataFrame:
    """One row per real (line, direction, merged variant, month, day, hour)
    block -- n_observations from the block's own rows (mode, since issue #7
    documents only 3/1,130 groups show any within-block variation)."""
    g = effective_df.groupby(BLOCK_KEYS)
    out = g.agg(
        n_observations=("n_observations", lambda s: s.mode().iloc[0]),
        variant_type_v2=("variant_type_v2", "first"),
    ).reset_index()
    out["day_label"] = out["day_of_week"].map(DAY_LABELS)
    return out


def missing_stops(variant_summary: pd.DataFrame, line: int, direction: str, variant_id: int) -> set[int]:
    row = variant_summary[
        (variant_summary["route_name"] == line)
        & (variant_summary["direction_group"] == direction)
        & (variant_summary["route_variant_id"] == variant_id)
    ]
    if row.empty:
        return set()
    raw = row.iloc[0]["missing_stop_codes"]
    codes = ast.literal_eval(raw) if isinstance(raw, str) else []
    return {int(c) for c in codes}


def reference_stop_set(effective_df: pd.DataFrame, line: int, direction: str) -> set[int]:
    ref = effective_df[
        (effective_df["route_name"] == line)
        & (effective_df["direction_group"] == direction)
        & (effective_df["variant_type_v2"] == "reference")
    ]
    return set(ref["stop_code"].unique().tolist())


def main_blocked_variant(effective_summary: pd.DataFrame, line: int, direction: str):
    """The highest-count merged variant classified 'blocked' for this
    (line, direction) -- the one that actually drives the blockade-share
    numerator, as opposed to tiny (n=1-2) singleton deviations that also
    clear the >15-stop rule but carry no real weight."""
    sub = effective_summary[
        (effective_summary["route_name"] == line)
        & (effective_summary["direction_group"] == direction)
        & (effective_summary["variant_type_v2"] == "blocked")
    ]
    if sub.empty:
        return None
    return sub.sort_values("count", ascending=False).iloc[0]


def build_footprints(effective_df, effective_summary, variant_summary):
    """Recompute the two blockade footprints from data in this pass:
    for each line/direction, take the main (highest-count) merged variant
    classified 'blocked', and pull its missing_stop_codes from
    variant_summary.csv (valid because a merged id is always the
    representative raw id -- pipeline.variant_merges never invents a new
    id). Footprint = union of missing stops across all 4 line/directions
    in the group."""
    records = []
    footprints = {}
    for group_name, line_dirs in [("corridor_17_19", CORRIDOR_LINE_DIRS), ("aza_9_97", AZA_LINE_DIRS)]:
        union = set()
        for line, direction in line_dirs:
            mv = main_blocked_variant(effective_summary, line, direction)
            if mv is None:
                continue
            stops = missing_stops(variant_summary, line, direction, int(mv["route_variant_id"]))
            union |= stops
            records.append({
                "footprint_group": group_name, "line": line, "direction": direction,
                "merged_variant_id": int(mv["route_variant_id"]), "count": int(mv["count"]),
                "n_stops": int(mv["n_stops"]), "missing_stop_codes": sorted(stops),
                "n_missing": len(stops),
            })
        footprints[group_name] = union
    records_df = pd.DataFrame(records)
    return footprints, records_df


def footprint_overlap_for_line(effective_df, variant_summary, line, footprint_stops):
    """For each direction of `line`: how many footprint stops does the
    reference route touch, and does the line's own main blocked variant
    (if any) actually skip footprint stops (real corridor detour) or not
    (trivial/unrelated deviation, cf. 22B in disagreement_deep_dive.md)."""
    rows = []
    for direction in ["direction_A", "direction_B"]:
        if not (effective_df[(effective_df.route_name == line) & (effective_df.direction_group == direction)]).shape[0]:
            continue
        ref_stops = reference_stop_set(effective_df, line, direction)
        ref_touch = ref_stops & footprint_stops
        blocked_variants = effective_df[
            (effective_df.route_name == line) & (effective_df.direction_group == direction)
            & (effective_df.variant_type_v2 == "blocked")
        ]["route_variant_id"].unique()
        best_overlap = 0
        best_vid = None
        best_count = 0
        for vid in blocked_variants:
            stops = missing_stops(variant_summary, line, direction, int(vid))
            overlap = len(stops & footprint_stops)
            cnt = effective_df[
                (effective_df.route_name == line) & (effective_df.direction_group == direction)
                & (effective_df.route_variant_id == vid)
            ].drop_duplicates(subset=BLOCK_KEYS).shape[0]
            if overlap > best_overlap or (overlap == best_overlap and cnt > best_count):
                best_overlap, best_vid, best_count = overlap, int(vid), cnt
        rows.append({
            "line": line, "direction": direction,
            "ref_stops_in_footprint": len(ref_touch),
            "ref_footprint_stops": sorted(ref_touch),
            "best_blocked_variant_id": best_vid,
            "best_blocked_variant_footprint_overlap": best_overlap,
            "best_blocked_variant_n_blocks": best_count,
        })
    return pd.DataFrame(rows)


LINE_ORDER_FOR_CELL = {
    "november_wednesday": [17, 19, 22, 9, 97],
    "december_wednesday": [17, 19, 22, 9],
    "october_monday": [17, 19, 22, 9],
}


def cell_slot_table(blocks: pd.DataFrame, month: int, day_label: str, lines: list[int]) -> pd.DataFrame:
    cell = blocks[
        (blocks["month"] == month) & (blocks["day_label"] == day_label) & (blocks["route_name"].isin(lines))
    ].copy()
    return cell.sort_values(["route_name", "direction_group", "scheduled_departure_time"])


VT_COLORS = {"no_service": "#eeeeee", "reference": "#4C72B0", "regular": "#f4a261", "blocked": "#d62728", "noise": "#999999"}
VT_CODE = {"reference": 1, "regular": 2, "blocked": 3, "noise": 1.5}


def plot_cell_timeline(cell: pd.DataFrame, title: str, out_path, lines_order: list[int]):
    row_keys = []
    for line in lines_order:
        for direction in ["direction_A", "direction_B"]:
            if ((cell["route_name"] == line) & (cell["direction_group"] == direction)).any():
                row_keys.append((line, direction))
    hours = sorted(cell["scheduled_departure_time"].unique())

    grid = np.zeros((len(row_keys), len(hours)))
    n_grid = np.zeros((len(row_keys), len(hours)))
    for ri, (line, direction) in enumerate(row_keys):
        sub = cell[(cell["route_name"] == line) & (cell["direction_group"] == direction)]
        by_hour = {r.scheduled_departure_time: r for r in sub.itertuples()}
        for ci, h in enumerate(hours):
            r = by_hour.get(h)
            if r is None:
                grid[ri, ci] = 0
                n_grid[ri, ci] = 0
            else:
                grid[ri, ci] = VT_CODE.get(r.variant_type_v2, 2)
                n_grid[ri, ci] = r.n_observations

    cmap = ListedColormap([VT_COLORS["no_service"], VT_COLORS["reference"], VT_COLORS["regular"], VT_COLORS["blocked"]])
    fig, ax = plt.subplots(figsize=(max(9, 0.55 * len(hours)), 0.6 * len(row_keys) + 2))
    ax.imshow(grid, cmap=cmap, vmin=0, vmax=3, aspect="auto")
    ax.set_xticks(range(len(hours)))
    ax.set_xticklabels([f"{h}:00" for h in hours], fontsize=8, rotation=45)
    row_labels = [f"Line {l} ({d[-1]})" for l, d in row_keys]
    ax.set_yticks(range(len(row_keys)))
    ax.set_yticklabels(row_labels, fontsize=9)
    for (l, d), tick in zip(row_keys, ax.get_yticklabels()):
        tick.set_color(config.LINE_COLORS.get(l, "black"))
        tick.set_fontweight("bold")

    for ri in range(len(row_keys)):
        for ci in range(len(hours)):
            n = n_grid[ri, ci]
            if n <= 0:
                continue
            low_conf = n < MIN_N_RELIABLE
            txt_color = "black" if grid[ri, ci] in (0, 2) else "white"
            label = f"n={int(n)}" + ("*" if low_conf else "")
            ax.text(ci, ri, label, ha="center", va="center", fontsize=6.5, color=txt_color)

    ax.set_title(title, fontsize=12, fontweight="bold")
    legend = [
        Patch(color=VT_COLORS["reference"], label="Reference variant"),
        Patch(color=VT_COLORS["regular"], label="Regular (non-reference, <=15 stops)"),
        Patch(color=VT_COLORS["blocked"], label="Blocked (>15-stop) variant"),
        Patch(color=VT_COLORS["no_service"], label="No service this hour-slot"),
    ]
    fig.legend(handles=legend, loc="lower center", ncol=4, fontsize=8, bbox_to_anchor=(0.5, -0.05))
    fig.text(
        0.5, -0.12,
        "How to read: each column is one scheduled hour actually operated that day; cell color is variant_type_v2 "
        "(effective/merged classification) in that exact slot; n=block sample size, '*' marks n<8 (CLAUDE.md's own "
        "low-confidence floor) -- do not over-read starred cells.",
        ha="center", fontsize=8, wrap=True, transform=fig.transFigure,
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved -> {out_path}")


def timing_spread(cell: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (line, direction), sub in cell.groupby(["route_name", "direction_group"]):
        blocked = sub[sub["variant_type_v2"] == "blocked"]
        non_blocked = sub[sub["variant_type_v2"] != "blocked"]
        rows.append({
            "route_name": line, "direction_group": direction,
            "n_blocked_hours": blocked["scheduled_departure_time"].nunique(),
            "median_hour_blocked": blocked["scheduled_departure_time"].median() if len(blocked) else np.nan,
            "n_nonblocked_hours": non_blocked["scheduled_departure_time"].nunique(),
            "median_hour_nonblocked": non_blocked["scheduled_departure_time"].median() if len(non_blocked) else np.nan,
        })
    return pd.DataFrame(rows)


def part_a():
    effective_df, effective_summary, variant_summary = load_data()
    blocks = block_table(effective_df)

    footprints, footprint_records = build_footprints(effective_df, effective_summary, variant_summary)
    footprint_records.to_csv(OUT_DIR / "footprints.csv", index=False)
    print("\n=== FOOTPRINTS ===")
    for name, stops in footprints.items():
        print(f"{name}: {len(stops)} stops -> {sorted(stops)}")
    print(footprint_records.to_string(index=False))

    for cell_spec in CELLS:
        key, month, day_label, lines = cell_spec["key"], cell_spec["month"], cell_spec["day_label"], cell_spec["lines"]
        print(f"\n\n========== CELL: {cell_spec['title']} ==========")
        cell = cell_slot_table(blocks, month, day_label, lines)
        cell.to_csv(OUT_DIR / f"slot_table_{key}.csv", index=False)
        print(f"Saved -> slot_table_{key}.csv ({len(cell)} slots)")

        print("\n-- Per (line,direction) share in this cell (recomputed) --")
        for (line, direction), sub in cell.groupby(["route_name", "direction_group"]):
            n_total = len(sub)
            n_blocked = (sub["variant_type_v2"] == "blocked").sum()
            print(f"  {line} {direction}: {n_blocked}/{n_total} = {n_blocked/n_total:.1%} blocked-slots (pooled-hour n_slots, not observation n)")

        print("\n-- Per line combined (both directions; line 22: direction A only), matches docs/10 pooling --")
        for line, sub in cell.groupby("route_name"):
            # fix_22b_central_prompt.md -- direction_B never contributes to
            # the "blocked" numerator anymore (variant_merges forces it to
            # "non_corridor"), but pooling it in still dilutes the
            # denominator, so line 22's combined share is direction_A only,
            # matching docs/10's now-corrected pooling (config.LINE_22_SHARE_DIRECTION).
            if line == 22:
                sub = sub[sub["direction_group"] == config.LINE_22_SHARE_DIRECTION]
            n_total = len(sub)
            n_blocked = (sub["variant_type_v2"] == "blocked").sum()
            n_obs_sum = sub["n_observations"].sum()
            label = "Line 22 (dir A)" if line == 22 else f"Line {line}"
            print(f"  {label}: {n_blocked}/{n_total} slots = {n_blocked/n_total:.1%}; sum n_observations={n_obs_sum}")

        print("\n-- Timing spread --")
        ts = timing_spread(cell)
        print(ts.to_string(index=False))
        ts.to_csv(OUT_DIR / f"timing_spread_{key}.csv", index=False)

        print("\n-- Footprint overlap (corridor 17/19/22) --")
        overlap_corridor = footprint_overlap_for_line(effective_df, variant_summary, 22, footprints["corridor_17_19"])
        for line in [17, 19]:
            print(footprint_overlap_for_line(effective_df, variant_summary, line, footprints["corridor_17_19"]).to_string(index=False))
        print(overlap_corridor.to_string(index=False))

        print("\n-- Footprint overlap (Aza 9/97) --")
        for line in [9, 97]:
            print(footprint_overlap_for_line(effective_df, variant_summary, line, footprints["aza_9_97"]).to_string(index=False))

        title = f"{cell_spec['title']} -- Hour-Level Variant Type by Line/Direction"
        plot_cell_timeline(cell, title, OUT_DIR / f"timeline_{key}.png", LINE_ORDER_FOR_CELL[key])


def part_b():
    print("\n\n========== PART B: line 22, December ==========")
    effective_df, effective_summary, variant_summary = load_data()
    block_keys = BLOCK_KEYS

    dec22 = effective_df[(effective_df.route_name == 22) & (effective_df.month == 12)]
    dec_blocks = dec22.drop_duplicates(subset=block_keys)

    # Step 1: direction split, every December weekday (not just Wednesday)
    rows = []
    for day in [1, 2, 3, 4, 5]:
        for direction in ["direction_A", "direction_B"]:
            sub = dec_blocks[(dec_blocks.day_of_week == day) & (dec_blocks.direction_group == direction)]
            nb = int((sub.variant_type_v2 == "blocked").sum())
            rows.append({"day_of_week": day, "day_label": DAY_LABELS[day], "direction_group": direction,
                         "n_blocked": nb, "n_total": len(sub), "share": nb / len(sub) if len(sub) else np.nan})
        both = dec_blocks[dec_blocks.day_of_week == day]
        nb = int((both.variant_type_v2 == "blocked").sum())
        rows.append({"day_of_week": day, "day_label": DAY_LABELS[day], "direction_group": "BOTH",
                     "n_blocked": nb, "n_total": len(both), "share": nb / len(both) if len(both) else np.nan})
    direction_split = pd.DataFrame(rows)
    direction_split.to_csv(OUT_DIR / "line22_december_direction_split.csv", index=False)
    print(direction_split.to_string(index=False))

    # Step 2: duplicate-row check on df_cleaned (pre-merge) for this slice
    df_cleaned = pd.read_csv(config.DF_CLEANED_PATH, low_memory=False)
    raw_slice = df_cleaned[(df_cleaned.route_name == 22) & (df_cleaned.month == 12)]
    key_cols = ["route_name", "direction_group", "route_variant_id", "month", "day_of_week", "scheduled_departure_time", "stop_sequence"]
    dupe_key_groups = raw_slice.groupby(key_cols).size()
    dup_check = pd.DataFrame([{
        "n_key_groups": len(dupe_key_groups),
        "n_groups_with_gt1_row": int((dupe_key_groups > 1).sum()),
        "n_duplicated_record_ids": int(raw_slice["record_id"].duplicated().sum()),
    }])
    dup_check.to_csv(OUT_DIR / "line22_december_duplicate_check.csv", index=False)
    print("\n-- Duplicate-row check (raw df_cleaned, line22/Dec) --")
    print(dup_check.to_string(index=False))

    # Step 3: which merged variant(s) drive "blocked" in December, per direction, and their footprint overlap
    footprints, _ = build_footprints(effective_df, effective_summary, variant_summary)
    corridor_stops = footprints["corridor_17_19"]
    rows = []
    for direction in ["direction_A", "direction_B"]:
        sub = dec_blocks[dec_blocks.direction_group == direction]
        for vid, g in sub.groupby("route_variant_id"):
            stops = missing_stops(variant_summary, 22, direction, int(vid))
            rows.append({
                "direction_group": direction, "route_variant_id": int(vid),
                "variant_type_v2": g["variant_type_v2"].iloc[0],
                "n_december_blocks": len(g),
                "missing_stop_codes": sorted(stops),
                "n_missing": len(stops),
                "overlap_with_corridor_footprint": len(stops & corridor_stops),
            })
    variant_check = pd.DataFrame(rows)
    variant_check.to_csv(OUT_DIR / "line22_december_variant_check.csv", index=False)
    print("\n-- Which variant is 'blocked' in December, and does it touch the corridor footprint? --")
    print(variant_check.to_string(index=False))

    # Cross-check: same variant_id's behavior in every OTHER month (is Dec an outlier for direction_B?)
    b22 = effective_df[(effective_df.route_name == 22) & (effective_df.direction_group == "direction_B")]
    b22_blocks = b22.drop_duplicates(subset=block_keys)
    monthly = b22_blocks.pivot_table(index="month", columns="variant_type_v2", values="route_variant_id", aggfunc="count", fill_value=0)
    monthly["total"] = monthly.sum(axis=1)
    monthly["pct_blocked"] = (monthly.get("blocked", 0) / monthly["total"] * 100).round(1)
    monthly.to_csv(OUT_DIR / "line22_directionB_monthly_variant_share.csv")
    print("\n-- Line 22 direction_B: blocked share by month, whole year (is Dec an outlier?) --")
    print(monthly.to_string())

    # Step 4: fabrication/duplication check on December's direction_B
    # artifact blocks -- targets the specific raw variant ids (1, 4)
    # rather than variant_type_v2 == "blocked", since those are now
    # centrally reclassified "non_corridor" (fix_22b_central_prompt.md)
    # and this check must still run against the same blocks it always did.
    decB_blocked = dec22[(dec22.direction_group == "direction_B") & (dec22.route_variant_id.isin([1, 4]))]
    vectors = {}
    n_std0 = 0
    n_blocks = 0
    for key, g in decB_blocked.groupby(block_keys):
        g = g.sort_values("stop_sequence")
        vec = tuple(g["mean_cumulative_travel_time_min"].round(3).tolist())
        vectors.setdefault(vec, []).append(key)
        n_blocks += 1
        if (g["std_cumulative_travel_time_min"] == 0).all():
            n_std0 += 1
    n_dupe_vectors = sum(1 for ks in vectors.values() if len(ks) > 1)
    fabrication_check = pd.DataFrame([{
        "n_blocks": n_blocks, "n_unique_stop_level_vectors": len(vectors),
        "n_vectors_shared_by_gt1_block": n_dupe_vectors,
        "n_blocks_all_stops_std0": n_std0, "frac_std0": n_std0 / n_blocks if n_blocks else np.nan,
    }])
    fabrication_check.to_csv(OUT_DIR / "line22_december_fabrication_check.csv", index=False)
    print("\n-- Fabrication/duplication check (December, line22 direction_B blocked blocks) --")
    print(fabrication_check.to_string(index=False))

    # Control-line sanity check: 14/15 in December, every weekday
    blocks_all = effective_df.drop_duplicates(subset=block_keys)
    dec_all = blocks_all[blocks_all.month == 12]
    rows = []
    for line in [14, 15]:
        for day in [1, 2, 3, 4, 5]:
            sub = dec_all[(dec_all.route_name == line) & (dec_all.day_of_week == day)]
            if not len(sub):
                continue
            nb = int((sub.variant_type_v2 == "blocked").sum())
            rows.append({"route_name": line, "day_label": DAY_LABELS[day], "n_blocked": nb, "n_total": len(sub), "share": nb / len(sub)})
    control_check = pd.DataFrame(rows)
    control_check.to_csv(OUT_DIR / "control_sanity_december.csv", index=False)
    print("\n-- Control lines 14/15 sanity check, December weekdays --")
    print(control_check.to_string(index=False))


if __name__ == "__main__":
    part_a()
    part_b()
