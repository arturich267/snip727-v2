"""Offline ruBERT sentiment analysis service."""
import asyncio
import structlog
from typing import Dict, Optional
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import threading

logger = structlog.get_logger()


class SentimentAnalyzer:
    """Offline sentiment analysis using ruBERT model."""
    
    def __init__(self):
        self.model_name = "cointegrated/rubert-base-cased-sentence-sentiment"
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._initialized = False
        self._lock = threading.Lock()
    
    def _initialize_model(self) -> None:
        """Initialize model (thread-safe)."""
        if self._initialized:
            return
        
        with self._lock:
            if self._initialized:
                return
            
            try:
                logger.info("initializing_sentiment_model", model=self.model_name)
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
                self.model.to(self.device)
                self.model.eval()
                self._initialized = True
                logger.info("sentiment_model_initialized", device=str(self.device))
            except Exception as e:
                logger.error("sentiment_model_init_failed", error=str(e))
                raise
    
    async def analyze_sentiment(self, text: str) -> int:
        """Analyze sentiment of text.
        
        Returns:
            -1 for negative, 0 for neutral, +1 for positive
        """
        if not text or not text.strip():
            return 0
        
        # Initialize model if not done
        if not self._initialized:
            # Run initialization in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._initialize_model)
        
        try:
            # Run inference in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._analyze_sync, text)
            return result
        except Exception as e:
            logger.error("sentiment_analysis_failed", text=text[:100], error=str(e))
            return 0
    
    def _analyze_sync(self, text: str) -> int:
        """Synchronous sentiment analysis."""
        try:
            # Tokenize text
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                predicted_class = torch.argmax(predictions, dim=-1).item()
            
            # Convert to sentiment score
            # Model classes: 0=negative, 1=neutral, 2=positive
            if predicted_class == 0:
                return -1
            elif predicted_class == 2:
                return 1
            else:
                return 0
                
        except Exception as e:
            logger.error("sync_sentiment_analysis_failed", error=str(e))
            return 0
    
    async def analyze_crypto_sentiment(self, token_symbol: str, events: list) -> Dict[str, any]:
        """Analyze sentiment for crypto-related events."""
        sentiment_texts = []
        
        # Create text representations of events
        for event in events:
            if event.event_type == "v2_pair_created":
                sentiment_texts.append(f"New trading pair created for {token_symbol}")
            elif event.event_type == "v3_pool_created":
                sentiment_texts.append(f"New liquidity pool launched for {token_symbol}")
            elif event.event_type == "liquidity_spike":
                usd_value = event.data.get("estimated_usd", 0)
                sentiment_texts.append(f"Major liquidity addition of ${usd_value:,.0f} for {token_symbol}")
            elif event.event_type == "whale_buy":
                swap_value = event.data.get("swap_value_usd", 0)
                sentiment_texts.append(f"Large whale purchase of ${swap_value:,.0f} for {token_symbol}")
        
        if not sentiment_texts:
            return {"sentiment": 0, "confidence": 0.0, "texts": []}
        
        # Analyze each text
        sentiments = []
        for text in sentiment_texts:
            sentiment = await self.analyze_sentiment(text)
            sentiments.append(sentiment)
        
        # Calculate overall sentiment
        positive_count = sentiments.count(1)
        negative_count = sentiments.count(-1)
        neutral_count = sentiments.count(0)
        
        if positive_count > negative_count and positive_count > neutral_count:
            overall_sentiment = 1
        elif negative_count > positive_count and negative_count > neutral_count:
            overall_sentiment = -1
        else:
            overall_sentiment = 0
        
        confidence = max(sentiments.count(overall_sentiment), 0) / len(sentiments) if sentiments else 0
        
        return {
            "sentiment": overall_sentiment,
            "confidence": confidence,
            "texts": sentiment_texts,
            "sentiment_breakdown": {
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count
            }
        }


# Global analyzer instance
_analyzer: Optional[SentimentAnalyzer] = None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Get global sentiment analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentAnalyzer()
    return _analyzer