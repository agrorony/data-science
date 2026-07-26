# Prompt for Claude Design — visual language for the bus transit report

Paste this into a new Claude conversation to get 2–3 visual-direction options to choose from.

---

**Project (3 lines):** Final project for an Intro to Data Science course — an EDA of Israeli Ministry of Transport bus-arrival data for 7 bus lines serving the Rehavia neighborhood in Jerusalem. The core question is how recurring road closures near a protest site (Aza St.) affect trip reliability, using route-variant detection and travel-time analysis across ~600K cleaned records. Deliverable is a ≤10-page Word report (font ≥11, line spacing ≥1.15, 1-inch margins, numbered figures with descriptive titles) built around roughly 15 matplotlib chart types (a corridor map, route-variant heatmaps, bar charts, multi-line hourly charts) that currently have no shared style — each script picked its own ad-hoc colors and fonts.

**Fixed constraint — do not change:** each bus line already has an assigned color, used across figures for consistency: Line 17 `#b30000`, 19 `#e34a33`, 22 `#fc8d59` (reds — shared-corridor lines), 9 `#54278f`, 97 `#9e9ac8` (purples — non-shared-corridor lines), 14 `#045a8d`, 15 `#74a9cf` (blues — control lines). Any design must build around this palette as accent/data colors, not replace it.

**Task:** design one unified visual language covering both the report layout (heading styles, body font, accent color, spacing, figure caption/title convention) and the chart style (matplotlib rcParams: font family/size, background, gridline style, legend placement and style, axis-label conventions, footnote/"how to read" text style) — clean and academic, not flashy or busy. Figures mix Hebrew (RTL) stop/street names with English chart chrome, so typography needs to hold up for both.

Produce 2–3 distinct directions (e.g. minimal-academic vs. muted-editorial vs. high-contrast-technical) as mockups, each applied to:
1. A sample report title/section page.
2. A 7-bar comparison chart (one bar per line, using the fixed palette above).
3. A multi-line time-series chart (7 lines over hours of day, using the fixed palette).
4. A stop-presence heatmap (green/white "present vs missing" grid with rotated Hebrew stop-name labels).
5. The legend styling for a route map with colored line overlays.

For each direction, state explicitly: font choices, background/gridline treatment, how the 7 fixed line-colors are used consistently across chart types, and how figure titles/captions should read in the final report (per course rule: title must state the figure's main message, not just describe axes).

End by asking me to pick one direction (or mix elements from two) before anything is finalized.
