"""
NLP Service: Detects emergency type and confidence from text input.
Uses keyword matching in demo mode; HuggingFace classifier in full mode.
"""
import re
from typing import Optional
from app.config import get_settings

settings = get_settings()

EMERGENCY_KEYWORDS = {
    "road_accident": [
        "accident", "crash", "collision", "vehicle", "car", "bike", "truck",
        "motorcycle", "road", "hit", "knocked", "ran over", "overturned",
        "speed", "rash driving", "highway", "signal", "pedestrian struck"
    ],
    "cardiac_arrest": [
        "heart attack", "cardiac", "chest pain", "chest tightness", "palpitation",
        "heart stopped", "collapsed", "not breathing", "clutching chest",
        "heart failure", "sudden collapse", "unconscious cardiac"
    ],
    "stroke": [
        "stroke", "slurred speech", "face drooping", "arm weak", "vision loss",
        "sudden headache", "confusion speech", "brain attack", "paralysis",
        "one side weakness", "cannot speak"
    ],
    "bleeding": [
        "bleeding", "blood", "hemorrhage", "wound", "cut", "laceration",
        "gash", "stabbed", "deep cut", "bleeding profusely", "blood loss"
    ],
    "fracture": [
        "fracture", "broken bone", "broken arm", "broken leg", "cannot move",
        "swollen limb", "bone sticking", "deformity", "snap", "cracked bone"
    ],
    "fire_burn": [
        "burn", "fire", "flame", "scald", "hot liquid", "chemical burn",
        "acid attack", "electric shock", "explosion", "caught fire"
    ],
    "drowning": [
        "drowning", "submerged", "pulled from water", "near drowning",
        "pool accident", "river accident", "water rescue", "not breathing water"
    ],
    "head_injury": [
        "head injury", "head wound", "concussion", "skull fracture",
        "hit head", "head trauma", "unconscious hit", "brain injury",
        "head bleeding", "helmet crash"
    ],
}


def _keyword_classify(text: str) -> tuple[str, float]:
    """Rule-based emergency type classifier from keywords."""
    text_lower = text.lower()
    scores: dict[str, int] = {}

    for etype, keywords in EMERGENCY_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in text_lower)
        if count:
            scores[etype] = count

    if not scores:
        return "unknown", 0.3

    best = max(scores, key=lambda k: scores[k])
    total = sum(scores.values())
    confidence = min(scores[best] / max(total, 1) + 0.4, 0.95)
    return best, round(confidence, 2)


async def classify_text(text: str) -> dict:
    """
    Classify emergency type from text.
    Returns: {emergency_type, confidence, detected_keywords}
    """
    if not text or len(text.strip()) < 3:
        return {"emergency_type": "unknown", "confidence": 0.0, "detected_keywords": []}

    if settings.ai_mode == "full":
        try:
            return await _transformer_classify(text)
        except Exception:
            pass  # Fallback to keyword matching

    emergency_type, confidence = _keyword_classify(text)
    detected = [kw for kw in EMERGENCY_KEYWORDS.get(emergency_type, [])
                if kw in text.lower()]

    return {
        "emergency_type": emergency_type,
        "confidence": confidence,
        "detected_keywords": detected[:5],
    }


async def _transformer_classify(text: str) -> dict:
    """Use HuggingFace zero-shot classifier for better accuracy in full mode."""
    from transformers import pipeline
    candidate_labels = list(EMERGENCY_KEYWORDS.keys())
    classifier = pipeline(
        "zero-shot-classification",
        model="typeform/distilbert-base-uncased-mnli"
    )
    result = classifier(text, candidate_labels)
    best_label = result["labels"][0]
    best_score = result["scores"][0]
    return {
        "emergency_type": best_label,
        "confidence": round(best_score, 2),
        "detected_keywords": [],
    }
