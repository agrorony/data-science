"""Phase 05 -- baseline vs. stop-skipping variant figures.

One horizontal bar chart per (line, direction): each bar is a displayed,
stop-skipping variant, showing its day/hour-matched segment travel-time
delta vs. the baseline (govData/skip_comparison.csv, from
compute_skip_comparison.py). Green = faster than baseline across the
skipped segment, red = slower. Bars are annotated with n (matched
day/hour slots) and how many stops the variant skips.

Output: rony/figures/skip_comparison_<line>_<group>.png
"""

from __future__ import annotations

import ast

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch

from pipeline import config
from pipeline.stage10_route_deviation_heatmaps import rtl


def run() -> None:
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(config.GOV_DATA_DIR / "skip_comparison.csv")
    df["missing_stop_names"] = df["missing_stop_names"].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else []
    )

    for (line, group), sub in df.groupby(["route_name", "direction_group"]):
        sub = sub[sub["segment_time_delta_min"].notna()].sort_values("segment_time_delta_min")
        if sub.empty:
            print(f"line {line} / {group}: no variants with a measurable segment delta, skipped.")
            continue

        labels = [
            f"variant {int(r.route_variant_id)} | skips {int(r.n_missing)} stop(s) | n_matched={int(r.n_segment_matches)}"
            for r in sub.itertuples()
        ]
        colors = ["#1D9E75" if v < 0 else "#C44E52" for v in sub["segment_time_delta_min"]]

        fig_height = max(3, 0.4 * len(sub) + 1.5)
        fig, ax = plt.subplots(figsize=(11, fig_height))
        bars = ax.barh(labels, sub["segment_time_delta_min"], color=colors)
        ax.axvline(0, color="black", linewidth=0.8)
        ax.set_xlabel("Segment travel-time delta vs. baseline (min) -- day-of-week/hour matched")
        ax.set_title(f"Baseline vs. stop-skipping variants -- line {line} / {group}")
        ax.grid(alpha=0.3, axis="x")

        for bar, val in zip(bars, sub["segment_time_delta_min"]):
            ax.text(
                val + (0.15 if val >= 0 else -0.15), bar.get_y() + bar.get_height() / 2,
                f"{val:+.1f}", va="center", ha="left" if val >= 0 else "right", fontsize=8,
            )

        legend = [
            Patch(color="#1D9E75", label="Faster than baseline across the skipped segment"),
            Patch(color="#C44E52", label="Slower than baseline across the skipped segment"),
        ]
        ax.legend(handles=legend, loc="lower right", fontsize=8)

        fig.text(
            0.5, -0.02,
            "How to read: each bar compares one stop-skipping variant to the baseline (reference) route, "
            "restricted to the exact stops the variant skips, and only using the baseline's own travel time at "
            "the same day-of-week/hour the variant was observed (not the baseline's all-hours average). "
            "Negative (green) = skipping this segment is faster than the baseline; positive (red) = slower.",
            ha="center", va="top", fontsize=8, wrap=True,
        )

        fig.savefig(
            config.FIGURES_DIR / f"skip_comparison_{line}_{group}.png",
            dpi=120, bbox_inches="tight",
        )
        plt.close(fig)
        print(f"Saved -> rony/figures/skip_comparison_{line}_{group}.png ({len(sub)} variants)")


if __name__ == "__main__":
    run()
