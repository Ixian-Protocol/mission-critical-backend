"""
Application configuration management.
"""
import json
from functools import lru_cache
from typing import Any

from pydantic import computed_field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Ixian Protocol: Mission Critical Backend"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Backend API for Ixian Protocol's Mission Critical application."

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # CORS - includes frontend dev servers and mobile app origins
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:5173",  # Vite dev server
        "http://localhost:4173",  # Vite preview
        "capacitor://localhost",  # iOS Capacitor
        "http://localhost",       # Android Capacitor
        "https://localhost",      # Android Capacitor secure
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            # Handle JSON array string: '["http://localhost:3000","http://localhost:8000"]'
            if v.startswith("["):
                return json.loads(v)
            # Handle comma-separated string: "http://localhost:3000,http://localhost:8000"
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "app"

    # ntfy Notifications (optional)
    NTFY_URL: str | None = None  # e.g., "https://ntfy.sh" or "http://ntfy:80"
    NTFY_TOKEN: str | None = None  # Optional: for authenticated ntfy servers
    NTFY_TOPIC: str = "ixian-mission-critical"

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """Construct async database URL from components."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field
    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Construct sync database URL for Alembic migrations."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
