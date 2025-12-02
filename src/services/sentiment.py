import structlog


class SentimentService:
    """Sentiment analysis service."""

    def __init__(self) -> None:
        """Initialize sentiment service."""
        self.logger = structlog.get_logger(self.__class__.__name__)

    async def analyze_sentiment(self, pair_address: str) -> float:
        """Analyze sentiment for a pair."""
        self.logger.info("analyzing_sentiment", pair_address=pair_address)
        return 0.0
