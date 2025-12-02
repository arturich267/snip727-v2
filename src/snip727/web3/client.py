"""Async Web3 client with Redis caching and free RPC support."""
import asyncio
import json
import structlog
from typing import Any, Dict, List, Optional
import aiohttp
import redis.asyncio as redis
from web3 import Web3
from web3.providers.async_rpc import AsyncHTTPProvider

from snip727.core.config import get_settings

logger = structlog.get_logger()

# Free RPC endpoints that work in Russia without VPN
FREE_RPC_URLS = [
    "https://ethereum.publicnode.com",
    "https://rpc.ankr.com/eth",
    "https://eth.llamarpc.com",
    "https://ethereum.publicnode.com",
    "https://rpc.flashbots.net",
    "https://mainnet.eth.cloud.ava.do",
]


class AsyncWeb3Client:
    """Async Web3 client with failover and Redis caching."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.rpc_urls = FREE_RPC_URLS
        self.current_rpc_index = 0
        self.w3: Optional[Web3] = None
        self.redis_client: Optional[redis.Redis] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize Web3 client and Redis connection."""
        await self._connect_redis()
        await self._connect_web3()

    async def _connect_redis(self) -> None:
        """Connect to Redis."""
        try:
            self.redis_client = redis.from_url(self.settings.redis_url)
            await self.redis_client.ping()
            logger.info("redis_connected")
        except Exception as e:
            logger.error("redis_connection_failed", error=str(e))
            raise

    async def _connect_web3(self) -> None:
        """Connect to Web3 with failover."""
        for i in range(len(self.rpc_urls)):
            rpc_url = self.rpc_urls[self.current_rpc_index]
            try:
                self.session = aiohttp.ClientSession()
                provider = AsyncHTTPProvider(rpc_url, request_kwargs={'timeout': 30})
                self.w3 = Web3(provider, modules={'eth': []}, middlewares=[])
                
                # Test connection
                await self.w3.eth.chain_id
                logger.info("web3_connected", rpc_url=rpc_url)
                return
            except Exception as e:
                logger.warning("web3_connection_failed", rpc_url=rpc_url, error=str(e))
                self.current_rpc_index = (self.current_rpc_index + 1) % len(self.rpc_urls)
                if self.session:
                    await self.session.close()
        
        raise Exception("Failed to connect to any RPC endpoint")

    async def get_cached_data(self, key: str) -> Optional[Any]:
        """Get cached data from Redis."""
        if not self.redis_client:
            return None
        try:
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning("redis_cache_get_failed", key=key, error=str(e))
        return None

    async def set_cached_data(self, key: str, data: Any, ttl: int = 300) -> None:
        """Set cached data in Redis."""
        if not self.redis_client:
            return
        try:
            await self.redis_client.setex(key, ttl, json.dumps(data))
        except Exception as e:
            logger.warning("redis_cache_set_failed", key=key, error=str(e))

    async def get_block_number(self) -> int:
        """Get current block number with caching."""
        cache_key = "block_number"
        cached = await self.get_cached_data(cache_key)
        if cached:
            return cached

        if not self.w3:
            raise Exception("Web3 not initialized")

        try:
            block_number = await self.w3.eth.block_number
            await self.set_cached_data(cache_key, block_number, ttl=10)
            return block_number
        except Exception as e:
            logger.error("get_block_number_failed", error=str(e))
            await self._try_failover()
            raise

    async def get_logs(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get logs with caching."""
        cache_key = f"logs_{hash(str(sorted(kwargs.items())))}"
        cached = await self.get_cached_data(cache_key)
        if cached:
            return cached

        if not self.w3:
            raise Exception("Web3 not initialized")

        try:
            logs = await self.w3.eth.get_logs(**kwargs)
            await self.set_cached_data(cache_key, logs, ttl=60)
            return logs
        except Exception as e:
            logger.error("get_logs_failed", error=str(e))
            await self._try_failover()
            raise

    async def get_transaction_receipt(self, tx_hash: str) -> Dict[str, Any]:
        """Get transaction receipt."""
        if not self.w3:
            raise Exception("Web3 not initialized")

        try:
            receipt = await self.w3.eth.get_transaction_receipt(tx_hash)
            return receipt
        except Exception as e:
            logger.error("get_transaction_receipt_failed", tx_hash=tx_hash, error=str(e))
            await self._try_failover()
            raise

    async def _try_failover(self) -> None:
        """Try to failover to next RPC endpoint."""
        async with self._lock:
            logger.info("attempting_failover")
            if self.session:
                await self.session.close()
            self.current_rpc_index = (self.current_rpc_index + 1) % len(self.rpc_urls)
            await self._connect_web3()

    async def close(self) -> None:
        """Close connections."""
        if self.session:
            await self.session.close()
        if self.redis_client:
            await self.redis_client.close()


# Global client instance
_client: Optional[AsyncWeb3Client] = None


async def get_web3_client() -> AsyncWeb3Client:
    """Get global Web3 client instance."""
    global _client
    if _client is None:
        _client = AsyncWeb3Client()
        await _client.initialize()
    return _client


async def close_web3_client() -> None:
    """Close global Web3 client."""
    global _client
    if _client:
        await _client.close()
        _client = None