"""Phase 04 headline figure (revision round D) -- one barplot spanning
all 7 lines: mean end-to-end baseline travel time, both directions
pooled into a single distribution per line, with error bars from the
pooled standard deviation. Tall error bars = a line whose trip duration
is unpredictable; short error bars = a consistent, reliable trip time.

Output: docs/04_baselines/travel_time_all_lines.png
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from pipeline import config, variant_merges as vm, pooled_analysis as pa

OUTPUT_PATH = config.REPO_ROOT / "docs" / "04_baselines" / "travel_time_all_lines.png"


def run() -> None:
    df_cleaned = pd.read_csv(config.DF_CLEANED_PATH, low_memory=False)
    variant_summary = pd.read_csv(config.VARIANT_SUMMARY_PATH)
    effective_df, _ = vm.build_effective_df_cleaned(df_cleaned, variant_summary)

    endpoints = pa.block_endpoints(effective_df)
    baseline = pa.baseline_endpoints(endpoints)

    stats = (
        baseline.groupby("route_name")["end_time_min"]
        .agg(mean="mean", std="std", n="count")
        .reset_index()
        .sort_values("mean", ascending=False)
    )

    fig, ax = plt.subplots(figsize=(11, 6))
    x = range(len(stats))
    bars = ax.bar(x, stats["mean"], yerr=stats["std"], capsize=6, color="#4C72B0", ecolor="#C44E52", error_kw={"linewidth": 1.5})
    ax.set_xticks(x)
    ax.set_xticklabels([f"Line {int(l)}" for l in stats["route_name"]])
    ax.set_ylabel("Mean end-to-end travel time (min)\nbaseline variant, both directions pooled")
    ax.set_title("Baseline Trip Duration by Line -- Mean ± Std. Dev., Both Directions Pooled")
    ax.grid(alpha=0.3, axis="y")

    for xi, row in zip(x, stats.itertuples()):
        ax.text(xi, row.mean + row.std + 1.5, f"{row.mean:.0f}±{row.std:.0f} min\n(n={row.n:,})", ha="center", fontsize=8)

    fig.text(
        0.5, -0.05,
        "How to read: bar height is each line's mean baseline end-to-end travel time, pooling both directions "
        "into one distribution; the red error bar is one standard deviation. A tall error bar means that line's "
        "trip duration is unpredictable (varies a lot block to block); a short one means it's consistently close "
        "to the mean.",
        ha="center", va="top", fontsize=8, wrap=True,
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved -> {OUTPUT_PATH}")
    print(stats.to_string(index=False))


if __name__ == "__main__":
    run()
