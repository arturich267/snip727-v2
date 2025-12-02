"""Main application entry point for snip727-v2."""
import asyncio
import signal
import sys
import structlog

from snip727.core.config import get_settings
from snip727.db.models import Base
from snip727.db import engine
from snip727.web3.monitor import uniswap_monitor
from snip727.services.sentiment import sentiment_analyzer
from snip727.services.strategy import strategy_service

logger = structlog.get_logger()


class Snip727App:
    """Main application class."""
    
    def __init__(self):
        self.settings = get_settings()
        self.running = False
        self.tasks = []
        
    async def initialize(self) -> None:
        """Initialize all services."""
        logger.info("initializing_snip727_app")
        
        # Create database tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("database_tables_created")
        
        # Initialize services
        await sentiment_analyzer.initialize()
        await strategy_service.start()
        
        # Register strategy alert callback
        strategy_service.add_alert_callback(self._handle_strategy_alert)
        
        logger.info("services_initialized")
        
    async def start_services(self) -> None:
        """Start all monitoring services."""
        self.running = True
        
        # Start Uniswap monitor
        monitor_task = asyncio.create_task(self._run_monitor())
        self.tasks.append(monitor_task)
        
        # Start sentiment analysis
        sentiment_task = asyncio.create_task(sentiment_analyzer.start_continuous_analysis())
        self.tasks.append(sentiment_task)
        
        logger.info("monitoring_services_started")
        
    async def _run_monitor(self) -> None:
        """Run Uniswap monitor with error handling."""
        while self.running:
            try:
                await uniswap_monitor.start()
            except Exception as e:
                logger.error("monitor_crashed", error=str(e))
                await asyncio.sleep(30)  # Wait before restart
                
    async def _handle_strategy_alert(self, pool_address: str, message: str, signals: dict) -> None:
        """Handle strategy alerts."""
        logger.info("strategy_alert_received", pool_address=pool_address, signal_count=len(signals))
        
        # Here you could add additional alert handling
        # The bot already handles Telegram alerts
        
    async def shutdown(self) -> None:
        """Gracefully shutdown all services."""
        logger.info("shutting_down_snip727_app")
        
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
            
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Stop services
        await uniswap_monitor.stop()
        await sentiment_analyzer.close()
        await strategy_service.stop()
        
        logger.info("snip727_app_shutdown_complete")
        
    def run(self) -> None:
        """Run the application."""
        asyncio.run(self._run_async())
        
    async def _run_async(self) -> None:
        """Run the application asynchronously."""
        # Setup signal handlers
        def signal_handler(signum, frame):
            logger.info("signal_received", signum=signum)
            asyncio.create_task(self.shutdown())
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Initialize
            await self.initialize()
            
            # Start services
            await self.start_services()
            
            # Start bot (blocking)
            logger.info("starting_telegram_bot")
            # Note: bot_main is blocking, so we run it in the main task
            # In a real implementation, you might want to integrate it differently
            
            # For now, we'll run the bot in a separate task
            bot_task = asyncio.create_task(self._run_bot())
            self.tasks.append(bot_task)
            
            # Keep running until shutdown
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("keyboard_interrupt")
        except Exception as e:
            logger.error("app_crashed", error=str(e))
        finally:
            await self.shutdown()
            
    async def _run_bot(self) -> None:
        """Run Telegram bot."""
        try:
            # This is a simplified approach
            # In production, you'd integrate the bot better with asyncio
            from telegram.ext import Application
            
            application = Application.builder().token(self.settings.telegram_token).build()
            
            # Add handlers (simplified)
            from snip727.bot.main import start, status, pools, signals, stats
            from telegram.ext import CommandHandler
            
            application.add_handler(CommandHandler("start", start))
            application.add_handler(CommandHandler("status", status))
            application.add_handler(CommandHandler("pools", pools))
            application.add_handler(CommandHandler("signals", signals))
            application.add_handler(CommandHandler("stats", stats))
            
            await application.initialize()
            await application.start()
            await application.updater.start_polling()
            
            # Keep bot running
            while self.running:
                await asyncio.sleep(1)
                
            await application.updater.stop()
            await application.stop()
            await application.shutdown()
            
        except Exception as e:
            logger.error("bot_error", error=str(e))


async def main() -> None:
    """Main entry point."""
    app = Snip727App()
    await app._run_async()


if __name__ == "__main__":
    # For direct execution, run the full app
    if len(sys.argv) > 1 and sys.argv[1] == "bot-only":
        # Run bot only (for testing)
        from snip727.bot.main import main
        main()
    else:
        # Run full app
        app = Snip727App()
        app.run()