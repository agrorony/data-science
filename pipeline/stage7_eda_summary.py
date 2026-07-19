"""Stage 7 -- general EDA: coverage, count/confidence, travel-time anomalies.

Generalizes rony/eda_exploration.ipynb (see prompts/eda_agent_prompt.md)
from the old hardcoded 4-route MAIN_ROUTES list to all 7 lines / 13
(line, direction_group) groups, reading from the stage6 output
govData/df_cleaned.csv (already deduplicated upstream by
rebuild_ride_data_merged.py and stage4) instead of re-deriving dedup logic.

Travel-time-anomaly detection intentionally uses only variant_type=="regular"
rows for the per-route baseline (mean/std), since "blocked" detour variants
are expected to run long/differently -- mixing them into the baseline would
mask real anomalies and flag routine detours as "anomalies" redundantly
with stage8's detour-frequency analysis.

Produces:
  - rony/eda_summary_table.csv
  - rony/figures/heatmap_coverage.png
  - rony/figures/count_common_boxplot.png
  - rony/figures/travel_time_by_hour.png
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from pipeline import config

DAY_LABELS = {1: "Sun", 2: "Mon", 3: "Tue", 4: "Wed", 5: "Thu", 6: "Fri", 7: "Sat"}


def load_data() -> pd.DataFrame:
    df = pd.read_csv(config.DF_CLEANED_PATH)
    df["low_confidence"] = df["n_observations"] < config.LOW_CONFIDENCE_THRESHOLD
    df["hour_display"] = df["scheduled_departure_time"].replace({25: 1, 26: 2})
    df["day_label"] = df["day_of_week"].map(DAY_LABELS)
    df["group_label"] = df["route_name"].astype(str) + " / " + df["direction_group"].astype(str)
    return df


def coverage_gaps(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    confident = df[~df["low_confidence"]]
    for (group, day), sub in confident.groupby(["group_label", "day_label"]):
        active_hours = sorted(sub["hour_display"].unique())
        if not active_hours:
            continue
        hour_range = (min(active_hours), max(active_hours))
        gap_hours = [h for h in range(hour_range[0], hour_range[1] + 1) if h not in active_hours]
        rows.append(
            {
                "group_label": group,
                "day_label": day,
                "active_hours_count": len(active_hours),
                "hour_range": hour_range,
                "gap_hours": gap_hours,
                "gap_count": len(gap_hours),
            }
        )
    return pd.DataFrame(rows)


def plot_heatmap_coverage(df: pd.DataFrame, path) -> None:
    confident = df[~df["low_confidence"]]
    groups = sorted(confident["group_label"].unique())
    n = len(groups)
    ncols = 2
    nrows = -(-n // ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(12, 3.2 * nrows))
    axes = np.array(axes).reshape(-1)
    day_order = list(DAY_LABELS.values())

    for i, group in enumerate(groups):
        sub = confident[confident["group_label"] == group]
        pivot = (
            sub.groupby(["day_label", "hour_display"]).size().unstack(fill_value=0).reindex(day_order)
        )
        sns.heatmap(pivot, ax=axes[i], cmap="viridis", cbar=False)
        axes[i].set_title(group, fontsize=9)
        axes[i].set_xlabel("")
        axes[i].set_ylabel("")

    for j in range(n, len(axes)):
        axes[j].axis("off")

    fig.suptitle("Row coverage by day × hour, per line/direction (confident rows only)")
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_count_boxplot(df: pd.DataFrame, path) -> None:
    groups = sorted(df["group_label"].unique())
    n = len(groups)
    ncols = 2
    nrows = -(-n // ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(12, 3.2 * nrows))
    axes = np.array(axes).reshape(-1)
    day_order = list(DAY_LABELS.values())

    for i, group in enumerate(groups):
        sub = df[df["group_label"] == group]
        sns.boxplot(data=sub, x="day_label", y="n_observations", order=day_order, ax=axes[i])
        axes[i].axhline(config.LOW_CONFIDENCE_THRESHOLD, color="red", linestyle="--", linewidth=1)
        axes[i].set_title(group, fontsize=9)
        axes[i].set_xlabel("")

    for j in range(n, len(axes)):
        axes[j].axis("off")

    fig.suptitle(f"n_observations by day, per line/direction (red line = low-confidence threshold {config.LOW_CONFIDENCE_THRESHOLD})")
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(path, dpi=120)
    plt.close(fig)


def travel_time_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    confident = df[~df["low_confidence"] & (df["variant_type"] == "regular")]
    last_stop = (
        confident.sort_values("stop_sequence")
        .groupby(["group_label", "month", "day_label", "hour_display"])
        .tail(1)
    )
    stats = last_stop.groupby(["group_label", "day_label"])["mean_cumulative_travel_time_min"].agg(["mean", "std"])
    last_stop = last_stop.join(stats, on=["group_label", "day_label"])
    last_stop["z_score"] = (
        last_stop["mean_cumulative_travel_time_min"] - last_stop["mean"]
    ) / last_stop["std"]
    anomalies = last_stop[last_stop["z_score"].abs() > 2].copy()
    return anomalies.sort_values("z_score", key=lambda s: s.abs(), ascending=False)


def plot_travel_time_by_hour(df: pd.DataFrame, anomalies: pd.DataFrame, path) -> None:
    confident = df[~df["low_confidence"] & (df["variant_type"] == "regular")]
    last_stop = (
        confident.sort_values("stop_sequence")
        .groupby(["group_label", "month", "day_label", "hour_display"])
        .tail(1)
    )
    groups = sorted(confident["group_label"].unique())
    n = len(groups)
    ncols = 2
    nrows = -(-n // ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(12, 3.2 * nrows))
    axes = np.array(axes).reshape(-1)

    for i, group in enumerate(groups):
        sub = last_stop[last_stop["group_label"] == group]
        median_by_hour = sub.groupby(["day_label", "hour_display"])["mean_cumulative_travel_time_min"].median().reset_index()
        for day, day_sub in median_by_hour.groupby("day_label"):
            axes[i].plot(day_sub["hour_display"], day_sub["mean_cumulative_travel_time_min"], label=day, linewidth=1)
        anom_sub = anomalies[anomalies["group_label"] == group]
        if not anom_sub.empty:
            axes[i].scatter(anom_sub["hour_display"], anom_sub["mean_cumulative_travel_time_min"], color="red", marker="*", zorder=5)
        axes[i].set_title(group, fontsize=9)

    for j in range(n, len(axes)):
        axes[j].axis("off")

    fig.suptitle("Median total travel time by hour (regular-variant trips only; red star = |z|>2 anomaly)")
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(path, dpi=120)
    plt.close(fig)


def run() -> pd.DataFrame:
    sns.set_style("whitegrid")
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    df = load_data()
    gaps = coverage_gaps(df)
    plot_heatmap_coverage(df, config.FIGURES_DIR / "heatmap_coverage.png")
    plot_count_boxplot(df, config.FIGURES_DIR / "count_common_boxplot.png")
    anomalies = travel_time_anomalies(df)
    plot_travel_time_by_hour(df, anomalies, config.FIGURES_DIR / "travel_time_by_hour.png")

    low_conf_pct = (
        df.groupby(["group_label", "day_label"])["low_confidence"].mean().rename("low_conf_pct") * 100
    )
    median_count = df.groupby(["group_label", "day_label"])["n_observations"].median().rename("median_count_common")
    anomaly_hours = (
        anomalies.groupby(["group_label", "day_label"])["hour_display"]
        .apply(lambda s: ",".join(str(h) for h in sorted(s.unique())))
        .rename("anomaly_hours")
    )

    summary = gaps.set_index(["group_label", "day_label"]).join([low_conf_pct, median_count, anomaly_hours]).reset_index()
    summary["anomaly_hours"] = summary["anomaly_hours"].fillna("")
    summary.to_csv(config.EDA_SUMMARY_TABLE_PATH, index=False, encoding="utf-8-sig")

    print(f"Saved -> {config.EDA_SUMMARY_TABLE_PATH} ({len(summary)} rows)")
    print(f"Saved -> {config.FIGURES_DIR / 'heatmap_coverage.png'}")
    print(f"Saved -> {config.FIGURES_DIR / 'count_common_boxplot.png'}")
    print(f"Saved -> {config.FIGURES_DIR / 'travel_time_by_hour.png'}")
    print(f"{len(anomalies)} travel-time anomalies found (|z|>2) across all groups.")

    return summary


if __name__ == "__main__":
    run()
