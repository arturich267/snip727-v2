from web3 import AsyncHTTPProvider, AsyncWeb3

from src.core.config import Settings


class Web3Client:
    """Async Web3 client wrapper."""

    def __init__(self, settings: Settings) -> None:
        """Initialize Web3 client."""
        self.settings = settings
        self.w3 = AsyncWeb3(
            AsyncHTTPProvider(settings.web3_provider_url)
        )

    async def is_connected(self) -> bool:
        """Check if Web3 is connected."""
        return await self.w3.is_connected()

    async def get_block_number(self) -> int:
        """Get current block number."""
        return await self.w3.eth.block_number

    async def get_gas_price(self) -> int:
        """Get current gas price."""
        return await self.w3.eth.gas_price

    async def get_balance(self, address: str) -> int:
        """Get account balance."""
        return await self.w3.eth.get_balance(address)

    def is_address(self, address: str) -> bool:
        """Check if valid address format."""
        return self.w3.is_address(address)

    def to_checksum_address(self, address: str) -> str:
        """Convert to checksum address."""
        return self.w3.to_checksum_address(address)
