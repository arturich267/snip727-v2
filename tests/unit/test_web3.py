"""Test Web3 client."""

import os

import pytest

from src.web3.client import Web3Client


@pytest.mark.unit
def test_web3_client_initialization() -> None:
    """Test Web3 client initialization."""
    os.environ["BOT_TOKEN"] = "test_token"

    from src.core.config import Settings

    settings = Settings()
    client = Web3Client(settings)

    assert client.settings == settings
    assert client.w3 is not None


@pytest.mark.unit
def test_is_address() -> None:
    """Test address validation."""
    os.environ["BOT_TOKEN"] = "test_token"

    from src.core.config import Settings

    settings = Settings()
    client = Web3Client(settings)

    assert client.is_address("0x1234567890123456789012345678901234567890")
    assert not client.is_address("invalid")


@pytest.mark.unit
def test_to_checksum_address() -> None:
    """Test checksum address conversion."""
    os.environ["BOT_TOKEN"] = "test_token"

    from src.core.config import Settings

    settings = Settings()
    client = Web3Client(settings)

    checksum = client.to_checksum_address("0xb794f5ea0ba39494ce839613fffba74279579268")

    assert checksum.startswith("0x")
    assert len(checksum) == 42
