"""Phase 06 -- blockade/variant frequency heatmaps, house style.

Matches rony/figures/variant_frequency_heatmap.png exactly (the
pre-2026-07-19 reference this project's house style is defined against):
Reds colormap, vmin=0/vmax=1, % annotated in every cell, one labeled
colorbar per panel, month on x, day-of-week on y, bold panel titles.

**Revision round (sections C, E):** directions are now pooled into a
single combined figure per line (the per-direction panels have been
removed); "non-baseline (blocked)" now uses `variant_type_v2` from
`pipeline.variant_merges` -- the merged/excluded variant set (section A)
classified by the new absolute stop-count rule (section B: any
non-reference variant with >15 stops is "blocked", no fraction
threshold) -- instead of stage5's original fraction-based `variant_type`
column. This is what surfaces line 22's blockades correctly (see
docs/07_blockade_investigation's addendum).

One PNG per line: rony/figures/blockade_frequency_<line>.png.
"""

from __future__ import annotations

import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch, Rectangle
import numpy as np
import pandas as pd

from pipeline import config, variant_merges as vm, pooled_analysis as pa, stats_tests as st
from pipeline import style  # noqa: F401

PROTEST_LINES = [9, 17, 19, 22, 97]

DAY_LABELS = {1: "Sun", 2: "Mon", 3: "Tue", 4: "Wed", 5: "Thu", 6: "Fri", 7: "Sat"}
DAY_ORDER = list(DAY_LABELS.values())
MONTH_ORDER = list(range(1, 13))
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load_blocks() -> pd.DataFrame:
    df_cleaned = pd.read_csv(
        config.DF_CLEANED_PATH,
        usecols=["route_name", "direction_group", "route_variant_id", "month", "day_of_week", "scheduled_departure_time", "n_observations"],
        low_memory=False,
    )
    variant_summary = pd.read_csv(config.VARIANT_SUMMARY_PATH)
    effective_df, _ = vm.build_effective_df_cleaned(df_cleaned, variant_summary)

    blocks = effective_df.drop_duplicates(
        subset=["route_name", "direction_group", "route_variant_id", "month", "day_of_week", "scheduled_departure_time"]
    ).copy()
    blocks["day_label"] = blocks["day_of_week"].map(DAY_LABELS)
    blocks["is_non_baseline"] = blocks["variant_type_v2"] == "blocked"
    return blocks


def fraction_pivot(blocks: pd.DataFrame) -> pd.DataFrame:
    total = blocks.groupby(["day_label", "month"]).size()
    non_baseline = blocks[blocks["is_non_baseline"]].groupby(["day_label", "month"]).size()
    frac = (non_baseline / total).fillna(0)
    pivot = frac.unstack("month").reindex(index=DAY_ORDER, columns=MONTH_ORDER).fillna(0)
    n_pivot = total.unstack("month").reindex(index=DAY_ORDER, columns=MONTH_ORDER).fillna(0)
    return pivot, n_pivot


def draw_panel(ax, pivot: pd.DataFrame, n_pivot: pd.DataFrame, title: str, fig, colorbar: bool = True, title_fontsize: float = 12):
    im = ax.imshow(pivot.values, cmap="Reds", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(MONTH_ORDER)))
    ax.set_xticklabels(MONTH_LABELS)
    ax.set_yticks(range(len(DAY_ORDER)))
    ax.set_yticklabels(DAY_ORDER)
    ax.set_title(title, fontsize=title_fontsize, fontweight="bold")

    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            has_data = n_pivot.values[i, j] > 0
            val = pivot.values[i, j]
            text = f"{val:.0%}" if has_data else "-"
            color = "white" if val > 0.55 else "black"
            ax.text(j, i, text, ha="center", va="center", fontsize=7.5, color=color if has_data else "#999999")

    if colorbar:
        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label("Share of hour-slots on a non-baseline (blocked) variant")
    return im


LINE_GRID_ORDER = style.LINE_ORDER  # fixed order: 17, 19, 22, 9, 97, 14, 15
OUT_DIR = config.REPO_ROOT / "docs" / "06_blockade_frequency"


def plot_combined_all_lines(pivots: dict[int, tuple[pd.DataFrame, pd.DataFrame]], out_path) -> None:
    """Section C -- all 7 lines' heatmaps as subplots (4x2 grid), one
    shared colorbar, common 0-100% scale."""
    fig, axes = plt.subplots(4, 2, figsize=(15, 13.5))
    axes_flat = axes.ravel()
    fig.subplots_adjust(top=0.90, bottom=0.06, hspace=0.55, wspace=0.25, left=0.05, right=0.9)

    im = None
    for ax, line in zip(axes_flat, LINE_GRID_ORDER):
        pivot, n_pivot = pivots[line]
        title = f"Line {line}" + (" (control)" if line in (14, 15) else "") + (" (dir A)" if line == 22 else "")
        im = draw_panel(ax, pivot, n_pivot, title, fig, colorbar=False, title_fontsize=11)

    for ax in axes_flat[len(LINE_GRID_ORDER):]:
        ax.axis("off")

    fig.suptitle(
        "Estimated Blockade Frequency, All Lines\n"
        "Share of hour-slots (month x day of week) using a non-baseline (blocked) variant, both directions pooled "
        "(line 22: direction A only)",
        fontsize=14, y=0.97,
    )
    cbar = fig.colorbar(im, ax=axes_flat[: len(LINE_GRID_ORDER)], fraction=0.025, pad=0.02, shrink=0.8)
    cbar.set_label("Share of hour-slots on a non-baseline (blocked) variant")
    fig.text(
        0.5, 0.01,
        "How to read: each panel is one line's month x day-of-week blockade-share heatmap on a shared 0-100% scale, "
        "so panels are directly comparable; '-' = no data for that cell. "
        + config.LINE_22_DIR_A_FOOTNOTE,
        ha="center", va="top", fontsize=9, wrap=True,
    )
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved -> {out_path}")


SATURDAY_SUMMARY_GROUPS = [
    ("Shared\nblocked\nsegment", [17, 19, 22]),
    ("Aza St.\nnon-shared", [9, 97]),
    ("Controls", [14, 15]),
]


def plot_saturday_summary(
    pivots: dict[int, tuple[pd.DataFrame, pd.DataFrame]],
    out_path,
) -> None:
    """Rows=lines, columns=months, cell=Saturday blockade share (%), one
    compact panel comparing all lines at a glance. Revision round 3,
    section D: rows grouped 17/19/22 (shared blocked segment), 9/97 (Aza
    St. non-shared), 14/15 (controls), with a separator line and group
    label between each block, row labels colored via config.LINE_COLORS
    (section A).

    Revision round 4, section B / fix_22b_central_prompt.md: line 22's row
    reads `pivots[22]`, which `run()` already computes from direction_A
    only (config.LINE_22_SHARE_DIRECTION) -- direction_B barely touches the
    blockade footprint and pooling it in would dilute line 22's real
    corridor exposure. Row label becomes "22 (dir A)"; no separate
    direction-A-only computation lives in this function anymore."""
    row_order = [line for _, lines in SATURDAY_SUMMARY_GROUPS for line in lines]
    sat_share = pd.DataFrame({line: pivots[line][0].loc["Sat"] for line in row_order}).T
    sat_n = pd.DataFrame({line: pivots[line][1].loc["Sat"] for line in row_order}).T

    fig, ax = plt.subplots(figsize=(10, 4.6))
    row_labels = [f"Line {line} (dir A)" if line == 22 else f"Line {line}" for line in row_order]
    im = ax.imshow(sat_share.values, cmap="Reds", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(MONTH_ORDER)))
    ax.set_xticklabels(MONTH_LABELS)
    ax.set_yticks(range(len(row_order)))
    ax.set_yticklabels(row_labels)
    for line, tick in zip(row_order, ax.get_yticklabels()):
        tick.set_color(config.LINE_COLORS[line])
        tick.set_fontweight("bold")
    ax.set_title("Saturday Blockade Share by Line and Month", fontsize=13, fontweight="bold")

    for i in range(sat_share.shape[0]):
        for j in range(sat_share.shape[1]):
            has_data = sat_n.values[i, j] > 0
            val = sat_share.values[i, j]
            text = f"{val:.0%}" if has_data else "-"
            color = "white" if val > 0.55 else "black"
            ax.text(j, i, text, ha="center", va="center", fontsize=8, color=color if has_data else "#999999")

    # Group separators + labels
    boundary = -0.5
    for group_label, group_lines in SATURDAY_SUMMARY_GROUPS:
        boundary += len(group_lines)
        if boundary < len(row_order) - 0.5:
            ax.axhline(boundary, color="black", linewidth=1.3)
        center = boundary - len(group_lines) / 2
        ax.text(
            -0.42, center, group_label, ha="right", va="center", fontsize=7.5, style="italic",
            linespacing=1.3, transform=ax.get_yaxis_transform(),
        )

    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("Saturday share of hour-slots on a non-baseline (blocked) variant")
    fig.text(
        0.5, -0.05,
        "How to read: blockades concentrate on Saturdays project-wide (docs/06_blockade_frequency/README.md); this "
        "panel isolates the Saturday row of every line's heatmap so the seven lines can be compared at a glance. "
        "Rows are grouped and separated by physical exposure to the closure (see group labels at left). "
        + config.LINE_22_DIR_A_FOOTNOTE,
        ha="center", va="top", fontsize=8, wrap=True,
    )
    fig.subplots_adjust(left=0.24)
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved -> {out_path}")


# ---------------------------------------------------------------------------
# Section C (revision round 3) -- 100%-vs-other disagreement windows
# ---------------------------------------------------------------------------

# (month, day_label) cells where protest lines 9/17/97 sit at 100% but 19
# and/or 22 sit substantially lower -- found by scanning fraction_pivot for
# cells with >=3 lines at >=90% and >=1 line below 70% (n>=3 per line).
DISAGREEMENT_WINDOWS = [(4, "Sat"), (6, "Sat")]


def plot_disagreement_windows(blocks: pd.DataFrame, out_path) -> pd.DataFrame:
    """Section C -- for cells where most protest lines show ~100% blockade
    share but one or two disagree, show every line's actual per-(hour,
    direction) schedule and variant type for that exact cell: does the
    disagreeing line simply run extra hours the 100%-lines don't operate
    (a scheduling/denominator artifact), or does it run the SAME
    hour-slots but on its regular/baseline variant (genuine differential
    exposure)? Extends docs/07_blockade_investigation's Hypothesis 4
    with concrete per-window evidence, without touching that folder."""
    rows_for_table = []
    fig, axes = plt.subplots(1, len(DISAGREEMENT_WINDOWS), figsize=(8.5 * len(DISAGREEMENT_WINDOWS), 4.3))
    if len(DISAGREEMENT_WINDOWS) == 1:
        axes = [axes]

    cmap = ListedColormap(["#eeeeee", "#4C72B0", "#d62728"])
    for ax, (month, day_label) in zip(axes, DISAGREEMENT_WINDOWS):
        cell = blocks[(blocks["month"] == month) & (blocks["day_label"] == day_label) & (blocks["route_name"].isin(PROTEST_LINES))]
        col_keys = sorted(set(zip(cell["scheduled_departure_time"], cell["direction_group"])))
        col_labels = [f"{h}:00\n{d.replace('direction_', '')}" for h, d in col_keys]

        grid = np.zeros((len(PROTEST_LINES), len(col_keys)))  # 0=no service, 1=reference/regular, 2=blocked
        for li, line in enumerate(PROTEST_LINES):
            by_key = {
                (r.scheduled_departure_time, r.direction_group): r.variant_type_v2
                for r in cell[cell["route_name"] == line].itertuples()
            }
            for ci, key in enumerate(col_keys):
                vt = by_key.get(key)
                grid[li, ci] = 2 if vt == "blocked" else (1 if vt is not None else 0)
                rows_for_table.append({"month": month, "day": day_label, "route_name": line, "hour": key[0], "direction_group": key[1], "variant_type_v2": vt})

        ax.imshow(grid, cmap=cmap, vmin=0, vmax=2, aspect="auto")
        ax.set_xticks(range(len(col_labels)))
        ax.set_xticklabels(col_labels, fontsize=8)
        shares = {
            l: f"{(grid[li] == 2).sum()}/{(grid[li] > 0).sum()}"
            for li, l in enumerate(PROTEST_LINES) if (grid[li] > 0).sum() > 0
        }
        ax.set_yticks(range(len(PROTEST_LINES)))
        ax.set_yticklabels([f"Line {l} ({shares.get(l, '-')})" for l in PROTEST_LINES], fontsize=9)
        for l, tick in zip(PROTEST_LINES, ax.get_yticklabels()):
            tick.set_color(config.LINE_COLORS[l])
            tick.set_fontweight("bold")
        month_name = MONTH_LABELS[month - 1]
        ax.set_title(f"{day_label} {month_name} (blocked/total slots per line)", fontsize=10, fontweight="bold")

    legend = [
        Patch(color="#d62728", label="Blocked variant"),
        Patch(color="#4C72B0", label="Reference/regular variant"),
        Patch(color="#eeeeee", label="No service this hour-slot"),
    ]
    fig.legend(handles=legend, loc="lower center", ncol=3, fontsize=9, bbox_to_anchor=(0.5, -0.05))
    fig.suptitle(
        "Why Do Protest Lines Disagree in 'Mostly-100%' Windows? Per-Hour Schedule, Two Example Saturdays",
        fontsize=13, fontweight="bold", y=1.05,
    )
    fig.text(
        0.5, -0.12,
        "How to read: each column is one (hour, direction) slot actually operated that Saturday; cell color is that "
        "line's variant type in that exact slot. Lines 17/9/97 are red (blocked) in nearly every slot shown; lines "
        "19 and especially 22 run the SAME hour-slots but some of them blue (regular) -- their lower overall share "
        "is genuine differential exposure at the same time, not extra out-of-window service diluting the denominator.",
        ha="center", fontsize=8, wrap=True,
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved -> {out_path}")
    return pd.DataFrame(rows_for_table)


# ---------------------------------------------------------------------------
# Revision round 4, section A -- line 22B Saturday timeline + pass-through cost
#
# docs/06_blockade_frequency/disagreement_deep_dive.md's Hypotheses 1/2/bonus
# finding, as one figure: 22B doesn't detour around the 17/19 closure like
# every other shared-corridor line/direction does -- it keeps driving
# through on its reference route, at a small time cost.
# ---------------------------------------------------------------------------

TIMELINE_ROWS = [
    (17, "direction_A"), (17, "direction_B"),
    (19, "direction_A"), (19, "direction_B"),
    (22, "direction_A"), (22, "direction_B"),
]
TIMELINE_HOURS = list(range(19, 25))


def saturday_evening_share_grid(blocks: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Per (line, direction) row and Saturday evening hour (19:00-24:00): the
    share of Saturdays with data for that slot on which the line ran a
    blocked (`variant_type_v2 == "blocked"`) variant. A "Saturday" is one
    distinct month's worth of Saturday data (the finest granularity the
    aggregated data has -- there is no per-calendar-date column). Returns
    (share, k, n) where share = k/n (NaN when n == 0, i.e. that
    line/direction never ran that hour on any Saturday), k = count of
    blocked Saturdays, n = count of Saturdays with data, both per cell."""
    sat = blocks[blocks["day_label"] == "Sat"]
    row_labels = [f"{line}{direction[-1]}" for line, direction in TIMELINE_ROWS]
    k_rows, n_rows = {}, {}
    for (line, direction), row_label in zip(TIMELINE_ROWS, row_labels):
        sub = sat[(sat["route_name"] == line) & (sat["direction_group"] == direction)]
        k_row, n_row = [], []
        for h in TIMELINE_HOURS:
            s = sub[sub["scheduled_departure_time"] == h]
            n_row.append(int(s["month"].nunique()))
            k_row.append(int(s.loc[s["is_non_baseline"], "month"].nunique()))
        k_rows[row_label] = k_row
        n_rows[row_label] = n_row
    k_df = pd.DataFrame.from_dict(k_rows, orient="index", columns=TIMELINE_HOURS)
    n_df = pd.DataFrame.from_dict(n_rows, orient="index", columns=TIMELINE_HOURS)
    share = (k_df / n_df.replace(0, np.nan)).astype(float)
    return share, k_df, n_df


def line22b_passthrough_cost(effective_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """22B's reference-route end-to-end Saturday travel time, split by
    whether the (month, hour) slot is one where lines 17/19 (either
    direction) ran a blocked variant that Saturday -- reproduces
    disagreement_deep_dive.md's bonus finding (~4.5 min gap, n=21 vs 5)."""
    scope = effective_df[(effective_df["route_name"].isin([17, 19])) & (effective_df["day_of_week"] == 7)]
    blocked = scope[scope["variant_type_v2"] == "blocked"]
    blocked_slots = set(zip(blocked["month"], blocked["scheduled_departure_time"]))

    endpoints = pa.block_endpoints(effective_df, min_observations=0)
    ep = endpoints[
        (endpoints["route_name"] == 22) & (endpoints["direction_group"] == "direction_B") & (endpoints["day_of_week"] == 7)
    ]
    ref = ep[ep["variant_type_v2"] == "reference"].copy()
    ref["group"] = [
        "17/19 blockade slot" if key in blocked_slots else "other Saturday slot"
        for key in zip(ref["month"], ref["scheduled_departure_time"])
    ]
    summary = ref.groupby("group")["end_time_min"].agg(n="count", mean="mean", median="median")
    summary = summary.reindex(["17/19 blockade slot", "other Saturday slot"])
    return ref, summary


def line22b_passthrough_stats(ref: pd.DataFrame) -> dict:
    """docs/12_statistics comparison -- 22B reference-route travel time,
    17/19-blockade Saturday slot (n=21) vs. other Saturday slot (n=5),
    unmatched (these are not day/hour-matched pairs, just two pools of
    Saturday slots). Small control group -- expect a wide CI."""
    a = ref.loc[ref["group"] == "17/19 blockade slot", "end_time_min"].to_numpy()
    b = ref.loc[ref["group"] == "other Saturday slot", "end_time_min"].to_numpy()
    return st.run_full_comparison(a, b)


def plot_saturday_timeline_and_cost_22b(blocks: pd.DataFrame, effective_df: pd.DataFrame, out_path) -> dict:
    share, k_df, n_df = saturday_evening_share_grid(blocks)
    ref, summary = line22b_passthrough_cost(effective_df)
    passthrough_stats = line22b_passthrough_stats(ref)

    fig, (ax_top, ax_bottom) = plt.subplots(2, 1, figsize=(9, 10.3), gridspec_kw={"height_ratios": [1, 0.9]})

    share_arr = share.values.astype(float)
    n_arr = n_df.values
    cmap = matplotlib.colormaps["Reds"].copy()
    cmap.set_bad(color="white")
    im = ax_top.imshow(np.ma.masked_invalid(share_arr), cmap=cmap, vmin=0, vmax=1, aspect="auto")

    for i in range(share_arr.shape[0]):
        for j in range(share_arr.shape[1]):
            if n_arr[i, j] == 0:
                ax_top.add_patch(Rectangle(
                    (j - 0.5, i - 0.5), 1, 1,
                    facecolor="#cfcfcf", hatch="///", edgecolor="white", linewidth=0.5,
                ))
            else:
                val = share_arr[i, j]
                color = "white" if val > 0.55 else "black"
                ax_top.text(j, i, f"{k_df.values[i, j]}/{n_arr[i, j]}", ha="center", va="center", fontsize=8, color=color)

    ax_top.set_xticks(range(len(TIMELINE_HOURS)))
    ax_top.set_xticklabels([f"{h % 24:02d}:00" for h in TIMELINE_HOURS])
    ax_top.set_yticks(range(len(share.index)))
    ax_top.set_yticklabels(share.index)
    row_line = {f"{line}{direction[-1]}": line for line, direction in TIMELINE_ROWS}
    for row_label, tick in zip(share.index, ax_top.get_yticklabels()):
        tick.set_color(config.LINE_COLORS[row_line[row_label]])
        tick.set_fontweight("bold")
    ax_top.set_xlabel("Saturday hour of day")

    sat = blocks[blocks["day_label"] == "Sat"]
    months_present = sorted(sat["month"].unique())
    n_saturdays_max = len(months_present)
    month_range = f"{MONTH_LABELS[months_present[0] - 1]}-{MONTH_LABELS[months_present[-1] - 1]}" if months_present else "n/a"
    subtitle = (
        f"Each cell: share of the Saturdays with data for that slot (up to {n_saturdays_max}, months "
        f"{month_range}) on which the line ran a detour (blocked) variant; k/n Saturdays printed in each cell."
    )
    fig.suptitle("Saturday Evening, 19:00-24:00: Who Detours, Who Keeps Running", fontsize=12, fontweight="bold", y=0.995)
    fig.text(0.5, 0.955, subtitle, ha="center", va="top", fontsize=8.5, style="italic")

    cbar = fig.colorbar(im, ax=ax_top, fraction=0.046, pad=0.04)
    cbar.set_label("Share of Saturdays on a detour variant")
    legend = [Patch(facecolor="#cfcfcf", hatch="///", edgecolor="white", label="No service / no data")]
    ax_top.legend(handles=legend, loc="upper left", bbox_to_anchor=(1.32, 1), fontsize=8, borderaxespad=0, frameon=False)

    order = ["17/19 blockade slot", "other Saturday slot"]
    x = range(len(order))
    bar_colors = ["#d62728", "#4C72B0"]
    ax_bottom.bar(x, summary["mean"], color=bar_colors, alpha=0.75, width=0.5)
    for xi, grp in zip(x, order):
        row = summary.loc[grp]
        ax_bottom.text(xi, row["mean"] + 1, f"n={int(row['n'])}\nmean={row['mean']:.1f} min", ha="center", fontsize=9)
    ax_bottom.set_xticks(x)
    ax_bottom.set_xticklabels(["Saturday slots\nwhen 17/19 blocked", "Other Saturday\nslots"])
    ax_bottom.set_ylabel("22B reference-route end-to-end travel time (min)")
    ax_bottom.set_title("Line 22B's Pass-Through Cost", fontsize=12, fontweight="bold")
    ax_bottom.grid(axis="y", alpha=0.3)

    gap = summary.loc["17/19 blockade slot", "mean"] - summary.loc["other Saturday slot", "mean"]
    row_22b = share.loc["22B"].dropna()
    b22_desc = (
        "22B's share is 0% throughout (its non-reference variants are non-corridor 1-stop swaps, never a real "
        "detour -- variant_merges.LINE_22_NON_CORRIDOR_DIRECTION)"
        if row_22b.max() == 0
        else f"22B's share stays low ({row_22b.min():.0%}-{row_22b.max():.0%}) throughout"
    )
    caption = (
        "How to read: top -- share of Saturdays each line-direction ran a detour variant at that evening hour "
        f"(k/n Saturdays with data, see subtitle above); 17A/17B/19A/19B/22A start near 100% early evening and taper "
        f"off as regular service resumes later, but {b22_desc} -- it doesn't detour "
        "around the closure, it drives through it. "
        f"Bottom -- 22B's own reference-route travel time in the n={int(summary.loc['17/19 blockade slot','n'])} "
        f"Saturday slots when 17/19 were actually blocked vs. the n={int(summary.loc['other Saturday slot','n'])} "
        "other Saturday slots it ran its reference route (small control group -- treat as suggestive, not "
        f"conclusive). It pays {gap:+.1f} min passing through during the blockade window "
        "(docs/06_blockade_frequency/disagreement_deep_dive.md). "
        f"Statistical test (docs/12_statistics, n=5 control group -- small n): {st.format_delta_annotation(passthrough_stats)}."
    )
    fig.text(0.5, -0.03, caption, ha="center", va="top", fontsize=8, wrap=True)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved -> {out_path}  (gap={gap:+.1f} min, {dict(summary['n'])})")
    return {"share": share, "k": k_df, "n": n_df, "cost_summary": summary, "gap_min": gap}


def run() -> None:
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    blocks = load_blocks()

    pivots: dict[int, tuple[pd.DataFrame, pd.DataFrame]] = {}
    for line, line_blocks in blocks.groupby("route_name"):
        # fix_22b_central_prompt.md -- line 22 pooled both-directions is
        # still diluted by direction_B's untouched-by-the-closure schedule
        # even after the central non_corridor fix (its full denominator
        # counts, it just never contributes to the numerator), so every
        # aggregate figure reports line 22 from direction_A only
        # (config.LINE_22_SHARE_DIRECTION). Storing the direction_A-only
        # pivot under pivots[22] means every downstream consumer of
        # `pivots` (plot_combined_all_lines, plot_saturday_summary) gets
        # the corrected line automatically, with one computation.
        is_line22 = line == 22
        if is_line22:
            line_blocks = line_blocks[line_blocks["direction_group"] == config.LINE_22_SHARE_DIRECTION]
        pivot, n_pivot = fraction_pivot(line_blocks)
        pivots[line] = (pivot, n_pivot)

        fig, ax = plt.subplots(1, 1, figsize=(9, 5.6))
        panel_title = f"Line {line} -- direction A only" if is_line22 else f"Line {line} -- all directions combined"
        draw_panel(ax, pivot, n_pivot, panel_title, fig)

        pooling_desc = "direction A only" if is_line22 else "both directions pooled"
        fig.suptitle(
            f"Line {line}: Estimated Blockade Frequency\n"
            f"Share of hour-slots (month x day of week) using a non-baseline (blocked) variant, {pooling_desc}",
            fontsize=13,
        )
        caption = (
            "How to read: each cell is the share of that month/day-of-week's hour-slots whose bus ran a non-baseline "
            f"(blocked, >15-stop) variant, {pooling_desc}; '-' = no data for that cell."
        )
        if is_line22:
            caption += " " + config.LINE_22_DIR_A_FOOTNOTE
        fig.text(0.5, -0.02, caption, ha="center", va="top", fontsize=8, wrap=True)
        fig.tight_layout(rect=[0, 0, 1, 0.88])
        out_path = config.FIGURES_DIR / f"blockade_frequency_{line}.png"
        fig.savefig(out_path, dpi=120, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved -> {out_path}")

        docs_line_dir = OUT_DIR / f"line_{line}"
        if docs_line_dir.exists():
            shutil.copy2(out_path, docs_line_dir / out_path.name)
            print(f"Synced -> {docs_line_dir / out_path.name}")

    plot_combined_all_lines(pivots, OUT_DIR / "blockade_all_lines.png")
    plot_saturday_summary(pivots, OUT_DIR / "blockade_saturday_summary.png")

    disagreement_table = plot_disagreement_windows(blocks, OUT_DIR / "disagreement_windows.png")
    disagreement_csv = OUT_DIR / "disagreement_windows.csv"
    disagreement_table.to_csv(disagreement_csv, index=False)
    print(f"Saved -> {disagreement_csv}")

    effective_df_full, _ = vm.build_effective_df_cleaned()
    line22_dir = OUT_DIR / "line_22"
    line22_dir.mkdir(parents=True, exist_ok=True)
    timeline_result = plot_saturday_timeline_and_cost_22b(
        blocks, effective_df_full, line22_dir / "saturday_timeline_and_cost_22B.png"
    )
    kn_table = timeline_result["k"].astype(str) + "/" + timeline_result["n"].astype(str)
    kn_table.index.name = "line_direction"
    kn_csv = line22_dir / "saturday_timeline_data.csv"
    kn_table.to_csv(kn_csv)
    print(f"Saved -> {kn_csv}")


if __name__ == "__main__":
    run()
