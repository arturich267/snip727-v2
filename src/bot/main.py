import structlog
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from src.bot.handlers import router
from src.core.config import Settings

logger = structlog.get_logger(__name__)


class BotManager:
    """Telegram bot manager."""

    def __init__(self, settings: Settings) -> None:
        """Initialize bot manager."""
        self.settings = settings
        self.bot = Bot(token=settings.bot_token)
        self.dp = Dispatcher()
        self.dp.include_router(router)

    async def setup_commands(self) -> None:
        """Set up bot commands."""
        commands = [
            BotCommand(command="start", description="Start bot"),
            BotCommand(command="status", description="Show bot status"),
            BotCommand(command="help", description="Show help"),
        ]
        await self.bot.set_my_commands(commands)
        logger.info("bot_commands_set")

    async def start(self) -> None:
        """Start polling."""
        logger.info("bot_starting")
        await self.setup_commands()
        await self.dp.start_polling(self.bot)

    async def stop(self) -> None:
        """Stop bot."""
        logger.info("bot_stopping")
        await self.bot.session.close()
