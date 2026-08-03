"""
Severity Service: Estimates injury severity from emergency type, context clues and input text.
Returns a 0-100 severity score and corresponding level.
"""
import re
from typing import Optional

SEVERITY_RULES = {
    # Base scores by emergency type
    "base_scores": {
        "cardiac_arrest": 92,
        "stroke": 85,
        "drowning": 80,
        "head_injury": 75,
        "bleeding": 70,
        "road_accident": 65,
        "fire_burn": 60,
        "fracture": 45,
        "unknown": 50,
    },
    # Modifier keywords that increase/decrease severity
    "increase_keywords": {
        "unconscious": +15, "not breathing": +20, "stopped breathing": +20,
        "no pulse": +20, "heavy bleeding": +15, "blood everywhere": +15,
        "multiple injured": +10, "trapped": +12, "fire": +10, "head wound": +10,
        "critical": +12, "severe": +8, "collapsed": +15, "unresponsive": +18,
        "child": +8, "elderly": +8, "pregnant": +10, "seizure": +12,
        "deep wound": +8, "bone sticking": +10, "compound fracture": +12,
    },
    "decrease_keywords": {
        "minor": -15, "small": -10, "conscious": -8, "awake": -5,
        "walking": -12, "talking": -8, "mild": -15, "slight": -12,
        "bruise": -10, "scratch": -15,
    },
}


def estimate_severity(
    emergency_type: str,
    text: Optional[str] = None,
    has_image: bool = False,
    has_voice: bool = False,
    confidence: float = 0.7,
) -> dict:
    """
    Estimate injury severity.
    Returns: {severity_score, severity_level, survival_probability, contributing_factors}
    """
    base = SEVERITY_RULES["base_scores"].get(emergency_type, 50)
    modifier = 0
    factors = []

    if text:
        text_lower = text.lower()
        for keyword, delta in SEVERITY_RULES["increase_keywords"].items():
            if keyword in text_lower:
                modifier += delta
                factors.append(f"'{keyword}' detected (+{delta})")

        for keyword, delta in SEVERITY_RULES["decrease_keywords"].items():
            if keyword in text_lower:
                modifier += delta
                factors.append(f"'{keyword}' detected ({delta})")

    # Adjust for confidence
    if confidence < 0.5:
        modifier -= 5

    score = max(0, min(100, base + modifier))

    # Survival probability: sigmoid-like mapping
    if score >= 90:
        survival = 0.25
    elif score >= 75:
        survival = 0.55
    elif score >= 55:
        survival = 0.78
    elif score >= 35:
        survival = 0.90
    else:
        survival = 0.97

    # Severity level
    if score >= 80:
        level = "CRITICAL"
    elif score >= 60:
        level = "SEVERE"
    elif score >= 35:
        level = "MODERATE"
    else:
        level = "MILD"

    return {
        "severity_score": round(score, 1),
        "severity_level": level,
        "survival_probability": round(survival, 2),
        "contributing_factors": factors[:5],
        "base_score": base,
        "modifier": modifier,
    }
