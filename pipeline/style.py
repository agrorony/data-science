"""Shared house style for final-report figures.

Import this once, before any figure is built, in every standalone
`plot_*.py` script and in `run_pipeline.py`. It only sets rcParams --
`LINE_COLORS` itself stays defined exactly once in `pipeline/config.py`
and is re-exported here purely for import convenience.
"""

from __future__ import annotations

import matplotlib.pyplot as plt

from pipeline.config import LINE_COLORS  # noqa: F401 (re-exported for convenience)

# The fixed left-to-right/top-to-bottom line order every multi-line chart
# (bars, lines, heatmap rows, legends) must use -- LINE_COLORS' own dict
# insertion order already matches it, so this just names that order.
LINE_ORDER: list[int] = list(LINE_COLORS.keys())

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Source Sans 3", "Arial", "DejaVu Sans"],
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.titleweight": "semibold",
    "axes.labelsize": 10,
    "axes.labelcolor": "#4a4a4a",
    "axes.edgecolor": "#e2e2e2",
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "axes.facecolor": "white",
    "figure.facecolor": "white",
    "grid.color": "#eeeeee",
    "grid.linewidth": 0.8,
    "xtick.color": "#8a8a8a",
    "ytick.color": "#8a8a8a",
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.frameon": False,
    "legend.fontsize": 9,
    "legend.loc": "best",
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})
