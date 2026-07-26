"""Phase 13 -- full-year relaxed-threshold blockade scan + confirmed-hours
calendar. Redoes and broadens phase 10/11's (month, day_of_week) scan under
a simpler, more permissive rule: flag any cell where >=3 lines independently
show blocked-share > 10%, no saturation exclusion, no baseline-relative
comparison, no n floor for inclusion (low-n cells are flagged, not dropped).
Every flagged cell then gets the hour-level treatment (no manual approval
gate -- this is a systematic pass, unlike phases 10/11's two-stage review).

Uses only the effective/merged classification
(`pipeline.variant_merges.build_effective_df_cleaned`, `variant_type_v2`)
on `govData/df_cleaned.csv`. Line 22's aggregate share is computed from
direction_A only throughout (`config.LINE_22_SHARE_DIRECTION`), consistent
with the project-wide fix in `fix_22b_central_prompt.md` -- direction_B can
never be "blocked" anymore (`variant_merges` forces it to "non_corridor"),
so pooling it into a shared denominator would still dilute line 22's real
exposure the same way the pre-fix pooled numerator used to inflate it.

Reuses phase 11's footprint derivation (`pipeline.analyze_deep_dive_windows
.build_footprints`) rather than redefining a new one, per the task brief.

Outputs (docs/13_full_year_calendar/):
  - blockade_frequency_full_<line>.png (all 7 lines) + grid
  - all_lines_month_day_share.csv, flagged_cells.csv
  - timeline_<month>_<day>.png per flagged cell
  - n_anomaly_report.csv (only >=2x / <=0.5x cases)
  - confirmed_hours.csv, calendar grid figure(s)
  - README.md (written separately)
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

from pipeline import config, variant_merges as vm
from pipeline.analyze_deep_dive_windows import (
    DAY_LABELS, MONTH_LABELS, BLOCK_KEYS, load_data, build_footprints, missing_stops,
    VT_COLORS, VT_CODE, MIN_N_RELIABLE,
)

DAY_ORDER = list(DAY_LABELS.values())
MONTH_ORDER = list(range(1, 13))
ALL_LINES = [9, 14, 15, 17, 19, 22, 97]
PROTEST_LINES = [9, 17, 19, 22, 97]

OUT_DIR = config.REPO_ROOT / "docs" / "13_full_year_calendar"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SHARE_THRESHOLD = 0.10   # relaxed rule: share > 10% counts as "elevated"
MIN_LINES_AGREEING = 3
MIN_N_RELIABLE_CELL = config.LOW_CONFIDENCE_THRESHOLD  # 8, CLAUDE.md issue #6

# Cells already given a full hour-level treatment elsewhere -- cite, don't re-derive.
PHASE11_CELLS = {(11, "Wed"), (12, "Wed"), (10, "Mon")}


def documented_reason(month: int, day_label: str) -> str | None:
    if day_label == "Sat":
        return ("Saturday pattern already documented in docs/06_blockade_frequency "
                "(see disagreement_deep_dive.md for the line 22B nuance, now fixed centrally)")
    if (month, day_label) in PHASE11_CELLS:
        return "hour-level deep dive already done in docs/11_deep_dive_candidate_windows/README.md"
    return None


def block_table(effective_df: pd.DataFrame) -> pd.DataFrame:
    g = effective_df.groupby(BLOCK_KEYS)
    out = g.agg(
        n_observations=("n_observations", lambda s: s.mode().iloc[0]),
        variant_type_v2=("variant_type_v2", "first"),
    ).reset_index()
    out["day_label"] = out["day_of_week"].map(DAY_LABELS)
    return out


def line_slice_for_share(blocks: pd.DataFrame, line: int) -> pd.DataFrame:
    """The project's line-22 direction_A-only convention for any aggregate
    (pooled-hour) share -- see pipeline.config.LINE_22_SHARE_DIRECTION."""
    sub = blocks[blocks["route_name"] == line]
    if line == 22:
        sub = sub[sub["direction_group"] == config.LINE_22_SHARE_DIRECTION]
    return sub


def fraction_pivot(sub: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    total = sub.groupby(["day_label", "month"]).size()
    non_baseline = sub[sub["variant_type_v2"] == "blocked"].groupby(["day_label", "month"]).size()
    frac = (non_baseline / total).fillna(0)
    pivot = frac.unstack("month").reindex(index=DAY_ORDER, columns=MONTH_ORDER).fillna(0)
    n_pivot = total.unstack("month").reindex(index=DAY_ORDER, columns=MONTH_ORDER).fillna(0)
    return pivot, n_pivot


def draw_panel(ax, pivot, n_pivot, title, fig, colorbar=True, title_fontsize=12):
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
        cbar.set_label("Share of hour-slots on a blocked variant")
    return im


def plot_per_line_heatmaps(pivots) -> None:
    for line in ALL_LINES:
        pivot, n_pivot = pivots[line]
        fig, ax = plt.subplots(figsize=(9, 4.6))
        label = "Line 22 (dir A)" if line == 22 else f"Line {line}" + (" (control)" if line in (14, 15) else "")
        draw_panel(ax, pivot, n_pivot, f"{label} -- Blockade Share by Month and Day of Week (relaxed scan)", fig)
        if line == 22:
            fig.text(0.5, -0.03, config.LINE_22_DIR_A_FOOTNOTE, ha="center", fontsize=8, wrap=True)
        fig.tight_layout()
        out_path = OUT_DIR / f"blockade_frequency_full_{line}.png"
        fig.savefig(out_path, dpi=120, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved -> {out_path}")


def plot_grid(pivots) -> None:
    fig, axes = plt.subplots(4, 2, figsize=(15, 14))
    axes_flat = axes.ravel()
    fig.subplots_adjust(top=0.90, bottom=0.08, hspace=0.55, wspace=0.25, left=0.05, right=0.9)
    im = None
    for ax, line in zip(axes_flat, ALL_LINES):
        pivot, n_pivot = pivots[line]
        label = "Line 22 (dir A)" if line == 22 else f"Line {line}" + (" (control)" if line in (14, 15) else "")
        im = draw_panel(ax, pivot, n_pivot, label, fig, colorbar=False, title_fontsize=11)
    for ax in axes_flat[len(ALL_LINES):]:
        ax.axis("off")
    fig.suptitle(
        "Phase 13 -- Full-Year Blockade Share, Relaxed Scan (share > 10%, >=3 lines flags a cell)",
        fontsize=14, y=0.97,
    )
    cbar = fig.colorbar(im, ax=axes_flat[: len(ALL_LINES)], fraction=0.025, pad=0.02, shrink=0.8)
    cbar.set_label("Share of hour-slots on a blocked variant")
    fig.text(0.5, 0.01, config.LINE_22_DIR_A_FOOTNOTE, ha="center", fontsize=8, wrap=True)
    out_path = OUT_DIR / "blockade_all_lines_grid_full.png"
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved -> {out_path}")


def build_long_table(pivots) -> pd.DataFrame:
    rows = []
    for line in ALL_LINES:
        pivot, n_pivot = pivots[line]
        for day in DAY_ORDER:
            for month in MONTH_ORDER:
                rows.append({
                    "route_name": line, "day_label": day, "month": month,
                    "share": pivot.loc[day, month], "n": int(n_pivot.loc[day, month]),
                })
    return pd.DataFrame(rows)


def find_flagged_cells(long_df: pd.DataFrame) -> pd.DataFrame:
    long_df = long_df.copy()
    long_df["elevated"] = long_df["share"] > SHARE_THRESHOLD
    long_df["low_n"] = long_df["n"] < MIN_N_RELIABLE_CELL

    candidates = []
    for (month, day), cell in long_df.groupby(["month", "day_label"]):
        elevated = cell[cell["elevated"]]
        if len(elevated) < MIN_LINES_AGREEING:
            continue
        doc = documented_reason(month, day)
        candidates.append({
            "month": month, "month_label": MONTH_LABELS[month - 1], "day_label": day,
            "n_lines_elevated": len(elevated),
            "lines_elevated_list": sorted(elevated["route_name"].tolist()),
            "lines_elevated": ", ".join(
                f"{r.route_name}:{r.share:.0%}(n={r.n}{'*' if r.low_n else ''})"
                for r in elevated.sort_values("share", ascending=False).itertuples()
            ),
            "any_low_n": bool(elevated["low_n"].any()),
            "documented_elsewhere": doc is not None,
            "documented_reason": doc or "not previously examined at hour level",
        })
    df = pd.DataFrame(candidates)
    if len(df):
        df = df.sort_values(["n_lines_elevated", "month"], ascending=[False, True]).reset_index(drop=True)
    return df


def part_a():
    effective_df, effective_summary, variant_summary = load_data()
    blocks = block_table(effective_df)

    pivots = {}
    for line in ALL_LINES:
        sub = line_slice_for_share(blocks, line)
        pivots[line] = fraction_pivot(sub)

    plot_per_line_heatmaps(pivots)
    plot_grid(pivots)

    long_df = build_long_table(pivots)
    long_df.to_csv(OUT_DIR / "all_lines_month_day_share.csv", index=False)
    print(f"Saved -> all_lines_month_day_share.csv ({len(long_df)} rows)")

    flagged = find_flagged_cells(long_df)
    flagged.to_csv(OUT_DIR / "flagged_cells.csv", index=False)
    print(f"\nFlagged {len(flagged)} cells (relaxed rule: >=3 lines, share > 10%):")
    print(flagged[["month_label", "day_label", "n_lines_elevated", "lines_elevated", "documented_reason"]].to_string(index=False))

    return effective_df, effective_summary, variant_summary, blocks, flagged


if __name__ == "__main__":
    part_a()
