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
import pandas as pd

from pipeline import config, variant_merges as vm

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


LINE_GRID_ORDER = [9, 14, 15, 17, 19, 22, 97]
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
        title = f"Line {line}" + (" (control)" if line in (14, 15) else "")
        im = draw_panel(ax, pivot, n_pivot, title, fig, colorbar=False, title_fontsize=11)

    for ax in axes_flat[len(LINE_GRID_ORDER):]:
        ax.axis("off")

    fig.suptitle(
        "Estimated Blockade Frequency, All Lines\n"
        "Share of hour-slots (month x day of week) using a non-baseline (blocked) variant, both directions pooled",
        fontsize=14, y=0.97,
    )
    cbar = fig.colorbar(im, ax=axes_flat[: len(LINE_GRID_ORDER)], fraction=0.025, pad=0.02, shrink=0.8)
    cbar.set_label("Share of hour-slots on a non-baseline (blocked) variant")
    fig.text(
        0.5, 0.01,
        "How to read: each panel is one line's month x day-of-week blockade-share heatmap on a shared 0-100% scale, "
        "so panels are directly comparable; '-' = no data for that cell.",
        ha="center", va="top", fontsize=9, wrap=True,
    )
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved -> {out_path}")


def plot_saturday_summary(pivots: dict[int, tuple[pd.DataFrame, pd.DataFrame]], out_path) -> None:
    """Optional extra -- rows=lines, columns=months, cell=Saturday
    blockade share (%), one compact panel comparing all lines at a glance."""
    sat_share = pd.DataFrame({line: pivots[line][0].loc["Sat"] for line in LINE_GRID_ORDER}).T
    sat_n = pd.DataFrame({line: pivots[line][1].loc["Sat"] for line in LINE_GRID_ORDER}).T

    fig, ax = plt.subplots(figsize=(9, 4.2))
    row_labels = [f"Line {line}" + (" (control)" if line in (14, 15) else "") for line in LINE_GRID_ORDER]
    im = ax.imshow(sat_share.values, cmap="Reds", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(MONTH_ORDER)))
    ax.set_xticklabels(MONTH_LABELS)
    ax.set_yticks(range(len(LINE_GRID_ORDER)))
    ax.set_yticklabels(row_labels)
    ax.set_title("Saturday Blockade Share by Line and Month", fontsize=13, fontweight="bold")

    for i in range(sat_share.shape[0]):
        for j in range(sat_share.shape[1]):
            has_data = sat_n.values[i, j] > 0
            val = sat_share.values[i, j]
            text = f"{val:.0%}" if has_data else "-"
            color = "white" if val > 0.55 else "black"
            ax.text(j, i, text, ha="center", va="center", fontsize=8, color=color if has_data else "#999999")

    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("Saturday share of hour-slots on a non-baseline (blocked) variant")
    fig.text(
        0.5, -0.05,
        "How to read: blockades concentrate on Saturdays project-wide (docs/06_blockade_frequency/README.md); this "
        "panel isolates the Saturday row of every line's heatmap so the seven lines can be compared at a glance.",
        ha="center", va="top", fontsize=8, wrap=True,
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved -> {out_path}")


def run() -> None:
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    blocks = load_blocks()

    pivots: dict[int, tuple[pd.DataFrame, pd.DataFrame]] = {}
    for line, line_blocks in blocks.groupby("route_name"):
        pivot, n_pivot = fraction_pivot(line_blocks)
        pivots[line] = (pivot, n_pivot)

        fig, ax = plt.subplots(1, 1, figsize=(9, 5.6))
        draw_panel(ax, pivot, n_pivot, f"Line {line} -- all directions combined", fig)

        fig.suptitle(
            f"Line {line}: Estimated Blockade Frequency\n"
            "Share of hour-slots (month x day of week) using a non-baseline (blocked) variant, both directions pooled",
            fontsize=13,
        )
        fig.text(
            0.5, -0.02,
            "How to read: each cell is the share of that month/day-of-week's hour-slots whose bus ran a non-baseline "
            "(blocked, >15-stop) variant, both directions of the line pooled together; '-' = no data for that cell.",
            ha="center", va="top", fontsize=8, wrap=True,
        )
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


if __name__ == "__main__":
    run()
