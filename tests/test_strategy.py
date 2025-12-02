"""Tests for N-of-4 strategy."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from snip727.services.strategy import Nof4Strategy, Signal
from snip727.web3.monitor import PoolEvent


@pytest.fixture
def strategy():
    """Create strategy instance."""
    return Nof4Strategy()


@pytest.fixture
def sample_pool_event():
    """Create sample pool event."""
    return PoolEvent(
        event_type="v2_pair_created",
        pool_address="0x123456789012345678901234567890",
        token0="0x1111111111111111111111111111111",
        token1="0x2222222222222222222222222222222",
        data={"all_pairs_length": 1000},
        block_number=12345,
        transaction_hash="0xabcdef1234567890abcdef1234567890abcdef1234567890",
    )


@pytest.mark.asyncio
async def test_process_event_new_pool(strategy, sample_pool_event):
    """Test processing new pool event."""
    initial_signals_count = len(strategy.signals)
    
    await strategy.process_event(sample_pool_event)
    
    assert len(strategy.signals) == initial_signals_count + 1
    assert strategy.signals[-1].signal_type == "new_pool"
    assert strategy.signals[-1].pool_address == sample_pool_event.pool_address


@pytest.mark.asyncio
async def test_process_event_liquidity_spike(strategy):
    """Test processing liquidity spike event."""
    event = PoolEvent(
        event_type="liquidity_spike",
        pool_address="0x123456789012345678901234567890",
        token0="",
        token1="",
        data={"estimated_usd": 50000},
        block_number=12345,
        transaction_hash="0xabcdef1234567890abcdef1234567890abcdef1234567890",
    )
    
    await strategy.process_event(event)
    
    assert len(strategy.signals) == 1
    assert strategy.signals[0].signal_type == "liquidity_spike"
    assert strategy.signals[0].confidence == 0.7  # 0.5 + 50000/100000 = 1.0, capped at 0.9


@pytest.mark.asyncio
async def test_process_event_whale_buy(strategy):
    """Test processing whale buy event."""
    event = PoolEvent(
        event_type="whale_buy",
        pool_address="0x123456789012345678901234567890",
        token0="",
        token1="",
        data={"swap_value_usd": 100000},
        block_number=12345,
        transaction_hash="0xabcdef1234567890abcdef1234567890abcdef1234567890",
    )
    
    await strategy.process_event(event)
    
    assert len(strategy.signals) == 1
    assert strategy.signals[0].signal_type == "whale_buy"
    assert strategy.signals[0].confidence == 0.85  # 0.6 + 100000/200000 = 1.1, capped at 0.95


@pytest.mark.asyncio
async def test_check_for_alerts_insufficient_signals(strategy):
    """Test alert check with insufficient signals."""
    # Add only 2 signals (less than required 3)
    pool_address = "0x123456789012345678901234567890"
    
    for i in range(2):
        signal = Signal(
            signal_type="liquidity_spike",
            pool_address=pool_address,
            confidence=0.8,
            data={},
            timestamp=datetime.now(),
        )
        strategy.signals.append(signal)
    
    # Mock callback
    callback = AsyncMock()
    strategy.add_alert_callback(callback)
    
    await strategy._check_for_alerts(pool_address)
    
    # Should not trigger alert
    callback.assert_not_called()


@pytest.mark.asyncio
async def test_check_for_alerts_sufficient_signals(strategy):
    """Test alert check with sufficient signals."""
    pool_address = "0x123456789012345678901234567890"
    
    # Add 3 signals of same type
    for i in range(3):
        signal = Signal(
            signal_type="liquidity_spike",
            pool_address=pool_address,
            confidence=0.8,
            data={},
            timestamp=datetime.now(),
        )
        strategy.signals.append(signal)
    
    # Mock sentiment analyzer
    with patch('snip727.services.strategy.get_sentiment_analyzer') as mock_get_analyzer:
        mock_analyzer = Mock()
        mock_analyzer.analyze_crypto_sentiment = AsyncMock(return_value={
            "sentiment": 1,
            "confidence": 0.8,
        })
        mock_get_analyzer.return_value = mock_analyzer
        
        # Mock callback
        callback = AsyncMock()
        strategy.add_alert_callback(callback)
        
        await strategy._check_for_alerts(pool_address)
        
        # Should trigger alert
        callback.assert_called_once()
        alert_data = callback.call_args[0][0]
        
        assert alert_data["pool_address"] == pool_address
        assert alert_data["signal_type"] == "liquidity_spike"
        assert alert_data["signal_count"] == 3


def test_get_recent_signals(strategy):
    """Test getting recent signals."""
    pool_address = "0x123456789012345678901234567890"
    
    # Add signals with different timestamps
    now = datetime.now()
    old_time = now - timedelta(hours=25)  # Older than 24 hours
    
    # Old signal (should not be included)
    old_signal = Signal(
        signal_type="new_pool",
        pool_address=pool_address,
        confidence=0.7,
        data={},
        timestamp=old_time,
    )
    strategy.signals.append(old_signal)
    
    # Recent signal (should be included)
    recent_signal = Signal(
        signal_type="liquidity_spike",
        pool_address=pool_address,
        confidence=0.8,
        data={},
        timestamp=now,
    )
    strategy.signals.append(recent_signal)
    
    recent_signals = strategy.get_recent_signals()
    
    assert len(recent_signals) == 1
    assert recent_signals[0]["type"] == "liquidity_spike"


def test_get_pool_stats(strategy):
    """Test getting pool statistics."""
    pool_address = "0x123456789012345678901234567890"
    
    # Add some data
    strategy.event_history[pool_address] = [Mock(), Mock()]  # 2 events
    
    # Add signals
    for signal_type in ["new_pool", "liquidity_spike", "liquidity_spike"]:
        signal = Signal(
            signal_type=signal_type,
            pool_address=pool_address,
            confidence=0.8,
            data={},
            timestamp=datetime.now(),
        )
        strategy.signals.append(signal)
    
    stats = strategy.get_pool_stats()
    
    assert stats["monitored_pools"] == 1
    assert stats["total_events"] == 2
    assert stats["total_signals"] == 3
    assert stats["signal_breakdown"]["new_pool"] == 1
    assert stats["signal_breakdown"]["liquidity_spike"] == 2