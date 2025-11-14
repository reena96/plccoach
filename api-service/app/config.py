"""Application configuration using Pydantic Settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "PLC Coach API"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"

    # Database
    database_url: str = ""
    db_pool_size: int = 20
    db_max_overflow: int = 0
    db_pool_pre_ping: bool = True

    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080"
    ]
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]

    # AWS (optional - for production)
    aws_region: str = "us-east-1"
    db_secret_name: str = "plccoach-db-password"

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    # Clever OAuth
    clever_client_id: str = ""
    clever_client_secret: str = ""
    clever_redirect_uri: str = "http://localhost:8000/auth/clever/callback"

    # Frontend
    frontend_url: str = "http://localhost:5173"  # Frontend URL for OAuth redirects

    # Session
    session_cookie_name: str = "plc_session"
    session_max_age: int = 86400  # 24 hours in seconds (absolute expiry)
    session_inactivity_minutes: int = 30  # Inactivity timeout in minutes
    session_secret_key: str = ""  # For SessionMiddleware (OAuth state storage)
    cleanup_schedule_hour: int = 2  # Hour (0-23) to run daily session cleanup (UTC)

    model_config = SettingsConfigDict(
        env_file=".env",  # Load from .env file for local development
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields in .env
    )


# Global settings instance
settings = Settings()
