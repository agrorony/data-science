"""Phase 04 headline figures.

**Round (section D):** one barplot spanning all 7 lines: mean end-to-end
baseline travel time, both directions pooled into a single distribution
per line.

**Revision round 3, section E:** error bars now show the standard error
of the mean (SEM = std / sqrt(n)) instead of the raw standard deviation
-- SEM answers "how precisely do we know the mean", std still answers
"how chaotic is this line's trip duration" and is kept as a reported
number. Bars are colored per line via config.LINE_COLORS (section A).
Also adds a second figure, `baseline_travel_time_by_hour.png`: each
line's baseline end-to-end travel time by departure hour, one curve per
line, SEM shading.

Output: docs/04_baselines/travel_time_all_lines.png,
docs/04_baselines/baseline_travel_time_by_hour.png
"""

from __future__ import annotations

import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from pipeline import config, variant_merges as vm, pooled_analysis as pa
from pipeline import style  # noqa: F401

OUT_DIR = config.REPO_ROOT / "docs" / "04_baselines"
OUTPUT_PATH = OUT_DIR / "travel_time_all_lines.png"
BY_HOUR_PATH = OUT_DIR / "baseline_travel_time_by_hour.png"


def sem(s: pd.Series) -> float:
    n = s.count()
    return s.std() / math.sqrt(n) if n > 1 else float("nan")


def plot_all_lines_bar(baseline: pd.DataFrame) -> pd.DataFrame:
    stats = (
        baseline.groupby("route_name")["end_time_min"]
        .agg(mean="mean", std="std", n="count")
        .reset_index()
        .sort_values("mean", ascending=False)
    )
    stats["sem"] = stats["std"] / stats["n"].pow(0.5)

    fig, ax = plt.subplots(figsize=(11, 6))
    x = range(len(stats))
    colors = [config.LINE_COLORS[int(l)] for l in stats["route_name"]]
    ax.bar(x, stats["mean"], yerr=stats["sem"], capsize=6, color=colors, ecolor="black", error_kw={"linewidth": 1.5})
    ax.set_xticks(x)
    ax.set_xticklabels([f"Line {int(l)}" for l in stats["route_name"]])
    ax.set_ylabel("Mean end-to-end travel time (min)\nbaseline variant, both directions pooled")
    ax.set_title("Baseline Trip Duration by Line -- Mean ± SEM, Both Directions Pooled")
    ax.grid(alpha=0.3, axis="y")

    for xi, row in zip(x, stats.itertuples()):
        ax.text(xi, row.mean + row.sem + 1.5, f"{row.mean:.0f} min (SEM ±{row.sem:.2f})\nstd={row.std:.1f}, n={row.n:,}", ha="center", fontsize=8)

    fig.text(
        0.5, -0.05,
        "How to read: bar height is each line's mean baseline end-to-end travel time, pooling both directions "
        "into one distribution; the black error bar is the standard error of the mean (SEM = std / sqrt(n)) -- how "
        "precisely the mean itself is known, not how spread out individual trips are. Std (reported per bar) still "
        "tells the chaos story: a large std means that line's individual trip durations vary a lot block to block, "
        "even though a large n can still pin the mean down precisely (small SEM).",
        ha="center", va="top", fontsize=8, wrap=True,
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved -> {OUTPUT_PATH}")
    print(stats.to_string(index=False))
    return stats


def plot_by_hour(baseline: pd.DataFrame) -> None:
    b = pa.drop_late_night_hours(baseline)
    grouped = b.groupby(["route_name", "scheduled_departure_time"])["end_time_min"]
    by_hour = grouped.agg(mean="mean", sem=sem, n="count").reset_index()

    fig, ax = plt.subplots(figsize=(11, 6.5))
    present = set(by_hour["route_name"].unique())
    for line in [l for l in style.LINE_ORDER if l in present]:
        sub = by_hour[by_hour["route_name"] == line].sort_values("scheduled_departure_time")
        color = config.LINE_COLORS[int(line)]
        ax.plot(sub["scheduled_departure_time"], sub["mean"], color=color, linewidth=2, marker="o", markersize=3.5, label=f"Line {int(line)}")
        ax.fill_between(sub["scheduled_departure_time"], sub["mean"] - sub["sem"], sub["mean"] + sub["sem"], color=color, alpha=0.15)

    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Mean end-to-end travel time (min)\nbaseline variant, both directions pooled")
    ax.set_title("Baseline Travel Time by Departure Hour, All Lines")
    ax.legend(fontsize=9, title="Line", ncol=2)
    ax.grid(alpha=0.3, axis="y")

    fig.text(
        0.5, -0.05,
        "How to read: for each line and departure hour, mean baseline end-to-end travel time (both directions "
        "pooled); shaded band is ±1 SEM. Lines that rise sharply at certain hours run slower at those departure "
        "times; a wide band means fewer observations (less certain mean) at that hour.",
        ha="center", va="top", fontsize=8, wrap=True,
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(BY_HOUR_PATH, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved -> {BY_HOUR_PATH}")


def run() -> None:
    df_cleaned = pd.read_csv(config.DF_CLEANED_PATH, low_memory=False)
    variant_summary = pd.read_csv(config.VARIANT_SUMMARY_PATH)
    effective_df, _ = vm.build_effective_df_cleaned(df_cleaned, variant_summary)

    endpoints = pa.block_endpoints(effective_df)
    baseline = pa.baseline_endpoints(endpoints)

    plot_all_lines_bar(baseline)
    plot_by_hour(baseline)


if __name__ == "__main__":
    run()
