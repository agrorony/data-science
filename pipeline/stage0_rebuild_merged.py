"""Stage 0 -- rebuild govData/ride_data_merged.csv from the raw government
source, with a block-aware, majority-vote dedup (replaces the flawed
per-row "keep highest count_common" logic in the old repo_root/
rebuild_ride_data_merged.py).

Why: the raw source contains a structural ~3x overlap (the same trip
block appears in ~3 overlapping export copies). The old script deduped
row-by-row on (route_id, month, DayOfWeek, HourSourceTime,
StopSequence_Rishui) by keeping whichever row had the highest
count_common. For the ~2% of duplicate-key groups where the overlapping
copies actually disagree on StopCode (not just count_common), that
tiebreak is arbitrary (often a coin-flip when count_common is tied) and
can graft the wrong stop onto an otherwise-correct sequence.

Fix: for each key, take the StopCode with a clear majority across the
duplicate rows; if there's no clear majority (a genuine tie), flag it
instead of silently guessing. Among the rows agreeing with the winning
StopCode, keep the one with the highest count_common (preserves the
original script's intent for genuine same-content duplicates) so that
all of a winning row's value columns (travel time, distance) come from
one real, internally-consistent row rather than being mixed.

See pipeline/STAGE0_DEDUP_NOTES.md for the full writeup (counts, examples,
methodology) for the course report.
"""

from __future__ import annotations

import pandas as pd

from pipeline import config

REQUIRED_COLUMNS = [
    "month",
    "route_id",
    "DayOfWeek",
    "HourSourceTime",
    "StopSequence_Rishui",
    "StopCode",
    "count_common",
    "timeCumSum_mean",
    "timeCumSum_std",
    "distCumSum_mean",
]

OUTPUT_COLUMNS = [
    "_id",
    "month",
    "route_id",
    "DayOfWeek",
    "HourSourceTime",
    "StopSequence_Rishui",
    "StopCode",
    "count_common",
    "timeCumSum_mean",
    "timeCumSum_std",
    "distCumSum_mean",
    "distCumSum_std",
]

KEY_COLS = ["route_id", "month", "DayOfWeek", "HourSourceTime", "StopSequence_Rishui"]


def validate_columns(df: pd.DataFrame) -> None:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Source file is missing required columns: {missing}")


def load_and_filter(source, targets_path) -> pd.DataFrame:
    target_route_ids = config.load_target_route_ids(targets_path)
    route_set = {rid for ids in target_route_ids.values() for rid in ids}

    chunks = pd.read_csv(source, sep="|", low_memory=False, chunksize=250_000)
    collected = []
    raw_rows = 0
    first_chunk = True

    for chunk in chunks:
        raw_rows += len(chunk)
        if first_chunk:
            validate_columns(chunk)
            first_chunk = False

        for col in ["month", "route_id", "DayOfWeek", "HourSourceTime", "StopSequence_Rishui", "StopCode", "count_common"]:
            chunk[col] = pd.to_numeric(chunk[col], errors="coerce")
        for col in ["timeCumSum_mean", "timeCumSum_std", "distCumSum_mean"]:
            chunk[col] = pd.to_numeric(chunk[col], errors="coerce")

        filtered = chunk[chunk["route_id"].isin(route_set)].copy()
        if not filtered.empty:
            collected.append(filtered)

    if not collected:
        raise ValueError("No rows from the source matched target route_ids.")

    print(f"Raw rows in source: {raw_rows:,}")
    return pd.concat(collected, ignore_index=True)


def resolve_group(group: pd.DataFrame) -> tuple[pd.Series, dict]:
    """Resolve one (route_id,month,DayOfWeek,HourSourceTime,StopSequence_Rishui)
    key's rows into a single winning row + an audit record."""
    counts = group["StopCode"].value_counts()
    top_count = counts.iloc[0]
    n_tied_for_top = (counts == top_count).sum()
    ambiguous = len(counts) > 1 and n_tied_for_top > 1

    if ambiguous:
        # No clear majority: fall back to highest count_common among the
        # tied-for-top StopCodes, but this row is flagged in the audit.
        tied_codes = counts[counts == top_count].index
        candidates = group[group["StopCode"].isin(tied_codes)]
        winning_stopcode = candidates.loc[candidates["count_common"].idxmax(), "StopCode"]
    else:
        winning_stopcode = counts.index[0]

    matching = group[group["StopCode"] == winning_stopcode]
    winner_idx = matching["count_common"].idxmax()
    winner = matching.loc[[winner_idx]]  # double brackets: keep as a 1-row DataFrame, not a Series,
    # so each column keeps its own dtype (a Series would flatten route_id/StopCode etc. to float64)

    audit = {
        "n_rows_in_group": len(group),
        "n_distinct_stopcodes": len(counts),
        "winning_stopcode": winning_stopcode,
        "winning_stopcode_votes": int(top_count),
        "ambiguous": ambiguous,
    }
    return winner, audit


def dedupe(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    dup_mask = df.duplicated(subset=KEY_COLS, keep=False)
    unique_rows = df[~dup_mask]
    dup_rows = df[dup_mask]

    print(f"Rows with a unique key (no dedup needed): {len(unique_rows):,}")
    print(f"Rows sharing a key with at least one other row: {len(dup_rows):,}")

    winners = []
    audit_records = []
    for key, group in dup_rows.groupby(KEY_COLS, sort=False):
        winner, audit = resolve_group(group)
        winners.append(winner)
        if audit["n_distinct_stopcodes"] > 1:
            record = dict(zip(KEY_COLS, key))
            record.update(audit)
            audit_records.append(record)

    resolved = pd.concat(winners, ignore_index=True) if winners else pd.DataFrame(columns=df.columns)
    deduped = pd.concat([unique_rows, resolved], ignore_index=True)
    audit_df = pd.DataFrame(audit_records)

    n_groups_with_disagreement = len(audit_df)
    n_ambiguous = int(audit_df["ambiguous"].sum()) if not audit_df.empty else 0
    print(f"Duplicate-key groups with a StopCode disagreement: {n_groups_with_disagreement:,}")
    print(f"  resolved by clear majority: {n_groups_with_disagreement - n_ambiguous:,}")
    print(f"  flagged ambiguous (no clear majority, fell back to max count_common): {n_ambiguous:,}")

    return deduped, audit_df


def run(source=None, targets_path=None, dest=None, audit_path=None) -> pd.DataFrame:
    source = source or config.RAW_SOURCE_PATH
    targets_path = targets_path or config.TARGET_ROUTE_IDS_PATH
    dest = dest or config.RIDE_DATA_MERGED_PATH
    audit_path = audit_path or config.STAGE0_DEDUP_AUDIT_PATH

    if not source.exists():
        raise FileNotFoundError(f"Missing raw source file: {source}")
    if not targets_path.exists():
        raise FileNotFoundError(f"Missing targets file: {targets_path}")

    df = load_and_filter(source, targets_path)
    print(f"Rows after target route_id filter: {len(df):,}")

    deduped, audit_df = dedupe(df)
    deduped = deduped.sort_values(KEY_COLS).reset_index(drop=True)
    deduped.insert(0, "_id", deduped.index + 1)
    deduped["distCumSum_std"] = pd.NA

    output = deduped[OUTPUT_COLUMNS]
    output.to_csv(dest, index=False)
    audit_df.to_csv(audit_path, index=False)

    present_route_ids = sorted(output["route_id"].dropna().astype(int).unique().tolist())
    print()
    print("Rebuild complete")
    print("=" * 40)
    print(f"Destination: {dest}")
    print(f"Rows after dedup: {len(output):,}")
    print(f"Present route_ids in output: {present_route_ids}")
    print(f"Audit report -> {audit_path} ({len(audit_df)} groups with a StopCode disagreement)")

    return output


if __name__ == "__main__":
    run()
