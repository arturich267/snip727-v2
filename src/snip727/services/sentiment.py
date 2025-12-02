"""Sentiment analysis service using DeepPavlov ruBERT."""
import asyncio
import feedparser
from datetime import datetime, timedelta
from typing import List, Optional
import aiohttp
from bs4 import BeautifulSoup
import structlog

from snip727.core.config import get_settings
from snip727.db.models import SentimentScore
from snip727.db import get_session

logger = structlog.get_logger()


class SentimentAnalyzer:
    """Sentiment analysis using DeepPavlov ruBERT model."""
    
    def __init__(self):
        self.settings = get_settings()
        self.model = None
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self) -> None:
        """Initialize the DeepPavlov model and HTTP session."""
        try:
            # Import DeepPavlov (may take time to download model)
            from deeppavlov import build_model
            
            # Build ruBERT sentiment model
            self.model = build_model("sentiment_ru_bert", download=True)
            logger.info("deeppavlov_model_loaded")
            
        except Exception as e:
            logger.error("deeppavlov_init_failed", error=str(e))
            # Fallback to simple sentiment analysis
            self.model = None
            
        self.session = aiohttp.ClientSession()
        logger.info("sentiment_analyzer_initialized")

    async def analyze_text(self, text: str) -> tuple[float, float]:
        """Analyze sentiment of text. Returns (score, confidence)."""
        if not text or not text.strip():
            return 0.0, 0.0
            
        try:
            if self.model:
                # Use DeepPavlov model
                result = self.model([text])
                if result and len(result) > 0:
                    # DeepPavlov returns sentiment labels and probabilities
                    # Convert to numeric score (-1 to 1) and confidence
                    sentiment_label = result[0][0] if result[0] else "neutral"
                    probs = result[1][0] if len(result) > 1 and result[1] else [0.33, 0.33, 0.34]
                    
                    if sentiment_label == "positive":
                        score = probs[0] if len(probs) > 0 else 0.5
                    elif sentiment_label == "negative":
                        score = -probs[1] if len(probs) > 1 else -0.5
                    else:
                        score = 0.0
                        
                    confidence = max(probs) if probs else 0.5
                    return score, confidence
            else:
                # Fallback simple sentiment analysis
                return self._simple_sentiment_analysis(text)
                
        except Exception as e:
            logger.error("sentiment_analysis_failed", error=str(e))
            return self._simple_sentiment_analysis(text)

    def _simple_sentiment_analysis(self, text: str) -> tuple[float, float]:
        """Simple rule-based sentiment analysis as fallback."""
        positive_words = ["хорошо", "отлично", "супер", "круто", "good", "great", "awesome", "🚀", "🔥", "💎", "🦍"]
        negative_words = ["плохо", "ужасно", "мусор", "scam", "bad", "terrible", "💩", "🚩"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            score = min(0.8, 0.3 + (positive_count - negative_count) * 0.1)
            confidence = 0.6
        elif negative_count > positive_count:
            score = max(-0.8, -0.3 - (negative_count - positive_count) * 0.1)
            confidence = 0.6
        else:
            score = 0.0
            confidence = 0.4
            
        return score, confidence

    async def scrape_telegram_channels(self) -> List[dict]:
        """Scrape messages from Telegram channels."""
        messages = []
        
        # Note: This is a simplified implementation
        # In production, you'd use Telegram Bot API or MTProto
        for channel in self.settings.telegram_channels:
            try:
                # This would require proper Telegram API integration
                # For now, we'll simulate with placeholder data
                logger.info("scraping_telegram_channel", channel=channel)
                
            except Exception as e:
                logger.error("telegram_scrape_failed", channel=channel, error=str(e))
                
        return messages

    async def scrape_nitter_feeds(self) -> List[dict]:
        """Scrape tweets from Nitter RSS feeds."""
        messages = []
        
        for feed_url in self.settings.nitter_feeds:
            try:
                async with self.session.get(feed_url) as response:
                    if response.status == 200:
                        feed_content = await response.text()
                        feed = feedparser.parse(feed_content)
                        
                        for entry in feed.entries[:10]:  # Get last 10 entries
                            # Clean HTML content
                            content = entry.get('description', entry.get('summary', ''))
                            if content:
                                soup = BeautifulSoup(content, 'html.parser')
                                clean_content = soup.get_text().strip()
                                
                                messages.append({
                                    'source': f'twitter_{feed_url.split("/")[-1]}',
                                    'content': clean_content,
                                    'timestamp': datetime(*entry.published_parsed[:6]) if entry.published_parsed else datetime.utcnow(),
                                    'url': entry.get('link', '')
                                })
                                
            except Exception as e:
                logger.error("nitter_scrape_failed", feed_url=feed_url, error=str(e))
                
        return messages

    async def extract_token_mentions(self, text: str) -> List[str]:
        """Extract token contract addresses from text."""
        import re
        
        # Find Ethereum/Base addresses (0x followed by 40 hex chars)
        address_pattern = r'0x[a-fA-F0-9]{40}'
        addresses = re.findall(address_pattern, text)
        
        # Normalize addresses
        return [addr.lower() for addr in addresses]

    async def analyze_and_save(self, source: str, content: str, timestamp: datetime, pool_address: Optional[str] = None) -> None:
        """Analyze sentiment and save to database."""
        try:
            score, confidence = await self.analyze_text(content)
            
            # Extract token addresses if not provided
            if not pool_address:
                addresses = await self.extract_token_mentions(content)
                if addresses:
                    pool_address = addresses[0]  # Use first address found
            
            async for session in get_session():
                sentiment_score = SentimentScore(
                    pool_address=pool_address,
                    source=source,
                    content=content[:500],  # Limit content length
                    score=score,
                    confidence=confidence,
                    timestamp=timestamp
                )
                
                session.add(sentiment_score)
                await session.commit()
                
                logger.info("sentiment_saved", 
                          source=source, 
                          score=score, 
                          confidence=confidence,
                          pool_address=pool_address)
                break  # Exit after getting session
                
        except Exception as e:
            logger.error("analyze_and_save_failed", error=str(e))

    async def start_continuous_analysis(self) -> None:
        """Start continuous sentiment analysis."""
        while True:
            try:
                # Scrape sources
                telegram_messages = await self.scrape_telegram_channels()
                twitter_messages = await self.scrape_nitter_feeds()
                
                all_messages = telegram_messages + twitter_messages
                
                # Analyze each message
                for msg in all_messages:
                    await self.analyze_and_save(
                        source=msg['source'],
                        content=msg['content'],
                        timestamp=msg['timestamp']
                    )
                
                # Wait before next iteration (5 minutes)
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error("continuous_analysis_error", error=str(e))
                await asyncio.sleep(60)  # Wait 1 minute before retry

    async def get_pool_sentiment(self, pool_address: str, hours: int = 24) -> Optional[float]:
        """Get average sentiment score for a pool in the last N hours."""
        try:
            async for session in get_session():
                from sqlalchemy import select, func
                
                cutoff_time = datetime.utcnow() - timedelta(hours=hours)
                
                result = await session.execute(
                    select(func.avg(SentimentScore.score))
                    .where(
                        SentimentScore.pool_address == pool_address.lower(),
                        SentimentScore.timestamp >= cutoff_time,
                        SentimentScore.confidence >= 0.5  # Only use high-confidence scores
                    )
                )
                
                avg_score = result.scalar()
                return float(avg_score) if avg_score is not None else None
                break  # Exit after getting session
                
        except Exception as e:
            logger.error("get_pool_sentiment_failed", pool_address=pool_address, error=str(e))
            return None

    async def close(self) -> None:
        """Close resources."""
        if self.session:
            await self.session.close()


# Global analyzer instance
sentiment_analyzer = SentimentAnalyzer()