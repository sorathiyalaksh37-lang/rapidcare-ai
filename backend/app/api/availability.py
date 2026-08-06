"""
Real-Time Availability API — Task 4
=====================================
Endpoints:
  GET  /api/hospitals/{hospital_id}/availability    — single hospital
  POST /api/hospitals/{hospital_id}/availability    — update (for hospital systems)
  GET  /api/hospitals/availability/summary          — aggregated stats
  WS   /ws/hospitals/availability                   — live broadcast (in ws.py)
"""
from fastapi import APIRouter, Path, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.availability_service import (
    get_hospital_availability,
    update_hospital_availability,
    get_availability_summary,
)

router = APIRouter(prefix="/api/hospitals", tags=["availability"])


class AvailabilityUpdate(BaseModel):
    icu_beds_available: Optional[int] = None
    icu_beds_total: Optional[int] = None
    er_beds_available: Optional[int] = None
    er_wait_time_min: Optional[int] = None
    general_beds_available: Optional[int] = None
    physicians_on_duty: Optional[int] = None
    nurses_on_duty: Optional[int] = None
    ventilators_available: Optional[int] = None
    operating_rooms_available: Optional[int] = None
    mri_available: Optional[bool] = None
    ct_scan_available: Optional[bool] = None
    is_accepting_patients: Optional[bool] = None
    trauma_team_ready: Optional[bool] = None


@router.get("/{hospital_id}/availability")
async def hospital_availability(hospital_id: str = Path(..., description="Hospital ID")):
    """Get real-time availability for a specific hospital."""
    data = await get_hospital_availability(hospital_id)
    return {"hospital_id": hospital_id, "availability": data}


@router.post("/{hospital_id}/availability")
async def update_availability(
    body: AvailabilityUpdate,
    hospital_id: str = Path(..., description="Hospital ID"),
):
    """
    Update hospital availability (called by hospital management systems).
    Pushes data to Redis; broadcast to WebSocket clients happens automatically.
    """
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    success = await update_hospital_availability(hospital_id, update_data)
    return {"success": success, "hospital_id": hospital_id, "fields_updated": list(update_data.keys())}


@router.get("/availability/summary")
async def availability_summary():
    """Aggregated availability statistics across all tracked hospitals."""
    return await get_availability_summary()
