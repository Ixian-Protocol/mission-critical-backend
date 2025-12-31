"""
Application configuration management.
"""
from pydantic_settings import BaseSettings
from pydantic import computed_field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "FastAPI Production Template"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Production-ready FastAPI application with clean architecture"

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
    ]

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
