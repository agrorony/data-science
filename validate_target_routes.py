import json
from pathlib import Path

import pandas as pd


DEFAULT_DATA_PATH = Path("govData/ride_data_merged.csv")
DEFAULT_TARGETS_PATH = Path("govData/target_route_ids.json")


def load_targets(path: Path) -> dict[int, list[int]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    targets: dict[int, list[int]] = {}
    for line_name, route_ids in raw.items():
        targets[int(line_name)] = [int(route_id) for route_id in route_ids]
    return targets


def main() -> None:
    if not DEFAULT_DATA_PATH.exists():
        raise FileNotFoundError(f"Missing dataset file: {DEFAULT_DATA_PATH}")
    if not DEFAULT_TARGETS_PATH.exists():
        raise FileNotFoundError(f"Missing targets file: {DEFAULT_TARGETS_PATH}")

    targets_by_line = load_targets(DEFAULT_TARGETS_PATH)

    route_series = pd.read_csv(DEFAULT_DATA_PATH, usecols=["route_id"])["route_id"]
    existing_route_ids = set(route_series.dropna().astype(int).tolist())

    requested_route_ids = sorted({route_id for ids in targets_by_line.values() for route_id in ids})
    present = sorted([route_id for route_id in requested_route_ids if route_id in existing_route_ids])
    missing = sorted([route_id for route_id in requested_route_ids if route_id not in existing_route_ids])

    print("Target route_id coverage check")
    print("=" * 36)
    print(f"Dataset: {DEFAULT_DATA_PATH}")
    print(f"Targets: {DEFAULT_TARGETS_PATH}")
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
        present_line = sorted([route_id for route_id in requested if route_id in existing_route_ids])
        missing_line = sorted([route_id for route_id in requested if route_id not in existing_route_ids])
        print(
            f"line {line_name}: requested={requested} | "
            f"present={present_line} | missing={missing_line}"
        )


if __name__ == "__main__":
    main()
