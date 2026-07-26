"""Phase 05 (revision round, section F) -- delta-style baseline vs.
blocked/special-variant comparison, replacing the original stop-skip
bar charts entirely.

Anchor: the top panel of docs/08_control_lines_15_14/line_15_hourly_pattern.png
(pipeline.plot_control_comparison) -- a per-hour line chart of the
travel-time gap, dashed zero line, grey shading over thin-data hours.
Here the two groups being compared are the line's own baseline variant
vs. its blocked/special variant (not blockade-window vs. matched-normal
month, as in phase 08), with both directions of the line pooled
(section C). Only the confirmed post-merge, post-exclusion variant set
(pipeline.variant_merges) enters the statistics -- excluded raw variants
never appear at all, and merged variants use their combined counts.

**Revision round 3, section B:** a merged variant is only eligible to
count as "blocked" here if its `count > MIN_BLOCKED_VARIANT_COUNT` --
see `filter_significant_blocked`'s docstring for why (singleton/
near-singleton near-full-length variants are recording noise, not real
detours, and are the *entire* reason control lines 14/15 showed up in
this phase at all).

One figure per line: docs/05_skip_comparison/line_<N>_baseline_vs_blocked_delta.png
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from pipeline import config, variant_merges as vm, pooled_analysis as pa, stats_tests as st
from pipeline import style  # noqa: F401

OUT_DIR = config.REPO_ROOT / "docs" / "05_skip_comparison"
THIN_THRESHOLD = 8  # fewer than this many blocked blocks at an hour -> shaded as thin
MIN_BLOCKED_VARIANT_COUNT = 5  # matches plot_variants_revised.RAW_COUNT_THRESHOLD


def filter_significant_blocked(effective_df: pd.DataFrame, effective_summary: pd.DataFrame, min_count: int = MIN_BLOCKED_VARIANT_COUNT) -> pd.DataFrame:
    """Section B2 -- every line (control or not) has a long tail of
    count<=5, near-full-length 'blocked' merged variants (missing just
    1-11 stops out of 30-67) that are near-certainly one-off recording
    noise, not real detours. Protest lines also have one or two dominant
    real-detour variants (count in the dozens to hundreds) so the noise
    is a minor contaminant there; control lines 14/15 have *no* dominant
    variant at all -- their entire 'blocked' bucket is this noise. This
    restricts blocked-variant eligibility to `count > min_count`, reusing
    plot_variants_revised.RAW_COUNT_THRESHOLD's own "real enough to
    matter" convention, WITHOUT touching variant_type_v2 itself (still
    used unmodified by phases 06/08/09)."""
    sig = effective_summary[effective_summary["count"] > min_count]
    eligible = set(zip(sig["route_name"], sig["direction_group"], sig["route_variant_id"]))

    keys = list(zip(effective_df["route_name"], effective_df["direction_group"], effective_df["route_variant_id"]))
    is_blocked = effective_df["variant_type_v2"] == "blocked"
    keep = [(not b) or (k in eligible) for b, k in zip(is_blocked, keys)]
    return effective_df[keep].copy()


def hour_medians(endpoints: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Return (median end-to-end time by hour, n blocks by hour). Hours
    25/26 (01:00/02:00 next day) are dropped entirely -- revision round 2
    global rule, see pooled_analysis.drop_late_night_hours."""
    e = pa.drop_late_night_hours(endpoints)
    e["hour_display"] = e["scheduled_departure_time"]
    med = e.groupby("hour_display")["end_time_min"].median()
    n = e.groupby("hour_display")["end_time_min"].size()
    return med, n


def compute_delta(baseline_ep: pd.DataFrame, blocked_ep: pd.DataFrame) -> tuple[pd.Series, list, pd.Series]:
    """Return (delta by hour, thin hours, blocked n by hour) -- shared by
    the per-line figure and the cross-line combined figure (section B)."""
    base_med, base_n = hour_medians(baseline_ep)
    blocked_med, blocked_n = hour_medians(blocked_ep)

    hours = sorted(set(base_med.index) & set(blocked_med.index))
    delta = pd.Series({h: blocked_med[h] - base_med[h] for h in hours}).sort_index()
    thin_hours = [h for h in hours if blocked_n.get(h, 0) < THIN_THRESHOLD]
    return delta, thin_hours, blocked_n


def phase05_stats(baseline_ep: pd.DataFrame, blocked_ep: pd.DataFrame) -> dict:
    """docs/12_statistics comparison -- blocked/special variant vs. baseline,
    all hours pooled, unmatched (the two groups are different route
    choices for the same slot pool, not day/hour-matched pairs)."""
    a = blocked_ep["end_time_min"].to_numpy()
    b = baseline_ep["end_time_min"].to_numpy()
    return st.run_full_comparison(a, b)


def plot_line_delta(line, baseline_ep: pd.DataFrame, blocked_ep: pd.DataFrame, out_path, stats_result: dict | None = None, stats_label: str | None = None, dir_a_only: bool = False) -> dict:
    delta, thin_hours, blocked_n = compute_delta(baseline_ep, blocked_ep)

    fig, ax = plt.subplots(figsize=(10, 5.5))

    band_labeled = False
    for hr in thin_hours:
        ax.axvspan(hr - 0.4, hr + 0.4, color="grey", alpha=0.18, zorder=0, label="Thin data (<8 blocked blocks)" if not band_labeled else "")
        band_labeled = True

    ax.plot(delta.index, delta.values, color="#d62728", linewidth=2.5, marker="o", markersize=5, label="Blocked variant minus baseline")
    ax.axhline(0, color="black", linewidth=1, linestyle="--", alpha=0.6)
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Extra travel time on blocked/special variant (min)")
    title = f"Line {line}" + (" (direction A only)" if dir_a_only else "") + ": Baseline vs. Blocked/Special Variant -- Travel-Time Delta by Hour"
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    overall_delta = blocked_ep["end_time_min"].median() - baseline_ep["end_time_min"].median()
    verdict = "costs time" if overall_delta > 0 else "saves time"
    pooling_desc = "direction A only" if dir_a_only else "both directions pooled"
    caption = (
        f"How to read: for each hour of day, the line plots (median travel time on the line's blocked/special "
        f"variant) minus (median travel time on its baseline variant), {pooling_desc} and using only the "
        f"confirmed post-merge variant set; positive = the special route is slower, negative = faster. Grey bands "
        f"mark hours with fewer than {THIN_THRESHOLD} blocked-variant observations. Overall (all hours pooled): the "
        f"special route {verdict} by {abs(overall_delta):.1f} min (n={len(blocked_ep):,} blocked vs "
        f"n={len(baseline_ep):,} baseline blocks)."
    )
    if stats_result is not None:
        label_note = f" ({stats_label})" if stats_label else ""
        caption += f" Statistical test{label_note} (docs/12_statistics): {st.format_delta_annotation(stats_result)}."
    if dir_a_only:
        caption += " " + config.LINE_22_DIR_A_FOOTNOTE
    fig.text(
        0.5, -0.05, caption,
        ha="center", va="top", fontsize=8, wrap=True,
    )
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)

    return {
        "route_name": line,
        "n_baseline": len(baseline_ep),
        "n_blocked": len(blocked_ep),
        "overall_median_delta_min": round(overall_delta, 1),
        "n_hours_thin": len(thin_hours),
        "n_hours_total": len(delta),
    }


CROSS_LINE_ORDER = [17, 19, 22, 9, 97]
CROSS_LINE_COLORS = config.LINE_COLORS  # section A -- single palette, defined once in config.py


def plot_all_lines_delta(line_deltas: dict[int, pd.Series], out_path) -> None:
    """Section B -- one combined figure: per-hour travel-time delta of the
    blocked variant vs. the baseline ride, one curve per line, lines
    17/19/22 in reds and 9/97 in purples, shared axes."""
    fig, ax = plt.subplots(figsize=(11, 6))

    for line in CROSS_LINE_ORDER:
        delta = line_deltas.get(line)
        if delta is None or delta.empty:
            continue
        ax.plot(
            delta.index, delta.values, color=CROSS_LINE_COLORS[line],
            linewidth=2.2, marker="o", markersize=4.5, label=f"Line {line} (dir A)" if line == 22 else f"Line {line}",
        )

    ax.axhline(0, color="black", linewidth=1, linestyle="--", alpha=0.6)
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Extra travel time on blocked/special variant vs. baseline (min)")
    ax.set_title(
        "Blocked/Special Variant vs. Baseline -- Travel-Time Delta by Hour, All Lines",
        fontsize=12, fontweight="bold",
    )
    ax.legend(fontsize=9, title="Line")
    ax.grid(True, alpha=0.3, axis="y")

    fig.text(
        0.5, -0.05,
        "How to read: for each hour of day and each line, (median travel time on that line's blocked/special "
        "variant) minus (median travel time on its baseline variant), both directions pooled and using only the "
        "confirmed post-merge variant set. Curves above the dashed zero line mean the detour costs time at that "
        "hour; curves below mean it saves time. " + config.LINE_22_DIR_A_FOOTNOTE,
        ha="center", va="top", fontsize=8, wrap=True,
    )
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Section F (revision round 3) -- line 97 detour-distance figure
# ---------------------------------------------------------------------------

DETOUR_DISTANCE_HEADLINE_LINE = 97
DETOUR_DISTANCE_OTHER_LINES = [9, 17, 19, 22]


def dominant_blocked_variant(effective_summary: pd.DataFrame, route_name: int) -> pd.Series:
    """The largest-count merged 'blocked' variant for a line -- its real,
    well-supported detour, as opposed to the count<=5 noise filtered out
    of the delta figures above (section B)."""
    sub = effective_summary[(effective_summary["route_name"] == route_name) & (effective_summary["variant_type_v2"] == "blocked")]
    return sub.loc[sub["count"].idxmax()]


def variant_distance_curve(effective_df: pd.DataFrame, route_name: int, direction_group: str, route_variant_id: int) -> pd.Series:
    sub = effective_df[
        (effective_df["route_name"] == route_name)
        & (effective_df["direction_group"] == direction_group)
        & (effective_df["route_variant_id"] == route_variant_id)
    ]
    return sub.groupby("stop_sequence")["mean_cumulative_distance_m"].mean().sort_index()


def draw_distance_panel(ax, baseline_curve: pd.Series, detour_curve: pd.Series, title: str, annotate: bool = True) -> dict:
    base_km = baseline_curve.values / 1000
    det_km = detour_curve.values / 1000
    ax.plot(range(len(base_km)), base_km, color="#4C72B0", linewidth=2, marker="o", markersize=3, label="Baseline route")
    ax.plot(range(len(det_km)), det_km, color="#d62728", linewidth=2, marker="o", markersize=3, label="Detour (blocked) route")
    ax.set_title(title, fontsize=10, fontweight="bold")
    ax.grid(alpha=0.3)

    end_base, end_det = base_km[-1], det_km[-1]
    delta_km = end_det - end_base
    delta_pct = 100 * delta_km / end_base
    if annotate:
        ax.text(
            0.03, 0.97, f"{delta_km:+.2f} km ({delta_pct:+.1f}%)",
            transform=ax.transAxes, ha="left", va="top", fontsize=9, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="grey", alpha=0.9),
        )
    return {"end_baseline_km": round(end_base, 2), "end_detour_km": round(end_det, 2), "delta_km": round(delta_km, 2), "delta_pct": round(delta_pct, 1)}


def run_detour_distance(effective_df: pd.DataFrame, effective_summary: pd.DataFrame) -> dict:
    stats: dict[int, dict] = {}

    # Headline: line 97
    line = DETOUR_DISTANCE_HEADLINE_LINE
    blocked_row = dominant_blocked_variant(effective_summary, line)
    direction = blocked_row["direction_group"]
    baseline_id = int(effective_summary.loc[
        (effective_summary["route_name"] == line) & (effective_summary["direction_group"] == direction) & (effective_summary["is_reference"]),
        "route_variant_id",
    ].iloc[0])
    baseline_curve = variant_distance_curve(effective_df, line, direction, baseline_id)
    detour_curve = variant_distance_curve(effective_df, line, direction, int(blocked_row["route_variant_id"]))

    line_dir = OUT_DIR / f"line_{line}"
    line_dir.mkdir(parents=True, exist_ok=True)
    headline_path = line_dir / "detour_distance.png"

    fig, ax = plt.subplots(figsize=(9, 5.5))
    row_stats = draw_distance_panel(ax, baseline_curve, detour_curve, "")
    ax.set_title(f"Line {line} ({direction}): Cumulative Distance -- Baseline vs. Detour Route", fontsize=12, fontweight="bold")
    ax.set_xlabel("Stop sequence (route order)")
    ax.set_ylabel("Cumulative distance (km)")
    ax.legend(fontsize=9)
    fig.text(
        0.5, -0.05,
        f"How to read: cumulative distance stop-by-stop along line {line}'s baseline route (n={int(effective_summary.loc[(effective_summary['route_name']==line)&(effective_summary['direction_group']==direction)&(effective_summary['is_reference']),'count'].iloc[0]):,} "
        f"blocks) vs. its dominant detour/blocked variant (n={int(blocked_row['count']):,} blocks); the detour ends "
        f"{row_stats['delta_km']:+.2f} km ({row_stats['delta_pct']:+.1f}%) relative to the baseline's "
        f"{row_stats['end_baseline_km']:.1f} km end-to-end distance -- line 97's blockade delay "
        "(docs/05_skip_comparison/README.md) is disproportionate to this extra distance, so most of the delay is "
        "congestion/signal time on the detour, not sheer extra length.",
        ha="center", va="top", fontsize=8, wrap=True,
    )
    fig.savefig(headline_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved -> {headline_path}  ({row_stats})")
    stats[line] = {"direction_group": direction, **row_stats}

    # Small multiples: other blocked lines, for context
    other_lines = [l for l in DETOUR_DISTANCE_OTHER_LINES if l in effective_summary.loc[effective_summary["variant_type_v2"] == "blocked", "route_name"].unique()]
    fig2, axes = plt.subplots(1, len(other_lines), figsize=(4.2 * len(other_lines), 4.2))
    if len(other_lines) == 1:
        axes = [axes]
    for ax2, l in zip(axes, other_lines):
        blocked_row_l = dominant_blocked_variant(effective_summary, l)
        direction_l = blocked_row_l["direction_group"]
        baseline_id_l = int(effective_summary.loc[
            (effective_summary["route_name"] == l) & (effective_summary["direction_group"] == direction_l) & (effective_summary["is_reference"]),
            "route_variant_id",
        ].iloc[0])
        baseline_curve_l = variant_distance_curve(effective_df, l, direction_l, baseline_id_l)
        detour_curve_l = variant_distance_curve(effective_df, l, direction_l, int(blocked_row_l["route_variant_id"]))
        row_stats_l = draw_distance_panel(ax2, baseline_curve_l, detour_curve_l, f"Line {l} ({direction_l})")
        stats[l] = {"direction_group": direction_l, **row_stats_l}

    axes[0].set_ylabel("Cumulative distance (km)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig2.legend(handles, labels, loc="lower center", ncol=2, fontsize=9, bbox_to_anchor=(0.5, -0.05))
    fig2.suptitle("Cumulative Distance, Baseline vs. Dominant Detour Route -- Other Blocked Lines (Context)", fontsize=12, fontweight="bold")
    fig2.text(0.5, -0.12, "How to read: same comparison as line 97's headline panel, one dominant blocked/detour variant per line, for context.", ha="center", fontsize=8, wrap=True)
    fig2.tight_layout(rect=[0, 0.05, 1, 0.95])
    other_path = OUT_DIR / "detour_distance_all_lines.png"
    fig2.savefig(other_path, dpi=120, bbox_inches="tight")
    plt.close(fig2)
    print(f"Saved -> {other_path}")

    return stats


def run() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df_cleaned = pd.read_csv(config.DF_CLEANED_PATH, low_memory=False)
    variant_summary = pd.read_csv(config.VARIANT_SUMMARY_PATH)
    effective_df_all, effective_summary = vm.build_effective_df_cleaned(df_cleaned, variant_summary)
    effective_df = filter_significant_blocked(effective_df_all, effective_summary)
    endpoints = pa.block_endpoints(effective_df)

    summary_rows = []
    line_deltas: dict[int, pd.Series] = {}
    for line in sorted(endpoints["route_name"].unique()):
        baseline_ep = pa.baseline_endpoints(endpoints, route_name=line)
        blocked_ep = pa.blocked_endpoints(endpoints, route_name=line)
        if blocked_ep.empty or baseline_ep.empty:
            print(f"line {line}: no blocked or no baseline blocks, skipped.")
            continue
        is_line22 = line == 22
        if is_line22:
            # fix_22b_central_prompt.md -- blocked_ep is already guaranteed
            # direction_A only for line 22 post-centralization
            # (variant_merges never labels direction_B "blocked"), but
            # baseline_ep still pools both directions unless filtered here,
            # which would compare direction_A's real detour against a
            # baseline contaminated by direction_B's different route. Filter
            # both endpoints the same way (config.LINE_22_SHARE_DIRECTION)
            # so the plotted curve and the stats test agree -- previously
            # only the stats test was filtered, leaving the figure itself
            # mismatched.
            baseline_ep = baseline_ep[baseline_ep["direction_group"] == config.LINE_22_SHARE_DIRECTION]
            blocked_ep = blocked_ep[blocked_ep["direction_group"] == config.LINE_22_SHARE_DIRECTION]
        stats_label = "direction A only" if is_line22 else None
        stats_result = phase05_stats(baseline_ep, blocked_ep)

        line_dir = OUT_DIR / f"line_{line}"
        line_dir.mkdir(parents=True, exist_ok=True)
        out_path = line_dir / "baseline_vs_blocked_delta.png"
        row = plot_line_delta(line, baseline_ep, blocked_ep, out_path, stats_result=stats_result, stats_label=stats_label, dir_a_only=is_line22)
        summary_rows.append(row)
        print(f"Saved -> {out_path}  ({row})")

        delta, _, _ = compute_delta(baseline_ep, blocked_ep)
        line_deltas[line] = delta

    summary = pd.DataFrame(summary_rows)
    summary_path = OUT_DIR / "baseline_vs_blocked_summary.csv"
    summary.to_csv(summary_path, index=False)
    print(f"Saved -> {summary_path}")
    print(summary.to_string(index=False))

    cross_line_path = OUT_DIR / "delta_all_lines.png"
    plot_all_lines_delta(line_deltas, cross_line_path)
    print(f"Saved -> {cross_line_path}")

    distance_stats = run_detour_distance(effective_df_all, effective_summary)
    print(f"Detour-distance stats: {distance_stats}")


if __name__ == "__main__":
    run()
