from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_database_url() -> str:
    # backend/ directory (…/backend/app/core/config.py -> …/backend)
    repo_root = Path(__file__).resolve().parents[3]
    db_path = repo_root / "database" / "sqlite" / "database.db"
    return f"sqlite:///{db_path}"


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "AI Student Performance Dashboard"
    app_version: str = "1.0.0"
    debug: bool = True

    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # CORS — comma-separated allowed origins
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Database
    database_url: str = _default_database_url()

    @field_validator("debug", mode="before")
    @classmethod
    def _coerce_debug(cls, v):
        # Some environments set DEBUG to non-boolean strings (e.g. "release").
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            s = v.strip().lower()
            if s in {"1", "true", "yes", "y", "on"}:
                return True
            if s in {"0", "false", "no", "n", "off"}:
                return False
            return False
        return bool(v)

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
