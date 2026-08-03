"""
Hospital Service: Finds nearest hospitals using Haversine distance and specialty matching.
"""
import math
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.hospital import Hospital

# Fallback demo hospitals for when DB is unavailable
DEMO_HOSPITALS = [
    {
        "id": "demo-1",
        "name": "Apollo Hospital",
        "city": "Mumbai",
        "state": "Maharashtra",
        "address": "Central Avenue, Mumbai",
        "phone": "1800-XXX-XXXX",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "specialties": ["trauma", "cardiac", "neurology"],
        "icu_beds_available": 45,
        "trauma_center": True,
        "helipad": True,
        "blood_bank": True,
        "avg_response_time_min": 8.0,
        "rating": 4.7,
        "distance_km": 2.3,
        "estimated_travel_min": 9,
    },
    {
        "id": "demo-2",
        "name": "City Emergency Hospital",
        "city": "Mumbai",
        "state": "Maharashtra",
        "address": "Hospital Road, Mumbai",
        "phone": "1800-YYY-XXXX",
        "latitude": 19.0896,
        "longitude": 72.8656,
        "specialties": ["trauma", "fracture", "burn"],
        "icu_beds_available": 20,
        "trauma_center": True,
        "helipad": False,
        "blood_bank": True,
        "avg_response_time_min": 12.0,
        "rating": 4.2,
        "distance_km": 4.1,
        "estimated_travel_min": 15,
    },
    {
        "id": "demo-3",
        "name": "Lilavati Hospital",
        "city": "Mumbai",
        "state": "Maharashtra",
        "address": "Bandra West, Mumbai",
        "phone": "022-XXXX-XXXX",
        "latitude": 19.0523,
        "longitude": 72.8246,
        "specialties": ["cardiac", "neurology", "orthopedic"],
        "icu_beds_available": 60,
        "trauma_center": True,
        "helipad": True,
        "blood_bank": True,
        "avg_response_time_min": 6.5,
        "rating": 4.8,
        "distance_km": 5.8,
        "estimated_travel_min": 20,
    },
]


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two GPS coordinates."""
    R = 6371  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _specialty_match_score(hospital_specialties: list, required: list) -> float:
    """Returns fraction of required specialties matched."""
    if not required:
        return 1.0
    matched = sum(1 for s in required if s in hospital_specialties)
    return matched / len(required)


async def find_nearest_hospitals(
    latitude: float,
    longitude: float,
    required_specialties: list[str],
    db: Optional[AsyncSession] = None,
    limit: int = 5,
) -> list[dict]:
    """
    Find nearest hospitals sorted by weighted score (distance + specialty match).
    """
    hospitals_raw = []

    if db:
        try:
            result = await db.execute(select(Hospital))
            db_hospitals = result.scalars().all()
            for h in db_hospitals:
                dist = _haversine(latitude, longitude, h.latitude, h.longitude)
                specialty_score = _specialty_match_score(h.specialties or [], required_specialties)
                travel_min = round(dist / 40 * 60)  # Assume 40 km/h average city speed

                hospitals_raw.append({
                    "id": h.id,
                    "name": h.name,
                    "city": h.city,
                    "state": h.state,
                    "address": h.address,
                    "phone": h.phone,
                    "latitude": h.latitude,
                    "longitude": h.longitude,
                    "specialties": h.specialties,
                    "icu_beds_available": h.icu_beds_available,
                    "trauma_center": h.trauma_center,
                    "helipad": h.helipad,
                    "blood_bank": h.blood_bank,
                    "avg_response_time_min": h.avg_response_time_min,
                    "rating": h.rating,
                    "distance_km": round(dist, 2),
                    "estimated_travel_min": max(travel_min, 3),
                    "specialty_match": specialty_score,
                })
        except Exception:
            pass

    if not hospitals_raw:
        # Use demo data with computed distances
        for h in DEMO_HOSPITALS:
            dist = _haversine(latitude, longitude, h["latitude"], h["longitude"])
            h = dict(h)
            h["distance_km"] = round(dist, 2)
            h["estimated_travel_min"] = max(round(dist / 40 * 60), 3)
            h["specialty_match"] = _specialty_match_score(h.get("specialties", []), required_specialties)
            hospitals_raw.append(h)

    # Sort: weighted score (lower distance better, higher specialty match better)
    def score(h):
        dist_score = 1 / (h["distance_km"] + 0.1)
        spec_score = h.get("specialty_match", 0.5) * 2
        icu_score = min(h.get("icu_beds_available", 0) / 100, 1.0)
        return dist_score + spec_score + icu_score

    hospitals_raw.sort(key=score, reverse=True)
    return hospitals_raw[:limit]
