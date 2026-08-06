"""
Hospital Finder API — Enhanced (Phase 1)
=========================================
Endpoints:
  GET /api/hospitals/nearby          — Find hospitals (ML-scored, 10,000+)
  GET /api/hospitals/search          — Search by name/city/specialty
  GET /api/hospitals/cache/status    — Cache stats
  POST /api/hospitals/cache/refresh  — Force OSM refresh
"""
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.db.database import get_db
from app.services.hospital_service import find_nearest_hospitals
from app.services.hospital_cache import get_cache_meta, refresh_hospital_cache, get_cached_hospitals

router = APIRouter(prefix="/api/hospitals", tags=["hospitals"])


@router.get("/nearby")
async def nearby_hospitals(
    latitude: float = Query(..., description="User latitude"),
    longitude: float = Query(..., description="User longitude"),
    specialties: str = Query("trauma", description="Comma-separated required specialties"),
    limit: int = Query(5, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Find nearest hospitals using 7-factor ML scoring.
    Sources: OSM (10,000+) → static fallback (500) → demo.
    Factors: Distance, Specialty, Availability, Traffic, Rating, Trauma Level, Acceptance.
    """
    required = [s.strip() for s in specialties.split(",") if s.strip()]
    hospitals = await find_nearest_hospitals(
        latitude=latitude,
        longitude=longitude,
        required_specialties=required,
        db=db,
        limit=limit,
    )
    return {
        "hospitals": hospitals,
        "count": len(hospitals),
        "query": {
            "latitude": latitude,
            "longitude": longitude,
            "specialties": required,
            "scoring": "7-factor ML (distance 25%, specialty 20%, availability 15%, "
                       "traffic 15%, rating 10%, trauma 10%, acceptance 5%)",
        },
    }


@router.get("/search")
async def search_hospitals(
    q: str = Query(..., min_length=2, description="Search query (name/city/specialty)"),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    limit: int = Query(10, ge=1, le=50),
):
    """Search hospitals by name, city, or specialty keyword."""
    all_hospitals = await get_cached_hospitals()
    q_lower = q.lower()

    matches = [
        h for h in all_hospitals
        if q_lower in (h.get("name") or "").lower()
        or q_lower in (h.get("city") or "").lower()
        or any(q_lower in s for s in (h.get("specialties") or []))
    ]

    # Sort by distance if coords provided
    if latitude is not None and longitude is not None:
        import math
        def dist(h):
            dlat = h["latitude"] - latitude
            dlon = h["longitude"] - longitude
            return math.sqrt(dlat**2 + dlon**2)
        matches.sort(key=dist)

    return {
        "results": matches[:limit],
        "count": len(matches),
        "query": q,
        "total_searched": len(all_hospitals),
    }


@router.get("/cache/status")
async def cache_status():
    """Returns hospital cache statistics."""
    meta = await get_cache_meta()
    return {
        "cache_status": "active",
        "metadata": meta,
        "cache_ttl_hours": 24,
        "source": "OSM Overpass API + 500 pre-verified static hospitals",
    }


@router.post("/cache/refresh")
async def refresh_cache(background_tasks: BackgroundTasks):
    """
    Trigger an OSM hospital cache refresh (runs in background).
    Returns immediately; refresh takes ~2 minutes for all India.
    """
    background_tasks.add_task(refresh_hospital_cache, force=True)
    return {
        "success": True,
        "message": "Hospital cache refresh started in background. "
                   "Check /api/hospitals/cache/status for progress.",
    }
