"""
Hospital finder API routes.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.services.hospital_service import find_nearest_hospitals

router = APIRouter(prefix="/api/hospitals", tags=["hospitals"])


@router.get("/nearby")
async def nearby_hospitals(
    latitude: float = Query(..., description="User latitude"),
    longitude: float = Query(..., description="User longitude"),
    specialties: str = Query("trauma", description="Comma-separated required specialties"),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Find nearest hospitals with required specialties."""
    required = [s.strip() for s in specialties.split(",") if s.strip()]
    hospitals = await find_nearest_hospitals(
        latitude=latitude,
        longitude=longitude,
        required_specialties=required,
        db=db,
        limit=limit,
    )
    return {"hospitals": hospitals, "count": len(hospitals)}
