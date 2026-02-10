"""
Agencity configuration.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_env: str = "development"
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://agencity:agencity@localhost:5432/agencity"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # LLM (OpenAI)
    openai_api_key: str = ""
    default_model: str = "gpt-4o"  # or "gpt-4o-mini" for faster/cheaper

    # Embeddings
    embedding_model: str = "text-embedding-3-small"

    # People Data Labs
    pdl_api_key: str = ""
    pdl_daily_budget_usd: float = 50.0

    # GitHub
    github_token: str = ""

    # Clado AI (LinkedIn search)
    clado_api_key: str = ""

    # Context Management (learned from OpenClaw)
    max_context_tokens: int = 100_000
    soft_trim_ratio: float = 0.3  # Trigger soft compression at 30%
    hard_clear_ratio: float = 0.5  # Trigger hard removal at 50%

    # Security
    secret_key: str = "dev-secret-change-in-production"
    access_token_expire_minutes: int = 60 * 24 * 7  # 1 week

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
