"""Async Web3 client with RPC fallback and Redis caching."""
import asyncio
import json
from typing import Any, Dict, List, Optional
import aiohttp
import redis
import structlog
from web3 import Web3

from snip727.core.config import get_settings

logger = structlog.get_logger()


class AsyncWeb3Client:
    """Async Web3 client with RPC fallback and Redis caching."""
    
    def __init__(self):
        self.settings = get_settings()
        self.w3: Optional[Web3] = None
        self.rpc_urls = self.settings.base_rpc_urls
        self.current_rpc_index = 0
        self.redis: Optional[redis.Redis] = None
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Uniswap ABIs
        self.uniswap_v2_factory_abi = [
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "pair", "type": "address"},
                    {"indexed": True, "name": "token0", "type": "address"},
                    {"indexed": True, "name": "token1", "type": "address"}
                ],
                "name": "PairCreated",
                "type": "event"
            }
        ]
        
        self.uniswap_v3_factory_abi = [
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "token0", "type": "address"},
                    {"indexed": True, "name": "token1", "type": "address"},
                    {"indexed": True, "name": "fee", "type": "uint24"},
                    {"indexed": True, "name": "tickSpacing", "type": "int24"},
                    {"indexed": False, "name": "pool", "type": "address"}
                ],
                "name": "PoolCreated",
                "type": "event"
            }
        ]
        
        self.pair_abi = [
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "sender", "type": "address"},
                    {"indexed": False, "name": "amount0", "type": "uint256"},
                    {"indexed": False, "name": "amount1", "type": "uint256"}
                ],
                "name": "Mint",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "sender", "type": "address"},
                    {"indexed": True, "name": "recipient", "type": "address"},
                    {"indexed": False, "name": "amount0In", "type": "uint256"},
                    {"indexed": False, "name": "amount1In", "type": "uint256"},
                    {"indexed": False, "name": "amount0Out", "type": "uint256"},
                    {"indexed": False, "name": "amount1Out", "type": "uint256"}
                ],
                "name": "Swap",
                "type": "event"
            }
        ]

    async def initialize(self) -> None:
        """Initialize the client with Web3 and Redis connections."""
        # Initialize Redis
        self.redis = redis.from_url(self.settings.redis_url)
        
        # Initialize aiohttp session
        self.session = aiohttp.ClientSession()
        
        # Try to connect to RPC endpoints
        await self._connect_to_rpc()
        
        logger.info("web3_client_initialized")

    async def _connect_to_rpc(self) -> None:
        """Connect to available RPC endpoint with fallback."""
        for i in range(len(self.rpc_urls)):
            rpc_url = self.rpc_urls[(self.current_rpc_index + i) % len(self.rpc_urls)]
            try:
                if rpc_url.startswith("wss://"):
                    # WebSocket connection
                    self.w3 = Web3(Web3.WebsocketProvider(rpc_url))
                else:
                    # HTTP connection
                    self.w3 = Web3(Web3.HTTPProvider(rpc_url))
                
                # Test connection
                if self.w3.is_connected():
                    self.current_rpc_index = (self.current_rpc_index + i) % len(self.rpc_urls)
                    logger.info("web3_connected", rpc_url=rpc_url)
                    return
                    
            except Exception as e:
                logger.warning("rpc_connection_failed", rpc_url=rpc_url, error=str(e))
                continue
        
        raise ConnectionError("Failed to connect to any RPC endpoint")

    async def get_cached_abi(self, contract_address: str) -> Optional[List[Dict]]:
        """Get ABI from Redis cache or fetch if not cached."""
        if not self.redis:
            return None
            
        cache_key = f"abi:{contract_address}"
        cached_abi = self.redis.get(cache_key)
        
        if cached_abi:
            return json.loads(cached_abi)
        
        # Try to fetch ABI (simplified - in production you'd use Etherscan API)
        return None

    async def cache_abi(self, contract_address: str, abi: List[Dict]) -> None:
        """Cache ABI in Redis."""
        if not self.redis:
            return
            
        cache_key = f"abi:{contract_address}"
        self.redis.setex(cache_key, 86400, json.dumps(abi))  # Cache for 24 hours

    async def get_latest_block_number(self) -> int:
        """Get the latest block number."""
        if not self.w3:
            await self._connect_to_rpc()
            
        try:
            return self.w3.eth.block_number
        except Exception as e:
            logger.error("get_block_number_failed", error=str(e))
            await self._connect_to_rpc()  # Try to reconnect
            return self.w3.eth.block_number

    async def get_block(self, block_number: int) -> Dict[str, Any]:
        """Get block information."""
        if not self.w3:
            await self._connect_to_rpc()
            
        try:
            block = self.w3.eth.get_block(block_number, full_transactions=True)
            return {
                "number": block.number,
                "hash": block.hash.hex(),
                "timestamp": block.timestamp,
                "transactions": [tx.hex() for tx in block.transactions]
            }
        except Exception as e:
            logger.error("get_block_failed", block_number=block_number, error=str(e))
            raise

    async def get_logs(self, **kwargs) -> List[Dict]:
        """Get logs from blockchain."""
        if not self.w3:
            await self._connect_to_rpc()
            
        try:
            logs = self.w3.eth.get_logs(**kwargs)
            return [log.__dict__ for log in logs]
        except Exception as e:
            logger.error("get_logs_failed", error=str(e), kwargs=kwargs)
            raise

    async def subscribe_to_events(self, contract_address: str, event_abi: List[Dict], callback):
        """Subscribe to contract events (WebSocket only)."""
        if not self.w3 or not hasattr(self.w3.provider, 'ws'):
            logger.warning("websocket_not_available")
            return
            
        try:
            contract = self.w3.eth.contract(address=contract_address, abi=event_abi)
            
            # Create event filter
            event_filter = contract.events[event_abi[0]["name"]].create_filter(fromBlock="latest")
            
            # Poll for new events
            while True:
                try:
                    for event in event_filter.get_new_entries():
                        await callback(event)
                    await asyncio.sleep(1)  # Poll every second
                except Exception as e:
                    logger.error("event_polling_error", error=str(e))
                    await asyncio.sleep(5)  # Wait before retry
                    
        except Exception as e:
            logger.error("subscribe_events_failed", error=str(e))
            raise

    async def close(self) -> None:
        """Close connections."""
        if self.session:
            await self.session.close()
        if self.redis:
            self.redis.close()


# Global client instance
web3_client = AsyncWeb3Client()