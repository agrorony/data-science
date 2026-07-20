"""Stage 9 -- control-vs-protest line comparison.

Generalizes rony/variant_analysis.ipynb's Line-15-as-control narrative
using config.CONTROL_PAIRS (only pairs the user has actually verified
geographically -- pairing requires knowing which lines share road
segments, which isn't derivable from the data alone). Pairs with no
entry are skipped with a log message rather than guessed.

For each (protest_line -> control_line) pair: identifies the protest
line's "high-detour" (month, day, hour) blocks (>=50% of that hour's
trips used a "blocked" variant, in any cluster), then compares the
control line's own total travel time during those same blocks vs. all
other blocks. A real "traffic-only" control should show a real (if
smaller) slowdown during those windows since it shares the road, without
ever taking a detour itself (its own variant_type stays "regular"
throughout).

Note: this operates at the whole-route level. The original
line15_segment_impact.png narrowed this to one specific shared road
segment (identified via Hebrew stop-name keyword lookup) -- reproducing
that precision for new pairs needs the user to supply the shared segment
per pair; this stage gives the coarser, fully automatic version.
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from pipeline import config

DAY_LABELS = {1: "Sun", 2: "Mon", 3: "Tue", 4: "Wed", 5: "Thu", 6: "Fri", 7: "Sat"}
HIGH_DETOUR_THRESHOLD = 0.5


def load_data():
    df_cleaned = pd.read_csv(config.DF_CLEANED_PATH, low_memory=False)
    df_cleaned["hour_display"] = df_cleaned["scheduled_departure_time"].replace({25: 1, 26: 2})
    df_cleaned["day_label"] = df_cleaned["day_of_week"].map(DAY_LABELS)
    return df_cleaned


def high_detour_blocks(df_cleaned: pd.DataFrame, protest_line) -> pd.DataFrame:
    scope = df_cleaned[df_cleaned["route_name"] == protest_line]
    blocks = scope.drop_duplicates(subset=["direction_group", "route_variant_id", "month", "day_of_week", "scheduled_departure_time"])
    total = blocks.groupby(["month", "day_of_week", "scheduled_departure_time"]).size()
    blocked = blocks[blocks["variant_type"] == "blocked"].groupby(["month", "day_of_week", "scheduled_departure_time"]).size()
    fraction = (blocked / total).fillna(0)
    return fraction[fraction >= HIGH_DETOUR_THRESHOLD].reset_index(name="detour_fraction")


def control_travel_time(df_cleaned: pd.DataFrame, control_line) -> pd.DataFrame:
    scope = df_cleaned[(df_cleaned["route_name"] == control_line) & (df_cleaned["variant_type"] == "regular")]
    last_stop = scope.sort_values("stop_sequence").groupby(
        ["direction_group", "month", "day_of_week", "scheduled_departure_time"]
    ).tail(1)
    return last_stop


def run() -> None:
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    df_cleaned = load_data()

    pairs = {k: v for k, v in config.CONTROL_PAIRS.items() if v is not None}
    if not pairs:
        print("No CONTROL_PAIRS defined -- nothing to do for stage9.")
        return

    for protest_line, control_line in pairs.items():
        protest_line, control_line = int(protest_line), int(control_line)
        high_blocks = high_detour_blocks(df_cleaned, protest_line)
        if high_blocks.empty:
            print(f"line {protest_line} -> control {control_line}: no high-detour blocks found, skipping.")
            continue

        control_tt = control_travel_time(df_cleaned, control_line)
        high_key = set(zip(high_blocks["month"], high_blocks["day_of_week"], high_blocks["scheduled_departure_time"]))
        control_tt = control_tt.copy()
        control_tt["is_high_detour_window"] = control_tt.apply(
            lambda r: (r["month"], r["day_of_week"], r["scheduled_departure_time"]) in high_key, axis=1
        )

        by_hour = control_tt.groupby(["hour_display", "is_high_detour_window"])["mean_cumulative_travel_time_min"].median().unstack()
        if True not in by_hour.columns or False not in by_hour.columns:
            print(f"line {protest_line} -> control {control_line}: insufficient overlap between high-detour windows and control data, skipping.")
            continue
        delta = (by_hour[True] - by_hour[False]).dropna()

        fig, ax = plt.subplots(figsize=(9, 4))
        ax.bar(delta.index, delta.values, color="darkorange")
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_xlabel("Hour of day")
        ax.set_ylabel("Delta travel time (min)")
        ax.set_title(
            f"Control line {control_line} travel-time delta during line {protest_line}'s "
            f"high-detour windows (>={HIGH_DETOUR_THRESHOLD:.0%} of trips detoured)"
        )
        fig.tight_layout()
        out_path = config.FIGURES_DIR / f"control_comparison_{protest_line}_vs_{control_line}.png"
        fig.savefig(out_path, dpi=120)
        plt.close(fig)
        print(f"Saved -> {out_path}")

    skipped = [line for line in config.LINES if line not in config.CONTROL_PAIRS]
    if skipped:
        print(f"Skipped (no control line defined in config.CONTROL_PAIRS yet): {skipped}")


if __name__ == "__main__":
    run()
