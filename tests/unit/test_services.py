"""Test service modules."""

import pytest

from src.services.monitoring import MonitoringService
from src.services.sentiment import SentimentService
from src.services.strategy import StrategyService
from src.services.trading import TradingService


@pytest.mark.unit
async def test_monitoring_service() -> None:
    """Test monitoring service."""
    service = MonitoringService()

    await service.start_monitoring()
    await service.stop_monitoring()


@pytest.mark.unit
async def test_sentiment_service() -> None:
    """Test sentiment service."""
    service = SentimentService()
    pair_address = "0x1234567890123456789012345678901234567890"

    score = await service.analyze_sentiment(pair_address)

    assert isinstance(score, float)
    assert -1.0 <= score <= 1.0


@pytest.mark.unit
async def test_strategy_service() -> None:
    """Test strategy service."""
    service = StrategyService()
    pair_address = "0x1234567890123456789012345678901234567890"

    result = await service.evaluate_trade_opportunity(pair_address)

    assert isinstance(result, bool)


@pytest.mark.unit
async def test_trading_service() -> None:
    """Test trading service."""
    service = TradingService()
    pair_address = "0x1234567890123456789012345678901234567890"

    tx_hash = await service.execute_trade(pair_address, 1.0)

    assert isinstance(tx_hash, str)
    assert tx_hash.startswith("0x")
