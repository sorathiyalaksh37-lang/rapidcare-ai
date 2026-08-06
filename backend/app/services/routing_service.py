"""
Routing Service — Task 5
========================
Traffic-aware ambulance ETA using Google Distance Matrix API with
intelligent fallbacks for when the API key is not available.

Performance target: < 100ms via Redis cache-first strategy.
Cache TTL: 10 minutes per route pair.

Fallback tiers:
  1. Google Distance Matrix API (requires GOOGLE_MAPS_API_KEY)
  2. Time-of-day speed model (peak/off-peak/night)
  3. Straight-line Haversine at 40 km/h
"""
from __future__ import annotations

import asyncio
import logging
import math
import time as time_module
from datetime import datetime, timezone

import aiohttp

logger = logging.getLogger(__name__)

# ── Route cache ───────────────────────────────────────────────────────────────
_ROUTE_CACHE: dict[str, tuple[float, float]] = {}  # key → (timestamp, eta_minutes)
_CACHE_TTL = 600  # 10 minutes

# ── Speed model (km/h) by time-of-day ────────────────────────────────────────
def _speed_kmh() -> float:
    """Return estimated urban speed based on current hour (IST)."""
    now_ist = datetime.now(timezone.utc).hour + 5  # rough IST offset
    hour = now_ist % 24
    if 7 <= hour <= 10 or 17 <= hour <= 20:   # peak hours
        return 15.0
    if 0 <= hour <= 5:                          # night
        return 55.0
    return 35.0  # off-peak daytime


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def _cache_key(orig_lat: float, orig_lon: float, dest_lat: float, dest_lon: float) -> str:
    return f"{round(orig_lat,3)},{round(orig_lon,3)}|{round(dest_lat,3)},{round(dest_lon,3)}"


async def _redis_get(key: str) -> float | None:
    try:
        import redis.asyncio as aioredis
        from app.config import get_settings
        r = aioredis.from_url(get_settings().redis_url, decode_responses=True, socket_timeout=1)
        val = await r.get(f"rapidcare:route:{key}")
        await r.aclose()
        return float(val) if val else None
    except Exception:
        return None


async def _redis_set(key: str, eta_min: float) -> None:
    try:
        import redis.asyncio as aioredis
        from app.config import get_settings
        r = aioredis.from_url(get_settings().redis_url, decode_responses=True, socket_timeout=1)
        await r.set(f"rapidcare:route:{key}", str(eta_min), ex=_CACHE_TTL)
        await r.aclose()
    except Exception:
        pass


async def get_eta(
    orig_lat: float, orig_lon: float,
    dest_lat: float, dest_lon: float,
    dest_id: str = "",
) -> float:
    """
    Get ETA in minutes from origin to destination.
    Returns cached value if available (< 100ms).
    """
    key = _cache_key(orig_lat, orig_lon, dest_lat, dest_lon)

    # 1. In-process cache (< 1ms)
    if key in _ROUTE_CACHE:
        ts, eta = _ROUTE_CACHE[key]
        if time_module.monotonic() - ts < _CACHE_TTL:
            return eta

    # 2. Redis cache (< 5ms)
    cached = await _redis_get(key)
    if cached is not None:
        _ROUTE_CACHE[key] = (time_module.monotonic(), cached)
        return cached

    # 3. Google Distance Matrix API
    from app.config import get_settings
    api_key = get_settings().google_maps_api_key
    if api_key:
        eta = await _google_eta(orig_lat, orig_lon, dest_lat, dest_lon, api_key)
        if eta is not None:
            _ROUTE_CACHE[key] = (time_module.monotonic(), eta)
            await _redis_set(key, eta)
            return eta

    # 4. Fallback: time-of-day speed model
    dist_km = _haversine_km(orig_lat, orig_lon, dest_lat, dest_lon)
    speed = _speed_kmh()
    eta = max((dist_km / speed) * 60.0, 2.0)
    _ROUTE_CACHE[key] = (time_module.monotonic(), eta)
    await _redis_set(key, eta)
    return round(eta, 1)


async def _google_eta(
    orig_lat: float, orig_lon: float,
    dest_lat: float, dest_lon: float,
    api_key: str,
) -> float | None:
    """Call Google Distance Matrix API with traffic_model=best_guess."""
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": f"{orig_lat},{orig_lon}",
        "destinations": f"{dest_lat},{dest_lon}",
        "mode": "driving",
        "departure_time": "now",
        "traffic_model": "best_guess",
        "units": "metric",
        "key": api_key,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                data = await resp.json()
        row = data.get("rows", [{}])[0]
        element = row.get("elements", [{}])[0]
        if element.get("status") == "OK":
            duration_in_traffic = element.get("duration_in_traffic") or element.get("duration")
            if duration_in_traffic:
                eta_min = duration_in_traffic["value"] / 60.0
                logger.debug("Google ETA: %.1f min", eta_min)
                return round(eta_min, 1)
    except Exception as exc:
        logger.debug("Google Distance Matrix failed: %s", exc)
    return None


async def get_bulk_etas(
    orig_lat: float,
    orig_lon: float,
    hospitals: list[dict],
    max_concurrent: int = 5,
) -> dict[str, float]:
    """
    Fetch ETAs for multiple hospitals concurrently.
    Uses batched Google Distance Matrix (up to 25 destinations per call)
    or individual fallback calls.

    Returns: dict of hospital_id → eta_minutes
    """
    if not hospitals:
        return {}

    from app.config import get_settings
    api_key = get_settings().google_maps_api_key

    # Try batched Google call first (most efficient)
    if api_key:
        result = await _google_batch_etas(orig_lat, orig_lon, hospitals, api_key)
        if result:
            return result

    # Fallback: concurrent individual ETA calls
    sem = asyncio.Semaphore(max_concurrent)

    async def _single(h: dict) -> tuple[str, float]:
        async with sem:
            eta = await get_eta(orig_lat, orig_lon, h["latitude"], h["longitude"], h.get("id", ""))
            return h.get("id", ""), eta

    tasks = [_single(h) for h in hospitals]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    etas: dict[str, float] = {}
    for r in results:
        if isinstance(r, tuple):
            hid, eta = r
            etas[hid] = eta
    return etas


async def _google_batch_etas(
    orig_lat: float, orig_lon: float,
    hospitals: list[dict],
    api_key: str,
) -> dict[str, float]:
    """Use batched Distance Matrix call (up to 25 destinations)."""
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    batch = hospitals[:25]  # API limit
    destinations = "|".join(f"{h['latitude']},{h['longitude']}" for h in batch)
    params = {
        "origins": f"{orig_lat},{orig_lon}",
        "destinations": destinations,
        "mode": "driving",
        "departure_time": "now",
        "traffic_model": "best_guess",
        "units": "metric",
        "key": api_key,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                data = await resp.json()

        results: dict[str, float] = {}
        elements = (data.get("rows", [{}])[0]).get("elements", [])
        for i, el in enumerate(elements):
            if i >= len(batch):
                break
            h = batch[i]
            hid = h.get("id", "")
            if el.get("status") == "OK":
                dur = el.get("duration_in_traffic") or el.get("duration")
                if dur:
                    eta = round(dur["value"] / 60.0, 1)
                    results[hid] = eta
                    key = _cache_key(orig_lat, orig_lon, h["latitude"], h["longitude"])
                    _ROUTE_CACHE[key] = (time_module.monotonic(), eta)
        logger.info("Batch Google ETA: %d/%d hospitals", len(results), len(batch))
        return results
    except Exception as exc:
        logger.debug("Batch Distance Matrix failed: %s", exc)
        return {}
