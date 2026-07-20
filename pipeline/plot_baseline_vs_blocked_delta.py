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

One figure per line: docs/05_skip_comparison/line_<N>_baseline_vs_blocked_delta.png
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from pipeline import config, variant_merges as vm, pooled_analysis as pa

OUT_DIR = config.REPO_ROOT / "docs" / "05_skip_comparison"
THIN_THRESHOLD = 8  # fewer than this many blocked blocks at an hour -> shaded as thin


def hour_medians(endpoints: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Return (median end-to-end time by hour_display, n blocks by hour_display)."""
    e = endpoints.copy()
    e["hour_display"] = e["scheduled_departure_time"].replace({25: 1, 26: 2})
    med = e.groupby("hour_display")["end_time_min"].median()
    n = e.groupby("hour_display")["end_time_min"].size()
    return med, n


def plot_line_delta(line, baseline_ep: pd.DataFrame, blocked_ep: pd.DataFrame, out_path) -> dict:
    base_med, base_n = hour_medians(baseline_ep)
    blocked_med, blocked_n = hour_medians(blocked_ep)

    hours = sorted(set(base_med.index) & set(blocked_med.index))
    delta = pd.Series({h: blocked_med[h] - base_med[h] for h in hours}).sort_index()
    thin_hours = [h for h in hours if blocked_n.get(h, 0) < THIN_THRESHOLD]

    fig, ax = plt.subplots(figsize=(10, 5.5))

    band_labeled = False
    for hr in thin_hours:
        ax.axvspan(hr - 0.4, hr + 0.4, color="grey", alpha=0.18, zorder=0, label="Thin data (<8 blocked blocks)" if not band_labeled else "")
        band_labeled = True

    ax.plot(delta.index, delta.values, color="#d62728", linewidth=2.5, marker="o", markersize=5, label="Blocked variant minus baseline")
    ax.axhline(0, color="black", linewidth=1, linestyle="--", alpha=0.6)
    ax.set_xlabel("Hour of day (25/26 shown as 01:00/02:00 next day)")
    ax.set_ylabel("Extra travel time on blocked/special variant (min)")
    ax.set_title(f"Line {line}: Baseline vs. Blocked/Special Variant -- Travel-Time Delta by Hour", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    overall_delta = blocked_ep["end_time_min"].median() - baseline_ep["end_time_min"].median()
    verdict = "costs time" if overall_delta > 0 else "saves time"
    fig.text(
        0.5, -0.05,
        f"How to read: for each hour of day, the line plots (median travel time on the line's blocked/special "
        f"variant) minus (median travel time on its baseline variant), both directions pooled and using only the "
        f"confirmed post-merge variant set; positive = the special route is slower, negative = faster. Grey bands "
        f"mark hours with fewer than {THIN_THRESHOLD} blocked-variant observations. Overall (all hours pooled): the "
        f"special route {verdict} by {abs(overall_delta):.1f} min (n={len(blocked_ep):,} blocked vs "
        f"n={len(baseline_ep):,} baseline blocks).",
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
        "n_hours_total": len(hours),
    }


def run() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df_cleaned = pd.read_csv(config.DF_CLEANED_PATH, low_memory=False)
    variant_summary = pd.read_csv(config.VARIANT_SUMMARY_PATH)
    effective_df, _ = vm.build_effective_df_cleaned(df_cleaned, variant_summary)
    endpoints = pa.block_endpoints(effective_df)

    summary_rows = []
    for line in sorted(endpoints["route_name"].unique()):
        baseline_ep = pa.baseline_endpoints(endpoints, route_name=line)
        blocked_ep = pa.blocked_endpoints(endpoints, route_name=line)
        if blocked_ep.empty or baseline_ep.empty:
            print(f"line {line}: no blocked or no baseline blocks, skipped.")
            continue
        line_dir = OUT_DIR / f"line_{line}"
        line_dir.mkdir(parents=True, exist_ok=True)
        out_path = line_dir / "baseline_vs_blocked_delta.png"
        row = plot_line_delta(line, baseline_ep, blocked_ep, out_path)
        summary_rows.append(row)
        print(f"Saved -> {out_path}  ({row})")

    summary = pd.DataFrame(summary_rows)
    summary_path = OUT_DIR / "baseline_vs_blocked_summary.csv"
    summary.to_csv(summary_path, index=False)
    print(f"Saved -> {summary_path}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    run()
