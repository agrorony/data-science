"""Stage 1 -- confirm govData/ride_data_merged.csv actually contains every
route_id in govData/target_route_ids.json.

Pipeline-owned replacement for the old repo_root/validate_target_routes.py
(same logic, now reading paths from config.py instead of hardcoding them).
"""

from __future__ import annotations

import pandas as pd

from pipeline import config


def run(data_path=None, targets_path=None) -> None:
    data_path = data_path or config.RIDE_DATA_MERGED_PATH
    targets_path = targets_path or config.TARGET_ROUTE_IDS_PATH

    if not data_path.exists():
        raise FileNotFoundError(f"Missing dataset file: {data_path}")
    if not targets_path.exists():
        raise FileNotFoundError(f"Missing targets file: {targets_path}")

    targets_by_line = config.load_target_route_ids(targets_path)

    route_series = pd.read_csv(data_path, usecols=["route_id"])["route_id"]
    existing_route_ids = set(route_series.dropna().astype(int).tolist())

    requested_route_ids = sorted({rid for ids in targets_by_line.values() for rid in ids})
    present = sorted(rid for rid in requested_route_ids if rid in existing_route_ids)
    missing = sorted(rid for rid in requested_route_ids if rid not in existing_route_ids)

    print("Target route_id coverage check")
    print("=" * 36)
    print(f"Dataset: {data_path}")
    print(f"Targets: {targets_path}")
    print(f"Requested route_ids: {len(requested_route_ids)}")
    print(f"Present: {len(present)}")
    print(f"Missing: {len(missing)}")
    print()

    print("Present route_ids:")
    print(present)
    print()

    print("Missing route_ids:")
    print(missing)
    print()

    print("Per-line status:")
    for line_name in sorted(targets_by_line):
        requested = targets_by_line[line_name]
        present_line = sorted(rid for rid in requested if rid in existing_route_ids)
        missing_line = sorted(rid for rid in requested if rid not in existing_route_ids)
        print(f"line {line_name}: requested={requested} | present={present_line} | missing={missing_line}")

    if missing:
        raise ValueError(f"Missing route_ids in {data_path}: {missing}")


if __name__ == "__main__":
    run()
