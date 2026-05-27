import csv
import json
import re
import time
from datetime import datetime, timedelta, timezone, date
from http.client import RemoteDisconnected
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

BASE_URL = "https://open-bus-stride-api.hasadna.org.il"
OUTPUT_DIR = Path("output")
PAGE_SIZE = 1000
TIMEOUT_SECONDS = 90
MAX_RETRIES = 8
BACKOFF_SECONDS = 1.5
WINDOW_DAYS = 7
MAX_PAGES_PER_SLICE = 5000


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def to_snake_case(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name or "col"


def flatten_record(record: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    flat: Dict[str, Any] = {}
    for key, value in record.items():
        key_name = f"{prefix}_{key}" if prefix else str(key)
        if isinstance(value, dict):
            flat.update(flatten_record(value, key_name))
        elif isinstance(value, list):
            # Keep table flat by storing list as a compact raw string.
            flat[key_name] = "|".join(str(x) for x in value)
        else:
            flat[key_name] = value
    return flat


def normalize_rows(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    normalized_rows: List[Dict[str, Any]] = []
    all_cols = set()

    for row in rows:
        flat = flatten_record(row)
        normalized: Dict[str, Any] = {}
        for key, value in flat.items():
            col = to_snake_case(key)
            normalized[col] = value
            all_cols.add(col)
        normalized_rows.append(normalized)

    columns = sorted(all_cols)
    return normalized_rows, columns


def is_temporal_column(col: str) -> bool:
    tokens = ("time", "date", "timestamp", "recorded_at", "scheduled", "updated")
    return any(token in col for token in tokens)


def to_iso_if_possible(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (int, float, bool)):
        return value

    text = str(value).strip()
    if not text:
        return text

    # Date only
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        try:
            return date.fromisoformat(text).isoformat()
        except ValueError:
            return text

    # ISO datetime with Z or offset
    candidate = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(candidate)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    except ValueError:
        return text


def clean_rows(rows: List[Dict[str, Any]], columns: List[str]) -> List[Dict[str, Any]]:
    cleaned: List[Dict[str, Any]] = []
    seen = set()

    for row in rows:
        normalized_row: Dict[str, Any] = {}
        for col in columns:
            value = row.get(col)
            if is_temporal_column(col):
                value = to_iso_if_possible(value)
            normalized_row[col] = value

        signature = tuple(normalized_row.get(col) for col in columns)
        if signature in seen:
            continue
        seen.add(signature)
        cleaned.append(normalized_row)

    return cleaned


def request_json(path: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    query = urlencode(params, doseq=True)
    url = f"{BASE_URL}{path}?{query}"

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = Request(url, headers={"User-Agent": "openbus-extractor/1.0"})
            with urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                payload = resp.read().decode("utf-8")
                data = json.loads(payload)
                if isinstance(data, list):
                    return data
                raise ValueError(f"Unexpected response type from {path}: {type(data)}")
        except (URLError, HTTPError, TimeoutError, ValueError, json.JSONDecodeError, RemoteDisconnected) as exc:
            last_error = exc
            if attempt == MAX_RETRIES:
                break
            time.sleep(BACKOFF_SECONDS * attempt)

    raise RuntimeError(f"Request failed for {url}: {last_error}")


def fetch_paginated(path: str, base_params: Dict[str, Any], page_size: int = PAGE_SIZE) -> List[Dict[str, Any]]:
    all_rows: List[Dict[str, Any]] = []
    offset = 0
    pages = 0
    seen_page_fingerprints = set()

    while True:
        pages += 1
        if pages > MAX_PAGES_PER_SLICE:
            print(f"Warning: hit max pages for {path} with params={base_params}")
            break

        params = dict(base_params)
        params["limit"] = page_size
        params["offset"] = offset

        batch = request_json(path, params)
        if not batch:
            break

        page_fingerprint = (
            str(batch[0].get("id", "")),
            str(batch[-1].get("id", "")),
            len(batch),
        )
        if page_fingerprint in seen_page_fingerprints:
            print(f"Warning: repeated page detected for {path} at offset={offset}; stopping slice")
            break
        seen_page_fingerprints.add(page_fingerprint)

        all_rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += len(batch)

    return all_rows


def iter_time_slices(start_dt: datetime, end_dt: datetime, slice_hours: int) -> Iterable[Tuple[datetime, datetime]]:
    cursor = start_dt
    delta = timedelta(hours=slice_hours)
    while cursor < end_dt:
        nxt = min(cursor + delta, end_dt)
        yield cursor, nxt
        cursor = nxt


def fetch_over_time_slices(
    path: str,
    from_param: str,
    to_param: str,
    start_dt: datetime,
    end_dt: datetime,
    slice_hours: int,
    page_size: int,
) -> List[Dict[str, Any]]:
    all_rows: List[Dict[str, Any]] = []

    for slice_start, slice_end in iter_time_slices(start_dt, end_dt, slice_hours):
        slice_from = iso_z(slice_start)
        slice_to = iso_z(slice_end)
        print(f"Fetching {path} slice: {slice_from} -> {slice_to}")
        slice_rows = fetch_paginated(
            path,
            {
                from_param: slice_from,
                to_param: slice_to,
            },
            page_size=page_size,
        )
        print(f"  slice rows: {len(slice_rows)}")
        all_rows.extend(slice_rows)

    return all_rows


def write_csv(path: Path, rows: List[Dict[str, Any]], columns: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def unique_non_null(values: Iterable[Any]) -> set:
    out = set()
    for v in values:
        if v is None:
            continue
        text = str(v).strip()
        if text:
            out.add(text)
    return out


def main() -> None:
    end_dt = utc_now()
    start_dt = end_dt - timedelta(days=WINDOW_DAYS)

    start_iso = iso_z(start_dt)
    end_iso = iso_z(end_dt)

    print(f"Window UTC: {start_iso} -> {end_iso}")

    rides_raw = fetch_over_time_slices(
        "/siri_rides/list",
        "scheduled_start_time_from",
        "scheduled_start_time_to",
        start_dt,
        end_dt,
        slice_hours=24,
        page_size=1000,
    )
    print(f"Fetched rides raw total: {len(rides_raw)}")

    ride_stops_raw = fetch_over_time_slices(
        "/siri_ride_stops/list",
        "siri_ride__scheduled_start_time_from",
        "siri_ride__scheduled_start_time_to",
        start_dt,
        end_dt,
        slice_hours=3,
        page_size=300,
    )
    print(f"Fetched ride_stops raw total: {len(ride_stops_raw)}")

    vehicle_locations_raw = fetch_over_time_slices(
        "/siri_vehicle_locations/list",
        "recorded_at_time_from",
        "recorded_at_time_to",
        start_dt,
        end_dt,
        slice_hours=6,
        page_size=600,
    )
    print(f"Fetched vehicle_locations raw total: {len(vehicle_locations_raw)}")

    rides_norm, rides_cols = normalize_rows(rides_raw)
    ride_stops_norm, ride_stops_cols = normalize_rows(ride_stops_raw)
    vehicle_locations_norm, vehicle_locations_cols = normalize_rows(vehicle_locations_raw)

    rides_clean = clean_rows(rides_norm, rides_cols)
    ride_stops_clean = clean_rows(ride_stops_norm, ride_stops_cols)
    vehicle_locations_clean = clean_rows(vehicle_locations_norm, vehicle_locations_cols)

    rides_path = OUTPUT_DIR / "rides.csv"
    ride_stops_path = OUTPUT_DIR / "ride_stops.csv"
    vehicle_locations_path = OUTPUT_DIR / "vehicle_locations.csv"

    write_csv(rides_path, rides_clean, rides_cols)
    write_csv(ride_stops_path, ride_stops_clean, ride_stops_cols)
    write_csv(vehicle_locations_path, vehicle_locations_clean, vehicle_locations_cols)

    unique_rides = unique_non_null(row.get("id") for row in rides_clean)

    stop_ids = unique_non_null(row.get("siri_stop_id") for row in ride_stops_clean)
    if not stop_ids:
        stop_ids = unique_non_null(row.get("gtfs_stop_id") for row in ride_stops_clean)

    vehicles_from_rides = unique_non_null(row.get("vehicle_ref") for row in rides_clean)
    vehicles_from_vl = unique_non_null(row.get("siri_ride_vehicle_ref") for row in vehicle_locations_clean)
    unique_vehicles = vehicles_from_rides.union(vehicles_from_vl)

    print("\nExtraction summary")
    print(f"records_rides={len(rides_clean)}")
    print(f"records_ride_stops={len(ride_stops_clean)}")
    print(f"records_vehicle_locations={len(vehicle_locations_clean)}")
    print(f"unique_rides={len(unique_rides)}")
    print(f"stops={len(stop_ids)}")
    print(f"vehicles={len(unique_vehicles)}")

    print("\nOutput files")
    print(str(rides_path.resolve()))
    print(str(ride_stops_path.resolve()))
    print(str(vehicle_locations_path.resolve()))


if __name__ == "__main__":
    main()
