"""
Agencity configuration.
"""

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_env: str = "development"
    debug: bool = True

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
    external_api_timeout_seconds: float = 30.0
    external_api_max_retries: int = 2
    allow_mock_external_search: bool = False

    # GitHub
    github_token: str = ""

    # Clado AI (LinkedIn search)
    clado_api_key: str = ""

    # Pearch AI (LinkedIn alternative)
    pearch_api_key: str = ""

    # Supabase (Candidate Database)
    supabase_url: str = ""
    supabase_key: str = ""

    # ProductHunt API
    producthunt_api_key: str = ""

    # Slack Integration
    slack_bot_token: str = ""  # xoxb-...
    slack_signing_secret: str = ""  # Signing secret from Slack app
    slack_client_id: str = ""  # For OAuth install flow
    slack_client_secret: str = ""  # For OAuth install flow
    slack_redirect_uri: str = ""  # OAuth redirect URI

    # Pinecone (Vector Search)
    pinecone_api_key: str = ""
    pinecone_index_name: str = "agencity-people"
    pinecone_environment: str = "us-east-1"  # or your region

    # Perplexity (Enrichment)
    perplexity_api_key: str = ""

    # Anthropic (Claude - Reasoning Layer)
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"  # Latest Claude model

    # Google Custom Search Engine
    google_cse_api_key: str = ""
    google_cse_id: str = ""  # Custom Search Engine ID

    # Context Management (learned from OpenClaw)
    max_context_tokens: int = 100_000
    soft_trim_ratio: float = 0.3  # Trigger soft compression at 30%
    hard_clear_ratio: float = 0.5  # Trigger hard removal at 50%

    # Security
    secret_key: str = "dev-secret-change-in-production"
    access_token_expire_minutes: int = 60 * 24 * 7  # 1 week
    agencity_internal_api_key: str = ""

    # ProofHire integration
    proofhire_api_base: str = "http://localhost:8000/api"
    proofhire_internal_api_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
