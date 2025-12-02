"""Uniswap V2/V3 monitor for Base network."""
import asyncio
from datetime import datetime
from typing import Dict, Optional
import structlog
from web3 import Web3
from web3.datastructures import AttributeDict

from snip727.core.config import get_settings
from snip727.db.models import Pool, TradeEvent, StrategySignal
from snip727.db import get_session
from snip727.web3.client import web3_client

logger = structlog.get_logger()


class UniswapMonitor:
    """Monitor Uniswap V2/V3 pools on Base network."""
    
    def __init__(self):
        self.settings = get_settings()
        self.running = False
        self.latest_block: Optional[int] = None
        
    async def start(self) -> None:
        """Start the monitor."""
        await web3_client.initialize()
        self.running = True
        self.latest_block = await web3_client.get_latest_block_number()
        
        logger.info("uniswap_monitor_started", latest_block=self.latest_block)
        
        # Start monitoring tasks
        tasks = [
            self.monitor_v2_factory(),
            self.monitor_v3_factory(),
            self.monitor_existing_pools()
        ]
        
        await asyncio.gather(*tasks)

    async def stop(self) -> None:
        """Stop the monitor."""
        self.running = False
        await web3_client.close()
        logger.info("uniswap_monitor_stopped")

    async def monitor_v2_factory(self) -> None:
        """Monitor Uniswap V2 Factory for new pairs."""
        while self.running:
            try:
                await self._subscribe_to_factory(
                    self.settings.uniswap_v2_factory,
                    "PairCreated",
                    self._handle_v2_pair_created
                )
            except Exception as e:
                logger.error("v2_factory_monitor_error", error=str(e))
                await asyncio.sleep(10)  # Wait before retry

    async def monitor_v3_factory(self) -> None:
        """Monitor Uniswap V3 Factory for new pools."""
        while self.running:
            try:
                await self._subscribe_to_factory(
                    self.settings.uniswap_v3_factory,
                    "PoolCreated", 
                    self._handle_v3_pool_created
                )
            except Exception as e:
                logger.error("v3_factory_monitor_error", error=str(e))
                await asyncio.sleep(10)  # Wait before retry

    async def _subscribe_to_factory(self, factory_address: str, event_name: str, callback) -> None:
        """Subscribe to factory events."""
        if event_name == "PairCreated":
            abi = web3_client.uniswap_v2_factory_abi
        else:
            abi = web3_client.uniswap_v3_factory_abi
            
        await web3_client.subscribe_to_events(factory_address, abi, callback)

    async def _handle_v2_pair_created(self, event: AttributeDict) -> None:
        """Handle V2 PairCreated event."""
        await self._save_pool(
            address=event.args.pair,
            token0=event.args.token0,
            token1=event.args.token1,
            fee=None,
            version="V2",
            factory=self.settings.uniswap_v2_factory,
            block_number=event.blockNumber,
            block_timestamp=datetime.fromtimestamp(event.timestamp) if hasattr(event, 'timestamp') else datetime.utcnow()
        )

    async def _handle_v3_pool_created(self, event: AttributeDict) -> None:
        """Handle V3 PoolCreated event."""
        await self._save_pool(
            address=event.args.pool,
            token0=event.args.token0,
            token1=event.args.token1,
            fee=event.args.fee,
            version="V3",
            factory=self.settings.uniswap_v3_factory,
            block_number=event.blockNumber,
            block_timestamp=datetime.fromtimestamp(event.timestamp) if hasattr(event, 'timestamp') else datetime.utcnow()
        )

    async def _save_pool(self, address: str, token0: str, token1: str, fee: Optional[int], 
                        version: str, factory: str, block_number: int, block_timestamp: datetime) -> None:
        """Save new pool to database."""
        async for session in get_session():
            try:
                # Check if pool already exists
                existing_pool = await session.get(Pool, address)
                if existing_pool:
                    return
                    
                pool = Pool(
                    address=address.lower(),
                    token0=token0.lower(),
                    token1=token1.lower(),
                    fee=fee,
                    version=version,
                    factory=factory.lower(),
                    block_number=block_number,
                    block_timestamp=block_timestamp
                )
                
                session.add(pool)
                await session.commit()
                
                # Create strategy signal for new pool
                signal = StrategySignal(
                    pool_address=address.lower(),
                    signal_type="new_pool",
                    signal_value=1.0,
                    block_number=block_number
                )
                session.add(signal)
                await session.commit()
                
                logger.info("new_pool_saved", 
                          address=address, 
                          version=version, 
                          token0=token0, 
                          token1=token1)
                
            except Exception as e:
                await session.rollback()
                logger.error("save_pool_failed", address=address, error=str(e))

    async def monitor_existing_pools(self) -> None:
        """Monitor existing pools for trade events."""
        while self.running:
            try:
                current_block = await web3_client.get_latest_block_number()
                
                # Get pools to monitor (last 100 blocks)
                async for session in get_session():
                    from sqlalchemy import select
                    result = await session.execute(
                        select(Pool).where(
                            Pool.block_number >= current_block - 100
                        ).order_by(Pool.block_number.desc()).limit(50)
                    )
                    pools = result.scalars().all()
                    break  # Exit after getting session
                
                # Monitor each pool for events
                for pool in pools:
                    await self._monitor_pool_events(pool, self.latest_block or current_block - 10, current_block)
                
                self.latest_block = current_block
                await asyncio.sleep(2)  # Poll every 2 seconds
                
            except Exception as e:
                logger.error("monitor_pools_error", error=str(e))
                await asyncio.sleep(10)

    async def _monitor_pool_events(self, pool: Pool, from_block: int, to_block: int) -> None:
        """Monitor specific pool for trade events."""
        try:
            # Get logs for this pool
            logs = await web3_client.get_logs(
                address=pool.address,
                fromBlock=from_block,
                toBlock=to_block,
                topics=[
                    None,  # Any event
                ]
            )
            
            for log in logs:
                await self._process_trade_event(pool, log)
                
        except Exception as e:
            logger.error("monitor_pool_events_failed", pool_address=pool.address, error=str(e))

    async def _process_trade_event(self, pool: Pool, log: Dict) -> None:
        """Process a trade event log."""
        try:
            # Decode the log based on event signature
            event_signature = log["topics"][0] if log["topics"] else None
            
            if not event_signature:
                return
                
            # Event signatures
            mint_signature = Web3.keccak(text="Mint(address,uint256,uint256)").hex()
            swap_signature = Web3.keccak(text="Swap(address,address,uint256,uint256,uint256,uint256)").hex()
            
            event_type = None
            trade_data = {}
            
            if event_signature == mint_signature:
                event_type = "Mint"
                # Decode Mint event (simplified)
                trade_data = await self._decode_mint_event(log)
            elif event_signature == swap_signature:
                event_type = "Swap"
                # Decode Swap event (simplified)
                trade_data = await self._decode_swap_event(log)
            
            if event_type and trade_data:
                await self._save_trade_event(pool, event_type, log, trade_data)
                
        except Exception as e:
            logger.error("process_trade_event_failed", error=str(e))

    async def _decode_mint_event(self, log: Dict) -> Dict:
        """Decode Mint event data."""
        # Simplified decoding - in production you'd use proper ABI decoding
        return {
            "amount0": 0.0,  # Would decode from log.data
            "amount1": 0.0,
        }

    async def _decode_swap_event(self, log: Dict) -> Dict:
        """Decode Swap event data."""
        # Simplified decoding - in production you'd use proper ABI decoding
        return {
            "amount0_in": 0.0,
            "amount1_in": 0.0,
            "amount0_out": 0.0,
            "amount1_out": 0.0,
        }

    async def _save_trade_event(self, pool: Pool, event_type: str, log: Dict, trade_data: Dict) -> None:
        """Save trade event to database and check for signals."""
        async for session in get_session():
            try:
                trade_event = TradeEvent(
                    pool_address=pool.address,
                    event_type=event_type,
                    transaction_hash=log["transactionHash"].hex(),
                    block_number=log["blockNumber"],
                    block_timestamp=datetime.utcnow(),  # Would get from block
                    log_index=log["logIndex"],
                    **trade_data
                )
                
                session.add(trade_event)
                await session.commit()
                
                # Check for strategy signals
                await self._check_strategy_signals(session, pool, trade_event)
                
                logger.info("trade_event_saved", 
                          pool_address=pool.address,
                          event_type=event_type,
                          tx_hash=log["transactionHash"].hex())
                
            except Exception as e:
                await session.rollback()
                logger.error("save_trade_event_failed", error=str(e))

    async def _check_strategy_signals(self, session, pool: Pool, trade_event: TradeEvent) -> None:
        """Check for strategy signals based on trade events."""
        current_block = await web3_client.get_latest_block_number()
        
        # Check for liquidity spike (Mint events)
        if trade_event.event_type == "Mint":
            # Get recent mint events for this pool
            from sqlalchemy import select
            recent_mints = await session.execute(
                select(TradeEvent).where(
                    TradeEvent.pool_address == pool.address,
                    TradeEvent.event_type == "Mint",
                    TradeEvent.block_number >= current_block - 50
                ).order_by(TradeEvent.block_number.desc())
            )
            mint_events = recent_mints.scalars().all()
            
            if len(mint_events) >= 2:
                # Simple liquidity spike detection
                avg_amount = sum(m.amount0 or 0 for m in mint_events) / len(mint_events)
                if avg_amount > 0:  # Would compare to historical average
                    signal = StrategySignal(
                        pool_address=pool.address,
                        signal_type="liquidity_spike",
                        signal_value=avg_amount,
                        block_number=current_block
                    )
                    session.add(signal)
                    await session.commit()
                    
                    logger.info("liquidity_spike_detected", 
                              pool_address=pool.address, 
                              value=avg_amount)
        
        # Check for whale buys (Swap events)
        elif trade_event.event_type == "Swap":
            if trade_event.amount0_in and trade_event.amount0_in > 0:
                # Simplified whale detection - would need pool reserves
                is_whale = trade_event.amount0_in > self.settings.whale_buy_threshold
                
                if is_whale:
                    signal = StrategySignal(
                        pool_address=pool.address,
                        signal_type="whale_buy",
                        signal_value=trade_event.amount0_in,
                        block_number=current_block
                    )
                    session.add(signal)
                    await session.commit()
                    
                    logger.info("whale_buy_detected", 
                              pool_address=pool.address, 
                              amount=trade_event.amount0_in)


# Global monitor instance
uniswap_monitor = UniswapMonitor()