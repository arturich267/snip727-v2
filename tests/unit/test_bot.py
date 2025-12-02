"""Test bot module."""

import os

import pytest


@pytest.mark.unit
def test_bot_manager_initialization() -> None:
    """Test bot manager initialization."""
    # Valid Telegram bot token format: <bot_id>:<token>
    os.environ["BOT_TOKEN"] = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"

    from src.bot.main import BotManager
    from src.core.config import Settings

    settings = Settings()
    manager = BotManager(settings)

    assert manager.bot is not None
    assert manager.dp is not None
    assert manager.settings == settings


@pytest.mark.unit
def test_keyboards() -> None:
    """Test keyboard generation."""
    from src.bot.keyboards import get_main_keyboard

    keyboard = get_main_keyboard()

    assert keyboard is not None
    assert len(keyboard.inline_keyboard) == 3
    assert keyboard.inline_keyboard[0][0].text == "📊 Status"
    assert keyboard.inline_keyboard[1][0].text == "⚙️ Settings"
    assert keyboard.inline_keyboard[2][0].text == "📈 Stats"
