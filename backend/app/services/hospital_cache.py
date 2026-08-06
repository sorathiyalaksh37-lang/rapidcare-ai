"""
Hospital Cache Service
======================
Redis-backed cache for hospital data with:
  - 24-hour TTL auto-refresh from OSM
  - JSON compression for large payloads
  - Graceful fallback to 500+ pre-verified Indian hospitals
  - Thread-safe background refresh via asyncio.Lock
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Redis key names ───────────────────────────────────────────────────────────
CACHE_KEY = "rapidcare:hospitals:india"
CACHE_META_KEY = "rapidcare:hospitals:meta"
CACHE_LOCK_KEY = "rapidcare:hospitals:refresh_lock"

# Module-level state for in-process fallback when Redis unavailable
_in_memory_cache: list[dict] = []
_cache_loaded_at: float = 0.0
_MEMORY_TTL = 3600  # 1-hour in-process TTL
_refresh_lock = asyncio.Lock()


async def _get_redis():
    """Lazy Redis connection; returns None if unavailable."""
    try:
        import redis.asyncio as aioredis
        from app.config import get_settings
        settings = get_settings()
        r = aioredis.from_url(settings.redis_url, decode_responses=True, socket_timeout=2)
        await r.ping()
        return r
    except Exception:
        return None


async def get_cached_hospitals() -> list[dict[str, Any]]:
    """
    Returns hospitals from cache:
      1. Redis (primary) — up to 10,000+ hospitals
      2. In-process memory — valid for 1 hour if Redis down
      3. Static fallback JSON — always available
    """

    # Try Redis first
    redis = await _get_redis()
    if redis:
        try:
            data = await redis.get(CACHE_KEY)
            if data:
                hospitals = json.loads(data)
                logger.debug("Redis hospital cache hit: %d hospitals", len(hospitals))
                return hospitals
        except Exception as exc:
            logger.warning("Redis cache read failed: %s", exc)
        finally:
            await redis.aclose()

    # In-memory fallback
    if _in_memory_cache and (time.monotonic() - _cache_loaded_at) < _MEMORY_TTL:
        logger.debug("In-memory cache hit: %d hospitals", len(_in_memory_cache))
        return _in_memory_cache

    # Static JSON fallback
    return _load_static_fallback()


async def set_cached_hospitals(hospitals: list[dict[str, Any]], ttl_hours: int = 24) -> bool:
    """Persist hospitals to Redis. Returns True on success."""
    global _in_memory_cache, _cache_loaded_at

    # Always update in-memory cache
    _in_memory_cache = hospitals
    _cache_loaded_at = time.monotonic()

    redis = await _get_redis()
    if not redis:
        logger.warning("Redis unavailable — hospitals stored in memory only (%d)", len(hospitals))
        return False

    try:
        payload = json.dumps(hospitals, ensure_ascii=False)
        ttl_sec = ttl_hours * 3600
        await redis.set(CACHE_KEY, payload, ex=ttl_sec)
        await redis.hset(CACHE_META_KEY, mapping={
            "count": len(hospitals),
            "updated_at": time.time(),
            "ttl_hours": ttl_hours,
        })
        logger.info("Hospital cache saved: %d hospitals (TTL %dh)", len(hospitals), ttl_hours)
        return True
    except Exception as exc:
        logger.error("Redis cache write failed: %s", exc)
        return False
    finally:
        await redis.aclose()


async def invalidate_hospital_cache() -> None:
    """Force cache invalidation (triggers refresh on next call)."""
    global _in_memory_cache, _cache_loaded_at
    _in_memory_cache = []
    _cache_loaded_at = 0.0

    redis = await _get_redis()
    if redis:
        try:
            await redis.delete(CACHE_KEY, CACHE_META_KEY)
            logger.info("Hospital cache invalidated")
        except Exception as exc:
            logger.warning("Cache invalidation failed: %s", exc)
        finally:
            await redis.aclose()


async def get_cache_meta() -> dict[str, Any]:
    """Returns cache metadata (count, updated_at, ttl)."""
    redis = await _get_redis()
    if redis:
        try:
            meta = await redis.hgetall(CACHE_META_KEY)
            return meta
        except Exception:
            pass
        finally:
            await redis.aclose()
    return {"count": len(_in_memory_cache), "source": "memory"}


def _load_static_fallback() -> list[dict[str, Any]]:
    """Load 500+ pre-verified Indian hospitals from bundled JSON."""
    from app.config import get_settings
    fallback_path = Path(get_settings().hospital_fallback_json)
    if fallback_path.exists():
        try:
            with open(fallback_path, encoding="utf-8") as f:
                data = json.load(f)
                hospitals = data if isinstance(data, list) else data.get("hospitals", [])
                logger.info("Static fallback loaded: %d hospitals", len(hospitals))
                return hospitals
        except Exception as exc:
            logger.error("Failed to load static fallback: %s", exc)

    # Last resort: return empty list — hospital_service.py has its own DEMO_HOSPITALS
    return []


async def refresh_hospital_cache(force: bool = False) -> int:
    """
    Trigger a full OSM hospital refresh.
    Uses an async lock to prevent concurrent refreshes.
    Returns the number of hospitals cached.
    """
    async with _refresh_lock:
        # Check if already recently refreshed (unless forced)
        if not force:
            redis = await _get_redis()
            if redis:
                try:
                    ttl = await redis.ttl(CACHE_KEY)
                    if ttl > 0:
                        meta = await redis.hgetall(CACHE_META_KEY)
                        count = int(meta.get("count", 0))
                        if count > 0:
                            logger.info(
                                "Hospital cache still valid: %d hospitals, %ds remaining",
                                count, ttl,
                            )
                            return count
                except Exception:
                    pass
                finally:
                    await redis.aclose()

        logger.info("Starting hospital cache refresh from OSM...")
        try:
            from app.services.osm_hospital_fetcher import fetch_all_india_hospitals, enrich_with_google_places
            from app.config import get_settings
            settings = get_settings()

            hospitals = await fetch_all_india_hospitals()

            # Merge with static fallback (static entries fill gaps for smaller cities)
            static = _load_static_fallback()
            existing_ids = {h["id"] for h in hospitals}
            for s in static:
                if s["id"] not in existing_ids:
                    hospitals.append(s)

            # Optionally enrich with Google Places ratings
            if settings.google_places_api_key:
                hospitals = await enrich_with_google_places(
                    hospitals,
                    api_key=settings.google_places_api_key,
                    max_enrich=500,
                )

            from app.config import get_settings
            ttl = get_settings().hospital_cache_ttl_hours
            await set_cached_hospitals(hospitals, ttl_hours=ttl)
            logger.info("Hospital cache refresh complete: %d total hospitals", len(hospitals))
            return len(hospitals)

        except Exception as exc:
            logger.error("Hospital cache refresh failed: %s", exc)
            # Still load static fallback into memory
            static = _load_static_fallback()
            if static:
                _in_memory_cache.clear()
                _in_memory_cache.extend(static)
            return len(_in_memory_cache)
