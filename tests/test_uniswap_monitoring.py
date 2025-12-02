"""Tests for Uniswap monitoring functionality."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from snip727.web3.client import AsyncWeb3Client
from snip727.web3.monitor import UniswapMonitor
from snip727.services.sentiment import SentimentAnalyzer
from snip727.services.strategy import StrategyService
from snip727.db.models import Pool, StrategySignal, SentimentScore


@pytest.fixture
def mock_web3_client():
    """Mock Web3 client."""
    client = AsyncWeb3Client()
    client.w3 = MagicMock()
    client.w3.is_connected.return_value = True
    client.w3.eth.block_number = 12345
    client.redis = AsyncMock()
    client.session = AsyncMock()
    return client


@pytest.fixture
def mock_settings():
    """Mock settings."""
    from snip727.core.config import Settings
    
    settings = Settings()
    settings.base_rpc_urls = ["wss://mock.rpc"]
    settings.uniswap_v2_factory = "0x1234567890123456789012345678901234567890"
    settings.uniswap_v3_factory = "0x0987654321098765432109876543210987654321"
    settings.liquidity_spike_threshold = 5.0
    settings.whale_buy_threshold = 0.005
    settings.new_pool_blocks_threshold = 15
    settings.sentiment_threshold = 0.6
    settings.strategy_signals_required = 3
    
    return settings


@pytest.mark.asyncio
async def test_web3_client_initialization():
    """Test Web3 client initialization."""
    client = AsyncWeb3Client()
    
    with patch('redis.from_url') as mock_redis:
        mock_redis.return_value = AsyncMock()
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value = AsyncMock()
            
            with patch.object(client, '_connect_to_rpc') as mock_connect:
                mock_connect.return_value = None
                
                await client.initialize()
                
                mock_redis.assert_called_once()
                mock_session.assert_called_once()
                mock_connect.assert_called_once()


@pytest.mark.asyncio
async def test_sentiment_analyzer_simple():
    """Test sentiment analyzer simple fallback."""
    analyzer = SentimentAnalyzer()
    analyzer.model = None  # Force fallback mode
    
    # Test positive sentiment
    score, confidence = await analyzer.analyze_text("This is good and awesome 🚀")
    assert score > 0
    assert confidence > 0
    
    # Test negative sentiment
    score, confidence = await analyzer.analyze_text("This is bad and terrible 💩")
    assert score < 0
    assert confidence > 0
    
    # Test neutral sentiment
    score, confidence = await analyzer.analyze_text("This is a normal text")
    assert score == 0.0
    assert confidence > 0


@pytest.mark.asyncio
async def test_strategy_service_signal_evaluation():
    """Test strategy service signal evaluation."""
    service = StrategyService()
    
    # Mock current block
    with patch.object(service, '_get_current_block', return_value=1000):
        # Test signal validity
        signal = StrategySignal(
            pool_address="0x1234567890123456789012345678901234567890",
            signal_type="new_pool",
            signal_value=1.0,
            block_number=990  # Within threshold
        )
        
        is_valid = await service._is_signal_valid(signal, 1000)
        assert is_valid == True
        
        # Test expired signal
        signal.block_number = 950  # Outside threshold
        is_valid = await service._is_signal_valid(signal, 1000)
        assert is_valid == False


@pytest.mark.asyncio
async def test_pool_creation_signal():
    """Test pool creation generates signal."""
    monitor = UniswapMonitor()
    
    # Mock event
    mock_event = MagicMock()
    mock_event.args.pair = "0x1234567890123456789012345678901234567890"
    mock_event.args.token0 = "0x1111111111111111111111111111111111111111"
    mock_event.args.token1 = "0x2222222222222222222222222222222222222222"
    mock_event.blockNumber = 12345
    mock_event.timestamp = 1634567890
    
    with patch('snip727.db.get_session') as mock_session:
        # Mock the async generator properly
        called_add = []
        called_commit = []
        
        class MockSession:
            def __init__(self):
                pass
                
            def add(self, obj):
                called_add.append(obj)
                
            async def commit(self):
                called_commit.append(True)
                
            async def get(self, model, id):
                return None
                
            async def __aenter__(self):
                return self
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
        
        async def mock_session_gen():
            yield MockSession()
            
        mock_session.return_value = mock_session_gen()
        
        await monitor._save_pool(
            address=mock_event.args.pair,
            token0=mock_event.args.token0,
            token1=mock_event.args.token1,
            fee=None,
            version="V2",
            factory="0x3333333333333333333333333333333333333333",
            block_number=mock_event.blockNumber,
            block_timestamp=datetime.fromtimestamp(mock_event.timestamp)
        )
        
        # Verify session.add was called for both Pool and StrategySignal
        assert len(called_add) == 2


@pytest.mark.asyncio
async def test_alert_score_calculation():
    """Test alert score calculation."""
    service = StrategyService()
    
    # Test signals with different weights
    signals = {
        'new_pool': {'value': 1.0},
        'liquidity_spike': {'value': 10.0},
        'whale_buy': {'value': 1.0},
        'sentiment': {'value': 0.8}
    }
    
    score = service._calculate_alert_score(signals)
    assert 0 <= score <= 1
    
    # Test with only some signals
    partial_signals = {
        'new_pool': {'value': 1.0},
        'sentiment': {'value': 0.5}
    }
    
    partial_score = service._calculate_alert_score(partial_signals)
    assert partial_score < score  # Should be lower with fewer signals


@pytest.mark.asyncio
async def test_token_address_extraction():
    """Test token address extraction from text."""
    analyzer = SentimentAnalyzer()
    
    text = "Check out this token 0x1234567890123456789012345678901234567890 and also 0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"
    
    addresses = await analyzer.extract_token_mentions(text)
    
    assert len(addresses) == 2
    assert "0x1234567890123456789012345678901234567890".lower() in addresses
    assert "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd".lower() in addresses


@pytest.mark.asyncio
async def test_get_pool_sentiment():
    """Test getting pool sentiment score."""
    analyzer = SentimentAnalyzer()
    
    with patch('snip727.db.get_session') as mock_session:
        # Mock database query result
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0.75
        
        class MockSession:
            async def execute(self, query):
                return mock_result
                
            async def __aenter__(self):
                return self
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
        
        async def mock_session_gen():
            yield MockSession()
            
        mock_session.return_value = mock_session_gen()
        
        score = await analyzer.get_pool_sentiment("0x1234567890123456789012345678901234567890")
        
        assert score == 0.75


def test_models_creation():
    """Test database model creation."""
    # Test Pool model
    pool = Pool(
        address="0x1234567890123456789012345678901234567890",
        token0="0x1111111111111111111111111111111111111111",
        token1="0x2222222222222222222222222222222222222222",
        version="V2",
        factory="0x3333333333333333333333333333333333333333",
        block_number=12345,
        block_timestamp=datetime.utcnow()
    )
    
    assert pool.address == "0x1234567890123456789012345678901234567890"
    assert pool.version == "V2"
    
    # Test StrategySignal model
    signal = StrategySignal(
        pool_address="0x1234567890123456789012345678901234567890",
        signal_type="new_pool",
        signal_value=1.0,
        is_active=True
    )
    
    assert signal.signal_type == "new_pool"
    assert signal.is_active == True
    
    # Test SentimentScore model
    sentiment = SentimentScore(
        source="test",
        content="Test content",
        score=0.8,
        confidence=0.9,
        timestamp=datetime.utcnow()
    )
    
    assert sentiment.score == 0.8
    assert sentiment.confidence == 0.9