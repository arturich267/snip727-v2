"""Tests for imports and module availability."""


def test_import_core() -> None:
    """Test core module imports."""
    from src.snip727.core import config
    assert config is not None


def test_import_bot() -> None:
    """Test bot module imports."""
    from src.snip727.bot import main
    assert main is not None


def test_import_db() -> None:
    """Test db module imports."""
    from src.snip727 import db
    assert db is not None


def test_import_web3() -> None:
    """Test web3 module imports."""
    from src.snip727 import web3
    assert web3 is not None
