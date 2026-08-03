"""
First-Aid Service: Retrieves relevant first-aid protocols using TF-IDF RAG.
Matches emergency type and text context to knowledge base entries.
"""
import json
import os
from typing import Optional
from pathlib import Path

KB_PATH = Path(__file__).parent.parent / "knowledge_base" / "first_aid_protocols.json"

_protocols: list[dict] = []
_tfidf_matrix = None
_vectorizer = None


def _load_kb() -> list[dict]:
    global _protocols
    if not _protocols:
        with open(KB_PATH, "r") as f:
            data = json.load(f)
            _protocols = data["protocols"]
    return _protocols


def _build_tfidf():
    global _tfidf_matrix, _vectorizer
    if _tfidf_matrix is not None:
        return
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        protocols = _load_kb()
        docs = []
        for p in protocols:
            kw_str = " ".join(p["keywords"])
            doc = f"{p['title']} {p['description']} {kw_str}"
            docs.append(doc)
        _vectorizer = TfidfVectorizer(stop_words="english")
        _tfidf_matrix = _vectorizer.fit_transform(docs)
    except Exception:
        pass


def get_first_aid(
    emergency_type: str,
    text: Optional[str] = None,
) -> dict:
    """
    Return first-aid steps, warnings, and required hospital specialties
    for the detected emergency type, optionally refined by free text.
    """
    protocols = _load_kb()

    # Primary: exact match by emergency_type
    matched = None
    for p in protocols:
        if p["emergency_type"] == emergency_type:
            matched = p
            break

    # Secondary: TF-IDF search if text is provided and no match
    if not matched and text:
        _build_tfidf()
        if _vectorizer and _tfidf_matrix is not None:
            try:
                import numpy as np
                from sklearn.metrics.pairwise import cosine_similarity
                q_vec = _vectorizer.transform([text])
                sims = cosine_similarity(q_vec, _tfidf_matrix).flatten()
                best_idx = int(np.argmax(sims))
                if sims[best_idx] > 0.05:
                    matched = protocols[best_idx]
            except Exception:
                pass

    # Fallback: return road accident protocol
    if not matched:
        matched = protocols[0]

    return {
        "protocol_id": matched["id"],
        "title": matched["title"],
        "steps": matched["steps"],
        "warnings": matched["warnings"],
        "required_specialties": matched.get("required_specialties", ["trauma"]),
    }
