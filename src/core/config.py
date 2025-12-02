from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Bot Configuration
    bot_token: str
    bot_admin_ids: str = "123456789"
    bot_log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+asyncpg://snip727:snip727@localhost:5432/snip727_db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Web3 Configuration
    web3_provider_url: str = "https://mainnet.base.org"
    web3_chain_id: int = 8453

    # Uniswap Configuration
    uniswap_factory_v2: str = "0x8909Dc15e40953b386FA8f440dB7f0DDA8221820"
    uniswap_router_v2: str = "0x4752ba5DBc23f44D87826ADF0FF190cF7ec87b9b"
    uniswap_factory_v3: str = "0x33128a8fC17869897dcE68Ed026d694621f6FDaD"
    uniswap_swap_router_v3: str = "0x2626664c2603336E57B271c5C0b26F421741e481"

    # Strategy Configuration
    min_liquidity_usd: float = 5000.0
    max_price_impact: float = 0.5
    gas_price_multiplier: float = 1.2
    slippage_tolerance: float = 0.01

    # Monitoring
    monitoring_interval_seconds: int = 5
    sentiment_check_interval_seconds: int = 60

    # Environment
    environment: str = "development"
    debug: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False

    def get_admin_ids(self) -> list[int]:
        """Parse admin IDs from comma-separated string."""
        return [int(uid.strip()) for uid in self.bot_admin_ids.split(",")]
