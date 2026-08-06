"""
Hospital Service (Phase 1 — Full Upgrade)
==========================================
Replaces demo 50-hospital list with:
  - 10,000+ hospitals from OSM via hospital_cache (24h Redis TTL)
  - 7-factor ML-weighted scoring (Task 3)
  - Traffic-aware ETA from routing_service (Task 5)
  - Real-time availability overlay from availability_service (Task 4)
  - 5-minute Redis score cache via scoring_cache

Scoring Weights:
  Distance          25%  — Haversine + exponential decay
  Specialty Match   20%  — Token overlap with synonym expansion
  Availability      15%  — ICU beds normalized
  Traffic ETA       15%  — Real-time travel time vs straight-line
  Patient Rating    10%  — Normalised 0-5 → 0-10
  Trauma Level      10%  — Level 1=10, Level 2=7, Level 3=4, None=0
  Accept. History    5%  — Historical acceptance rate from Redis
"""
from __future__ import annotations

import asyncio
import math
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Specialty synonym expansion ──────────────────────────────────────────────
SPECIALTY_SYNONYMS: dict[str, list[str]] = {
    "trauma": ["trauma", "accident", "emergency", "casualty", "general"],
    "cardiac": ["cardiac", "heart", "cardio", "coronary"],
    "stroke": ["stroke", "neurology", "neuro", "brain"],
    "head_injury": ["head_injury", "neurology", "neuro", "brain", "trauma"],
    "burn": ["burn", "trauma"],
    "fracture": ["fracture", "orthopedic", "trauma"],
    "bleeding": ["bleeding", "trauma", "cardiac"],
    "drowning": ["drowning", "trauma", "respiratory"],
    "road_accident": ["trauma", "accident", "orthopedic", "fracture"],
    "cardiac_arrest": ["cardiac", "cardiac_arrest", "emergency"],
    "neurology": ["neurology", "neuro", "stroke", "head_injury"],
    "orthopedic": ["orthopedic", "fracture"],
}


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two GPS coordinates (Haversine formula)."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _expand_specialties(required: list[str]) -> set[str]:
    """Expand required specialties using synonym map."""
    expanded = set(required)
    for r in required:
        expanded.update(SPECIALTY_SYNONYMS.get(r, []))
    return expanded


# ── 7-Factor ML Scoring ──────────────────────────────────────────────────────

class MLHospitalScorer:
    """
    Computes a weighted multi-factor recommendation score for each hospital.

    Factors and weights:
        distance         0.25
        specialty_match  0.20
        availability     0.15
        traffic_eta      0.15
        rating           0.10
        trauma_level     0.10
        acceptance_rate  0.05
    """

    WEIGHTS = {
        "distance": 0.25,
        "specialty": 0.20,
        "availability": 0.15,
        "traffic": 0.15,
        "rating": 0.10,
        "trauma": 0.10,
        "acceptance": 0.05,
    }

    def __init__(
        self,
        lat: float,
        lon: float,
        required_specialties: list[str],
        traffic_etas: dict[str, float] | None = None,
        availability_data: dict[str, dict] | None = None,
        acceptance_rates: dict[str, float] | None = None,
    ):
        self.lat = lat
        self.lon = lon
        self.required = required_specialties
        self.required_expanded = _expand_specialties(required_specialties)
        self.traffic_etas = traffic_etas or {}
        self.availability = availability_data or {}
        self.acceptance = acceptance_rates or {}

    def score(self, h: dict) -> float:
        """Return composite score 0–100 for a hospital dict."""
        raw = {
            "distance": self._distance_score(h),
            "specialty": self._specialty_score(h),
            "availability": self._availability_score(h),
            "traffic": self._traffic_score(h),
            "rating": self._rating_score(h),
            "trauma": self._trauma_score(h),
            "acceptance": self._acceptance_score(h),
        }
        total = sum(raw[k] * self.WEIGHTS[k] for k in raw)
        return round(total, 4)

    def score_breakdown(self, h: dict) -> dict[str, float]:
        """Return per-factor scores for explainability."""
        return {
            "distance_score": self._distance_score(h),
            "specialty_score": self._specialty_score(h),
            "availability_score": self._availability_score(h),
            "traffic_score": self._traffic_score(h),
            "rating_score": self._rating_score(h),
            "trauma_score": self._trauma_score(h),
            "acceptance_score": self._acceptance_score(h),
        }

    def _distance_score(self, h: dict) -> float:
        """Exponential decay: nearby hospitals overwhelmingly preferred. Max 100."""
        dist = h.get("distance_km", _haversine(self.lat, self.lon, h["latitude"], h["longitude"]))
        # decay constant: 8km half-life
        return 100.0 * math.exp(-dist / 11.5)

    def _specialty_score(self, h: dict) -> float:
        """Fraction of required specialties matched (with synonym expansion). 0–100."""
        if not self.required:
            return 80.0
        h_specs = set(h.get("specialties") or [])
        matched = h_specs & self.required_expanded
        # Direct match bonus
        direct = sum(1 for r in self.required if r in h_specs)
        direct_ratio = direct / len(self.required)
        expanded_ratio = len(matched) / max(len(self.required_expanded), 1)
        return (0.6 * direct_ratio + 0.4 * expanded_ratio) * 100.0

    def _availability_score(self, h: dict) -> float:
        """ICU beds available, normalised. 0–100."""
        hid = h.get("id", "")
        live = self.availability.get(hid, {})
        icu = live.get("icu_beds_available", h.get("icu_beds_available", 0))
        # 50+ beds = full score
        return min(icu / 50.0, 1.0) * 100.0

    def _traffic_score(self, h: dict) -> float:
        """
        Compare traffic ETA to naive straight-line ETA.
        If traffic ETA ≈ naive ETA → high score.
        If traffic ETA is 3× naive → low score.
        """
        hid = h.get("id", "")
        dist = h.get("distance_km", 5.0)
        naive_min = dist / 40.0 * 60.0  # 40 km/h assumption
        traffic_min = self.traffic_etas.get(hid, naive_min)
        ratio = naive_min / max(traffic_min, 1.0)
        return min(ratio, 1.0) * 100.0

    def _rating_score(self, h: dict) -> float:
        """Normalise 0–5 rating to 0–100. Zero rating → neutral 60."""
        rating = h.get("rating", 0)
        if not rating:
            return 60.0
        return min(rating / 5.0, 1.0) * 100.0

    def _trauma_score(self, h: dict) -> float:
        """Trauma center level: L1=100, L2=70, L3=40, none=0."""
        level = h.get("trauma_level", 0)
        if level == 1:
            return 100.0
        if level == 2:
            return 70.0
        if level == 3:
            return 40.0
        if h.get("trauma_center"):
            return 40.0
        return 0.0

    def _acceptance_score(self, h: dict) -> float:
        """Historical acceptance rate 0–1 → 0–100. Defaults to 75."""
        rate = self.acceptance.get(h.get("id", ""), 0.75)
        return rate * 100.0


# ── Hospital retrieval + ranking ─────────────────────────────────────────────

async def find_nearest_hospitals(
    latitude: float,
    longitude: float,
    required_specialties: list[str],
    db=None,
    limit: int = 5,
) -> list[dict]:
    """
    Find and rank nearest hospitals using 7-factor ML scoring.
    Sources: OSM cache (10,000+) → static fallback (500) → DB → demo.
    """
    from app.services.scoring_cache import get_cached_scores, set_cached_scores

    # ── Score cache check ─────────────────────────────────────────────────
    cached = await get_cached_scores(latitude, longitude, required_specialties)
    if cached:
        logger.debug("Returning scored hospitals from cache")
        return cached[:limit]

    # ── Fetch hospital pool ──────────────────────────────────────────────
    hospitals_raw = await _load_hospitals(latitude, longitude, db)

    # ── Fetch async enhancements (traffic, availability, acceptance) ──────
    traffic_etas, availability_data, acceptance_rates = await asyncio.gather(
        _get_traffic_etas(latitude, longitude, hospitals_raw[:50]),  # top 50 candidates
        _get_availability_data(hospitals_raw[:50]),
        _get_acceptance_rates(hospitals_raw[:50]),
        return_exceptions=True,
    )
    traffic_etas = traffic_etas if isinstance(traffic_etas, dict) else {}
    availability_data = availability_data if isinstance(availability_data, dict) else {}
    acceptance_rates = acceptance_rates if isinstance(acceptance_rates, dict) else {}

    # ── Compute distances and add to each hospital ────────────────────────
    for h in hospitals_raw:
        if "distance_km" not in h:
            h["distance_km"] = round(_haversine(latitude, longitude, h["latitude"], h["longitude"]), 2)
        naive_min = h["distance_km"] / 40.0 * 60.0
        h["estimated_travel_min"] = max(int(traffic_etas.get(h.get("id", ""), naive_min)), 3)

    # ── Score + rank ──────────────────────────────────────────────────────
    scorer = MLHospitalScorer(
        lat=latitude,
        lon=longitude,
        required_specialties=required_specialties,
        traffic_etas=traffic_etas,
        availability_data=availability_data,
        acceptance_rates=acceptance_rates,
    )

    for h in hospitals_raw:
        h["_score"] = scorer.score(h)
        h["score_breakdown"] = scorer.score_breakdown(h)
        h["specialty_match"] = scorer._specialty_score(h) / 100.0

    hospitals_raw.sort(key=lambda h: h["_score"], reverse=True)

    # ── Apply live availability overlay ──────────────────────────────────
    for h in hospitals_raw:
        hid = h.get("id", "")
        if hid in availability_data:
            live = availability_data[hid]
            h["icu_beds_available"] = live.get("icu_beds_available", h.get("icu_beds_available", 0))
            h["er_wait_time_min"] = live.get("er_wait_time_min", None)
            h["is_accepting_patients"] = live.get("is_accepting_patients", True)

    # ── Cache and return ──────────────────────────────────────────────────
    scored = hospitals_raw[:limit * 4]  # cache more for pagination
    await set_cached_scores(latitude, longitude, required_specialties, scored)
    return hospitals_raw[:limit]


async def _load_hospitals(lat: float, lon: float, db=None) -> list[dict]:
    """Load hospitals from OSM cache → DB → demo fallback."""
    hospitals: list[dict] = []

    # 1) OSM / Redis cache (primary source)
    try:
        from app.services.hospital_cache import get_cached_hospitals
        cached = await get_cached_hospitals()
        if cached:
            logger.debug("Using hospital cache: %d hospitals", len(cached))
            return cached
    except Exception as exc:
        logger.warning("Hospital cache unavailable: %s", exc)

    # 2) Database (PostgreSQL)
    if db:
        try:
            from sqlalchemy import select
            from app.models.hospital import Hospital
            result = await db.execute(select(Hospital))
            db_hospitals = result.scalars().all()
            for h in db_hospitals:
                hospitals.append({
                    "id": h.id, "name": h.name, "city": h.city,
                    "state": h.state, "address": h.address, "phone": h.phone,
                    "latitude": h.latitude, "longitude": h.longitude,
                    "specialties": h.specialties or [],
                    "icu_beds_available": h.icu_beds_available,
                    "trauma_center": h.trauma_center, "trauma_level": 2,
                    "helipad": h.helipad, "blood_bank": h.blood_bank,
                    "avg_response_time_min": h.avg_response_time_min,
                    "rating": h.rating or 0, "source": "db",
                })
            if hospitals:
                return hospitals
        except Exception as exc:
            logger.warning("DB hospital load failed: %s", exc)

    # 3) Demo fallback
    logger.warning("Using demo hospital fallback")
    return _demo_hospitals()


def _demo_hospitals() -> list[dict]:
    """Minimal demo hospitals covering top Indian cities."""
    return [
        {"id": "demo-1", "name": "Apollo Hospital", "city": "Mumbai", "state": "Maharashtra",
         "address": "Central Avenue, Mumbai", "phone": "022-26711000",
         "latitude": 19.0760, "longitude": 72.8777,
         "specialties": ["trauma", "cardiac", "neurology"],
         "icu_beds_available": 45, "trauma_center": True, "trauma_level": 1,
         "helipad": True, "blood_bank": True, "avg_response_time_min": 8.0, "rating": 4.7, "source": "demo"},
        {"id": "demo-2", "name": "AIIMS Delhi", "city": "New Delhi", "state": "Delhi",
         "address": "Ansari Nagar, New Delhi", "phone": "011-26588500",
         "latitude": 28.5672, "longitude": 77.2100,
         "specialties": ["trauma", "cardiac", "neurology", "burn", "fracture"],
         "icu_beds_available": 120, "trauma_center": True, "trauma_level": 1,
         "helipad": True, "blood_bank": True, "avg_response_time_min": 6.0, "rating": 4.9, "source": "demo"},
        {"id": "demo-3", "name": "Manipal Hospital", "city": "Bengaluru", "state": "Karnataka",
         "address": "HAL Airport Road, Bengaluru", "phone": "080-25024444",
         "latitude": 12.9716, "longitude": 77.5946,
         "specialties": ["trauma", "cardiac", "orthopedic"],
         "icu_beds_available": 80, "trauma_center": True, "trauma_level": 2,
         "helipad": False, "blood_bank": True, "avg_response_time_min": 9.0, "rating": 4.6, "source": "demo"},
        {"id": "demo-4", "name": "Care Hospital", "city": "Hyderabad", "state": "Telangana",
         "address": "Banjara Hills, Hyderabad", "phone": "040-30418888",
         "latitude": 17.3850, "longitude": 78.4867,
         "specialties": ["cardiac", "neurology", "trauma"],
         "icu_beds_available": 60, "trauma_center": True, "trauma_level": 2,
         "helipad": False, "blood_bank": True, "avg_response_time_min": 10.0, "rating": 4.5, "source": "demo"},
        {"id": "demo-5", "name": "MGM Hospital", "city": "Chennai", "state": "Tamil Nadu",
         "address": "Perambur, Chennai", "phone": "044-25571419",
         "latitude": 13.0827, "longitude": 80.2707,
         "specialties": ["trauma", "orthopedic", "fracture"],
         "icu_beds_available": 35, "trauma_center": True, "trauma_level": 3,
         "helipad": False, "blood_bank": True, "avg_response_time_min": 12.0, "rating": 4.2, "source": "demo"},
    ]


async def _get_traffic_etas(lat: float, lon: float, hospitals: list[dict]) -> dict[str, float]:
    """Get real-time traffic ETAs from routing_service."""
    try:
        from app.services.routing_service import get_bulk_etas
        etas = await get_bulk_etas(lat, lon, hospitals)
        return etas
    except Exception as exc:
        logger.debug("Traffic ETA unavailable: %s", exc)
        return {}


async def _get_availability_data(hospitals: list[dict]) -> dict[str, dict]:
    """Get real-time availability from availability_service."""
    try:
        from app.services.availability_service import get_bulk_availability
        return await get_bulk_availability([h["id"] for h in hospitals])
    except Exception as exc:
        logger.debug("Availability data unavailable: %s", exc)
        return {}


async def _get_acceptance_rates(hospitals: list[dict]) -> dict[str, float]:
    """Get historical acceptance rates from Redis."""
    try:
        import redis.asyncio as aioredis
        from app.config import get_settings
        r = aioredis.from_url(get_settings().redis_url, decode_responses=True, socket_timeout=1)
        rates = {}
        for h in hospitals:
            val = await r.get(f"rapidcare:acceptance:{h['id']}")
            if val:
                rates[h["id"]] = float(val)
        await r.aclose()
        return rates
    except Exception:
        return {}
