"""
Location Detection API — Task 2
================================
Endpoints:
  POST /api/location/detect  — 4-layer automatic detection
  POST /api/location/geocode — address → coordinates
  GET  /api/location/bounds  — India bounding box info
"""
from fastapi import APIRouter, Request, Query
from pydantic import BaseModel
from typing import Optional
from app.services.location_service import detect_location, geocode_address

router = APIRouter(prefix="/api/location", tags=["location"])


class LocationDetectRequest(BaseModel):
    gps_lat: Optional[float] = None
    gps_lon: Optional[float] = None
    address: Optional[str] = None


class GeocodeRequest(BaseModel):
    address: str


@router.post("/detect")
async def detect(request: Request, body: LocationDetectRequest = LocationDetectRequest()):
    """
    4-layer location detection.
    Priority: GPS (if provided) → Google WiFi → IP → Address → Default (Mumbai)
    """
    client_ip = request.client.host if request.client else None
    # Handle proxied IPs
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()

    location = await detect_location(
        client_ip=client_ip,
        gps_lat=body.gps_lat,
        gps_lon=body.gps_lon,
        address=body.address,
    )
    return {
        "success": True,
        "location": location,
        "layer_description": {
            1: "Browser GPS (±10m)",
            2: "WiFi/Network (±50m)",
            3: "IP Geolocation (±5km)",
            4: "Address Geocode (±100m)",
            0: "Default fallback (Mumbai)",
        }.get(location.get("layer", 0), "Unknown"),
    }


@router.post("/geocode")
async def geocode(body: GeocodeRequest):
    """Convert a text address to GPS coordinates via Nominatim."""
    result = await geocode_address(body.address)
    if not result:
        return {"success": False, "message": "Address not found"}
    return {"success": True, "location": result}


@router.get("/bounds")
async def india_bounds():
    """Return India's geographic bounding box."""
    return {
        "india_bounds": {
            "south": 8.0, "north": 37.0,
            "west": 68.0, "east": 97.0,
        },
        "center": {"latitude": 20.5937, "longitude": 78.9629},
        "description": "India geographic bounds for location validation",
    }
