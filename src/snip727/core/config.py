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
    # Base network settings
    base_rpc_urls: list[str] = [
        "wss://base.gateway.tenderly.co",
        "wss://base-mainnet.blastapi.io",
        "https://mainnet.base.org",
        "https://base.publicnode.com",
    ]
    
    # Uniswap contracts
    uniswap_v2_factory: str = "0x4200000000000000000000000000000000000006"  # Base Uniswap V2 Factory
    uniswap_v3_factory: str = "0x33128a8fC17869897dcE68Ed026d694621f6FDfD"  # Base Uniswap V3 Factory
    
    # Monitoring settings
    liquidity_spike_threshold: float = 5.0  # 5x spike
    whale_buy_threshold: float = 0.005  # 0.5% of pool
    new_pool_blocks_threshold: int = 15
    sentiment_threshold: float = 0.6
    
    # Sentiment analysis
    telegram_channels: list[str] = []
    nitter_feeds: list[str] = ["https://nitter.net/elonmusk/rss"]
    
    # Strategy settings
    strategy_signals_required: int = 3  # N-of-4 strategy

    # Logging
    log_level: str = "INFO"


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
