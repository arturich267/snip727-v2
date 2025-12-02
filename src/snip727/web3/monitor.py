"""Uniswap V2/V3 pool monitoring with event subscription."""
import asyncio
import structlog
from typing import Callable, Dict, List, Optional, Set
from web3 import Web3
from web3.contract import Contract
from web3.datastructures import AttributeDict

from snip727.core.config import get_settings
from snip727.web3.client import get_web3_client

logger = structlog.get_logger()

# Uniswap V2 Factory ABI (minimal)
UNISWAP_V2_FACTORY_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "token0", "type": "address"},
            {"indexed": True, "name": "token1", "type": "address"},
            {"indexed": False, "name": "pair", "type": "address"},
            {"indexed": False, "name": "allPairsLength", "type": "uint256"},
        ],
        "name": "PairCreated",
        "type": "event",
    }
]

# Uniswap V2 Pair ABI (minimal)
UNISWAP_V2_PAIR_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "sender", "type": "address"},
            {"indexed": False, "name": "amount0", "type": "uint256"},
            {"indexed": False, "name": "amount1", "type": "uint256"},
        ],
        "name": "Mint",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "sender", "type": "address"},
            {"indexed": True, "name": "recipient", "type": "address"},
            {"indexed": False, "name": "amount0In", "type": "uint256"},
            {"indexed": False, "name": "amount1In", "type": "uint256"},
            {"indexed": False, "name": "amount0Out", "type": "uint256"},
            {"indexed": False, "name": "amount1Out", "type": "uint256"},
        ],
        "name": "Swap",
        "type": "event",
    },
]

# Uniswap V3 Factory ABI (minimal)
UNISWAP_V3_FACTORY_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "token0", "type": "address"},
            {"indexed": True, "name": "token1", "type": "address"},
            {"indexed": True, "name": "fee", "type": "uint24"},
            {"indexed": True, "name": "tickSpacing", "type": "int24"},
            {"indexed": False, "name": "pool", "type": "address"},
        ],
        "name": "PoolCreated",
        "type": "event",
    }
]


class PoolEvent:
    """Represents a pool-related event."""
    
    def __init__(
        self,
        event_type: str,
        pool_address: str,
        token0: str,
        token1: str,
        data: Dict[str, any],
        block_number: int,
        transaction_hash: str,
    ):
        self.event_type = event_type
        self.pool_address = pool_address
        self.token0 = token0
        self.token1 = token1
        self.data = data
        self.block_number = block_number
        self.transaction_hash = transaction_hash


class UniswapMonitor:
    """Monitor Uniswap V2/V3 pools for new pairs and trading activity."""
    
    def __init__(self, on_event: Callable[[PoolEvent], None]):
        self.settings = get_settings()
        self.on_event = on_event
        self.client = None
        self.w3 = None
        self.v2_factory = None
        self.v3_factory = None
        self.monitored_pools: Set[str] = set()
        self.running = False
        
    async def initialize(self) -> None:
        """Initialize monitor and contracts."""
        self.client = await get_web3_client()
        self.w3 = self.client.w3
        
        # Initialize contracts
        self.v2_factory = self.w3.eth.contract(
            address=self.settings.uniswap_v2_factory,
            abi=UNISWAP_V2_FACTORY_ABI
        )
        
        self.v3_factory = self.w3.eth.contract(
            address=self.settings.uniswap_v3_factory,
            abi=UNISWAP_V3_FACTORY_ABI
        )
        
        logger.info("monitor_initialized")
    
    async def start(self) -> None:
        """Start monitoring."""
        if not self.client or not self.w3:
            await self.initialize()
        
        self.running = True
        logger.info("monitor_starting")
        
        # Start monitoring tasks
        tasks = [
            self._monitor_v2_pairs(),
            self._monitor_v3_pairs(),
            self._monitor_existing_pools(),
        ]
        
        await asyncio.gather(*tasks)
    
    async def stop(self) -> None:
        """Stop monitoring."""
        self.running = False
        logger.info("monitor_stopped")
    
    async def _monitor_v2_pairs(self) -> None:
        """Monitor new V2 pairs."""
        while self.running:
            try:
                latest_block = await self.client.get_block_number()
                from_block = latest_block - 100  # Look back 100 blocks
                
                # Get PairCreated events
                events = await self.client.get_logs(
                    address=self.settings.uniswap_v2_factory,
                    topics=[
                        self.w3.keccak(text="PairCreated(address,address,address,uint256)").hex()
                    ],
                    fromBlock=from_block,
                    toBlock="latest"
                )
                
                for event in events:
                    await self._handle_v2_pair_created(event)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error("v2_monitor_error", error=str(e))
                await asyncio.sleep(60)
    
    async def _monitor_v3_pairs(self) -> None:
        """Monitor new V3 pools."""
        while self.running:
            try:
                latest_block = await self.client.get_block_number()
                from_block = latest_block - 100
                
                # Get PoolCreated events
                events = await self.client.get_logs(
                    address=self.settings.uniswap_v3_factory,
                    topics=[
                        self.w3.keccak(text="PoolCreated(address,address,uint24,int24,address)").hex()
                    ],
                    fromBlock=from_block,
                    toBlock="latest"
                )
                
                for event in events:
                    await self._handle_v3_pool_created(event)
                
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error("v3_monitor_error", error=str(e))
                await asyncio.sleep(60)
    
    async def _monitor_existing_pools(self) -> None:
        """Monitor trading activity on existing pools."""
        while self.running:
            try:
                if not self.monitored_pools:
                    await asyncio.sleep(60)
                    continue
                
                latest_block = await self.client.get_block_number()
                from_block = latest_block - 50  # Look back 50 blocks
                
                # Monitor Mint and Swap events for all pools
                for pool_address in list(self.monitored_pools):
                    try:
                        # Mint events (liquidity additions)
                        mint_events = await self.client.get_logs(
                            address=pool_address,
                            topics=[
                                self.w3.keccak(text="Mint(address,uint256,uint256)").hex()
                            ],
                            fromBlock=from_block,
                            toBlock="latest"
                        )
                        
                        for event in mint_events:
                            await self._handle_mint_event(pool_address, event)
                        
                        # Swap events
                        swap_events = await self.client.get_logs(
                            address=pool_address,
                            topics=[
                                self.w3.keccak(text="Swap(address,address,uint256,uint256,uint256,uint256)").hex()
                            ],
                            fromBlock=from_block,
                            toBlock="latest"
                        )
                        
                        for event in swap_events:
                            await self._handle_swap_event(pool_address, event)
                    
                    except Exception as e:
                        logger.warning("pool_monitor_error", pool=pool_address, error=str(e))
                
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error("existing_pools_monitor_error", error=str(e))
                await asyncio.sleep(60)
    
    async def _handle_v2_pair_created(self, event: Dict[str, any]) -> None:
        """Handle V2 PairCreated event."""
        try:
            decoded = self.v2_factory.events.PairCreated().process_log(event)
            
            pool_event = PoolEvent(
                event_type="v2_pair_created",
                pool_address=decoded.args.pair,
                token0=decoded.args.token0,
                token1=decoded.args.token1,
                data={"all_pairs_length": decoded.args.allPairsLength},
                block_number=decoded.blockNumber,
                transaction_hash=decoded.transactionHash.hex(),
            )
            
            self.monitored_pools.add(decoded.args.pair)
            await self.on_event(pool_event)
            
            logger.info(
                "v2_pair_created",
                pool=decoded.args.pair,
                token0=decoded.args.token0,
                token1=decoded.args.token1
            )
            
        except Exception as e:
            logger.error("handle_v2_pair_error", error=str(e))
    
    async def _handle_v3_pool_created(self, event: Dict[str, any]) -> None:
        """Handle V3 PoolCreated event."""
        try:
            decoded = self.v3_factory.events.PoolCreated().process_log(event)
            
            pool_event = PoolEvent(
                event_type="v3_pool_created",
                pool_address=decoded.args.pool,
                token0=decoded.args.token0,
                token1=decoded.args.token1,
                data={"fee": decoded.args.fee, "tickSpacing": decoded.args.tickSpacing},
                block_number=decoded.blockNumber,
                transaction_hash=decoded.transactionHash.hex(),
            )
            
            self.monitored_pools.add(decoded.args.pool)
            await self.on_event(pool_event)
            
            logger.info(
                "v3_pool_created",
                pool=decoded.args.pool,
                token0=decoded.args.token0,
                token1=decoded.args.token1,
                fee=decoded.args.fee
            )
            
        except Exception as e:
            logger.error("handle_v3_pool_error", error=str(e))
    
    async def _handle_mint_event(self, pool_address: str, event: Dict[str, any]) -> None:
        """Handle Mint event (liquidity addition)."""
        try:
            # Create pair contract to decode event
            pair_contract = self.w3.eth.contract(address=pool_address, abi=UNISWAP_V2_PAIR_ABI)
            decoded = pair_contract.events.Mint().process_log(event)
            
            # Calculate approximate USD value (simplified)
            amount0 = float(decoded.args.amount0)
            amount1 = float(decoded.args.amount1)
            estimated_usd = (amount0 + amount1) / 1e18  # Rough estimate
            
            if estimated_usd >= self.settings.min_liquidity_usd:
                pool_event = PoolEvent(
                    event_type="liquidity_spike",
                    pool_address=pool_address,
                    token0="",
                    token1="",  # Will be filled by caller
                    data={
                        "amount0": amount0,
                        "amount1": amount1,
                        "estimated_usd": estimated_usd,
                        "sender": decoded.args.sender,
                    },
                    block_number=decoded.blockNumber,
                    transaction_hash=decoded.transactionHash.hex(),
                )
                
                await self.on_event(pool_event)
                
                logger.info(
                    "liquidity_spike",
                    pool=pool_address,
                    estimated_usd=estimated_usd
                )
                
        except Exception as e:
            logger.error("handle_mint_error", pool=pool_address, error=str(e))
    
    async def _handle_swap_event(self, pool_address: str, event: Dict[str, any]) -> None:
        """Handle Swap event."""
        try:
            pair_contract = self.w3.eth.contract(address=pool_address, abi=UNISWAP_V2_PAIR_ABI)
            decoded = pair_contract.events.Swap().process_log(event)
            
            # Calculate swap value
            amount0_in = float(decoded.args.amount0In)
            amount1_in = float(decoded.args.amount1In)
            amount0_out = float(decoded.args.amount0Out)
            amount1_out = float(decoded.args.amount1Out)
            
            total_in = (amount0_in + amount1_in) / 1e18
            total_out = (amount0_out + amount1_out) / 1e18
            swap_value = max(total_in, total_out)
            
            if swap_value >= self.settings.whale_threshold_usd:
                pool_event = PoolEvent(
                    event_type="whale_buy",
                    pool_address=pool_address,
                    token0="",
                    token1="",  # Will be filled by caller
                    data={
                        "amount0_in": amount0_in,
                        "amount1_in": amount1_in,
                        "amount0_out": amount0_out,
                        "amount1_out": amount1_out,
                        "swap_value_usd": swap_value,
                        "sender": decoded.args.sender,
                        "recipient": decoded.args.recipient,
                    },
                    block_number=decoded.blockNumber,
                    transaction_hash=decoded.transactionHash.hex(),
                )
                
                await self.on_event(pool_event)
                
                logger.info(
                    "whale_buy",
                    pool=pool_address,
                    swap_value_usd=swap_value
                )
                
        except Exception as e:
            logger.error("handle_swap_error", pool=pool_address, error=str(e))