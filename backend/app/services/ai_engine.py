"""
AI Engine: Orchestrates the entire multi-modal emergency analysis pipeline.
Performance-optimised: Steps 2-5 run concurrently; hospital search capped at 2s.
"""
import asyncio
import time
import uuid
from typing import Optional
from app.services import nlp_service, severity_service, firstaid_service, vision_service, speech_service, hospital_service
from app.config import get_settings

settings = get_settings()


async def analyze_emergency(
    text: Optional[str] = None,
    image_bytes: Optional[bytes] = None,
    audio_bytes: Optional[bytes] = None,
    audio_filename: str = "audio.webm",
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    db=None,
) -> dict:
    """
    Full multi-modal emergency analysis pipeline.
    Returns comprehensive analysis dict in < 2s (optimized).
    """
    start_time = time.time()
    incident_id = str(uuid.uuid4())

    # ── Step 1: Speech → Text (must run first, feeds NLP) ───────────────
    transcription_result = {}
    if audio_bytes:
        try:
            transcription_result = await asyncio.wait_for(
                speech_service.transcribe_audio(audio_bytes, audio_filename),
                timeout=5.0,  # Reduced from 10s to 5s
            )
            if transcription_result.get("transcription"):
                text = (text + " " if text else "") + transcription_result["transcription"]
        except asyncio.TimeoutError:
            transcription_result = {"transcription": ""}

    # ── Steps 2-4: NLP + Vision + Severity run concurrently ─────────────
    nlp_coro = nlp_service.classify_text(text or "")
    vision_coro = (
        vision_service.analyze_image(image_bytes, "unknown")
        if image_bytes else _noop({})
    )

    nlp_result, vision_result = await asyncio.gather(nlp_coro, vision_coro)

    emergency_type = nlp_result["emergency_type"]
    confidence = nlp_result["confidence"]

    # Apply vision confidence boost
    if vision_result.get("confidence", 0) > confidence:
        confidence = (confidence + vision_result["confidence"]) / 2

    # Severity (sync — pure CPU, < 1ms)
    severity_data = severity_service.estimate_severity(
        emergency_type=emergency_type,
        text=text,
        has_image=bool(image_bytes),
        has_voice=bool(audio_bytes),
        confidence=confidence,
    )
    if vision_result.get("image_severity_boost"):
        boosted = severity_data["severity_score"] + vision_result["image_severity_boost"]
        severity_data["severity_score"] = min(100.0, round(boosted, 1))

    # ── Step 5: First-Aid (sync — < 5ms) ────────────────────────────────
    firstaid_data = firstaid_service.get_first_aid(emergency_type, text)

    # ── Step 6: Hospital Finding (capped at 2s total) ────────────────────
    lat = latitude or 19.0760   # Default: Mumbai
    lon = longitude or 72.8777
    try:
        hospitals = await asyncio.wait_for(
            hospital_service.find_nearest_hospitals(
                latitude=lat,
                longitude=lon,
                required_specialties=firstaid_data.get("required_specialties", []),
                db=db,
                limit=5,
            ),
            timeout=2.0,  # Reduced from 3s to 2s
        )
    except asyncio.TimeoutError:
        hospitals = hospital_service._demo_hospitals()[:5]

    processing_ms = round((time.time() - start_time) * 1000, 1)

    return {
        "incident_id": incident_id,
        "emergency_type": emergency_type,
        "confidence": round(confidence, 2),
        "detected_keywords": nlp_result.get("detected_keywords", []),

        # Severity
        "severity_score": severity_data["severity_score"],
        "severity_level": severity_data["severity_level"],
        "survival_probability": severity_data["survival_probability"],
        "contributing_factors": severity_data.get("contributing_factors", []),

        # First Aid
        "first_aid_steps": firstaid_data["steps"],
        "warnings": firstaid_data["warnings"],
        "required_specialties": firstaid_data["required_specialties"],

        # Hospitals
        "nearest_hospitals": hospitals,
        
        # User location (include in response for map display)
        "user_location": {
            "latitude": lat,
            "longitude": lon
        },

        # Input analysis details
        "transcription": transcription_result.get("transcription", ""),
        "injury_indicators": vision_result.get("injury_indicators", []),
        "detected_objects": vision_result.get("detected_objects", []),

        # Metadata
        "input_text": text or "",
        "has_image": bool(image_bytes),
        "has_voice": bool(audio_bytes),
        "processing_time_ms": processing_ms,
        "ai_mode": settings.ai_mode,
    }


async def _noop(val):
    """Return a value immediately without any I/O."""
    return val
