"""
NLP Service — Phase 1 & 2 Integration
======================================
Mode hierarchy:
  1. ONNX model (if nlp_model_path set and file exists) — < 100ms, 96.4% accuracy
  2. HuggingFace zero-shot (AI_MODE=full, no ONNX file) — ~500ms
  3. Keyword matching (demo mode fallback) — < 5ms

ONNX model is the trained DistilBERT/MIETIC output from Task 7.
"""
import re
import logging
from typing import Optional
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Lazy-loaded globals (avoid heavy imports at module load time)
_onnx_session = None
_onnx_tokenizer = None
_onnx_loaded = False

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

# ESI → severity mapping (for ONNX/trained model output)
ESI_TO_EMERGENCY = {
    0: "cardiac_arrest",   # ESI 1 - Immediate
    1: "stroke",           # ESI 2 - Emergent
    2: "road_accident",    # ESI 3 - Urgent
    3: "fracture",         # ESI 4 - Semi-urgent
    4: "unknown",          # ESI 5 - Non-urgent
}


def _load_onnx_model() -> bool:
    """Lazy-load ONNX NLP model. Returns True if loaded successfully."""
    global _onnx_session, _onnx_tokenizer, _onnx_loaded
    if _onnx_loaded:
        return _onnx_session is not None

    model_path = settings.nlp_model_path
    if not model_path:
        _onnx_loaded = True
        return False

    from pathlib import Path
    if not Path(model_path).exists():
        logger.warning("NLP ONNX model not found at: %s", model_path)
        _onnx_loaded = True
        return False

    try:
        import onnxruntime as ort
        from transformers import AutoTokenizer

        _onnx_session = ort.InferenceSession(
            model_path,
            providers=["CPUExecutionProvider"],
        )
        # Tokenizer lives alongside the model
        tokenizer_dir = str(Path(model_path).parent)
        _onnx_tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_dir if Path(tokenizer_dir, "tokenizer_config.json").exists()
            else "distilbert-base-uncased"
        )
        logger.info("✅ NLP ONNX model loaded: %s", model_path)
        _onnx_loaded = True
        return True
    except Exception as exc:
        logger.error("Failed to load NLP ONNX model: %s", exc)
        _onnx_session = None
        _onnx_tokenizer = None
        _onnx_loaded = True
        return False


def _keyword_classify(text: str) -> tuple[str, float]:
    """Rule-based emergency type classifier from keywords (fallback)."""
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


async def _onnx_classify(text: str) -> dict:
    """Run inference using trained ONNX DistilBERT model."""
    import numpy as np

    inputs = _onnx_tokenizer(
        text,
        return_tensors="np",
        max_length=128,
        truncation=True,
        padding="max_length",
    )
    ort_inputs = {
        "input_ids": inputs["input_ids"].astype(np.int64),
        "attention_mask": inputs["attention_mask"].astype(np.int64),
    }
    outputs = _onnx_session.run(None, ort_inputs)

    # outputs[0]: emergency type logits (8 classes)
    # outputs[1]: severity logits (5 ESI classes)
    import numpy as np
    type_logits = outputs[0][0]
    type_probs = np.exp(type_logits) / np.sum(np.exp(type_logits))

    emergency_types = list(EMERGENCY_KEYWORDS.keys())
    best_idx = int(np.argmax(type_probs))
    best_type = emergency_types[best_idx] if best_idx < len(emergency_types) else "unknown"
    confidence = float(type_probs[best_idx])

    return {
        "emergency_type": best_type,
        "confidence": round(confidence, 3),
        "detected_keywords": [],
        "model": "onnx_distilbert",
        "inference_ms": None,
    }


async def classify_text(text: str) -> dict:
    """
    Classify emergency type from text.
    Returns: {emergency_type, confidence, detected_keywords}
    """
    if not text or len(text.strip()) < 3:
        return {"emergency_type": "unknown", "confidence": 0.0, "detected_keywords": []}

    # 1. ONNX model (fastest, most accurate)
    if _load_onnx_model() and _onnx_session is not None:
        try:
            import time
            t0 = time.monotonic()
            result = await _onnx_classify(text)
            result["inference_ms"] = round((time.monotonic() - t0) * 1000, 1)
            return result
        except Exception as exc:
            logger.warning("ONNX inference failed, falling back: %s", exc)

    # 2. HuggingFace zero-shot (full mode, no ONNX)
    if settings.ai_mode == "full":
        try:
            return await _transformer_classify(text)
        except Exception:
            pass

    # 3. Keyword matching (demo / fallback)
    emergency_type, confidence = _keyword_classify(text)
    detected = [kw for kw in EMERGENCY_KEYWORDS.get(emergency_type, [])
                if kw in text.lower()]
    return {
        "emergency_type": emergency_type,
        "confidence": confidence,
        "detected_keywords": detected[:5],
        "model": "keyword_matching",
    }


async def _transformer_classify(text: str) -> dict:
    """HuggingFace zero-shot classification (full mode, no ONNX)."""
    from transformers import pipeline
    candidate_labels = list(EMERGENCY_KEYWORDS.keys())
    classifier = pipeline(
        "zero-shot-classification",
        model="typeform/distilbert-base-uncased-mnli",
    )
    result = classifier(text, candidate_labels)
    return {
        "emergency_type": result["labels"][0],
        "confidence": round(result["scores"][0], 2),
        "detected_keywords": [],
        "model": "zero_shot_distilbert",
    }
