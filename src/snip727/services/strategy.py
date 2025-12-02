"""N-of-4 strategy service for alert generation."""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import structlog

from snip727.core.config import get_settings
from snip727.db.models import Pool, StrategySignal, Alert
from snip727.db import get_session
from snip727.services.sentiment import sentiment_analyzer

logger = structlog.get_logger()


class StrategyService:
    """N-of-4 strategy implementation for trading signals."""
    
    def __init__(self):
        self.settings = get_settings()
        self.running = False
        self.alert_callbacks: List[callable] = []
        
    def add_alert_callback(self, callback: callable) -> None:
        """Add callback function for alerts."""
        self.alert_callbacks.append(callback)
        
    async def start(self) -> None:
        """Start the strategy service."""
        self.running = True
        logger.info("strategy_service_started")
        
        # Start continuous evaluation
        await asyncio.create_task(self._continuous_evaluation())
        
    async def stop(self) -> None:
        """Stop the strategy service."""
        self.running = False
        logger.info("strategy_service_stopped")

    async def _continuous_evaluation(self) -> None:
        """Continuously evaluate strategy signals."""
        while self.running:
            try:
                # Get pools with recent activity
                pools_to_check = await self._get_active_pools()
                
                for pool_address in pools_to_check:
                    await self._evaluate_pool(pool_address)
                
                # Wait before next evaluation
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error("continuous_evaluation_error", error=str(e))
                await asyncio.sleep(30)

    async def _get_active_pools(self) -> List[str]:
        """Get pools with recent signals."""
        try:
            async for session in get_session():
                from sqlalchemy import select, distinct
                
                # Get pools with signals in the last hour
                cutoff_time = datetime.utcnow() - timedelta(hours=1)
                
                result = await session.execute(
                    select(distinct(StrategySignal.pool_address))
                    .where(
                        StrategySignal.created_at >= cutoff_time,
                        StrategySignal.is_active
                    )
                )
                
                return [row[0] for row in result.fetchall()]
                break  # Exit after getting session
                
        except Exception as e:
            logger.error("get_active_pools_failed", error=str(e))
            return []

    async def _evaluate_pool(self, pool_address: str) -> None:
        """Evaluate a pool for strategy signals."""
        try:
            signals = await self._get_pool_signals(pool_address)
            signal_count = len(signals)
            
            if signal_count >= self.settings.strategy_signals_required:
                # Generate alert
                await self._generate_alert(pool_address, signals)
                
        except Exception as e:
            logger.error("evaluate_pool_failed", pool_address=pool_address, error=str(e))

    async def _get_pool_signals(self, pool_address: str) -> Dict[str, Dict]:
        """Get all active signals for a pool."""
        signals = {}
        current_block = await self._get_current_block()
        
        try:
            async for session in get_session():
                from sqlalchemy import select
                
                # Get strategy signals
                result = await session.execute(
                    select(StrategySignal)
                    .where(
                        StrategySignal.pool_address == pool_address.lower(),
                        StrategySignal.is_active
                    )
                )
                
                strategy_signals = result.scalars().all()
                
                for signal in strategy_signals:
                    # Check if signal is still valid
                    if await self._is_signal_valid(signal, current_block):
                        signals[signal.signal_type] = {
                            'value': signal.signal_value,
                            'created_at': signal.created_at,
                            'block_number': signal.block_number
                        }
                
                # Check sentiment signal
                sentiment_score = await sentiment_analyzer.get_pool_sentiment(pool_address)
                if sentiment_score and sentiment_score >= self.settings.sentiment_threshold:
                    signals['sentiment'] = {
                        'value': sentiment_score,
                        'created_at': datetime.utcnow(),
                        'block_number': current_block
                    }
                
                break  # Exit after getting session
                
        except Exception as e:
            logger.error("get_pool_signals_failed", pool_address=pool_address, error=str(e))
            
        return signals

    async def _is_signal_valid(self, signal: StrategySignal, current_block: int) -> bool:
        """Check if a signal is still valid."""
        # Check expiration
        if signal.expires_at and signal.expires_at < datetime.utcnow():
            return False
            
        # Check block age for time-sensitive signals
        if signal.signal_type in ['new_pool', 'liquidity_spike', 'whale_buy']:
            if signal.block_number and current_block - signal.block_number > self.settings.new_pool_blocks_threshold:
                return False
                
        return True

    async def _get_current_block(self) -> int:
        """Get current block number."""
        try:
            from snip727.web3.client import web3_client
            return await web3_client.get_latest_block_number()
        except Exception:
            return 0

    async def _generate_alert(self, pool_address: str, signals: Dict[str, Dict]) -> None:
        """Generate and send alert for pool."""
        try:
            # Get pool information
            pool_info = await self._get_pool_info(pool_address)
            if not pool_info:
                return
                
            # Calculate alert score
            signal_count = len(signals)
            alert_score = self._calculate_alert_score(signals)
            
            # Create alert message
            message = self._create_alert_message(pool_info, signals, signal_count, alert_score)
            
            # Save alert to database
            await self._save_alert(pool_address, signals, signal_count, alert_score, message)
            
            # Send alerts via callbacks
            for callback in self.alert_callbacks:
                try:
                    await callback(pool_address, message, signals)
                except Exception as e:
                    logger.error("alert_callback_failed", error=str(e))
                    
            logger.info("alert_generated", 
                       pool_address=pool_address, 
                       signal_count=signal_count,
                       score=alert_score)
                       
        except Exception as e:
            logger.error("generate_alert_failed", pool_address=pool_address, error=str(e))

    async def _get_pool_info(self, pool_address: str) -> Optional[Dict]:
        """Get pool information."""
        try:
            async for session in get_session():
                pool = await session.get(Pool, pool_address.lower())
                if pool:
                    return {
                        'address': pool.address,
                        'token0': pool.token0,
                        'token1': pool.token1,
                        'version': pool.version,
                        'fee': pool.fee,
                        'created_at': pool.created_at
                    }
                break  # Exit after getting session
        except Exception as e:
            logger.error("get_pool_info_failed", pool_address=pool_address, error=str(e))
            
        return None

    def _calculate_alert_score(self, signals: Dict[str, Dict]) -> float:
        """Calculate alert score based on signals."""
        score = 0.0
        
        # Weight different signals
        signal_weights = {
            'new_pool': 0.3,
            'liquidity_spike': 0.25,
            'whale_buy': 0.25,
            'sentiment': 0.2
        }
        
        for signal_type, signal_data in signals.items():
            weight = signal_weights.get(signal_type, 0.1)
            
            if signal_type == 'sentiment':
                # Sentiment is already normalized -1 to 1
                value = max(0, signal_data['value'])  # Only positive sentiment
            else:
                # Normalize other signals (simplified)
                value = min(1.0, signal_data['value'] / 100.0) if signal_data['value'] else 0.5
                
            score += weight * value
            
        return min(1.0, score)

    def _create_alert_message(self, pool_info: Dict, signals: Dict[str, Dict], 
                            signal_count: int, alert_score: float) -> str:
        """Create alert message for Telegram."""
        signal_emojis = {
            'new_pool': '🆕',
            'liquidity_spike': '📈',
            'whale_buy': '🐋',
            'sentiment': '💬'
        }
        
        # Create signal summary
        signal_summary = " ".join([
            f"{signal_emojis.get(signal_type, '🔔')}{signal_type.replace('_', ' ').title()}"
            for signal_type in signals.keys()
        ])
        
        # Format token addresses
        token0_short = f"{pool_info['token0'][:6]}...{pool_info['token0'][-4:]}"
        token1_short = f"{pool_info['token1'][:6]}...{pool_info['token1'][-4:]}"
        
        message = (
            f"🚨 *UNISWAP ALERT* 🚨\n\n"
            f"📍 Pool: `{pool_info['address']}`\n"
            f"💱 Pair: {token0_short} / {token1_short}\n"
            f"🏷️ Version: {pool_info['version']}"
        )
        
        if pool_info['fee']:
            message += f" (Fee: {pool_info['fee']/10000:.2f}%)"
            
        message += f"\n\n🎯 Signals ({signal_count}/4): {signal_summary}"
        message += f"\n📊 Score: {alert_score:.2f}"
        
        # Add inline buttons hint
        message += f"\n\n[🔗 View on BaseScan](https://basescan.org/address/{pool_info['address']})"
        
        return message

    async def _save_alert(self, pool_address: str, signals: Dict[str, Dict], 
                         signal_count: int, alert_score: float, message: str) -> None:
        """Save alert to database."""
        try:
            async for session in get_session():
                alert = Alert(
                    pool_address=pool_address.lower(),
                    alert_type="strategy_signal",
                    message=message,
                    signal_count=signal_count,
                    sentiment_score=signals.get('sentiment', {}).get('value')
                )
                
                session.add(alert)
                await session.commit()
                break  # Exit after getting session
                
        except Exception as e:
            logger.error("save_alert_failed", pool_address=pool_address, error=str(e))

    async def get_current_signals(self) -> List[Dict]:
        """Get current active signals for all pools."""
        try:
            async for session in get_session():
                from sqlalchemy import select
                
                # Get recent signals
                cutoff_time = datetime.utcnow() - timedelta(hours=1)
                
                result = await session.execute(
                    select(StrategySignal, Pool)
                    .join(Pool, StrategySignal.pool_address == Pool.address)
                    .where(
                        StrategySignal.created_at >= cutoff_time,
                        StrategySignal.is_active
                    )
                    .order_by(StrategySignal.created_at.desc())
                    .limit(50)
                )
                
                signals_list = []
                for signal, pool in result:
                    signals_list.append({
                        'pool_address': pool.address,
                        'token0': pool.token0,
                        'token1': pool.token1,
                        'signal_type': signal.signal_type,
                        'signal_value': signal.signal_value,
                        'created_at': signal.created_at
                    })
                    
                return signals_list
                break  # Exit after getting session
                
        except Exception as e:
            logger.error("get_current_signals_failed", error=str(e))
            return []


# Global strategy service instance
strategy_service = StrategyService()