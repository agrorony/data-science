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


def draw_panel(ax, pivot: pd.DataFrame, n_pivot: pd.DataFrame, title: str, fig) -> None:
    im = ax.imshow(pivot.values, cmap="Reds", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(MONTH_ORDER)))
    ax.set_xticklabels(MONTH_LABELS)
    ax.set_yticks(range(len(DAY_ORDER)))
    ax.set_yticklabels(DAY_ORDER)
    ax.set_title(title, fontsize=12, fontweight="bold")

    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            has_data = n_pivot.values[i, j] > 0
            val = pivot.values[i, j]
            text = f"{val:.0%}" if has_data else "-"
            color = "white" if val > 0.55 else "black"
            ax.text(j, i, text, ha="center", va="center", fontsize=7.5, color=color if has_data else "#999999")

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Share of hour-slots on a non-baseline (blocked) variant")


def run() -> None:
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    blocks = load_blocks()

    for line, line_blocks in blocks.groupby("route_name"):
        pivot, n_pivot = fraction_pivot(line_blocks)

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


if __name__ == "__main__":
    run()
