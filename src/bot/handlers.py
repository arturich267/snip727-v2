import structlog
from aiogram import Router
from aiogram.types import Message

from src.bot.keyboards import get_main_keyboard
from src.core.config import Settings

logger = structlog.get_logger(__name__)

router = Router()
settings = Settings()


@router.message()
async def start_handler(message: Message) -> None:
    """Handle /start command."""
    logger.info("start_command_received", user_id=message.from_user.id)

    welcome_text = (
        "🤖 Snip727-V2 Bot\n\n"
        "Welcome to the DeFi sniping bot for Uniswap V2/V3 on Base chain.\n\n"
        "Choose an option below:"
    )

    await message.answer(welcome_text, reply_markup=get_main_keyboard())
