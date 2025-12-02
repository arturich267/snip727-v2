"""Tests for configuration module."""
from src.snip727.core.config import get_settings


def test_get_settings() -> None:
    """Test getting settings."""
    settings = get_settings()
    assert settings is not None
    assert hasattr(settings, "telegram_token")
    assert hasattr(settings, "database_url")
    assert hasattr(settings, "redis_url")
    assert hasattr(settings, "log_level")
