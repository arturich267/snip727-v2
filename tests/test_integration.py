"""Integration tests for the complete system."""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from snip727.services.strategy import get_strategy
from snip727.services.sentiment import get_sentiment_analyzer
from snip727.web3.monitor import PoolEvent


@pytest.mark.asyncio
async def test_full_signal_pipeline():
    """Test complete signal generation pipeline."""
    # Get strategy instance
    strategy = get_strategy()
    analyzer = get_sentiment_analyzer()
    
    # Mock sentiment analysis
    with patch.object(analyzer, 'analyze_crypto_sentiment') as mock_sentiment:
        mock_sentiment.return_value = {
            "sentiment": 1,
            "confidence": 0.8,
            "texts": ["New liquidity pool launched", "Major liquidity addition"],
            "sentiment_breakdown": {"positive": 2, "negative": 0, "neutral": 0}
        }
        
        # Mock alert callback
        alert_callback = AsyncMock()
        strategy.add_alert_callback(alert_callback)
        
        pool_address = "0x123456789012345678901234567890"
        
        # Create 3 liquidity spike events (should trigger alert)
        for i in range(3):
            event = PoolEvent(
                event_type="liquidity_spike",
                pool_address=pool_address,
                token0="0x1111111111111111111111111111",
                token1="0x2222222222222222222222222",
                data={"estimated_usd": 50000 + i * 10000},
                block_number=12345 + i,
                transaction_hash=f"0xabcdef12345678{i:04d}",
            )
            
            await strategy.process_event(event)
        
        # Check if alert was triggered
        alert_callback.assert_called_once()
        alert_data = alert_callback.call_args[0][0]
        
        assert alert_data["pool_address"] == pool_address
        assert alert_data["signal_type"] == "liquidity_spike"
        assert alert_data["signal_count"] == 3
        assert alert_data["confidence"] >= 0.8
        assert alert_data["sentiment"]["sentiment"] == 1


@pytest.mark.asyncio
async def test_sentiment_analyzer_initialization():
    """Test sentiment analyzer can be initialized."""
    analyzer = get_sentiment_analyzer()
    
    # Should be able to call without error (mocked)
    with patch('snip727.services.sentiment.AutoTokenizer') as mock_tokenizer, \
         patch('snip727.services.sentiment.AutoModelForSequenceClassification') as mock_model:
        
        mock_tokenizer.from_pretrained.return_value = Mock()
        mock_model.from_pretrained.return_value = Mock()
        
        # Test initialization
        analyzer._initialize_model()
        assert analyzer._initialized
        mock_tokenizer.from_pretrained.assert_called_once_with("cointegrated/rubert-base-cased-sentence-sentiment")
        mock_model.from_pretrained.assert_called_once_with("cointegrated/rubert-base-cased-sentence-sentiment")


@pytest.mark.asyncio
async def test_web3_client_creation():
    """Test Web3 client can be created."""
    with patch('snip727.web3.client.redis') as mock_redis, \
         patch('snip727.web3.client.Web3') as mock_web3, \
         patch('snip727.web3.client.aiohttp') as mock_aiohttp:
        
        # Mock Redis
        mock_redis.from_url.return_value = Mock()
        mock_redis.from_url.return_value.ping = AsyncMock()
        
        # Mock Web3
        mock_w3_instance = Mock()
        mock_w3_instance.eth.chain_id = AsyncMock(return_value=1)
        mock_web3.return_value = mock_w3_instance
        
        # Mock aiohttp
        mock_session = Mock()
        mock_aiohttp.ClientSession.return_value = mock_session
        
        from snip727.web3.client import AsyncWeb3Client
        
        client = AsyncWeb3Client()
        await client.initialize()
        
        assert client.redis_client is not None
        assert client.w3 is not None


def test_imports():
    """Test all imports work correctly."""
    # These should not raise ImportError
    from snip727.core.config import get_settings
    from snip727.db.models import Pool, TradeEvent, SentimentScore, Signal, AlertLog
    from snip727.services.sentiment import get_sentiment_analyzer
    from snip727.services.strategy import get_strategy
    from snip727.web3.client import get_web3_client
    from snip727.web3.monitor import UniswapMonitor, PoolEvent
    from snip727.bot.main import start, status, pools, signals, stats
    
    # Test settings can be loaded
    settings = get_settings()
    assert hasattr(settings, 'telegram_token')
    assert hasattr(settings, 'uniswap_v2_factory')
    assert hasattr(settings, 'min_liquidity_usd')