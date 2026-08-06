"""
RapidCare AI — FastAPI Application Entry Point (Phase 1 Enhanced)
"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db.database import init_db
from app.api import emergency, hospitals, reports, ws, location, availability

settings = get_settings()
logger = logging.getLogger(__name__)

# Background task handles
_bg_tasks: list[asyncio.Task] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle — registers all background services."""
    logger.info("🚀 RapidCare AI starting up (mode=%s)...", settings.ai_mode)

    # ── Database init ────────────────────────────────────────────────────
    try:
        await init_db()
        logger.info("✅ Database initialized")
        from app.db.seed_hospitals import seed
        await seed()
    except Exception as e:
        logger.warning("⚠️  DB init skipped (running without DB): %s", e)

    # ── Hospital cache warm-up (Task 1) ──────────────────────────────────
    try:
        from app.services.hospital_cache import refresh_hospital_cache
        # Non-blocking: start refresh in background, don't wait for it
        _bg_tasks.append(
            asyncio.create_task(
                _background_hospital_refresh(),
                name="hospital_cache_refresh",
            )
        )
        logger.info("✅ Hospital cache refresh task scheduled")
    except Exception as e:
        logger.warning("⚠️  Hospital cache task failed to start: %s", e)

    # ── Availability simulation task (Task 4) ────────────────────────────
    try:
        from app.services.availability_service import simulate_availability_updates
        from app.services.hospital_cache import get_cached_hospitals
        # Pre-load a sample of hospital IDs for simulation
        hospitals_list = await get_cached_hospitals()
        demo_ids = [h["id"] for h in hospitals_list[:200]] if hospitals_list else [
            "demo-1", "demo-2", "demo-3", "demo-4", "demo-5"
        ]
        _bg_tasks.append(
            asyncio.create_task(
                simulate_availability_updates(demo_ids),
                name="availability_simulation",
            )
        )
        logger.info("✅ Availability simulation task started (%d hospitals)", len(demo_ids))
    except Exception as e:
        logger.warning("⚠️  Availability simulation failed to start: %s", e)

    yield

    # ── Cleanup ──────────────────────────────────────────────────────────
    logger.info("🛑 RapidCare AI shutting down.")
    for task in _bg_tasks:
        task.cancel()
    await asyncio.gather(*_bg_tasks, return_exceptions=True)


async def _background_hospital_refresh():
    """
    Periodically refresh hospital cache from OSM every 24 hours.
    First refresh happens immediately on startup (non-blocking check).
    """
    from app.services.hospital_cache import refresh_hospital_cache
    while True:
        try:
            count = await refresh_hospital_cache(force=False)
            logger.info("Hospital cache: %d hospitals available", count)
        except Exception as exc:
            logger.error("Hospital cache refresh error: %s", exc)
        # Wait 24 hours before next refresh
        await asyncio.sleep(24 * 3600)


# ── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="RapidCare AI",
    description=(
        "AI Emergency Medical Assistant — multi-modal emergency analysis, "
        "first aid, ML hospital routing, and real-time availability tracking"
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(emergency.router)
app.include_router(hospitals.router)
app.include_router(availability.router)
app.include_router(location.router)
app.include_router(reports.router)
app.include_router(ws.router)


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    from app.services.hospital_cache import get_cache_meta
    cache_meta = await get_cache_meta()
    return {
        "status": "healthy",
        "service": "RapidCare AI",
        "version": "2.0.0",
        "ai_mode": settings.ai_mode,
        "environment": settings.environment,
        "hospital_cache": cache_meta,
        "features": {
            "osm_hospitals": "active",
            "ml_scoring": "active (7-factor)",
            "location_detection": "active (4-layer)",
            "real_time_availability": "active",
            "traffic_routing": "active" if settings.google_maps_api_key else "fallback (time-of-day model)",
        },
    }


@app.get("/")
async def root():
    return {
        "message": "🚨 RapidCare AI — Emergency Medical Assistant",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "analyze": "POST /api/emergency/analyze",
            "hospitals_nearby": "GET /api/hospitals/nearby",
            "hospitals_search": "GET /api/hospitals/search",
            "hospitals_cache": "GET /api/hospitals/cache/status",
            "location_detect": "POST /api/location/detect",
            "location_geocode": "POST /api/location/geocode",
            "availability": "GET /api/hospitals/{id}/availability",
            "report": "POST /api/reports/generate",
            "live_ambulance": "WS /ws/live/{incident_id}",
            "live_availability": "WS /ws/hospitals/availability",
            "ws_stats": "GET /ws/stats",
        },
    }
