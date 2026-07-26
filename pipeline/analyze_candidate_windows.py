"""Phase 10 -- hunt for NEW candidate (month, day_of_week) windows worth an
hour-level deep dive, using a signal DIFFERENT from docs/06's disagreement
deep dive.

docs/06_blockade_frequency/disagreement_deep_dive.md already found and fully
explained the "majority near 100%, one outlier disagrees" pattern (line 22
direction B geometry, Saturdays in April/June). This script instead looks
for the opposite shape: (month, day_of_week) cells where NO line is
anywhere near saturation, but SEVERAL independent lines simultaneously show
a similar, non-trivial, elevated blocked-share relative to their own
typical/baseline level -- a "shared moderate signal" that wouldn't jump out
as a wall of red in the existing heatmaps.

Uses the exact same effective/merged classification as phase 06
(`pipeline.variant_merges.build_effective_df_cleaned`, `variant_type_v2`)
and the same month x day-of-week pooling (hours + directions pooled) as
`pipeline/plot_blockade_frequency.py` -- the loading/pivot/draw helpers below
are copied from that module rather than imported, because the on-disk copy
of pipeline/plot_blockade_frequency.py in this checkout is truncated (ends
mid-docstring around line 310, confirmed shorter than the same file at
HEAD via `git show HEAD:pipeline/plot_blockade_frequency.py`); importing it
directly raised a SyntaxError. This script does not modify that file.

Outputs (docs/10_candidate_windows/):
  - blockade_frequency_<line>.png for all 7 lines (same house style as 06)
  - blockade_all_lines_grid.png (7-panel grid, common 0-100% scale)
  - all_lines_month_day_share.csv (long-format line x month x day share + n)
  - candidate_windows.csv (ranked candidate cells with supporting numbers)
  - README.md (summary + rationale, written separately)
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pipeline import config, variant_merges as vm

DAY_LABELS = {1: "Sun", 2: "Mon", 3: "Tue", 4: "Wed", 5: "Thu", 6: "Fri", 7: "Sat"}
DAY_ORDER = list(DAY_LABELS.values())
MONTH_ORDER = list(range(1, 13))
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
LINE_GRID_ORDER = [9, 14, 15, 17, 19, 22, 97]

OUT_DIR = config.REPO_ROOT / "docs" / "10_candidate_windows"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ALL_LINES = LINE_GRID_ORDER

# Saturation / low-n / elevation thresholds -- documented in README.
SATURATION_CEIL = 0.85      # "near saturation" -- exclude cells where ANY line >= this
MIN_N_RELIABLE = 8          # cells with n_pivot < this are flagged low-confidence (CLAUDE.md issue #6)
ELEVATION_MARGIN = 0.15     # a line's cell share must exceed its own baseline by this much (pp) to count as "elevated"
MIN_LINES_AGREEING = 3      # need at least this many lines elevated at once


def load_blocks() -> pd.DataFrame:
    """Same effective-classification load as phase 06's load_blocks()."""
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


def fraction_pivot(blocks: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Copied verbatim from pipeline/plot_blockade_frequency.py."""
    total = blocks.groupby(["day_label", "month"]).size()
    non_baseline = blocks[blocks["is_non_baseline"]].groupby(["day_label", "month"]).size()
    frac = (non_baseline / total).fillna(0)
    pivot = frac.unstack("month").reindex(index=DAY_ORDER, columns=MONTH_ORDER).fillna(0)
    n_pivot = total.unstack("month").reindex(index=DAY_ORDER, columns=MONTH_ORDER).fillna(0)
    return pivot, n_pivot


def draw_panel(ax, pivot: pd.DataFrame, n_pivot: pd.DataFrame, title: str, fig, colorbar: bool = True, title_fontsize: float = 12):
    """Copied verbatim from pipeline/plot_blockade_frequency.py (house style:
    Reds colormap, 0-1 scale, % annotated, labeled colorbar, bold title)."""
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


def per_line_pivots(blocks: pd.DataFrame) -> dict[int, tuple[pd.DataFrame, pd.DataFrame]]:
    """fix_22b_central_prompt.md -- line 22 pooled both-directions is
    diluted by direction_B's untouched-by-the-closure schedule sitting in
    the denominator (its non-reference variants are "non_corridor", never
    "blocked", so they never add to the numerator either), so line 22 is
    computed from direction_A only here too, matching phase 06's policy
    (config.LINE_22_SHARE_DIRECTION) -- this is what makes this phase's
    numbers comparable to docs/06's."""
    pivots = {}
    for line in ALL_LINES:
        sub = blocks[blocks["route_name"] == line]
        if line == 22:
            sub = sub[sub["direction_group"] == config.LINE_22_SHARE_DIRECTION]
        pivot, n_pivot = fraction_pivot(sub)
        pivots[line] = (pivot, n_pivot)
    return pivots


def plot_per_line_heatmaps(pivots) -> None:
    for line in ALL_LINES:
        pivot, n_pivot = pivots[line]
        fig, ax = plt.subplots(figsize=(9, 4.2))
        title = (
            f"Line {line}" + (" (control)" if line in (14, 15) else "") + (" (direction A only)" if line == 22 else "")
            + " -- Blockade Share by Month and Day of Week"
        )
        draw_panel(ax, pivot, n_pivot, title, fig, colorbar=True)
        if line == 22:
            fig.text(0.5, -0.03, config.LINE_22_DIR_A_FOOTNOTE, ha="center", va="top", fontsize=8, wrap=True, style="italic")
        fig.tight_layout()
        out_path = OUT_DIR / f"blockade_frequency_{line}.png"
        fig.savefig(out_path, dpi=120, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved -> {out_path}")


def plot_grid(pivots) -> None:
    fig, axes = plt.subplots(4, 2, figsize=(15, 13.5))
    axes_flat = axes.ravel()
    fig.subplots_adjust(top=0.90, bottom=0.06, hspace=0.55, wspace=0.25, left=0.05, right=0.9)
    im = None
    for ax, line in zip(axes_flat, ALL_LINES):
        pivot, n_pivot = pivots[line]
        title = f"Line {line}" + (" (control)" if line in (14, 15) else "") + (" (dir A)" if line == 22 else "")
        im = draw_panel(ax, pivot, n_pivot, title, fig, colorbar=False, title_fontsize=11)
    for ax in axes_flat[len(ALL_LINES):]:
        ax.axis("off")
    fig.suptitle(
        "Phase 10 -- Blockade Share, All 7 Lines, Full Year\n"
        "(same pooling as docs/06 -- line 22: direction A only; search grid for new multi-line candidate windows)",
        fontsize=14, y=0.97,
    )
    cbar = fig.colorbar(im, ax=axes_flat[: len(ALL_LINES)], fraction=0.025, pad=0.02, shrink=0.8)
    cbar.set_label("Share of hour-slots on a non-baseline (blocked) variant")
    out_path = OUT_DIR / "blockade_all_lines_grid.png"
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved -> {out_path}")


def build_long_table(pivots) -> pd.DataFrame:
    rows = []
    for line in ALL_LINES:
        pivot, n_pivot = pivots[line]
        for day in DAY_ORDER:
            for month in MONTH_ORDER:
                share = pivot.loc[day, month]
                n = n_pivot.loc[day, month]
                rows.append({"route_name": line, "day_label": day, "month": month, "share": share, "n": int(n)})
    return pd.DataFrame(rows)


def compute_baselines(long_df: pd.DataFrame) -> pd.Series:
    """Each line's own baseline = median share across all cells with
    n >= MIN_N_RELIABLE for that line, excluding Saturday (Saturday is
    already known/expected to be different -- CLAUDE.md issue #5 -- so we
    want a weekday-typical baseline to compare weekday elevation against)."""
    weekday = long_df[(long_df["n"] >= MIN_N_RELIABLE) & (long_df["day_label"] != "Sat")]
    return weekday.groupby("route_name")["share"].median()


def find_candidates(long_df: pd.DataFrame, baselines: pd.Series) -> pd.DataFrame:
    long_df = long_df.copy()
    long_df["baseline"] = long_df["route_name"].map(baselines)
    long_df["elevated"] = (
        (long_df["n"] >= MIN_N_RELIABLE)
        & (long_df["share"] < SATURATION_CEIL)
        & (long_df["share"] >= long_df["baseline"] + ELEVATION_MARGIN)
    )

    reliable = long_df[long_df["n"] >= MIN_N_RELIABLE]
    max_share_per_cell = reliable.groupby(["month", "day_label"])["share"].max()
    no_saturation_cells = max_share_per_cell[max_share_per_cell < SATURATION_CEIL].index

    candidates = []
    for (month, day) in no_saturation_cells:
        cell = long_df[(long_df["month"] == month) & (long_df["day_label"] == day)]
        elevated_lines = cell[cell["elevated"]]
        if len(elevated_lines) >= MIN_LINES_AGREEING:
            candidates.append({
                "month": month,
                "month_label": MONTH_LABELS[month - 1],
                "day_label": day,
                "n_lines_elevated": len(elevated_lines),
                "lines_elevated": ", ".join(
                    f"{r.route_name}:{r.share:.0%}(n={r.n},base={r.baseline:.0%})"
                    for r in elevated_lines.sort_values("share", ascending=False).itertuples()
                ),
                "max_share_in_cell": cell[cell["n"] >= MIN_N_RELIABLE]["share"].max(),
                "min_n_among_elevated": elevated_lines["n"].min(),
            })
    cand_df = pd.DataFrame(candidates)
    if len(cand_df):
        cand_df = cand_df.sort_values(["n_lines_elevated", "min_n_among_elevated"], ascending=[False, False])
    return cand_df


def main():
    blocks = load_blocks()
    pivots = per_line_pivots(blocks)
    plot_per_line_heatmaps(pivots)
    plot_grid(pivots)

    long_df = build_long_table(pivots)
    long_df.to_csv(OUT_DIR / "all_lines_month_day_share.csv", index=False)
    print(f"Saved -> {OUT_DIR / 'all_lines_month_day_share.csv'}")

    baselines = compute_baselines(long_df)
    print("\nPer-line weekday baseline (median share, n>=8, excl. Saturday):")
    print(baselines)

    cand_df = find_candidates(long_df, baselines)
    cand_df.to_csv(OUT_DIR / "candidate_windows.csv", index=False)
    print(f"Saved -> {OUT_DIR / 'candidate_windows.csv'}")
    print("\nCandidates:")
    print(cand_df.to_string(index=False) if len(cand_df) else "(none found at current thresholds)")


if __name__ == "__main__":
    main()
