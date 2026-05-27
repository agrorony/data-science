"""
OpenBus – small validation extraction
  - Jerusalem area only (bounding-box filter on ride_stops)
  - 1 day window  (2026-05-02, 07:00–11:00 Israel = 04:00–08:00 UTC)
  - max 5 operator/line pairs
  - ride_stops and vehicle_locations driven by ride IDs (no broad time-range pagination)
  - prints per-endpoint timings and record counts
"""

import csv
import json
import time
from http.client import RemoteDisconnected
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# ─── Configuration ──────────────────────────────────────────────────────────

BASE_URL   = "https://open-bus-stride-api.hasadna.org.il"
OUTPUT_DIR = Path("output_sample")

# 1-day window (UTC) for validation
DAY_DATE = "2026-05-02"
DAY_FROM = "2026-05-02T00:00:00Z"
DAY_TO   = "2026-05-02T23:59:59Z"

# Jerusalem bounding box (WGS-84)
JLM_LAT_MIN = 31.72
JLM_LAT_MAX = 31.85
JLM_LON_MIN = 35.15
JLM_LON_MAX = 35.25

MAX_PAIRS          = 5    # distinct operator/line pairs to collect
MAX_RIDES_PER_PAIR = 10   # rides fetched per pair
SAMPLE_LIMIT       = 200  # page size for geographic discovery scan
MAX_DISCOVERY_ROWS = 5000 # hard cap rows scanned from ride_stops

TIMEOUT     = 45
MAX_RETRIES = 5
BACKOFF     = 2.0

# ─── HTTP helpers ────────────────────────────────────────────────────────────

def get_json(path: str, params: dict) -> list:
    query = urlencode(params, doseq=True)
    url   = f"{BASE_URL}{path}?{query}"
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = Request(url, headers={"User-Agent": "openbus-validate/1.0"})
            with urlopen(req, timeout=TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if isinstance(data, list):
                    return data
                raise ValueError(f"Non-list response from {path}")
        except (URLError, HTTPError, TimeoutError,
                RemoteDisconnected, ValueError, json.JSONDecodeError) as exc:
            last_exc = exc
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF * attempt)
    raise RuntimeError(f"FAILED {url}\n  → {last_exc}")


def timed_get(label: str, path: str, params: dict) -> tuple[list, float]:
    t0   = time.perf_counter()
    data = get_json(path, params)
    elapsed = time.perf_counter() - t0
    print(f"  [{label}] {len(data)} rows  ({elapsed:.1f}s)  params={params}")
    return data, elapsed


def as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def in_jerusalem_bbox(row: dict) -> bool:
    lat = as_float(row.get("lat"))
    lon = as_float(row.get("lon"))
    if lat is None or lon is None:
        lat = as_float(row.get("gtfs_stop__lat"))
        lon = as_float(row.get("gtfs_stop__lon"))
    if lat is None or lon is None:
        lat = as_float(row.get("nearest_siri_vehicle_location__lat"))
        lon = as_float(row.get("nearest_siri_vehicle_location__lon"))
    if lat is None or lon is None:
        lat = as_float(row.get("siri_vehicle_location__lat"))
        lon = as_float(row.get("siri_vehicle_location__lon"))
    if lat is None or lon is None:
        return False
    return (
        JLM_LAT_MIN <= lat <= JLM_LAT_MAX
        and JLM_LON_MIN <= lon <= JLM_LON_MAX
    )

# ─── Step 1 – discover Jerusalem-area ride_stops (geographic filter) ─────────

print("=" * 60)
print("STEP 1  Discover Jerusalem-area ride_stops (geographic filter)")
print(f"  window: {DAY_FROM} → {DAY_TO}")
print(f"  bbox:   lat [{JLM_LAT_MIN},{JLM_LAT_MAX}]  lon [{JLM_LON_MIN},{JLM_LON_MAX}]")
print()

timings: dict[str, list] = {"discovery": [], "rides": [], "ride_stops": [], "vehicle_locations": []}
discovery_rows: list[dict] = []
pairs_seen: dict[tuple, dict] = {}
seed_ride_ids: list[str] = []

offset = 0
rows_scanned = 0
while rows_scanned < MAX_DISCOVERY_ROWS and len(pairs_seen) < MAX_PAIRS:
    page, elapsed = timed_get(
        f"vehicle_locations/discovery offset={offset}",
        "/siri_vehicle_locations/list",
        {
            "recorded_at_time_from": DAY_FROM,
            "recorded_at_time_to": DAY_TO,
            "lat__greater_or_equal": JLM_LAT_MIN,
            "lat__lower_or_equal": JLM_LAT_MAX,
            "lon__greater_or_equal": JLM_LON_MIN,
            "lon__lower_or_equal": JLM_LON_MAX,
            "limit": SAMPLE_LIMIT,
            "offset": offset,
        },
    )
    timings["discovery"].append(elapsed)
    if not page:
        break
    rows_scanned += len(page)
    offset += SAMPLE_LIMIT

    for row in page:
        if not in_jerusalem_bbox(row):
            continue
        discovery_rows.append(row)
        ride_id = row.get("siri_ride__id")
        if ride_id is not None:
            seed_ride_ids.append(str(ride_id))

        op = row.get("siri_route__operator_ref")
        line = row.get("siri_route__line_ref")
        if op is None or line is None:
            continue
        try:
            key = (int(op), int(line))
        except (TypeError, ValueError):
            continue
        if key not in pairs_seen:
            pairs_seen[key] = {"operator_ref": int(op), "line_ref": int(line)}
        if len(pairs_seen) >= MAX_PAIRS:
            break

# Extract up to MAX_PAIRS distinct (operator_ref, line_ref) pairs
# ride_stops records carry gtfs_route__operator_ref + gtfs_route__line_ref
if not pairs_seen:
    print("  No operator/line pairs found in discovery. Falling back to top discovery row ride IDs.")
else:
    print(f"  Discovery scanned rows: {rows_scanned}, Jerusalem-matching rows: {len(discovery_rows)}")

print(f"\n  Found {len(pairs_seen)} operator/line pairs:")
for k in pairs_seen:
    print(f"    operator={k[0]}  line={k[1]}")

# ─── Step 2 – fetch rides per pair ───────────────────────────────────────────

print()
print("=" * 60)
print("STEP 2  Fetch rides per operator/line pair")
print()

all_rides: list[dict] = []

for pair in pairs_seen.values():
    rows, elapsed = timed_get(
        f"rides op={pair['operator_ref']} line={pair['line_ref']}",
        "/siri_rides/list",
        {
            "siri_route__operator_refs": pair["operator_ref"],
            "siri_route__line_refs":     pair["line_ref"],
            "scheduled_start_time_from": DAY_FROM,
            "scheduled_start_time_to":   DAY_TO,
            "limit": MAX_RIDES_PER_PAIR,
        },
    )
    timings["rides"].append(elapsed)
    all_rides.extend(rows)

# Deduplicate by ride id
seen_ids: set = set()
unique_rides: list[dict] = []
for r in all_rides:
    if r["id"] not in seen_ids:
        seen_ids.add(r["id"])
        unique_rides.append(r)

ride_ids = [str(r["id"]) for r in unique_rides]
print(f"\n  Total unique rides collected: {len(unique_rides)}")
if not ride_ids:
    # Fallback: use ride IDs directly from geo-filtered vehicle-location discovery
    fallback_ids = list(dict.fromkeys(seed_ride_ids))[:20]
    ride_ids = fallback_ids
    print(f"  Fallback: using {len(ride_ids)} ride IDs from discovery rows")

# ─── Step 3 – fetch ride_stops by ride IDs (no broad time range!) ────────────

print()
print("=" * 60)
print("STEP 3  Fetch ride_stops by ride IDs")
print(f"  ride IDs: {ride_ids[:10]}{'...' if len(ride_ids) > 10 else ''}")
print()

all_ride_stops: list[dict] = []

# Chunk ride IDs into groups of 5 to stay well within URL/server limits
CHUNK = 5
for i in range(0, len(ride_ids), CHUNK):
    chunk = ride_ids[i : i + CHUNK]
    rows, elapsed = timed_get(
        f"ride_stops chunk {i//CHUNK + 1}",
        "/siri_ride_stops/list",
        {
            "siri_ride_ids": ",".join(chunk),
            "limit": 100,
        },
    )
    timings["ride_stops"].append(elapsed)
    all_ride_stops.extend(rows)

print(f"\n  Total ride_stop rows: {len(all_ride_stops)}")

# ─── Step 4 – fetch vehicle_locations by ride IDs ────────────────────────────

print()
print("=" * 60)
print("STEP 4  Fetch vehicle_locations by ride IDs")
print()

all_vehicle_locs: list[dict] = []

for i in range(0, len(ride_ids), CHUNK):
    chunk = ride_ids[i : i + CHUNK]
    rows, elapsed = timed_get(
        f"vehicle_locs chunk {i//CHUNK + 1}",
        "/siri_vehicle_locations/list",
        {
            "siri_rides__ids": ",".join(chunk),
            "limit": 100,
        },
    )
    timings["vehicle_locations"].append(elapsed)
    all_vehicle_locs.extend(rows)

print(f"\n  Total vehicle_location rows: {len(all_vehicle_locs)}")

# ─── Step 5 – flatten, clean and write CSVs ──────────────────────────────────

print()
print("=" * 60)
print("STEP 5  Flatten, clean and write CSVs")

def to_flat_row(record: dict) -> dict:
    flat = {}
    for k, v in record.items():
        col = k.lower().strip()
        if isinstance(v, list):
            flat[col] = "|".join(str(x) for x in v)
        elif isinstance(v, dict):
            for sk, sv in v.items():
                flat[f"{col}__{sk.lower()}"] = sv
        else:
            flat[col] = v
    return flat


def write_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        print(f"  (no rows to write: {path})")
        return
    flat_rows = [to_flat_row(r) for r in rows]
    # Deduplicate
    seen = set()
    deduped = []
    all_keys = sorted({k for r in flat_rows for k in r})
    for row in flat_rows:
        sig = tuple(row.get(k) for k in all_keys)
        if sig not in seen:
            seen.add(sig)
            deduped.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
        writer.writeheader()
        for row in deduped:
            writer.writerow(row)
    print(f"  Wrote {len(deduped)} rows → {path}")


rides_path  = OUTPUT_DIR / "rides.csv"
stops_path  = OUTPUT_DIR / "ride_stops.csv"
vl_path     = OUTPUT_DIR / "vehicle_locations.csv"

write_csv(unique_rides,    rides_path)
write_csv(all_ride_stops,  stops_path)
write_csv(all_vehicle_locs, vl_path)

# ─── Summary ─────────────────────────────────────────────────────────────────

print()
print("=" * 60)
print("EXTRACTION SUMMARY")
print(f"  records_rides              = {len(unique_rides)}")
print(f"  records_ride_stops         = {len(all_ride_stops)}")
print(f"  records_vehicle_locations  = {len(all_vehicle_locs)}")
print()
unique_ride_ids = {str(r.get("id")) for r in unique_rides}
unique_stop_ids = (
    {str(r.get("siri_stop_id")) for r in all_ride_stops if r.get("siri_stop_id")}
    or {str(r.get("gtfs_stop_id")) for r in all_ride_stops if r.get("gtfs_stop_id")}
)
unique_vehicle_refs = (
    {str(r.get("vehicle_ref")) for r in unique_rides if r.get("vehicle_ref")}
    | {str(r.get("siri_ride__vehicle_ref")) for r in all_vehicle_locs if r.get("siri_ride__vehicle_ref")}
)
print(f"  unique_rides               = {len(unique_ride_ids)}")
print(f"  unique_stops               = {len(unique_stop_ids)}")
print(f"  unique_vehicles            = {len(unique_vehicle_refs)}")
print()
print("TIMING (seconds per endpoint)")
for ep, ts in timings.items():
    if ts:
        print(f"  {ep:25s}  calls={len(ts)}  min={min(ts):.1f}  max={max(ts):.1f}  total={sum(ts):.1f}")
    else:
        print(f"  {ep:25s}  (no calls)")
print()
print("OUTPUT FILES")
for p in (rides_path, stops_path, vl_path):
    print(f"  {p.resolve()}")
