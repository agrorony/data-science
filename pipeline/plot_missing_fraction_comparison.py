"""Phase 07 support figure -- why line 22's Aza-corridor closure is
classified 'regular' while the same closure is 'blocked' on other lines.

For each line/direction, plots the missing_fraction (n_missing /
reference route stop count) of its largest observed variant that shares
the known Aza-corridor missing-stop signature (config.CRITICAL_STOPS),
against stage5_variant_classification.MINOR_MISSING_FRACTION (0.10) --
the fixed cutoff below which a variant is labeled 'regular' (routine
noise) rather than 'blocked'.

House style matches pipeline/plot_blockade_frequency.py: Reds colormap,
% annotated per bar, labeled colorbar, fig.text caption.

Not part of the regular pipeline run -- a one-off diagnostic for
docs/07_blockade_investigation/README.md.
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import numpy as np

from pipeline import config
from pipeline.stage5_variant_classification import MINOR_MISSING_FRACTION

# Manually identified from govData/candidate_variant_labels.csv: for each
# line/direction, the variant that best represents the Aza-corridor
# closure signature (matches missing_stop_names against config.CRITICAL_STOPS
# street names) with the largest observation count among that group.
# See docs/07_blockade_investigation/README.md for the full audit.
ROWS = [
    # (label, count, n_missing, ref_n_stops, current_label)
    ("Line 9 -- direction_B",  43, 7,  63, "blocked"),
    ("Line 9 -- direction_A",   2, 7,  67, "blocked"),
    ("Line 17 -- direction_A", 27, 6,  47, "blocked"),
    ("Line 17 -- direction_B", 32, 5,  49, "blocked"),
    ("Line 19 -- direction_A", 84, 6,  42, "blocked"),
    ("Line 19 -- direction_B", 52, 5,  37, "blocked"),
    ("Line 22 -- direction_A", 96, 4,  55, "regular (!)"),
    ("Line 22 -- direction_B",  1, 11, 52, "blocked"),
    ("Line 97 -- direction_A", 22, 4,  30, "blocked"),
    ("Line 97 -- direction_B",  7, 4,  34, "blocked"),
]


def run() -> None:
    labels = [r[0] for r in ROWS]
    counts = [r[1] for r in ROWS]
    fractions = [r[2] / r[3] for r in ROWS]
    statuses = [r[4] for r in ROWS]

    order = np.argsort(fractions)
    labels = [labels[i] for i in order]
    counts = [counts[i] for i in order]
    fractions = [fractions[i] for i in order]
    statuses = [statuses[i] for i in order]

    vmax = max(fractions) * 1.15
    norm = mcolors.Normalize(vmin=0, vmax=vmax)
    cmap = cm.get_cmap("Reds")

    fig, ax = plt.subplots(figsize=(9.5, 6.2))
    y_pos = np.arange(len(labels))
    bar_colors = [cmap(norm(f)) for f in fractions]
    bars = ax.barh(y_pos, fractions, color=bar_colors, edgecolor="#444444", height=0.65)

    for i, (frac, n, status) in enumerate(zip(fractions, counts, statuses)):
        text_color = "white" if norm(frac) > 0.55 else "black"
        ax.text(frac / 2 if frac > 0.03 else frac + 0.01, i, f"{frac:.1%}",
                 ha="center" if frac > 0.03 else "left", va="center",
                 fontsize=9, color=text_color if frac > 0.03 else "black", fontweight="bold")
        ax.text(max(fractions) * 1.02, i, f"n={n}, currently → {status}",
                 va="center", fontsize=8.5, color="#333333")

    ax.axvline(MINOR_MISSING_FRACTION, color="black", linestyle="--", linewidth=1.3)
    ax.text(MINOR_MISSING_FRACTION + 0.003, 0.15,
             f"stage5 cutoff ({MINOR_MISSING_FRACTION:.0%})",
             rotation=90, va="bottom", ha="left", fontsize=8.5, fontweight="bold")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=9.5)
    ax.set_xlabel("Missing-stop fraction of largest Aza-corridor-matching variant (n_missing / reference route stop count)")
    ax.set_xlim(0, max(fractions) * 1.55)
    ax.set_title(
        "Same Corridor Closure, Different Classification Outcome by Route Length",
        fontsize=13, fontweight="bold"
    )

    sm = cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.046, pad=0.08)
    cbar.set_label("Missing-stop fraction")

    caption = (
        "Every line's largest observed variant matching the known Aza-corridor missing-stop set (config.CRITICAL_STOPS)\n"
        "is labeled 'blocked' except line 22 direction_A's -- its variant has the highest observation count of all (n=96)\n"
        "but the smallest fraction (7.3%), because line 22's reference route (55 stops) is longer than lines 9/17/19/97's,\n"
        "diluting the same fixed ~4-6 missing stops below stage5's fixed 10% cutoff."
    )
    fig.text(0.5, 0.005, caption, ha="center", fontsize=9, style="italic")

    plt.tight_layout(rect=[0, 0.09, 1, 1])
    out_path = config.REPO_ROOT / "docs" / "07_blockade_investigation" / "missing_fraction_by_line.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved -> {out_path}")


if __name__ == "__main__":
    run()
