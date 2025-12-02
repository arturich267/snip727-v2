"""Test logging setup."""

import os

import pytest


@pytest.mark.unit
def test_logger_setup() -> None:
    """Test logger setup."""
    os.environ["BOT_TOKEN"] = "test_token"

    from src.core.config import Settings
    from src.utils.logger import setup_logging

    settings = Settings()

    # Should not raise any exception
    setup_logging(settings)


@pytest.mark.unit
def test_logger_setup_with_debug() -> None:
    """Test logger setup with debug mode."""
    os.environ["BOT_TOKEN"] = "test_token"
    os.environ["DEBUG"] = "true"

    from src.core.config import Settings
    from src.utils.logger import setup_logging

    settings = Settings()

    # Should not raise any exception
    setup_logging(settings)
