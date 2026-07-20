"""Stage 3 -- BLOCKING CHECKPOINT: investigate multi-route_id lines.

Several lines now map to more than one route_id (e.g. line 19 -> 5
route_ids). Before anything downstream treats those route_ids as
interchangeable variants of the same line, this stage compares them
pairwise (stop-set overlap, reverse-sequence / direction check, month
coverage) and writes:

  - govData/route_id_comparison_report.csv  (evidence, for review)
  - govData/route_id_decisions.json         (template to fill in)

run_pipeline.py refuses to run stage4 onward until every multi-route_id
line in the decisions file has a non-null "treatment". This stage does
not decide anything itself -- it only gathers evidence.
"""

from __future__ import annotations

import json
from collections import Counter

import pandas as pd

from pipeline import config

VALID_TREATMENTS = {"pool", "keep_separate", "direction_pair"}


def most_common_sequence(df_route: pd.DataFrame) -> tuple[tuple, int, int]:
    """Return (most_common_stop_sequence, its_occurrence_count, n_blocks)."""
    block_keys = ["month", "day_of_week", "scheduled_departure_time"]
    sequences = (
        df_route.sort_values("stop_sequence")
        .groupby(block_keys, sort=False)["stop_code"]
        .apply(lambda s: tuple(s.tolist()))
    )
    n_blocks = len(sequences)
    if n_blocks == 0:
        return tuple(), 0, 0
    counts = Counter(sequences.tolist())
    most_common_seq, seq_count = counts.most_common(1)[0]
    return most_common_seq, seq_count, n_blocks


def summarize_route_id(df: pd.DataFrame, route_id: int) -> dict:
    sub = df[df["route_id"] == route_id]
    months = sorted(sub["month"].dropna().unique().tolist())
    days = sorted(sub["day_of_week"].dropna().unique().tolist())
    seq, seq_count, n_blocks = most_common_sequence(sub)
    return {
        "route_id": route_id,
        "n_rows": len(sub),
        "n_blocks": n_blocks,
        "months": months,
        "days": days,
        "most_common_seq": seq,
        "most_common_seq_count": seq_count,
        "n_stops": len(seq),
        "stops_set": set(seq),
    }


def classify_pair(a: dict, b: dict) -> str:
    if not a["stops_set"] or not b["stops_set"]:
        return "insufficient data (one route_id has no blocks in this dataset)"

    is_reverse = a["most_common_seq"] == tuple(reversed(b["most_common_seq"]))
    if is_reverse:
        return "reverse of each other -- likely opposite-direction pair"

    union = a["stops_set"] | b["stops_set"]
    jaccard = len(a["stops_set"] & b["stops_set"]) / len(union) if union else 0.0

    months_a, months_b = set(a["months"]), set(b["months"])
    months_overlap = bool(months_a & months_b)
    row_ratio = min(a["n_rows"], b["n_rows"]) / max(a["n_rows"], b["n_rows"])
    stops_ratio = min(a["n_stops"], b["n_stops"]) / max(a["n_stops"], b["n_stops"])

    if jaccard > 0.85:
        return "near-identical stop sets -- likely the same physical route (variant or id replacement)"

    # Near-zero stop-code overlap is ambiguous by itself: this dataset commonly
    # assigns a distinct stop_code per direction (opposite-side stop poles), so
    # a real direction pair will ALSO show ~0 overlap. Route length and volume
    # being similar, with overlapping months, is the distinguishing signal.
    if jaccard < 0.15 and stops_ratio > 0.6 and row_ratio > 0.3 and months_overlap:
        return (
            "near-zero stop overlap but similar route length/volume and "
            "overlapping months -- likely an opposite-direction pair using "
            "direction-specific stop codes, NOT necessarily a different "
            "physical route (verify on a map before assuming otherwise)"
        )
    if row_ratio < 0.1 or not months_overlap:
        return (
            "sparse/rare relative to its counterpart (little data and/or "
            "non-overlapping months) -- possibly a temporary or alternate "
            "route_id rather than a regular concurrent variant, needs review"
        )
    if jaccard < 0.3:
        return "disjoint stop sets with comparable volume -- not a clear direction pair, needs manual review (check on a map)"
    return "partial stop overlap -- needs manual review"


def run(renamed_path=None, report_path=None, decisions_path=None) -> pd.DataFrame:
    renamed_path = renamed_path or config.RENAMED_RIDE_DATA_PATH
    report_path = report_path or config.ROUTE_ID_COMPARISON_REPORT_PATH
    decisions_path = decisions_path or config.ROUTE_ID_DECISIONS_PATH

    df = pd.read_csv(renamed_path)

    targets = config.load_target_route_ids()
    rows = []
    decisions_template: dict[str, dict] = {}

    # Preserve any already-filled-in decisions (this stage is meant to be
    # rerunnable, e.g. as part of run_pipeline.py, without wiping out a
    # human/agent's prior review).
    existing_decisions: dict[str, dict] = {}
    if decisions_path.exists():
        existing_decisions = json.loads(decisions_path.read_text(encoding="utf-8"))

    for line in config.MULTI_ROUTE_ID_LINES:
        route_ids = targets[line]
        summaries = {rid: summarize_route_id(df, rid) for rid in route_ids}

        existing_entry = existing_decisions.get(line)
        if existing_entry and existing_entry.get("route_ids") == route_ids:
            decisions_template[line] = existing_entry
        else:
            decisions_template[line] = {
                "route_ids": route_ids,
                "treatment": None,
                "notes": "",
            }

        for i, rid_a in enumerate(route_ids):
            for rid_b in route_ids[i + 1 :]:
                a, b = summaries[rid_a], summaries[rid_b]
                union = a["stops_set"] | b["stops_set"]
                jaccard = (
                    len(a["stops_set"] & b["stops_set"]) / len(union) if union else 0.0
                )
                rows.append(
                    {
                        "line": line,
                        "route_id_a": rid_a,
                        "route_id_b": rid_b,
                        "n_rows_a": a["n_rows"],
                        "n_rows_b": b["n_rows"],
                        "n_stops_a": a["n_stops"],
                        "n_stops_b": b["n_stops"],
                        "months_a": a["months"],
                        "months_b": b["months"],
                        "stop_set_jaccard": round(jaccard, 3),
                        "row_ratio": round(
                            min(a["n_rows"], b["n_rows"]) / max(a["n_rows"], b["n_rows"]), 3
                        ),
                        "stops_ratio": round(
                            min(a["n_stops"], b["n_stops"]) / max(a["n_stops"], b["n_stops"]), 3
                        ),
                        "months_overlap": bool(set(a["months"]) & set(b["months"])),
                        "is_reverse_sequence": a["most_common_seq"]
                        == tuple(reversed(b["most_common_seq"])),
                        "hint": classify_pair(a, b),
                    }
                )

    report_df = pd.DataFrame(rows)
    report_df.to_csv(report_path, index=False, encoding="utf-8-sig")
    decisions_path.write_text(
        json.dumps(decisions_template, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"Saved -> {report_path} ({len(report_df)} route_id pairs across {len(config.MULTI_ROUTE_ID_LINES)} lines)")
    print(f"Saved -> {decisions_path} (template -- fill in 'treatment' for each line before continuing)")
    print()
    print("Lines requiring a decision:", config.MULTI_ROUTE_ID_LINES)
    print(f"Valid treatment values: {sorted(VALID_TREATMENTS)}")

    return report_df


def decisions_complete(decisions_path=None) -> bool:
    decisions_path = decisions_path or config.ROUTE_ID_DECISIONS_PATH
    if not decisions_path.exists():
        return False
    decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
    for line in config.MULTI_ROUTE_ID_LINES:
        entry = decisions.get(line)
        if not entry or entry.get("treatment") not in VALID_TREATMENTS:
            return False
    return True


if __name__ == "__main__":
    run()
