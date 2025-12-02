import structlog

logger = structlog.get_logger()


class MonitoringService:
    """Uniswap pair monitoring service."""

    def __init__(self) -> None:
        """Initialize monitoring service."""
        self.logger = structlog.get_logger(self.__class__.__name__)

    async def start_monitoring(self) -> None:
        """Start monitoring pairs."""
        self.logger.info("Monitoring service started")

    async def stop_monitoring(self) -> None:
        """Stop monitoring pairs."""
        self.logger.info("Monitoring service stopped")
