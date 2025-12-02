"""Test configuration module."""

import os

import pytest

from src.core.config import Settings


@pytest.mark.unit
def test_settings_load() -> None:
    """Test loading settings from environment."""
    os.environ["BOT_TOKEN"] = "test_token_123"
    os.environ["BOT_ADMIN_IDS"] = "123456,789012"

    settings = Settings()

    assert settings.bot_token == "test_token_123"
    assert settings.bot_admin_ids == "123456,789012"
    assert settings.web3_chain_id == 8453


@pytest.mark.unit
def test_get_admin_ids() -> None:
    """Test parsing admin IDs."""
    os.environ["BOT_TOKEN"] = "test_token"
    os.environ["BOT_ADMIN_IDS"] = "123,456,789"

    settings = Settings()
    admin_ids = settings.get_admin_ids()

    assert admin_ids == [123, 456, 789]


@pytest.mark.unit
def test_default_values() -> None:
    """Test default configuration values."""
    os.environ["BOT_TOKEN"] = "test_token"

    settings = Settings()

    assert settings.environment == "development"
    assert settings.debug is False
    assert settings.min_liquidity_usd == 5000.0
    assert settings.slippage_tolerance == 0.01
