"""Integration tests for database."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.integration
async def test_pair_create_and_read(test_session: AsyncSession) -> None:
    """Test creating and reading pair from database."""
    from src.db.models import Pair

    pair = Pair(
        pair_address="0x1234567890123456789012345678901234567890",
        token0="0x0000000000000000000000000000000000000001",
        token1="0x0000000000000000000000000000000000000002",
        pool_type="V2",
        liquidity=100000.0,
    )

    test_session.add(pair)
    await test_session.commit()
    await test_session.refresh(pair)

    assert pair.id is not None

    result = await test_session.execute(
        select(Pair).where(Pair.pair_address == "0x1234567890123456789012345678901234567890")
    )
    fetched_pair = result.scalar_one_or_none()

    assert fetched_pair is not None
    assert fetched_pair.pool_type == "V2"
    assert fetched_pair.liquidity == 100000.0
