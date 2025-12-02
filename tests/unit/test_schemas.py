"""Test Pydantic schemas."""

import pytest

from src.schemas.models import PairSchema, SentimentSchema, TradeSchema


@pytest.mark.unit
def test_pair_schema_validation() -> None:
    """Test PairSchema validation."""
    data = {
        "pair_address": "0x1234567890123456789012345678901234567890",
        "token0": "0x0000000000000000000000000000000000000001",
        "token1": "0x0000000000000000000000000000000000000002",
        "pool_type": "V2",
    }

    pair = PairSchema(**data)

    assert pair.pair_address == "0x1234567890123456789012345678901234567890"
    assert pair.pool_type == "V2"


@pytest.mark.unit
def test_trade_schema_validation() -> None:
    """Test TradeSchema validation."""
    data = {
        "pair_address": "0x1234567890123456789012345678901234567890",
        "tx_hash": "0x" + "a" * 64,
        "amount_in": 1.0,
        "amount_out": 2.0,
        "slippage": 0.01,
        "status": "completed",
    }

    trade = TradeSchema(**data)

    assert trade.amount_in == 1.0
    assert trade.status == "completed"


@pytest.mark.unit
def test_sentiment_schema_validation() -> None:
    """Test SentimentSchema validation."""
    data = {
        "pair_address": "0x1234567890123456789012345678901234567890",
        "score": 0.75,
        "source": "twitter",
    }

    sentiment = SentimentSchema(**data)

    assert sentiment.score == 0.75
    assert -1.0 <= sentiment.score <= 1.0


@pytest.mark.unit
def test_sentiment_schema_score_range() -> None:
    """Test SentimentSchema score validation."""
    with pytest.raises(ValueError):
        SentimentSchema(
            pair_address="0x1234567890123456789012345678901234567890",
            score=1.5,
            source="twitter",
        )
