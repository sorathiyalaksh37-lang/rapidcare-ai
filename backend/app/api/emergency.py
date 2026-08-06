"""
Emergency Analysis API routes.
"""
from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.ai_engine import analyze_emergency
from app.services.report_service import generate_report
from app.models.incident import Incident

router = APIRouter(prefix="/api/emergency", tags=["emergency"])


@router.post("/analyze")
async def analyze(
    background_tasks: BackgroundTasks,
    text: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Multi-modal emergency analysis endpoint.
    Accepts text, image, and/or audio. Returns full AI analysis.
    """
    # Read file bytes
    image_bytes = await image.read() if image else None
    audio_bytes = await audio.read() if audio else None
    audio_filename = audio.filename if audio else "audio.webm"

    if not any([text, image_bytes, audio_bytes]):
        raise HTTPException(status_code=400, detail="At least one input (text, image, or audio) is required.")

    # Run full AI analysis
    result = await analyze_emergency(
        text=text,
        image_bytes=image_bytes,
        audio_bytes=audio_bytes,
        audio_filename=audio_filename,
        latitude=latitude,
        longitude=longitude,
        db=db,
    )

    # Generate report
    incident_data = dict(result)
    incident_data["hospitals"] = result.get("nearest_hospitals", [])
    incident_data["severity_data"] = {
        "severity_score": result["severity_score"],
        "severity_level": result["severity_level"],
        "survival_probability": result["survival_probability"],
        "contributing_factors": result["contributing_factors"],
    }
    incident_data["firstaid_data"] = {
        "steps": result["first_aid_steps"],
        "warnings": result["warnings"],
        "required_specialties": result["required_specialties"],
    }
    report = generate_report(incident_data)
    result["report"] = report

    # Save incident to DB in background
    background_tasks.add_task(_save_incident, db, result)

    return JSONResponse(content=result)


@router.get("/incidents")
async def list_incidents(db: AsyncSession = Depends(get_db)):
    """List recent incidents."""
    from sqlalchemy import select
    result = await db.execute(
        select(Incident).order_by(Incident.created_at.desc()).limit(20)
    )
    incidents = result.scalars().all()
    return [
        {
            "id": inc.id,
            "emergency_type": inc.emergency_type,
            "severity_level": inc.severity_level,
            "severity_score": inc.severity_score,
            "created_at": inc.created_at.isoformat() if inc.created_at else None,
            "status": inc.status,
        }
        for inc in incidents
    ]


async def _save_incident(db: AsyncSession, result: dict):
    """Background task: persist incident to database."""
    try:
        incident = Incident(
            id=result["incident_id"],
            input_text=result.get("input_text", ""),
            emergency_type=result["emergency_type"],
            severity_score=result["severity_score"],
            severity_level=result["severity_level"],
            survival_probability=result["survival_probability"],
            confidence_score=result["confidence"],
            first_aid_steps=result["first_aid_steps"],
            warnings=result["warnings"],
            ai_report=result.get("report"),
        )
        db.add(incident)
        await db.commit()
    except Exception as e:
        print(f"[DB] Failed to save incident: {e}")
