"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    cors_origins: str = "http://localhost:3000"

    # Database
    database_url: str = "postgresql://proofhire:proofhire@localhost:5432/proofhire"
    database_url_test: str = "postgresql://proofhire:proofhire@localhost:5432/proofhire_test"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # S3 / MinIO
    s3_endpoint_url: str | None = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "proofhire-artifacts"
    s3_region: str = "us-east-1"

    # JWT
    jwt_secret_key: str = "your-super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Anthropic
    anthropic_api_key: str | None = None

    # Runner
    runner_timeout_seconds: int = 600
    runner_memory_limit_mb: int = 512
    runner_cpu_limit: float = 1.0

    # Internal API (for runner callbacks)
    internal_api_key: str = "dev-internal-key-change-in-production"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
