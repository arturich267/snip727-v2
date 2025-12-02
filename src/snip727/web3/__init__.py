"""Web3 integration module."""
from web3 import Web3

from snip727.core.config import get_settings

settings = get_settings()

w3 = Web3(Web3.HTTPProvider(settings.web3_provider_url))
