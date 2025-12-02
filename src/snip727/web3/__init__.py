"""Web3 integration module."""
from web3 import Web3

from snip727.core.config import get_settings
from snip727.web3.client import web3_client
from snip727.web3.monitor import uniswap_monitor

settings = get_settings()

w3 = Web3(Web3.HTTPProvider(settings.web3_provider_url))

__all__ = ["w3", "web3_client", "uniswap_monitor"]
