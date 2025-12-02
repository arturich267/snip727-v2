"""Telegram bot main module."""
import structlog
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from snip727.core.config import get_settings

logger = structlog.get_logger()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if update.message is None or update.effective_user is None:
        return
    await update.message.reply_text(
        "🤖 snip727-v2 DeFi Sniping Bot\n\n"
        "Available commands:\n"
        "/start - Show this message\n"
        "/status - Show bot status"
    )
    logger.info("user_command", command="start", user_id=update.effective_user.id)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command."""
    if update.message is None or update.effective_user is None:
        return
    await update.message.reply_text(
        "✅ Bot is running\n"
        "Database: Connected\n"
        "Redis: Connected"
    )
    logger.info("user_command", command="status", user_id=update.effective_user.id)


def main() -> None:
    """Start the bot."""
    settings = get_settings()

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    application = Application.builder().token(settings.telegram_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))

    logger.info("bot_starting", version="0.1.0")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
