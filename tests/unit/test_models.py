"""Test database models."""

import pytest


@pytest.mark.unit
def test_pair_model() -> None:
    """Test Pair model creation."""
    from src.db.models import Pair

    pair = Pair(
        pair_address="0x1234567890123456789012345678901234567890",
        token0="0x0000000000000000000000000000000000000001",
        token1="0x0000000000000000000000000000000000000002",
        pool_type="V2",
        liquidity=100000.0,
    )

    assert pair.pair_address == "0x1234567890123456789012345678901234567890"
    assert pair.pool_type == "V2"
    assert pair.liquidity == 100000.0


@pytest.mark.unit
def test_trade_model() -> None:
    """Test Trade model creation."""
    from src.db.models import Trade

    trade = Trade(
        pair_address="0x1234567890123456789012345678901234567890",
        tx_hash="0x" + "a" * 64,
        amount_in=1.0,
        amount_out=2.0,
        slippage=0.01,
        status="completed",
    )

    assert trade.amount_in == 1.0
    assert trade.amount_out == 2.0
    assert trade.status == "completed"


@pytest.mark.unit
def test_sentiment_model() -> None:
    """Test Sentiment model creation."""
    from src.db.models import Sentiment

    sentiment = Sentiment(
        pair_address="0x1234567890123456789012345678901234567890",
        score=0.75,
        source="twitter",
    )

    assert sentiment.score == 0.75
    assert sentiment.source == "twitter"
