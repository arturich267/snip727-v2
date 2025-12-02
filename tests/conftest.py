"""Pytest configuration and fixtures."""

import os
from collections.abc import AsyncGenerator

import pytest

# Set environment variables before any imports
if not os.environ.get("BOT_TOKEN"):
    os.environ["BOT_TOKEN"] = "test_token_123456"

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import Settings
from src.db.base import Base
from src.db.models import Pair, Sentiment, Trade  # noqa: F401
from src.web3.client import Web3Client


@pytest.fixture(scope="session")
def event_loop():
    """Event loop for async tests."""
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_settings() -> Settings:
    """Test settings."""
    return Settings()


@pytest.fixture
async def test_db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def test_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest.fixture
async def web3_client(test_settings: Settings) -> Web3Client:
    """Web3 client fixture."""
    return Web3Client(test_settings)
