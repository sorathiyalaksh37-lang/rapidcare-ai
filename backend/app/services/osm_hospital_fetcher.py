"""
OSM Hospital Fetcher
====================
Fetches 10,000+ hospitals from OpenStreetMap Overpass API (free, no API key).
Runs async with aiohttp, rate-limited to 10 req/s, with tenacity retry logic.

Query covers India bounds (8°N–37°N, 68°E–97°E) using a paginated bounding-box
approach to stay within OSM's 10k element response limit per call.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from typing import Any

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
# Tile grid: split India into ~24 tiles so each query stays under OSM limits
INDIA_TILES: list[tuple[float, float, float, float]] = [
    # (south, west, north, east)
    (8.0, 68.0, 14.0, 77.0), (8.0, 77.0, 14.0, 86.0), (8.0, 86.0, 14.0, 97.0),
    (14.0, 68.0, 20.0, 75.0), (14.0, 75.0, 20.0, 82.0), (14.0, 82.0, 20.0, 89.0), (14.0, 89.0, 20.0, 97.0),
    (20.0, 68.0, 25.0, 75.0), (20.0, 75.0, 25.0, 80.0), (20.0, 80.0, 25.0, 85.0), (20.0, 85.0, 25.0, 91.0), (20.0, 91.0, 25.0, 97.0),
    (25.0, 68.0, 30.0, 74.0), (25.0, 74.0, 30.0, 79.0), (25.0, 79.0, 30.0, 84.0), (25.0, 84.0, 30.0, 89.0), (25.0, 89.0, 30.0, 97.0),
    (30.0, 68.0, 34.0, 74.0), (30.0, 74.0, 34.0, 79.0), (30.0, 79.0, 34.0, 84.0), (30.0, 84.0, 34.0, 89.0), (30.0, 89.0, 34.0, 97.0),
    (34.0, 68.0, 37.0, 78.0), (34.0, 78.0, 37.0, 97.0),
]
_RATE_LIMIT = 10  # max requests per second
_LAST_REQUEST: list[float] = [0.0]
_REQUEST_LOCK = asyncio.Lock()


def _overpass_query(south: float, west: float, north: float, east: float) -> str:
    """Build Overpass QL query for hospitals in a bounding box."""
    bbox = f"{south},{west},{north},{east}"
    return f"""
[out:json][timeout:60];
(
  node["amenity"="hospital"]({bbox});
  way["amenity"="hospital"]({bbox});
  node["healthcare"="hospital"]({bbox});
  way["healthcare"="hospital"]({bbox});
  node["amenity"="clinic"]["emergency"="yes"]({bbox});
);
out center tags;
""".strip()


async def _rate_limit_sleep() -> None:
    """Enforce rate limiting — max 10 req/s."""
    async with _REQUEST_LOCK:
        elapsed = time.monotonic() - _LAST_REQUEST[0]
        if elapsed < 1.0 / _RATE_LIMIT:
            await asyncio.sleep(1.0 / _RATE_LIMIT - elapsed)
        _LAST_REQUEST[0] = time.monotonic()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
    reraise=False,
)
async def _fetch_tile(
    session: aiohttp.ClientSession,
    south: float, west: float, north: float, east: float,
) -> list[dict[str, Any]]:
    """Fetch one bounding-box tile from Overpass API."""
    await _rate_limit_sleep()
    query = _overpass_query(south, west, north, east)
    try:
        async with session.post(
            OVERPASS_URL,
            data=query,
            timeout=aiohttp.ClientTimeout(total=90),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data.get("elements", [])
    except Exception as exc:
        logger.warning("OSM tile (%s,%s,%s,%s) failed: %s", south, west, north, east, exc)
        return []


def _normalise_element(el: dict[str, Any]) -> dict[str, Any] | None:
    """Convert an OSM element to RapidCare hospital dict. Returns None if invalid."""
    tags = el.get("tags", {})
    name = tags.get("name") or tags.get("name:en") or tags.get("operator")
    if not name:
        return None

    # Coordinates: nodes have lat/lon directly; ways have a "center" key
    lat = el.get("lat") or (el.get("center") or {}).get("lat")
    lon = el.get("lon") or (el.get("center") or {}).get("lon")
    if lat is None or lon is None:
        return None

    # Deterministic ID from OSM element
    uid = hashlib.md5(f"osm-{el.get('type')}-{el.get('id')}".encode()).hexdigest()[:16]

    # Infer specialties from tags
    specialties: list[str] = []
    tag_str = " ".join(f"{k} {v}" for k, v in tags.items()).lower()
    specialty_map = {
        "trauma": ["trauma", "accident", "emergency", "casualty"],
        "cardiac": ["cardiac", "heart", "cardio"],
        "neurology": ["neuro", "brain", "stroke"],
        "burn": ["burn"],
        "fracture": ["orthop", "bone", "fracture"],
        "pediatric": ["pediatric", "child", "children"],
        "maternity": ["maternity", "obstet", "gynae"],
    }
    for spec, keywords in specialty_map.items():
        if any(kw in tag_str for kw in keywords):
            specialties.append(spec)
    if not specialties:
        specialties = ["general"]

    # Trauma center heuristic
    trauma = "trauma" in specialties or tags.get("emergency") in ("yes", "trauma_center")
    level = tags.get("trauma_level") or tags.get("emergency:level")
    trauma_level = int(level) if level and level.isdigit() and 1 <= int(level) <= 3 else (1 if trauma else 0)

    return {
        "id": uid,
        "name": name.strip(),
        "city": tags.get("addr:city") or tags.get("addr:district") or "",
        "state": tags.get("addr:state") or "",
        "address": ", ".join(filter(None, [
            tags.get("addr:housenumber"), tags.get("addr:street"),
            tags.get("addr:city"), tags.get("addr:state"),
        ])),
        "phone": tags.get("phone") or tags.get("contact:phone") or "",
        "website": tags.get("website") or tags.get("contact:website") or "",
        "latitude": float(lat),
        "longitude": float(lon),
        "specialties": specialties,
        "icu_beds_available": 20,       # OSM doesn't track live beds; default
        "trauma_center": trauma,
        "trauma_level": trauma_level,
        "helipad": tags.get("helipad") == "yes",
        "blood_bank": "blood" in tag_str,
        "avg_response_time_min": 10.0,
        "rating": 0.0,                  # Populated from Google Places if key present
        "source": "osm",
        "osm_id": el.get("id"),
    }


def _deduplicate(hospitals: list[dict]) -> list[dict]:
    """Remove duplicates by (name hash + lat/lon rounded to 3dp)."""
    seen: set[str] = set()
    unique: list[dict] = []
    for h in hospitals:
        key = f"{h['name'].lower().replace(' ', '')[:20]}_{round(h['latitude'], 3)}_{round(h['longitude'], 3)}"
        if key not in seen:
            seen.add(key)
            unique.append(h)
    return unique


async def fetch_all_india_hospitals(
    tiles: list[tuple[float, float, float, float]] | None = None,
    max_concurrent: int = 3,
) -> list[dict[str, Any]]:
    """
    Fetch all Indian hospitals from OSM Overpass.
    Uses tiled bounding-box queries with concurrent fetching.

    Args:
        tiles: Optional custom tile list (defaults to INDIA_TILES)
        max_concurrent: Max simultaneous OSM requests (be a good citizen!)

    Returns:
        List of normalised hospital dicts; typically 8,000–15,000 results.
    """
    tiles = tiles or INDIA_TILES
    all_elements: list[dict[str, Any]] = []

    connector = aiohttp.TCPConnector(limit=max_concurrent, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=connector) as session:
        semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_with_semaphore(tile):
            async with semaphore:
                s, w, n, e = tile
                logger.info("Fetching OSM tile: %s,%s → %s,%s", s, w, n, e)
                elements = await _fetch_tile(session, s, w, n, e)
                return elements

        tasks = [fetch_with_semaphore(t) for t in tiles]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in results:
            if isinstance(r, list):
                all_elements.extend(r)
            elif isinstance(r, Exception):
                logger.warning("Tile fetch exception: %s", r)

    # Normalise + deduplicate
    hospitals = []
    for el in all_elements:
        h = _normalise_element(el)
        if h:
            hospitals.append(h)

    hospitals = _deduplicate(hospitals)
    logger.info("OSM fetch complete: %d unique hospitals", len(hospitals))
    return hospitals


async def enrich_with_google_places(
    hospitals: list[dict],
    api_key: str,
    max_enrich: int = 1000,
) -> list[dict]:
    """
    Optionally enrich hospital data with Google Places ratings and phone numbers.
    Only processes hospitals missing ratings (rate-limited to avoid high API costs).
    """
    if not api_key:
        return hospitals

    connector = aiohttp.TCPConnector(limit=5)
    async with aiohttp.ClientSession(connector=connector) as session:
        enriched = 0
        for h in hospitals:
            if enriched >= max_enrich:
                break
            if h.get("rating", 0) > 0:
                continue
            try:
                await asyncio.sleep(0.1)  # ~10 req/s
                url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
                params = {
                    "location": f"{h['latitude']},{h['longitude']}",
                    "radius": 100,
                    "type": "hospital",
                    "keyword": h["name"][:30],
                    "key": api_key,
                }
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    data = await resp.json()
                    results = data.get("results", [])
                    if results:
                        r = results[0]
                        h["rating"] = r.get("rating", 0)
                        h["google_place_id"] = r.get("place_id", "")
                        if r.get("formatted_phone_number") and not h["phone"]:
                            h["phone"] = r.get("formatted_phone_number", "")
                        enriched += 1
            except Exception as exc:
                logger.debug("Google Places enrich failed for %s: %s", h["name"], exc)

    logger.info("Google Places enrichment: %d hospitals updated", enriched)
    return hospitals
