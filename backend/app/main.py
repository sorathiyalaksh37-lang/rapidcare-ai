"""
RapidCare AI — FastAPI Application Entry Point
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db.database import init_db
from app.api import emergency, hospitals, reports, ws

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle events."""
    # Startup
    print("🚀 RapidCare AI starting up...")
    try:
        await init_db()
        print("✅ Database initialized")
        # Seed hospitals if needed
        from app.db.seed_hospitals import seed
        await seed()
    except Exception as e:
        print(f"⚠️  DB init skipped (running without DB): {e}")
    yield
    # Shutdown
    print("🛑 RapidCare AI shutting down.")


app = FastAPI(
    title="RapidCare AI",
    description="AI Emergency Medical Assistant — multi-modal emergency analysis, first aid, and hospital routing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────────────────────
app.include_router(emergency.router)
app.include_router(hospitals.router)
app.include_router(reports.router)
app.include_router(ws.router)


# ── Health Check ─────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "RapidCare AI",
        "version": "1.0.0",
        "ai_mode": settings.ai_mode,
        "environment": settings.environment,
    }


@app.get("/")
async def root():
    return {
        "message": "🚨 RapidCare AI — Emergency Medical Assistant",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "analyze": "POST /api/emergency/analyze",
            "hospitals": "GET /api/hospitals/nearby",
            "report": "POST /api/reports/generate",
            "live": "WS /ws/live/{incident_id}",
        },
    }
