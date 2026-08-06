from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

# Look for .env in backend dir OR one level up (project root)
_ENV_FILE = ".env" if Path(".env").exists() else str(Path(__file__).parent.parent.parent / ".env")


class Settings(BaseSettings):
    # App
    app_name: str = "RapidCare AI"
    environment: str = "development"
    debug: bool = True
    secret_key: str = "change-me"
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    # Database
    database_url: str = "sqlite+aiosqlite:///./rapidcare.db"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # AI
    ai_mode: str = "demo"  # "full" or "demo"
    whisper_model: str = "small"
    openai_api_key: str = ""

    # ── Google APIs ─────────────────────────────────────────────────────
    google_maps_api_key: str = ""           # Distance Matrix + Directions
    google_places_api_key: str = ""         # Hospital details + ratings
    google_geolocation_api_key: str = ""    # WiFi/network location (Layer 2)

    # ── OSM / Location ──────────────────────────────────────────────────
    osm_overpass_url: str = "https://overpass-api.de/api/interpreter"
    # India bounding box: S,W,N,E
    india_bounds: str = "8.0,68.0,37.0,97.0"
    # Fallback IP geolocation services
    ip_geo_primary_url: str = "http://ip-api.com/json"
    ip_geo_fallback_url: str = "https://ipinfo.io/json"

    # ── Cache TTLs ──────────────────────────────────────────────────────
    hospital_cache_ttl_hours: int = 24          # OSM hospital refresh
    location_cache_ttl_seconds: int = 300       # IP geolocation cache
    score_cache_ttl_seconds: int = 300          # Hospital scoring cache
    availability_cache_ttl_seconds: int = 5    # Real-time bed/wait cache
    routing_cache_ttl_seconds: int = 600       # Traffic routing cache

    # ── Hospital data paths ─────────────────────────────────────────────
    hospital_fallback_json: str = str(
        Path(__file__).parent / "db" / "indian_hospitals_500.json"
    )

    # ── ML Models ───────────────────────────────────────────────────────
    models_dir: str = str(Path(__file__).parent.parent.parent.parent / "ml" / "models")
    nlp_model_path: str = ""       # ONNX path; empty = use demo keyword mode
    vision_model_path: str = ""    # ONNX path; empty = use demo mock
    survival_model_path: str = ""  # ONNX path; empty = use sigmoid formula
    triage_model_path: str = ""    # ONNX path; empty = skip

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def india_bounds_tuple(self) -> tuple[float, float, float, float]:
        """Returns (south, west, north, east) floats."""
        parts = [float(x.strip()) for x in self.india_bounds.split(",")]
        return tuple(parts)  # type: ignore

    class Config:
        env_file = _ENV_FILE
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
