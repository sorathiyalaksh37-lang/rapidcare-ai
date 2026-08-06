"""
Location Service — Task 2 (4-Layer Detection)
=============================================
Priority layers:
  1. Browser GPS     (passed from frontend) — ±10m accuracy
  2. Google WiFi API (from request context)  — ±50m
  3. IP Geolocation  (ip-api.com + ipinfo fallback) — ±5km
  4. Address geocode (GeoPy + Nominatim)     — ±100m

All results cached in Redis for 5 minutes per IP.
India bounds validation: 8°N–37°N, 68°E–97°E.
Performance target: < 2s.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

import aiohttp
from geopy.geocoders import Nominatim
from geopy.adapters import AioHTTPAdapter

logger = logging.getLogger(__name__)

# India geographic bounds
INDIA_BOUNDS = {"min_lat": 8.0, "max_lat": 37.0, "min_lon": 68.0, "max_lon": 97.0}

_LOC_CACHE: dict[str, tuple[float, dict]] = {}  # ip → (timestamp, location)
_CACHE_TTL = 300  # 5 minutes


def _in_india(lat: float, lon: float) -> bool:
    return (INDIA_BOUNDS["min_lat"] <= lat <= INDIA_BOUNDS["max_lat"] and
            INDIA_BOUNDS["min_lon"] <= lon <= INDIA_BOUNDS["max_lon"])


async def _redis_get_loc(key: str) -> dict | None:
    try:
        import redis.asyncio as aioredis
        from app.config import get_settings
        r = aioredis.from_url(get_settings().redis_url, decode_responses=True, socket_timeout=1)
        val = await r.get(f"rapidcare:loc:{key}")
        await r.aclose()
        return json.loads(val) if val else None
    except Exception:
        return None


async def _redis_set_loc(key: str, location: dict) -> None:
    try:
        import redis.asyncio as aioredis
        from app.config import get_settings
        r = aioredis.from_url(get_settings().redis_url, decode_responses=True, socket_timeout=1)
        await r.set(f"rapidcare:loc:{key}", json.dumps(location), ex=_CACHE_TTL)
        await r.aclose()
    except Exception:
        pass


async def detect_location(
    client_ip: str | None = None,
    gps_lat: float | None = None,
    gps_lon: float | None = None,
    address: str | None = None,
) -> dict[str, Any]:
    """
    4-layer location detection. Returns a location dict with:
      latitude, longitude, city, state, accuracy_m, layer, source
    """
    # Layer 1: Browser GPS (highest accuracy)
    if gps_lat is not None and gps_lon is not None:
        loc = await _layer1_gps(gps_lat, gps_lon)
        if loc:
            return loc

    # Layer 4: Address geocoding (if address provided, try before IP)
    if address:
        loc = await _layer4_address(address)
        if loc:
            return loc

    # Check cache (IP-based layers 2 & 3)
    cache_key = (client_ip or "unknown").replace(".", "-")
    if cache_key in _LOC_CACHE:
        ts, cached = _LOC_CACHE[cache_key]
        if time.monotonic() - ts < _CACHE_TTL:
            return cached

    redis_cached = await _redis_get_loc(cache_key)
    if redis_cached:
        return redis_cached

    # Layer 2: Google Geolocation API
    from app.config import get_settings
    geo_key = get_settings().google_geolocation_api_key
    if geo_key:
        loc = await _layer2_google_wifi(geo_key)
        if loc:
            await _cache_location(cache_key, loc)
            return loc

    # Layer 3: IP Geolocation
    if client_ip:
        loc = await _layer3_ip_geolocation(client_ip)
        if loc:
            await _cache_location(cache_key, loc)
            return loc

    # Default: Mumbai (most populous city)
    return {
        "latitude": 19.0760,
        "longitude": 72.8777,
        "city": "Mumbai",
        "state": "Maharashtra",
        "country": "India",
        "accuracy_m": 50000,
        "layer": 0,
        "source": "default",
    }


async def _layer1_gps(lat: float, lon: float) -> dict | None:
    """Layer 1: Accept browser GPS coords and reverse geocode."""
    if not _in_india(lat, lon):
        logger.debug("GPS coords outside India: %s, %s", lat, lon)
        # Still return even if outside India (international support)

    city, state = await _reverse_geocode(lat, lon)
    return {
        "latitude": lat,
        "longitude": lon,
        "city": city,
        "state": state,
        "country": "India",
        "accuracy_m": 10,
        "layer": 1,
        "source": "browser_gps",
    }


async def _layer2_google_wifi(api_key: str) -> dict | None:
    """Layer 2: Google Geolocation API (WiFi/cellular towers)."""
    url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={api_key}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json={"considerIp": True},
                timeout=aiohttp.ClientTimeout(total=3),
            ) as resp:
                data = await resp.json()
        loc = data.get("location", {})
        lat, lon = loc.get("lat"), loc.get("lng")
        if lat is not None and lon is not None:
            city, state = await _reverse_geocode(lat, lon)
            return {
                "latitude": lat, "longitude": lon,
                "city": city, "state": state, "country": "India",
                "accuracy_m": int(data.get("accuracy", 50)),
                "layer": 2, "source": "google_geolocation",
            }
    except Exception as exc:
        logger.debug("Google Geolocation failed: %s", exc)
    return None


async def _layer3_ip_geolocation(ip: str) -> dict | None:
    """Layer 3: IP-based geolocation (ip-api.com → ipinfo.io fallback)."""
    from app.config import get_settings
    settings = get_settings()

    # Primary: ip-api.com (free, 45 req/min)
    try:
        async with aiohttp.ClientSession() as session:
            url = f"http://ip-api.com/json/{ip}?fields=status,lat,lon,city,regionName,country,countryCode"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=3)) as resp:
                data = await resp.json()
        if data.get("status") == "success":
            lat, lon = data.get("lat"), data.get("lon")
            if lat is not None and lon is not None:
                return {
                    "latitude": lat, "longitude": lon,
                    "city": data.get("city", ""),
                    "state": data.get("regionName", ""),
                    "country": data.get("country", "India"),
                    "accuracy_m": 5000,
                    "layer": 3, "source": "ip_api",
                }
    except Exception:
        pass

    # Fallback: ipinfo.io
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://ipinfo.io/{ip}/json",
                timeout=aiohttp.ClientTimeout(total=3),
            ) as resp:
                data = await resp.json()
        loc_str = data.get("loc", "")
        if loc_str and "," in loc_str:
            lat_s, lon_s = loc_str.split(",")
            return {
                "latitude": float(lat_s), "longitude": float(lon_s),
                "city": data.get("city", ""),
                "state": data.get("region", ""),
                "country": data.get("country", "IN"),
                "accuracy_m": 10000,
                "layer": 3, "source": "ipinfo",
            }
    except Exception as exc:
        logger.debug("ipinfo fallback failed: %s", exc)
    return None


async def _layer4_address(address: str) -> dict | None:
    """Layer 4: Geocode a text address via Nominatim."""
    try:
        async with Nominatim(
            user_agent="rapidcare-ai",
            adapter_factory=AioHTTPAdapter,
            timeout=5,
        ) as geolocator:
            location = await geolocator.geocode(
                f"{address}, India",
                country_codes="IN",
                exactly_one=True,
            )
            if location:
                lat, lon = location.latitude, location.longitude
                raw = location.raw.get("address", {})
                return {
                    "latitude": lat, "longitude": lon,
                    "city": raw.get("city") or raw.get("town") or raw.get("village", ""),
                    "state": raw.get("state", ""),
                    "country": "India",
                    "accuracy_m": 100,
                    "formatted_address": location.address,
                    "layer": 4, "source": "nominatim",
                }
    except Exception as exc:
        logger.debug("Nominatim geocode failed: %s", exc)
    return None


async def _reverse_geocode(lat: float, lon: float) -> tuple[str, str]:
    """Reverse geocode coordinates to (city, state)."""
    try:
        async with Nominatim(
            user_agent="rapidcare-ai",
            adapter_factory=AioHTTPAdapter,
            timeout=3,
        ) as geolocator:
            location = await geolocator.reverse(f"{lat}, {lon}", language="en")
            if location:
                raw = location.raw.get("address", {})
                city = (raw.get("city") or raw.get("town") or
                        raw.get("village") or raw.get("county") or "")
                state = raw.get("state", "")
                return city, state
    except Exception:
        pass
    return "", ""


async def _cache_location(key: str, loc: dict) -> None:
    _LOC_CACHE[key] = (time.monotonic(), loc)
    await _redis_set_loc(key, loc)


async def geocode_address(address: str) -> dict | None:
    """Public API: geocode an address string → lat/lon."""
    return await _layer4_address(address)
