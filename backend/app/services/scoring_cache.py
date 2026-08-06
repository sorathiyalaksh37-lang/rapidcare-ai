"""
Hospital Scoring Cache
======================
Redis cache for ML hospital recommendation scores.
TTL: 5 minutes (matches Task 3 requirements).
Key: rapidcare:scores:{lat_3dp}:{lon_3dp}:{specialties_hash}
"""
from __future__ import annotations

import hashlib
import json
import logging
import time

logger = logging.getLogger(__name__)

SCORE_KEY_PREFIX = "rapidcare:scores"
_in_memory_scores: dict[str, tuple[float, list]] = {}  # key -> (timestamp, scores)
_MEMORY_TTL = 300  # 5 minutes


def _score_key(lat: float, lon: float, specialties: list[str]) -> str:
    spec_str = ",".join(sorted(specialties))
    spec_hash = hashlib.md5(spec_str.encode()).hexdigest()[:8]
    return f"{SCORE_KEY_PREFIX}:{round(lat, 3)}:{round(lon, 3)}:{spec_hash}"


async def get_cached_scores(
    lat: float, lon: float, specialties: list[str]
) -> list[dict] | None:
    """Returns cached scored hospital list or None if cache miss."""
    key = _score_key(lat, lon, specialties)

    # In-memory check
    if key in _in_memory_scores:
        ts, scores = _in_memory_scores[key]
        if time.monotonic() - ts < _MEMORY_TTL:
            logger.debug("Score cache hit (memory): %s", key)
            return scores
        del _in_memory_scores[key]

    # Redis check
    try:
        import redis.asyncio as aioredis
        from app.config import get_settings
        r = aioredis.from_url(get_settings().redis_url, decode_responses=True, socket_timeout=1)
        data = await r.get(key)
        await r.aclose()
        if data:
            return json.loads(data)
    except Exception:
        pass
    return None


async def set_cached_scores(
    lat: float, lon: float, specialties: list[str], scores: list[dict]
) -> None:
    """Cache scored hospital list for 5 minutes."""
    key = _score_key(lat, lon, specialties)
    _in_memory_scores[key] = (time.monotonic(), scores)

    try:
        import redis.asyncio as aioredis
        from app.config import get_settings
        r = aioredis.from_url(get_settings().redis_url, decode_responses=True, socket_timeout=1)
        await r.set(key, json.dumps(scores), ex=_MEMORY_TTL)
        await r.aclose()
    except Exception:
        pass
