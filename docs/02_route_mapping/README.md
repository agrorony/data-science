# 02 — route_id ↔ Commercial Line Mapping

This is the project's reference key: every commercial line to its
underlying `route_id`(s), direction group, and terminal stops. **Any
later report that uses `direction_A` / `direction_B` links back to this
table** (Global Rules) — those labels are not geographic ("north/south");
they only mean "whichever `route_id` group was assigned A vs. B below."

## How the direction split was determined

Lines with more than one `route_id` were compared pairwise by
`pipeline/stage3_investigate_route_ids.py`, a blocking checkpoint that
the rest of the pipeline refuses to run past until a human confirms a
`treatment` for every multi-`route_id` line. For each pair of `route_id`s
it computes: stop-set Jaccard overlap, whether one route's most common
stop sequence is the exact reverse of the other's, row-count ratio,
stop-count ratio, and whether the two `route_id`s' active months
overlap. A key subtlety: this dataset commonly assigns a **distinct
stop_code per direction** (opposite-side stop poles on the same street),
so a genuine direction pair still shows *near-zero* stop-code overlap —
the distinguishing signal is that the two `route_id`s have *similar*
route length and ride volume and are active in the *same* months, not
that their stops literally match. The evidence for each line is recorded
in `govData/route_id_comparison_report.csv`; the confirmed decision (with
supporting notes) is in `govData/route_id_decisions.json`.

Every multi-`route_id` line in this project's scope was confirmed as a
**`direction_pair`** — two `route_id`s covering the same physical
corridor in opposite directions. None required `pool` (treat as one
undifferentiated group) or `keep_separate` (unrelated routes sharing a
line number) treatment.

## Key table

| Line | route_id(s) → direction | n_rows | n_stops | First stop (direction start) | Last stop (direction end) |
|---|---|---|---|---|---|
| **15** | `37936` (single id — see note below) | 57,836 | 48 | האומן/ברעם (`3300`) | האומן/ברעם (`6267`) |
| **22** | direction_A: `5499` | 62,044 | 55 | ברעם/האומן (`3324`) | מסוף 700 / שד' נווה יעקב (`1487`) |
| | direction_B: `5502` | 58,748 | 52 | שדרות נווה יעקב/משה סנה (`61`) | חניון תלפיות/ברעם (`3294`) |
| **19** | direction_A: `10802` (main), `10803` (sparse alt., 1,514 rows) | 53,011 / 1,514 | 42 / 40 | כניסה ראשית/הדסה עין כרם (`2314`) | מסוף הר הצופים/מרטין בובר (`1370`) |
| | direction_B: `10804` (main), `10806` (348 rows), `10807` (144 rows) | 48,870 / 348 / 144 | 37 / 29 / 12 | מסוף הר הצופים/בנימין מזר (`1366`) | כניסה ראשית/הדסה עין כרם (`2326`) |
| **17** | direction_A: `10398` | 25,535 | 47 | אריה דולצ'ין/יעקב צור (`6004`) | מסוף הר הצופים/מרטין בובר (`1370`) |
| | direction_B: `10399` | 34,606 | 49 | מסוף הר הצופים/בנימין מזר (`1366`) | דולצ'ין/בן פורת (`3005`) |
| **9** | direction_A: `11107` | 62,384 | 67 | תחנה תפעולית/ביטוח לאומי (`1507`) | חניון מלחה (`2021`) |
| | direction_B: `11108` | 52,312 | 63 | חניון רכבת מלחה/דרך יצחק מודעי (`5853`) | בנייני האומה/הנשיא השישי (`800`) |
| **97** | direction_A: `36950` | 35,847 | 30 | תחנה תפעולית/ביטוח לאומי (`1507`) | `5912` — **unmapped, see below** |
| | direction_B: `36951` | 41,403 | 34 | `5912` — **unmapped, see below** | בנייני האומה/הנשיא השישי (`800`) |
| **14** | direction_A: `10179` | 34,138 | 40 | תחנה תפעולית/ביטוח לאומי (`1507`) | קניון מלחה/א''ס מכבי (`2923`) |
| | direction_B: `10180` | 34,921 | 35 | קניון מלחה/א''ס מכבי (`2923`) | שדרות שז''ר/בנייני האומה (`4218`) |

First/last stop = the two ends of each `route_id`'s single most common
stop sequence (the same "reference sequence" concept used later for
baseline-variant detection in `docs/04_baselines/`), read from
`govData/renamed_ride_data.csv` and named via `govData/jerusalem_stops.csv`.

## Notes and unresolved items

- **Line 15 has no direction split.** It is the only line with a single
  `route_id` (`37936`) in the current target scope, so
  `stage3_investigate_route_ids.py` never evaluates it — there is no
  second `route_id` to compare against. Its reference sequence starts
  and ends at the same street corner (האומן/ברעם) under two different
  `stop_code`s (`3300` vs. `6267` — opposite-side poles), consistent with
  a loop/circular route rather than a there-and-back line. **Line 15
  therefore has no `direction_A`/`direction_B` distinction in any later
  phase** — figures and reports for line 15 should say so explicitly
  rather than defaulting to a direction label.
- **Line 19 and line 17 share terminal stops** (מסוף הר הצופים/בנימין מזר
  ↔ מסוף הר הצופים/מרטין בובר, at Mount Scopus) with each other's
  opposite directions — both lines run the Mount Scopus corridor. This
  is useful context for `docs/09_lines_9_97/`-style cross-line
  comparisons but is not itself a route_id decision.
- **Line 19's and line 17's "direction_A" each bundle a sparse
  same-`route_id`-group alternate:** `10803` (1,514 rows, 90.7% stop
  overlap with `10802`) and, on the direction_B side, `10806`/`10807`
  (348/144 rows). `route_id_decisions.json` treats these as minor
  same-direction variants rather than a separate direction — stage4/5's
  variant-detection logic (Phase 03) is what actually classifies them as
  rare stop-skipping variants of the main reference sequence, not stage3.
- **Unresolved: stop_code `5912`** (the line 97 direction split point)
  has no entry in `govData/jerusalem_stops.csv`. It was not resolvable in
  `govData/stop_code_to_name_mapping.csv` (empty for this code) or
  `govData/stations.csv` either — that file's columns are malformed (the
  first data row was saved as the header, so `stop_code` isn't a usable
  key) and would need to be re-exported from source before it can help.
  Line 97 figures/reports should reference this stop as `stop_code 5912`
  until a name is resolved, rather than guessing.

**Sources:** `pipeline/stage3_investigate_route_ids.py`,
`govData/route_id_decisions.json`, `govData/route_id_comparison_report.csv`,
`govData/target_route_ids.json`, `govData/renamed_ride_data.csv`,
`govData/jerusalem_stops.csv`.
