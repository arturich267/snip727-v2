"""Tests for sentiment analysis service."""
from unittest.mock import MagicMock, patch
from snip727.services.sentiment import analyze_sentiment, get_sentiment_pipeline


def test_get_sentiment_pipeline():
    """Test that pipeline is created and cached."""
    pipeline = get_sentiment_pipeline()
    assert pipeline is not None
    
    pipeline2 = get_sentiment_pipeline()
    assert pipeline is pipeline2


@patch("snip727.services.sentiment.pipeline")
def test_analyze_sentiment_positive(mock_pipeline):
    """Test positive sentiment analysis."""
    mock_model = MagicMock()
    mock_model.return_value = [{"label": "positive", "score": 0.95}]
    mock_pipeline.return_value = mock_model
    
    import snip727.services.sentiment
    snip727.services.sentiment._sentiment_pipeline = None
    
    result = analyze_sentiment("This is great!")
    assert result == 1


@patch("snip727.services.sentiment.pipeline")
def test_analyze_sentiment_negative(mock_pipeline):
    """Test negative sentiment analysis."""
    mock_model = MagicMock()
    mock_model.return_value = [{"label": "negative", "score": 0.85}]
    mock_pipeline.return_value = mock_model
    
    import snip727.services.sentiment
    snip727.services.sentiment._sentiment_pipeline = None
    
    result = analyze_sentiment("This is terrible!")
    assert result == -1


@patch("snip727.services.sentiment.pipeline")
def test_analyze_sentiment_neutral(mock_pipeline):
    """Test neutral sentiment analysis."""
    mock_model = MagicMock()
    mock_model.return_value = [{"label": "neutral", "score": 0.5}]
    mock_pipeline.return_value = mock_model
    
    import snip727.services.sentiment
    snip727.services.sentiment._sentiment_pipeline = None
    
    result = analyze_sentiment("This is okay.")
    assert result == 0


@patch("snip727.services.sentiment.pipeline")
def test_analyze_sentiment_low_confidence_positive(mock_pipeline):
    """Test positive sentiment with low confidence returns neutral."""
    mock_model = MagicMock()
    mock_model.return_value = [{"label": "positive", "score": 0.55}]
    mock_pipeline.return_value = mock_model
    
    import snip727.services.sentiment
    snip727.services.sentiment._sentiment_pipeline = None
    
    result = analyze_sentiment("This is somewhat positive.")
    assert result == 0


@patch("snip727.services.sentiment.pipeline")
def test_analyze_sentiment_low_confidence_negative(mock_pipeline):
    """Test negative sentiment with low confidence returns neutral."""
    mock_model = MagicMock()
    mock_model.return_value = [{"label": "negative", "score": 0.55}]
    mock_pipeline.return_value = mock_model
    
    import snip727.services.sentiment
    snip727.services.sentiment._sentiment_pipeline = None
    
    result = analyze_sentiment("This is somewhat negative.")
    assert result == 0


@patch("snip727.services.sentiment.pipeline")
def test_analyze_sentiment_empty_text(mock_pipeline):
    """Test empty text returns neutral."""
    result = analyze_sentiment("")
    assert result == 0
    mock_pipeline.assert_not_called()


@patch("snip727.services.sentiment.pipeline")
def test_analyze_sentiment_whitespace_only(mock_pipeline):
    """Test whitespace-only text returns neutral."""
    result = analyze_sentiment("   ")
    assert result == 0
    mock_pipeline.assert_not_called()


@patch("snip727.services.sentiment.pipeline")
def test_analyze_sentiment_long_text(mock_pipeline):
    """Test that long text is truncated to 512 characters."""
    mock_model = MagicMock()
    mock_model.return_value = [{"label": "positive", "score": 0.95}]
    mock_pipeline.return_value = mock_model
    
    import snip727.services.sentiment
    snip727.services.sentiment._sentiment_pipeline = None
    
    long_text = "x" * 1000
    result = analyze_sentiment(long_text)
    
    assert result == 1
    mock_model.assert_called_once()
    call_args = mock_model.call_args[0][0]
    assert len(call_args) == 512
