"""Stage 2 — rename columns and tag every row with its line (route_name).

Replaces avishagi/change_colmn_name.ipynb's per-file, 4-route-only rename
step. Produces a single govData/renamed_ride_data.csv covering all lines
and all route_ids in govData/target_route_ids.json -- route_id is kept as
a column, never split into per-line files.
"""

from __future__ import annotations

import pandas as pd

from pipeline import config


def run(source_path=None, dest_path=None) -> pd.DataFrame:
    source_path = source_path or config.RIDE_DATA_MERGED_PATH
    dest_path = dest_path or config.RENAMED_RIDE_DATA_PATH

    df = pd.read_csv(source_path)
    df = df.rename(columns=config.RENAME_COLUMNS)

    route_id_to_line = config.ROUTE_ID_TO_LINE
    df["route_name"] = df["route_id"].map(route_id_to_line)

    unmapped = df[df["route_name"].isna()]
    if not unmapped.empty:
        unmapped_ids = sorted(unmapped["route_id"].dropna().unique().tolist())
        print(
            f"WARNING: {len(unmapped)} rows have a route_id not present in "
            f"target_route_ids.json and got route_name = NaN: {unmapped_ids}"
        )

    df.to_csv(dest_path, index=False)

    print(f"Saved -> {dest_path} ({len(df):,} rows)")
    print(f"Lines present: {sorted(df['route_name'].dropna().unique().tolist())}")
    for line in config.LINES:
        n_rows = (df["route_name"] == line).sum()
        route_ids = sorted(df.loc[df["route_name"] == line, "route_id"].unique().tolist())
        print(f"  line {line}: {n_rows:,} rows, route_ids present: {route_ids}")

    return df


if __name__ == "__main__":
    run()
