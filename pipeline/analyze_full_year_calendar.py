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
    DAY_LABELS, MONTH_LABELS, BLOCK_KEYS, load_data, build_footprints, MIN_N_RELIABLE,
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


def slot_purity_global_check(blocks: pd.DataFrame) -> pd.DataFrame:
    """Global re-verification of the variant-purity claim (a slot = (line,
    direction, month, day, hour), ignoring route_variant_id): how many
    blocked-containing slots mix a blocked and a reference variant. This
    project's own docs/11 deep dive didn't need this check; the number
    cited in the prompt ("905 slots, 1 mixed") could not be located
    anywhere in this repo, so it is recomputed here from scratch against
    the current (post fix_22b_central_prompt.md) effective classification
    rather than assumed -- the qualitative finding (purity is
    near-universal) holds regardless of the exact denominator."""
    slot_keys = ["route_name", "direction_group", "month", "day_of_week", "scheduled_departure_time"]
    g = blocks.groupby(slot_keys)
    n_variants = g["route_variant_id"].nunique()
    has_blocked = g.apply(lambda d: (d["variant_type_v2"] == "blocked").any())
    has_reference = g.apply(lambda d: (d["variant_type_v2"] == "reference").any())
    mixed = (n_variants > 1) & has_blocked & has_reference
    result = pd.DataFrame([{
        "n_slots_total": len(n_variants),
        "n_blocked_containing_slots": int(has_blocked.sum()),
        "n_mixed_blocked_reference_slots": int(mixed.sum()),
    }])
    print("\n=== Global slot-purity re-verification ===")
    print(result.to_string(index=False))
    if mixed.sum():
        print("Mixed slot(s):", list(n_variants[mixed].index))
    return result, mixed[mixed].index.tolist()


def line_confirmed_at_hour(cell_blocks: pd.DataFrame, line: int, hour: int) -> tuple[bool, dict]:
    """Does `line` have a confirmed-blocked slot at this hour (pure + n>=8 +
    variant_type_v2=='blocked')? For line 22, only direction_A counts
    (config.LINE_22_SHARE_DIRECTION) -- direction_B can never be blocked
    post-fix, but is excluded from agreement-counting for the same
    denominator-dilution reason as Part A's share computation."""
    directions = [config.LINE_22_SHARE_DIRECTION] if line == 22 else ["direction_A", "direction_B"]
    detail = {}
    confirmed = False
    for direction in directions:
        sub = cell_blocks[
            (cell_blocks["route_name"] == line) & (cell_blocks["direction_group"] == direction)
            & (cell_blocks["scheduled_departure_time"] == hour)
        ]
        if sub.empty:
            continue
        n_variants = sub["route_variant_id"].nunique()
        pure = n_variants == 1
        vt = sub["variant_type_v2"].iloc[0] if pure else "MIXED(" + "/".join(sorted(sub["variant_type_v2"].unique())) + ")"
        n_obs = int(sub["n_observations"].sum())
        detail[direction] = {"pure": pure, "variant_type_v2": vt, "n_observations": n_obs}
        if pure and n_obs >= MIN_N_RELIABLE_CELL and sub["variant_type_v2"].iloc[0] == "blocked":
            confirmed = True
    return confirmed, detail


def nearest_reference_n(cell_line_dir_blocks: pd.DataFrame, hour: int) -> tuple[int | None, int | None]:
    """Nearest hour (by |distance|, ties broken toward the earlier hour)
    running the reference variant for this (line, direction, month, day) --
    returns (reference_hour, its n_observations) or (None, None)."""
    ref = cell_line_dir_blocks[cell_line_dir_blocks["variant_type_v2"] == "reference"].copy()
    if ref.empty:
        return None, None
    ref["dist"] = (ref["scheduled_departure_time"] - hour).abs()
    ref = ref.sort_values(["dist", "scheduled_departure_time"])
    row = ref.iloc[0]
    return int(row["scheduled_departure_time"]), int(row["n_observations"])


VT_CODE_13 = {"reference": 1, "regular": 2, "blocked": 3, "non_corridor": 2, "noise": 2}
VT_COLORS_13 = {"no_service": "#eeeeee", "reference": "#4C72B0", "regular": "#f4a261", "blocked": "#d62728"}


def plot_cell_timeline(cell_blocks: pd.DataFrame, lines: list[int], title: str, out_path, confirmed_hours: set[int]):
    row_keys = []
    for line in lines:
        for direction in ["direction_A", "direction_B"]:
            if ((cell_blocks["route_name"] == line) & (cell_blocks["direction_group"] == direction)).any():
                row_keys.append((line, direction))
    hours = sorted(cell_blocks["scheduled_departure_time"].unique())
    if not row_keys or not hours:
        return

    grid = np.zeros((len(row_keys), len(hours)))
    n_grid = np.zeros((len(row_keys), len(hours)))
    impure_grid = np.zeros((len(row_keys), len(hours)), dtype=bool)
    for ri, (line, direction) in enumerate(row_keys):
        sub = cell_blocks[(cell_blocks["route_name"] == line) & (cell_blocks["direction_group"] == direction)]
        for ci, h in enumerate(hours):
            s = sub[sub["scheduled_departure_time"] == h]
            if s.empty:
                continue
            pure = s["route_variant_id"].nunique() == 1
            impure_grid[ri, ci] = not pure
            vt = s["variant_type_v2"].iloc[0] if pure else "regular"
            grid[ri, ci] = VT_CODE_13.get(vt, 2)
            n_grid[ri, ci] = s["n_observations"].sum()

    cmap = ListedColormap([VT_COLORS_13["no_service"], VT_COLORS_13["reference"], VT_COLORS_13["regular"], VT_COLORS_13["blocked"]])
    fig, ax = plt.subplots(figsize=(max(9, 0.55 * len(hours)), 0.6 * len(row_keys) + 2.2))
    ax.imshow(grid, cmap=cmap, vmin=0, vmax=3, aspect="auto")
    ax.set_xticks(range(len(hours)))
    ax.set_xticklabels([f"{h}:00" for h in hours], fontsize=8, rotation=45)
    for h, ci in zip(hours, range(len(hours))):
        if h in confirmed_hours:
            ax.axvspan(ci - 0.5, ci + 0.5, facecolor="none", edgecolor="black", linewidth=2.2, zorder=5)
    row_labels = [f"Line {l} ({d[-1]})" + (" [excl. from agreement]" if l == 22 and d == "direction_B" else "") for l, d in row_keys]
    ax.set_yticks(range(len(row_keys)))
    ax.set_yticklabels(row_labels, fontsize=8)
    for (l, d), tick in zip(row_keys, ax.get_yticklabels()):
        tick.set_color(config.LINE_COLORS.get(l, "black"))
        tick.set_fontweight("bold")
    for ri in range(len(row_keys)):
        for ci in range(len(hours)):
            n = n_grid[ri, ci]
            if n <= 0:
                continue
            label = ("IMPURE" if impure_grid[ri, ci] else f"n={int(n)}") + ("*" if 0 < n < MIN_N_RELIABLE else "")
            txt_color = "black" if grid[ri, ci] in (0, 2) else "white"
            ax.text(ci, ri, label, ha="center", va="center", fontsize=6, color=txt_color)
    ax.set_title(title, fontsize=12, fontweight="bold")
    legend = [
        Patch(color=VT_COLORS_13["reference"], label="Reference variant"),
        Patch(color=VT_COLORS_13["regular"], label="Regular / non_corridor / impure slot"),
        Patch(color=VT_COLORS_13["blocked"], label="Blocked (>15-stop) variant"),
        Patch(facecolor="none", edgecolor="black", linewidth=2.2, label="Confirmed hour (>=3 lines agree)"),
    ]
    fig.legend(handles=legend, loc="lower center", ncol=2, fontsize=8, bbox_to_anchor=(0.5, -0.1))
    fig.text(
        0.5, -0.17,
        "How to read: black outline = hour confirmed by >=3 elevated lines independently (pure slot, n>=8, blocked); "
        "'IMPURE' = more than one route_variant_id in that exact slot (never counted as confirmed); "
        "n=block sample size, '*' marks n<8. Line 22 direction_B is shown but excluded from agreement-counting "
        "(non_corridor, see pipeline/config.py:LINE_22_SHARE_DIRECTION).",
        ha="center", fontsize=7.5, wrap=True, transform=fig.transFigure,
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=115, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved -> {out_path}")


def confirmed_hour_ranges(hours: list[int]) -> list[str]:
    if not hours:
        return []
    hours = sorted(hours)
    ranges = []
    start = prev = hours[0]
    for h in hours[1:]:
        if h == prev + 1:
            prev = h
            continue
        ranges.append((start, prev))
        start = prev = h
    ranges.append((start, prev))
    return [f"{a}-{b+1}h" if a != b else f"{a}h" for a, b in ranges]


def part_b(effective_df, effective_summary, variant_summary, blocks, flagged):
    # Footprints are not redefined here -- reused verbatim from phase 11
    # (pipeline.analyze_deep_dive_windows.build_footprints), per the task
    # brief ("do not redefine a new footprint if an existing one already
    # covers the relevant stops"). Not otherwise used in the confirmed-hour
    # logic below (that logic only needs variant_type_v2 + purity), but
    # printed here for the record / cross-reference in the README.
    footprints, footprint_records = build_footprints(effective_df, effective_summary, variant_summary)
    print("\n=== Footprints reused from phase 11 ===")
    for name, stops in footprints.items():
        print(f"{name}: {len(stops)} stops -> {sorted(stops)}")

    purity_result, mixed_slots = slot_purity_global_check(blocks)

    calendar_rows = []
    anomaly_rows = []

    for _, cell_row in flagged.iterrows():
        month, day_label = cell_row["month"], cell_row["day_label"]
        lines = cell_row["lines_elevated_list"]
        key = f"{MONTH_LABELS[month-1].lower()}_{day_label.lower()}"
        print(f"\n\n========== FLAGGED CELL: {MONTH_LABELS[month-1]} {day_label} (lines: {lines}) ==========")

        cell_blocks = blocks[
            (blocks["month"] == month) & (blocks["day_label"] == day_label) & (blocks["route_name"].isin(lines))
        ].copy()

        hours = sorted(cell_blocks["scheduled_departure_time"].unique())
        confirmed_hours = []
        n_impure_candidates = 0
        n_lown_candidates = 0
        for h in hours:
            agree = 0
            for line in lines:
                confirmed, detail = line_confirmed_at_hour(cell_blocks, line, h)
                if confirmed:
                    agree += 1
                else:
                    for direction, d in detail.items():
                        if d["variant_type_v2"] == "blocked" and not d["pure"]:
                            n_impure_candidates += 1
                        elif d["variant_type_v2"] == "blocked" and d["n_observations"] < MIN_N_RELIABLE_CELL:
                            n_lown_candidates += 1
            if agree >= MIN_LINES_AGREEING:
                confirmed_hours.append(h)

        ranges = confirmed_hour_ranges(confirmed_hours)
        status = "confirmed" if ranges else "inconclusive"
        print(f"  Confirmed hours: {ranges if ranges else 'none'} (impure-blocked candidates seen: {n_impure_candidates}, low-n-blocked candidates seen: {n_lown_candidates})")

        # n-anomaly check for each line/direction contributing to a confirmed hour
        for h in confirmed_hours:
            for line in lines:
                directions = [config.LINE_22_SHARE_DIRECTION] if line == 22 else ["direction_A", "direction_B"]
                for direction in directions:
                    ld = cell_blocks[(cell_blocks["route_name"] == line) & (cell_blocks["direction_group"] == direction)]
                    slot = ld[ld["scheduled_departure_time"] == h]
                    if slot.empty or slot["route_variant_id"].nunique() != 1 or slot["variant_type_v2"].iloc[0] != "blocked":
                        continue
                    if slot["n_observations"].iloc[0] < MIN_N_RELIABLE_CELL:
                        continue
                    ref_hour, ref_n = nearest_reference_n(ld, h)
                    if ref_n is None or ref_n == 0:
                        continue
                    blocked_n = int(slot["n_observations"].iloc[0])
                    ratio = blocked_n / ref_n
                    if ratio >= 2 or ratio <= 0.5:
                        anomaly_rows.append({
                            "month_label": MONTH_LABELS[month - 1], "day_label": day_label,
                            "line": line, "direction": direction, "blocked_hour": h, "blocked_n": blocked_n,
                            "nearest_reference_hour": ref_hour, "reference_n": ref_n, "ratio": round(ratio, 2),
                        })

        plot_cell_timeline(
            cell_blocks, lines,
            f"{MONTH_LABELS[month-1]}, {day_label} -- Hour-Level Variant Type (flagged cell, relaxed rule)",
            OUT_DIR / f"timeline_{key}.png", set(confirmed_hours),
        )

        calendar_rows.append({
            "month": month, "month_label": MONTH_LABELS[month - 1], "day_label": day_label,
            "lines_elevated": lines, "status": status,
            "confirmed_hour_ranges": "; ".join(ranges) if ranges else "",
            "documented_elsewhere": cell_row["documented_elsewhere"],
            "documented_reason": cell_row["documented_reason"],
            "n_impure_blocked_candidates": n_impure_candidates,
            "n_lowN_blocked_candidates": n_lown_candidates,
        })

    calendar_df = pd.DataFrame(calendar_rows)
    calendar_df.to_csv(OUT_DIR / "confirmed_hours.csv", index=False)
    print("\n\n=== CALENDAR SUMMARY ===")
    print(calendar_df[["month_label", "day_label", "status", "confirmed_hour_ranges", "documented_elsewhere"]].to_string(index=False))

    anomaly_df = pd.DataFrame(anomaly_rows)
    anomaly_df.to_csv(OUT_DIR / "n_anomaly_report.csv", index=False)
    print(f"\n=== N-ANOMALY REPORT ({len(anomaly_df)} cases, ratio>=2x or <=0.5x) ===")
    if len(anomaly_df):
        print(anomaly_df.to_string(index=False))
    else:
        print("(none)")

    return calendar_df, anomaly_df


def plot_calendar_grid(calendar_df: pd.DataFrame, long_df: pd.DataFrame, out_path):
    """Month x day-of-week grid, one cell per (month, day). Confirmed cells
    show their hour range; flagged-but-inconclusive cells show a one-word
    reason; unflagged cells are blank. This -- not a percentage heatmap --
    is the deliverable: a plain "was there a confirmed blockage, and when"
    answer per cell."""
    grid_status = pd.DataFrame("", index=DAY_ORDER, columns=MONTH_ORDER)
    grid_color = np.zeros((len(DAY_ORDER), len(MONTH_ORDER)))  # 0=not flagged, 1=inconclusive, 2=confirmed

    for _, row in calendar_df.iterrows():
        day_idx = DAY_ORDER.index(row["day_label"])
        month_idx = row["month"] - 1
        if row["status"] == "confirmed":
            ranges = [r.strip() for r in row["confirmed_hour_ranges"].split(";")]
            grid_status.iloc[day_idx, month_idx] = "\n".join(ranges)
            grid_color[day_idx, month_idx] = 2
        else:
            reason = "artifact" if row["documented_elsewhere"] and "docs/06" in row["documented_reason"] else (
                "low n" if row["n_lowN_blocked_candidates"] >= row["n_impure_blocked_candidates"] else "impure"
            )
            grid_status.iloc[day_idx, month_idx] = f"inc.\n({reason})"
            grid_color[day_idx, month_idx] = 1

    cmap = ListedColormap(["#f7f7f7", "#fddbc7", "#d62728"])
    fig, ax = plt.subplots(figsize=(13, 6.5))
    ax.imshow(grid_color, cmap=cmap, vmin=0, vmax=2, aspect="auto")
    ax.set_xticks(range(len(MONTH_ORDER)))
    ax.set_xticklabels(MONTH_LABELS)
    ax.set_yticks(range(len(DAY_ORDER)))
    ax.set_yticklabels(DAY_ORDER)
    for i in range(len(DAY_ORDER)):
        for j in range(len(MONTH_ORDER)):
            txt = grid_status.iloc[i, j]
            if txt:
                fontsize = 6.5 if txt.count("\n") >= 2 else 7.5
                ax.text(j, i, txt, ha="center", va="center", fontsize=fontsize,
                        color="white" if grid_color[i, j] == 2 else "black")
    ax.set_title(
        "Phase 13 -- Confirmed-Hours Calendar (relaxed scan: >=3 lines, share > 10%)",
        fontsize=13, fontweight="bold",
    )
    legend = [
        Patch(color="#d62728", label="Confirmed (>=3 lines agree, pure + n>=8)"),
        Patch(color="#fddbc7", label="Flagged but inconclusive (reason in cell)"),
        Patch(color="#f7f7f7", label="Not flagged (relaxed rule not met)"),
    ]
    fig.legend(handles=legend, loc="lower center", ncol=3, fontsize=9, bbox_to_anchor=(0.5, -0.05))
    fig.tight_layout()
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved -> {out_path}")


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

    return effective_df, effective_summary, variant_summary, blocks, flagged, long_df


def part_c_control_sanity(blocks: pd.DataFrame):
    """Sanity check (same as phases 10/11): control lines 14/15 should
    never be flagged, let alone confirmed, anywhere on the calendar."""
    print("\n=== Control-line sanity check (14/15, full year) ===")
    for line in [14, 15]:
        sub = blocks[blocks["route_name"] == line]
        n_blocked = (sub["variant_type_v2"] == "blocked").sum()
        print(f"Line {line}: {n_blocked} blocked slots out of {len(sub)} project-wide "
              f"({n_blocked/len(sub):.2%}) -- should never independently clear the >10% cell-share bar")


if __name__ == "__main__":
    effective_df, effective_summary, variant_summary, blocks, flagged, long_df = part_a()
    calendar_df, anomaly_df = part_b(effective_df, effective_summary, variant_summary, blocks, flagged)
    plot_calendar_grid(calendar_df, long_df, OUT_DIR / "confirmed_hours_calendar.png")
    part_c_control_sanity(blocks)
