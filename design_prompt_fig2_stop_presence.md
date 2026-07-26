# Prompt for Claude Design — fix the "route deviation" figure

Paste this into a new Claude conversation. This is a focused follow-up to the earlier visual-language spec (Minimal Academic, 1a) — reuse those fonts/colors, but the *chart concept itself* needs rethinking, not just resizing.

---

**Project (3 lines):** Final project for an Intro to Data Science course — an EDA of Israeli bus data for 7 Jerusalem lines, centered on how recurring road closures near a protest site (Aza St.) force some lines into a detour. One figure needs to show, at a glance, that lines sharing the corridor consistently skip the same street segment on their dominant detour, while a control line runs one fixed route with no detour at all.

**What failed:** the first attempt was a green/white "present vs. missing" heatmap grid — 2 rows (reference route, dominant detour) × every stop along the route as a column, one panel per line/direction. With 4 lines needed (19, 9, 97, 15) it was still illegible: routes run 30–70 stops long, so cramming a label per stop (even rotated, even Hebrew-reshaped correctly) produces a wall of tiny vertical text no reader can parse. Shrinking the grid doesn't fix this — the problem is trying to label every stop when only a handful of stops (the ones inside the gap) actually matter to the story.

**Task:** design a cleaner alternative that makes the same point — "this line's detour skips a specific, consistent segment" — without labeling every stop. Think of it more as a small infographic than a dense data heatmap. Some directions worth exploring (pick/combine, or propose your own):
- A single horizontal bar per line representing the full reference route (start to end), with the skipped segment shown as a distinct visual break/highlight, annotated only with the entry and exit stop names of the gap (not every stop in between) plus the route's first/last stop.
- A simplified schematic (not to scale) showing "route in → gap of N stops (named: [first skipped stop] … [last skipped stop]) → route continues," repeated for lines 19, 9, and 97, with line 15 shown as a plain unbroken bar with a one-line "no detour observed" note.
- Keep each line's fixed color (19=#e34a33, 9=#54278f, 97=#9e9ac8, 15=#74a9cf) as the bar/route color, per the established palette — don't introduce new colors for this figure.

Four lines only, one representative direction each — 19 (its direction with the larger gap), 9 (its direction with the larger gap), 97 (its direction with the larger gap), 15 (single reference, no direction split, no detour). No grid of many small panels; this should read clearly at report size (roughly quarter-to-half a page), not require zooming in.

Produce 2–3 mockup options and ask me to pick one before finalizing. Once I pick, I'll bring the choice back to Claude Code to rebuild `docs/03_variants/fig2_stop_presence.png` from real data — so be concrete about the exact visual structure (bar shape, label placement, annotation style) so it's implementable in matplotlib, not just a decorative sketch.
