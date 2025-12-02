"""N-of-4 voting strategy for signal generation."""
import asyncio
import structlog
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta

from snip727.core.config import get_settings
from snip727.services.sentiment import get_sentiment_analyzer
from snip727.web3.monitor import PoolEvent

logger = structlog.get_logger()


class Signal:
    """Represents a trading signal."""
    
    def __init__(
        self,
        signal_type: str,
        pool_address: str,
        confidence: float,
        data: Dict[str, any],
        timestamp: datetime,
    ):
        self.signal_type = signal_type
        self.pool_address = pool_address
        self.confidence = confidence
        self.data = data
        self.timestamp = timestamp


class Nof4Strategy:
    """N-of-4 voting strategy for generating trading alerts."""
    
    def __init__(self):
        self.settings = get_settings()
        self.sentiment_analyzer = get_sentiment_analyzer()
        self.signals: List[Signal] = []
        self.event_history: Dict[str, List[PoolEvent]] = {}
        self.alert_callbacks: List[callable] = []
    
    def add_alert_callback(self, callback: callable) -> None:
        """Add callback for when alerts are generated."""
        self.alert_callbacks.append(callback)
    
    async def process_event(self, event: PoolEvent) -> None:
        """Process a pool event and potentially generate signals."""
        # Store event in history
        if event.pool_address not in self.event_history:
            self.event_history[event.pool_address] = []
        
        self.event_history[event.pool_address].append(event)
        
        # Keep only recent events (last hour)
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.event_history[event.pool_address] = [
            e for e in self.event_history[event.pool_address]
            if datetime.fromtimestamp(e.block_number * 12) > cutoff_time  # ~12s per block
        ]
        
        # Generate signals based on event
        await self._generate_signals(event)
        
        # Check if we have enough signals for an alert
        await self._check_for_alerts(event.pool_address)
    
    async def _generate_signals(self, event: PoolEvent) -> None:
        """Generate signals based on event type."""
        timestamp = datetime.now()
        
        if event.event_type in ["v2_pair_created", "v3_pool_created"]:
            # New pool signal
            signal = Signal(
                signal_type="new_pool",
                pool_address=event.pool_address,
                confidence=0.7,
                data=event.data,
                timestamp=timestamp,
            )
            self.signals.append(signal)
            logger.info("signal_generated", type="new_pool", pool=event.pool_address)
        
        elif event.event_type == "liquidity_spike":
            # Liquidity spike signal
            estimated_usd = event.data.get("estimated_usd", 0)
            confidence = min(0.9, 0.5 + (estimated_usd / 100000))  # Higher confidence for larger amounts
            
            signal = Signal(
                signal_type="liquidity_spike",
                pool_address=event.pool_address,
                confidence=confidence,
                data=event.data,
                timestamp=timestamp,
            )
            self.signals.append(signal)
            logger.info("signal_generated", type="liquidity_spike", pool=event.pool_address, confidence=confidence)
        
        elif event.event_type == "whale_buy":
            # Whale buy signal
            swap_value = event.data.get("swap_value_usd", 0)
            confidence = min(0.95, 0.6 + (swap_value / 200000))  # Higher confidence for larger amounts
            
            signal = Signal(
                signal_type="whale_buy",
                pool_address=event.pool_address,
                confidence=confidence,
                data=event.data,
                timestamp=timestamp,
            )
            self.signals.append(signal)
            logger.info("signal_generated", type="whale_buy", pool=event.pool_address, confidence=confidence)
    
    async def _check_for_alerts(self, pool_address: str) -> None:
        """Check if we have enough signals for an alert (N-of-4 voting)."""
        # Get recent signals for this pool (last 30 minutes)
        cutoff_time = datetime.now() - timedelta(minutes=30)
        recent_signals = [
            s for s in self.signals
            if s.pool_address == pool_address and s.timestamp > cutoff_time
        ]
        
        if len(recent_signals) < 3:  # Need at least 3 signals for N-of-4
            return
        
        # Count signal types
        signal_types = [s.signal_type for s in recent_signals]
        type_counts = {stype: signal_types.count(stype) for stype in set(signal_types)}
        
        # Check if any signal type has >= 3 occurrences (N-of-4 with N=3)
        for signal_type, count in type_counts.items():
            if count >= 3:
                # Generate sentiment analysis
                events = self.event_history.get(pool_address, [])
                sentiment_result = await self.sentiment_analyzer.analyze_crypto_sentiment(
                    "TOKEN", events  # We'll use generic token name for now
                )
                
                # Calculate overall confidence
                relevant_signals = [s for s in recent_signals if s.signal_type == signal_type]
                avg_confidence = sum(s.confidence for s in relevant_signals) / len(relevant_signals)
                
                # Combine with sentiment confidence
                sentiment_boost = sentiment_result.get("confidence", 0) * 0.3
                overall_confidence = min(0.95, avg_confidence + sentiment_boost)
                
                # Check sentiment threshold
                if abs(sentiment_result.get("sentiment", 0)) >= self.settings.sentiment_threshold or overall_confidence >= 0.8:
                    alert_data = {
                        "pool_address": pool_address,
                        "signal_type": signal_type,
                        "signal_count": count,
                        "confidence": overall_confidence,
                        "sentiment": sentiment_result,
                        "events": [
                            {
                                "type": e.event_type,
                                "block": e.block_number,
                                "tx": e.transaction_hash,
                                "data": e.data,
                            }
                            for e in events[-5:]  # Last 5 events
                        ],
                        "timestamp": datetime.now().isoformat(),
                    }
                    
                    # Trigger alerts
                    for callback in self.alert_callbacks:
                        try:
                            await callback(alert_data)
                        except Exception as e:
                            logger.error("alert_callback_failed", error=str(e))
                    
                    logger.info(
                        "alert_generated",
                        pool=pool_address,
                        signal_type=signal_type,
                        confidence=overall_confidence,
                        sentiment=sentiment_result.get("sentiment", 0)
                    )
                    
                    # Clear old signals for this pool to avoid spam
                    self.signals = [s for s in self.signals if s.pool_address != pool_address]
                    break
    
    def get_recent_signals(self, pool_address: Optional[str] = None, limit: int = 50) -> List[Dict[str, any]]:
        """Get recent signals."""
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_signals = [
            s for s in self.signals
            if s.timestamp > cutoff_time and (pool_address is None or s.pool_address == pool_address)
        ]
        
        # Sort by timestamp (newest first) and limit
        recent_signals.sort(key=lambda x: x.timestamp, reverse=True)
        recent_signals = recent_signals[:limit]
        
        return [
            {
                "type": s.signal_type,
                "pool": s.pool_address,
                "confidence": s.confidence,
                "data": s.data,
                "timestamp": s.timestamp.isoformat(),
            }
            for s in recent_signals
        ]
    
    def get_pool_stats(self) -> Dict[str, any]:
        """Get statistics about monitored pools."""
        total_pools = len(self.event_history)
        total_events = sum(len(events) for events in self.event_history.values())
        total_signals = len(self.signals)
        
        # Signal type breakdown
        signal_types = [s.signal_type for s in self.signals]
        signal_breakdown = {stype: signal_types.count(stype) for stype in set(signal_types)}
        
        # Recent activity (last hour)
        cutoff_time = datetime.now() - timedelta(hours=1)
        recent_signals = [s for s in self.signals if s.timestamp > cutoff_time]
        
        return {
            "monitored_pools": total_pools,
            "total_events": total_events,
            "total_signals": total_signals,
            "signal_breakdown": signal_breakdown,
            "recent_signals_last_hour": len(recent_signals),
            "active_pools_last_hour": len(set(s.pool_address for s in recent_signals)),
        }


# Global strategy instance
_strategy: Optional[Nof4Strategy] = None


def get_strategy() -> Nof4Strategy:
    """Get global strategy instance."""
    global _strategy
    if _strategy is None:
        _strategy = Nof4Strategy()
    return _strategy