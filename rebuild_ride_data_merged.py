import argparse
import json
from datetime import datetime
from pathlib import Path
import shutil

import pandas as pd


DEFAULT_SOURCE = Path(r"C:\Users\ronys\Downloads\e3673768-3dc2-4e62-b0ea-cf763c07a037(3).csv")
DEFAULT_TARGETS = Path("govData/target_route_ids.json")
DEFAULT_DEST = Path("govData/ride_data_merged.csv")

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


def load_targets(path: Path) -> list[int]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    route_ids = sorted({int(route_id) for ids in raw.values() for route_id in ids})
    return route_ids


def validate_columns(df: pd.DataFrame) -> None:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Source file is missing required columns: {missing}")


def rebuild(source: Path, targets: Path, dest: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Missing source file: {source}")
    if not targets.exists():
        raise FileNotFoundError(f"Missing targets file: {targets}")

    target_route_ids = load_targets(targets)
    route_set = set(target_route_ids)

    chunks = pd.read_csv(source, sep="|", low_memory=False, chunksize=250_000)
    collected = []
    raw_rows = 0
    filtered_rows = 0
    first_chunk = True

    for chunk in chunks:
        raw_rows += len(chunk)
        if first_chunk:
            validate_columns(chunk)
            first_chunk = False

        for col in [
            "month",
            "route_id",
            "DayOfWeek",
            "HourSourceTime",
            "StopSequence_Rishui",
            "StopCode",
            "count_common",
        ]:
            chunk[col] = pd.to_numeric(chunk[col], errors="coerce")

        chunk["timeCumSum_mean"] = pd.to_numeric(chunk["timeCumSum_mean"], errors="coerce")
        chunk["timeCumSum_std"] = pd.to_numeric(chunk["timeCumSum_std"], errors="coerce")
        chunk["distCumSum_mean"] = pd.to_numeric(chunk["distCumSum_mean"], errors="coerce")

        filtered = chunk[chunk["route_id"].isin(route_set)].copy()
        filtered_rows += len(filtered)
        if not filtered.empty:
            collected.append(filtered)

    if not collected:
        raise ValueError("No rows from the source matched target route_ids.")

    df = pd.concat(collected, ignore_index=True)

    key_cols = [
        "route_id",
        "month",
        "DayOfWeek",
        "HourSourceTime",
        "StopSequence_Rishui",
    ]

    df = df.sort_values(key_cols + ["count_common"], ascending=[True, True, True, True, True, False])
    deduped = df.drop_duplicates(subset=key_cols, keep="first").copy()
    deduped_rows = len(deduped)

    deduped = deduped.sort_values(key_cols).reset_index(drop=True)
    deduped.insert(0, "_id", deduped.index + 1)
    deduped["distCumSum_std"] = pd.NA

    output = deduped[OUTPUT_COLUMNS]

    if dest.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = dest.with_suffix(f".backup_{stamp}.csv")
        shutil.copy2(dest, backup)
        print(f"Backup created: {backup}")

    output.to_csv(dest, index=False)

    present_route_ids = sorted(output["route_id"].dropna().astype(int).unique().tolist())
    missing_route_ids = [rid for rid in target_route_ids if rid not in present_route_ids]

    print("Rebuild complete")
    print("=" * 40)
    print(f"Source: {source}")
    print(f"Destination: {dest}")
    print(f"Raw rows in source: {raw_rows:,}")
    print(f"Rows after target route filter: {filtered_rows:,}")
    print(f"Rows after dedup: {deduped_rows:,}")
    print(f"Target route_ids: {target_route_ids}")
    print(f"Present route_ids in output: {present_route_ids}")
    print(f"Missing route_ids after rebuild: {missing_route_ids}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rebuild govData/ride_data_merged.csv from the 2024 government source file, "
            "filtered by target route IDs and deduplicated by project key."
        )
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Path to source CSV file")
    parser.add_argument("--targets", type=Path, default=DEFAULT_TARGETS, help="Path to target route map JSON")
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST, help="Path to output merged CSV")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    rebuild(args.source, args.targets, args.dest)