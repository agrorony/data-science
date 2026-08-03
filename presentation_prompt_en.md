# Prompt for Generating the Presentation

Copy the text in the box below into an AI presentation tool (e.g. Gamma, ChatGPT, Claude, etc.).

---

You are a professional presentation designer. Create a presentation (10–15 slides, for a 10–15 minute talk) based on an academic project analyzing public bus transit data in Jerusalem. Audience: instructor and students in an introductory data science course.

## Design and content rules — mandatory
- Minimal text on every slide: short title + up to 3-4 lines of text, each line one short sentence (max ~8-10 words). No paragraphs, no complex sentences.
- The chart/image is the hero of each slide, not the text. Text is secondary and supporting only.
- On every slide marked "[Chart placeholder: ...]" — leave a large, clear space (at least 60% of the slide area) for inserting an image/chart, with a placeholder caption naming the figure from the report.
- Clean design: uniform background (white/light), single consistent sans-serif font, consistent color palette (2-3 colors max), no unnecessary animations, no decoration.
- Each slide title = the slide's main takeaway (not just "Background" or "Results"), e.g. "Blockages cluster on Saturday nights."
- Speaker notes separate from the on-slide text — put the detailed talking points there. The visible slide text stays minimal.
- Keep the exact topic order and slide structure listed below.

## Slide structure

**Slide 1 — Title**
Title: "When is it safest to catch a bus out of Rehavia?" (or similar). Course name, student name(s).

**Slide 2 — Why this question**
Text: Rehavia is a hub of protests; the Prime Minister lives on Aza Street; police repeatedly close the street.
[Chart placeholder: Figure 1 — map of Rehavia neighborhood and the studied bus lines]

**Slide 3 — Research question**
Text: Main question — how can a Rehavia resident know the most reliable way to leave by bus, given road blockages?
3 sub-questions (one sentence each):
1. When and how often do blockages occur on Aza Street?
2. Does the detour make the trip longer or shorter?
3. Do the blockages also affect lines that don't pass through Aza Street?

**Slide 4 — The data**
Text: Ministry of Transport dataset, station arrival times by day and hour, 2024. 7 bus lines. Each row = average trip data for a line-month-day-hour-stop combination ("block" = one full trip).
[Chart placeholder: Table 1 — example block, line 19]

**Slide 5 — Data cleaning**
Text (3 lines, numbers only, "from X to Y" format):
- 708,642 records → 603,662 after removing duplicates
- 6.3% of rows flagged low-confidence (not deleted)
- Hours 25/26 remapped to 1/2 (midnight-2am)

**Slide 6 — Detecting route variants**
Text: Each line has a reference route (the most common one). A minority of trips skip a segment of stops — these are "variants."
[Chart placeholder: Figure 2 — map of skipped stops on Aza Street]

**Slide 7 — How long are the routes**
Text: Strong correlation between route length and travel time. Line 9 is longest (~20 km, ~90 min), line 97 is shortest (~10 km, ~44 min).
[Chart placeholder: Figure 3a]

**Slide 8 — Shared daily pattern**
Text: Travel time rises in the morning, peaks at midday, drops toward evening — across all 7 lines.
[Chart placeholder: Figure 3b]

**Slide 9 — How common are the blockages**
Text: 5%-12% of trips on lines passing Aza Street use the detour route; sharp jump on Saturday nights (66%-84%). Control lines 14/15: nearly 0%.
[Chart placeholder: Table 3 / Figure 5 — heatmap of blockage share by month and day]

**Slide 10 — When exactly do blockages happen**
Text: 21 confirmed blockage events at the day-of-week/hour level. 11 of 21 on Saturday nights (7pm-midnight). The rest on weekdays, clustered around Knesset session days.
[Chart placeholder: Figure 6 — heatmap of confirmed blockage hours]

**Slide 11 — Does the detour cost or save time**
Text: On average, the detour is faster than the regular route — saves 8 to 16 minutes, statistically significant for all 5 lines. During rush hour, the advantage disappears.
[Chart placeholder: Figure 7 — median travel time delta by hour]

**Slide 12 — Does the blockage "leak" to other lines**
Text: Lines 14/15 don't pass through Aza Street. Two statistical tests (Mann-Whitney, permutation) — no significant difference in their travel times during blockages.
[Chart placeholder: Table 4 — travel time comparison, blockage vs. normal]

**Slide 13 — Answer to the main question**
Text (one sharp conclusion sentence): Blockages cluster on Saturday nights; the detour is faster on average; control lines are unaffected. There's no real "risky line" to avoid leaving Rehavia.

**Slide 14 — Follow-up research**
Text (2 ideas, one line each):
- Extend to nationwide datasets to detect events (Meron pilgrimage, Tel Aviv Pride, protests)
- Analyze real impact on riders (walking time to an alternative stop)

**Slide 15 — Thank you / Questions**

## Additional note
All numeric figures in this prompt are exact from the report — do not change them or invent new data.
