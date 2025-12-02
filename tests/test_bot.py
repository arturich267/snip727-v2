"""Tests for bot module."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update
from telegram.ext import ContextTypes

from src.snip727.bot.main import start, status


@pytest.mark.asyncio
async def test_start_command() -> None:
    """Test /start command."""
    update = MagicMock(spec=Update)
    update.message = AsyncMock()
    update.effective_user.id = 123456
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

    await start(update, context)

    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "snip727-v2" in call_args


@pytest.mark.asyncio
async def test_status_command() -> None:
    """Test /status command."""
    update = MagicMock(spec=Update)
    update.message = AsyncMock()
    update.effective_user.id = 123456
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

    await status(update, context)

    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "Bot is running" in call_args
