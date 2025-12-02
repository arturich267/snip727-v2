"""Application configuration using Pydantic Settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Bot settings
    telegram_token: str = ""
    telegram_chat_id: str = ""

    # Database settings
    database_url: str = "postgresql+asyncpg://snip727:snip727@localhost:5432/snip727"
    redis_url: str = "redis://localhost:6379"

    # Web3 settings
    web3_provider_url: str = "http://localhost:8545"
    chain_id: int = 1

    # Logging
    log_level: str = "INFO"


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
