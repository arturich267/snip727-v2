"""Sentiment analysis service using rubert-base-cased-sentiment model."""
from typing import Literal
from transformers import pipeline

_sentiment_pipeline = None


def get_sentiment_pipeline():
    """Get or create sentiment analysis pipeline."""
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        _sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="cointegrated/rubert-base-cased-sentence-sentiment"
        )
    return _sentiment_pipeline


def analyze_sentiment(text: str) -> Literal[-1, 0, 1]:
    """
    Analyze sentiment of text and return score.
    
    Args:
        text: Text to analyze
        
    Returns:
        +1 for positive sentiment (score > 0.6)
        -1 for negative sentiment (score < 0.4)
        0 for neutral sentiment
    """
    if not text or not text.strip():
        return 0
    
    sentiment_model = get_sentiment_pipeline()
    result = sentiment_model(text[:512])[0]
    
    label = result["label"].lower()
    score = result["score"]
    
    if label == "positive" and score > 0.6:
        return 1
    elif label == "negative" and score > 0.6:
        return -1
    else:
        return 0
