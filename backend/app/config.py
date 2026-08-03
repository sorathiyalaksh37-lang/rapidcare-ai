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

    # Maps
    google_maps_api_key: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    class Config:
        env_file = _ENV_FILE
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
