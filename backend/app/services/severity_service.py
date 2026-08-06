"""
Severity Service — Phase 2 Integration
=======================================
Mode hierarchy:
  1. ONNX Survival Predictor (if survival_model_path set) — 87%+ accuracy
  2. Rule-based scoring with keyword modifiers (fallback)

The ONNX model is the trained neural network from Task 9.
Input features (50 total):
  - Emergency type (one-hot, 8 classes)
  - Keyword severity signals (up to 20 boolean features)
  - Has image / voice (2 bool)
  - NLP confidence (float)
  - Time of day, etc.
"""
import logging
from typing import Optional
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_onnx_survival_session = None
_survival_loaded = False

SEVERITY_RULES = {
    "base_scores": {
        "cardiac_arrest": 92, "stroke": 85, "drowning": 80,
        "head_injury": 75, "bleeding": 70, "road_accident": 65,
        "fire_burn": 60, "fracture": 45, "unknown": 50,
    },
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

EMERGENCY_TYPES = [
    "road_accident", "cardiac_arrest", "stroke", "drowning",
    "fire_burn", "fracture", "head_injury", "bleeding", "unknown",
]


def _load_survival_model() -> bool:
    """Lazy-load ONNX survival predictor."""
    global _onnx_survival_session, _survival_loaded
    if _survival_loaded:
        return _onnx_survival_session is not None

    model_path = settings.survival_model_path
    if not model_path:
        _survival_loaded = True
        return False

    from pathlib import Path
    if not Path(model_path).exists():
        logger.warning("Survival ONNX model not found at: %s", model_path)
        _survival_loaded = True
        return False

    try:
        import onnxruntime as ort
        _onnx_survival_session = ort.InferenceSession(
            model_path, providers=["CPUExecutionProvider"]
        )
        logger.info("✅ Survival ONNX model loaded: %s", model_path)
        _survival_loaded = True
        return True
    except Exception as exc:
        logger.error("Failed to load survival ONNX model: %s", exc)
        _survival_loaded = True
        return False


def _build_feature_vector(
    emergency_type: str,
    text: Optional[str],
    has_image: bool,
    has_voice: bool,
    confidence: float,
    severity_score: float,
) -> "list[float]":
    """Build 50-dimensional feature vector for survival predictor."""
    features = []

    # Emergency type one-hot (9)
    et_vec = [1.0 if emergency_type == et else 0.0 for et in EMERGENCY_TYPES]
    features.extend(et_vec)

    # Keyword signals (20 boolean features)
    text_lower = (text or "").lower()
    keyword_features = [
        "unconscious" in text_lower, "not breathing" in text_lower,
        "no pulse" in text_lower, "heavy bleeding" in text_lower,
        "trapped" in text_lower, "collapsed" in text_lower,
        "unresponsive" in text_lower, "critical" in text_lower,
        "severe" in text_lower, "seizure" in text_lower,
        "minor" in text_lower, "conscious" in text_lower,
        "walking" in text_lower, "talking" in text_lower,
        "mild" in text_lower, "child" in text_lower,
        "elderly" in text_lower, "pregnant" in text_lower,
        "compound fracture" in text_lower, "multiple injured" in text_lower,
    ]
    features.extend([float(f) for f in keyword_features])

    # Scalar features (5)
    features.extend([
        float(has_image), float(has_voice),
        confidence, severity_score / 100.0,
        len(text or "") / 500.0,  # text length normalised
    ])

    # Pad to exactly 50 features with zeros
    features.extend([0.0] * (50 - len(features)))
    return features[:50]


def _onnx_predict_survival(features: "list[float]") -> float:
    """Run survival predictor ONNX inference."""
    import numpy as np
    x = np.array([features], dtype=np.float32)
    outputs = _onnx_survival_session.run(None, {"input": x})
    prob = float(outputs[0][0][0])
    return round(max(0.01, min(0.99, prob)), 2)


def _rule_based_survival(severity_score: float, emergency_type: str) -> float:
    """Sigmoid-like survival estimate from severity score."""
    if severity_score >= 90:
        return 0.25
    if severity_score >= 75:
        return 0.55
    if severity_score >= 55:
        return 0.78
    if severity_score >= 35:
        return 0.90
    return 0.97


def estimate_severity(
    emergency_type: str,
    text: Optional[str] = None,
    has_image: bool = False,
    has_voice: bool = False,
    confidence: float = 0.7,
) -> dict:
    """
    Estimate injury severity score + survival probability.
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

    if confidence < 0.5:
        modifier -= 5

    score = max(0.0, min(100.0, base + modifier))

    # Severity level
    if score >= 80:
        level = "CRITICAL"
    elif score >= 60:
        level = "SEVERE"
    elif score >= 35:
        level = "MODERATE"
    else:
        level = "MILD"

    # Survival probability: ONNX model > rule-based fallback
    if _load_survival_model() and _onnx_survival_session is not None:
        try:
            features = _build_feature_vector(
                emergency_type, text, has_image, has_voice, confidence, score
            )
            survival = _onnx_predict_survival(features)
        except Exception as exc:
            logger.warning("Survival ONNX inference failed: %s", exc)
            survival = _rule_based_survival(score, emergency_type)
    else:
        survival = _rule_based_survival(score, emergency_type)

    return {
        "severity_score": round(score, 1),
        "severity_level": level,
        "survival_probability": survival,
        "contributing_factors": factors[:5],
        "base_score": base,
        "modifier": modifier,
        "survival_model": "onnx" if (_onnx_survival_session is not None) else "rule_based",
    }
