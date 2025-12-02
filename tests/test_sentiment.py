"""Tests for sentiment analysis."""
import pytest
from unittest.mock import Mock, patch

from snip727.services.sentiment import SentimentAnalyzer


@pytest.fixture
def sentiment_analyzer():
    """Create sentiment analyzer instance."""
    return SentimentAnalyzer()


@pytest.mark.asyncio
async def test_sentiment_analyzer_initialization(sentiment_analyzer):
    """Test sentiment analyzer initialization."""
    # Should not be initialized initially
    assert not sentiment_analyzer._initialized
    
    # Mock model loading
    with patch('snip727.services.sentiment.AutoTokenizer') as mock_tokenizer, \
         patch('snip727.services.sentiment.AutoModelForSequenceClassification') as mock_model:
        
        mock_tokenizer.from_pretrained.return_value = Mock()
        mock_model.from_pretrained.return_value = Mock()
        
        # Initialize
        sentiment_analyzer._initialize_model()
        
        # Should be initialized
        assert sentiment_analyzer._initialized
        mock_tokenizer.from_pretrained.assert_called_once_with("cointegrated/rubert-base-cased-sentence-sentiment")
        mock_model.from_pretrained.assert_called_once_with("cointegrated/rubert-base-cased-sentence-sentiment")


@pytest.mark.asyncio
async def test_analyze_sentiment_empty_text(sentiment_analyzer):
    """Test sentiment analysis with empty text."""
    result = await sentiment_analyzer.analyze_sentiment("")
    assert result == 0
    
    result = await sentiment_analyzer.analyze_sentiment("   ")
    assert result == 0


@pytest.mark.asyncio
async def test_analyze_sentiment_mocked(sentiment_analyzer):
    """Test sentiment analysis with mocked model."""
    # Mock the model and tokenizer
    with patch.object(sentiment_analyzer, '_initialize_model'), \
         patch.object(sentiment_analyzer, '_analyze_sync') as mock_analyze:
        
        mock_analyze.return_value = 1  # Positive sentiment
        
        result = await sentiment_analyzer.analyze_sentiment("Great token!")
        
        assert result == 1
        mock_analyze.assert_called_once_with("Great token!")


@pytest.mark.asyncio
async def test_analyze_crypto_sentiment_no_events(sentiment_analyzer):
    """Test crypto sentiment analysis with no events."""
    result = await sentiment_analyzer.analyze_crypto_sentiment("BTC", [])
    
    expected = {
        "sentiment": 0,
        "confidence": 0.0,
        "texts": [],
        "sentiment_breakdown": {"positive": 0, "negative": 0, "neutral": 0}
    }
    
    assert result == expected


@pytest.mark.asyncio
async def test_analyze_crypto_sentiment_with_events(sentiment_analyzer):
    """Test crypto sentiment analysis with events."""
    # Mock PoolEvent
    class MockPoolEvent:
        def __init__(self, event_type, data):
            self.event_type = event_type
            self.data = data
    
    events = [
        MockPoolEvent("v2_pair_created", {}),
        MockPoolEvent("liquidity_spike", {"estimated_usd": 50000}),
        MockPoolEvent("whale_buy", {"swap_value_usd": 100000}),
    ]
    
    with patch.object(sentiment_analyzer, 'analyze_sentiment') as mock_analyze:
        # Mock different sentiments for different texts
        mock_analyze.side_effect = [1, 1, 0]  # positive, positive, neutral
        
        result = await sentiment_analyzer.analyze_crypto_sentiment("TOKEN", events)
        
        assert result["sentiment"] == 1  # Overall positive
        assert result["confidence"] == 2/3  # 2 out of 3 positive
        assert len(result["texts"]) == 3
        assert result["sentiment_breakdown"]["positive"] == 2
        assert result["sentiment_breakdown"]["neutral"] == 1
        assert result["sentiment_breakdown"]["negative"] == 0