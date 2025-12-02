"""Main entry point for Snip727-V2 bot."""

import asyncio

import structlog

from src.bot.main import BotManager
from src.core.config import Settings
from src.utils.logger import setup_logging

logger = structlog.get_logger(__name__)


async def main() -> None:
    """Main async function."""
    settings = Settings()
    setup_logging(settings)

    logger.info("snip727_v2_starting", version="0.1.0")

    bot_manager = BotManager(settings)
    await bot_manager.start()


if __name__ == "__main__":
    asyncio.run(main())
