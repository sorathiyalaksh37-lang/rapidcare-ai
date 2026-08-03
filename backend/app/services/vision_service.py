"""
Vision Service: Analyzes uploaded images using YOLOv8 in full mode,
or returns mock analysis in demo mode.
"""
import os
import base64
from pathlib import Path
from app.config import get_settings

settings = get_settings()

MOCK_INJURY_DETECTIONS = {
    "road_accident": {
        "detected_objects": ["person (lying)", "blood_pool", "damaged_vehicle"],
        "injury_indicators": ["Visible bleeding", "Unconscious posture detected", "Head position suggests trauma"],
        "confidence": 0.87,
        "image_severity_boost": 15,
    },
    "fracture": {
        "detected_objects": ["person", "deformed_limb"],
        "injury_indicators": ["Limb deformity detected", "Abnormal joint angle"],
        "confidence": 0.79,
        "image_severity_boost": 8,
    },
    "burn": {
        "detected_objects": ["person", "burn_marks"],
        "injury_indicators": ["Skin discoloration detected", "Burn pattern identified"],
        "confidence": 0.82,
        "image_severity_boost": 10,
    },
    "bleeding": {
        "detected_objects": ["person", "blood"],
        "injury_indicators": ["Active bleeding detected", "Blood stain pattern identified"],
        "confidence": 0.91,
        "image_severity_boost": 12,
    },
    "head_injury": {
        "detected_objects": ["person", "head_wound"],
        "injury_indicators": ["Head wound visible", "Unconscious posture"],
        "confidence": 0.84,
        "image_severity_boost": 14,
    },
}

DEFAULT_MOCK = {
    "detected_objects": ["person"],
    "injury_indicators": ["Victim detected", "Injury pattern unclear from image"],
    "confidence": 0.60,
    "image_severity_boost": 5,
}


async def analyze_image(image_bytes: bytes, emergency_type: str) -> dict:
    """
    Analyze injury image.
    Full mode: uses YOLOv8 object detection.
    Demo mode: returns mock detections.
    """
    if not image_bytes:
        return {"detected_objects": [], "injury_indicators": [], "confidence": 0.0, "image_severity_boost": 0}

    if settings.ai_mode == "full":
        try:
            return await _yolo_analyze(image_bytes, emergency_type)
        except Exception as e:
            print(f"[Vision] YOLO analysis failed: {e}. Falling back to demo.")

    return MOCK_INJURY_DETECTIONS.get(emergency_type, DEFAULT_MOCK)


async def _yolo_analyze(image_bytes: bytes, emergency_type: str) -> dict:
    """YOLOv8-based injury image analysis."""
    import io
    from PIL import Image
    from ultralytics import YOLO

    model = YOLO("yolov8n.pt")  # Auto-downloads on first use
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    results = model(img, verbose=False)
    detected_names = []
    for r in results:
        for cls_id in r.boxes.cls.tolist():
            name = model.names[int(cls_id)]
            detected_names.append(name)

    # Map YOLO classes to injury indicators
    person_detected = "person" in detected_names
    injury_indicators = []
    if person_detected:
        injury_indicators.append("Person detected at scene")
    if len(detected_names) > 1:
        injury_indicators.append(f"Additional objects: {', '.join(set(detected_names) - {'person'})}")

    return {
        "detected_objects": list(set(detected_names)),
        "injury_indicators": injury_indicators,
        "confidence": 0.75 if person_detected else 0.40,
        "image_severity_boost": 10 if person_detected else 0,
    }
