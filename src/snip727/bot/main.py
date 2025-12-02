"""Telegram bot main module."""
import asyncio
import structlog
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from snip727.core.config import get_settings
from snip727.services.strategy import get_strategy
from snip727.web3.monitor import UniswapMonitor, PoolEvent
from snip727.web3.client import get_web3_client

logger = structlog.get_logger()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if update.message is None or update.effective_user is None:
        return
    await update.message.reply_text(
        "🤖 snip727-v2 DeFi Sniping Bot\n\n"
        "Available commands:\n"
        "/start - Show this message\n"
        "/status - Show bot status\n"
        "/pools - Show monitored pools\n"
        "/signals - Show recent signals\n"
        "/stats - Show statistics"
    )
    logger.info("user_command", command="start", user_id=update.effective_user.id)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command."""
    if update.message is None or update.effective_user is None:
        return
    
    try:
        strategy = get_strategy()
        stats = strategy.get_pool_stats()
        
        await update.message.reply_text(
            f"✅ Bot is running\n"
            f"📊 Monitored Pools: {stats['monitored_pools']}\n"
            f"📈 Total Events: {stats['total_events']}\n"
            f"🔔 Total Signals: {stats['total_signals']}\n"
            f"⚡ Recent Activity (1h): {stats['recent_signals_last_hour']} signals\n"
            f"🔗 Database: Connected\n"
            f"🗄️ Redis: Connected"
        )
    except Exception as e:
        await update.message.reply_text("❌ Error getting status")
        logger.error("status_command_error", error=str(e))
    
    logger.info("user_command", command="status", user_id=update.effective_user.id)


async def pools(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /pools command."""
    if update.message is None or update.effective_user is None:
        return
    
    try:
        strategy = get_strategy()
        stats = strategy.get_pool_stats()
        
        if stats['monitored_pools'] == 0:
            await update.message.reply_text("🏊 No pools being monitored yet")
            return
        
        message = f"🏊 Monitoring {stats['monitored_pools']} pools\n\n"
        message += "Recent activity:\n"
        
        if stats['active_pools_last_hour'] > 0:
            message += f"• {stats['active_pools_last_hour']} pools active in last hour\n"
        else:
            message += "• No activity in last hour\n"
        
        message += f"\nSignal breakdown:\n"
        for signal_type, count in stats['signal_breakdown'].items():
            message += f"• {signal_type}: {count}\n"
        
        await update.message.reply_text(message)
        
    except Exception as e:
        await update.message.reply_text("❌ Error getting pool information")
        logger.error("pools_command_error", error=str(e))
    
    logger.info("user_command", command="pools", user_id=update.effective_user.id)


async def signals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /signals command."""
    if update.message is None or update.effective_user is None:
        return
    
    try:
        strategy = get_strategy()
        signals = strategy.get_recent_signals(limit=10)
        
        if not signals:
            await update.message.reply_text("📡 No recent signals")
            return
        
        message = "📡 Recent Signals:\n\n"
        for signal in signals:
            pool_short = signal['pool'][:8] + "..." + signal['pool'][-4:]
            message += f"• {signal['type'].upper()}\n"
            message += f"  Pool: {pool_short}\n"
            message += f"  Confidence: {signal['confidence']:.2f}\n"
            message += f"  Time: {signal['timestamp'].split('T')[1][:5]}\n\n"
        
        await update.message.reply_text(message)
        
    except Exception as e:
        await update.message.reply_text("❌ Error getting signals")
        logger.error("signals_command_error", error=str(e))
    
    logger.info("user_command", command="signals", user_id=update.effective_user.id)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command."""
    if update.message is None or update.effective_user is None:
        return
    
    try:
        strategy = get_strategy()
        stats = strategy.get_pool_stats()
        
        message = "📊 Bot Statistics:\n\n"
        message += f"🏊 Monitored Pools: {stats['monitored_pools']}\n"
        message += f"📈 Total Events: {stats['total_events']}\n"
        message += f"🔔 Total Signals: {stats['total_signals']}\n"
        message += f"⚡ Recent Activity (1h): {stats['recent_signals_last_hour']} signals\n"
        message += f"🎯 Active Pools (1h): {stats['active_pools_last_hour']}\n\n"
        
        if stats['signal_breakdown']:
            message += "Signal Types:\n"
            for signal_type, count in stats['signal_breakdown'].items():
                message += f"• {signal_type}: {count}\n"
        
        await update.message.reply_text(message)
        
    except Exception as e:
        await update.message.reply_text("❌ Error getting statistics")
        logger.error("stats_command_error", error=str(e))
    
    logger.info("user_command", command="stats", user_id=update.effective_user.id)


async def handle_pool_event(event: PoolEvent) -> None:
    """Handle pool events from monitor."""
    strategy = get_strategy()
    await strategy.process_event(event)


async def handle_alert(alert_data: dict) -> None:
    """Handle alerts from strategy."""
    settings = get_settings()
    
    # Send Telegram alert
    try:
        pool_short = alert_data['pool_address'][:8] + "..." + alert_data['pool_address'][-4:]
        signal_type = alert_data['signal_type'].upper()
        confidence = alert_data['confidence']
        sentiment = alert_data.get('sentiment', {}).get('sentiment', 0)
        sentiment_emoji = "🟢" if sentiment > 0 else "🔴" if sentiment < 0 else "🟡"
        
        message = f"🚨 {signal_type} Alert {sentiment_emoji}\n\n"
        message += f"Pool: {pool_short}\n"
        message += f"Confidence: {confidence:.2f}\n"
        message += f"Signals: {alert_data['signal_count']}\n"
        message += f"Sentiment: {sentiment:+d}\n\n"
        
        if alert_data['events']:
            message += "Recent Events:\n"
            for event in alert_data['events'][:3]:
                message += f"• {event['type']} (Block {event['block']})\n"
        
        # Send to configured chat
        if settings.telegram_chat_id:
            application = Application.builder().token(settings.telegram_token).build()
            await application.bot.send_message(chat_id=settings.telegram_chat_id, text=message)
        
        logger.info("alert_sent", pool=alert_data['pool_address'], signal_type=signal_type)
        
    except Exception as e:
        logger.error("alert_send_failed", error=str(e))


def main() -> None:
    """Start the bot."""
    settings = get_settings()

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    async def start_monitoring() -> None:
        """Start monitoring in background."""
        try:
            # Initialize strategy
            strategy = get_strategy()
            strategy.add_alert_callback(handle_alert)
            
            # Initialize and start monitor
            monitor = UniswapMonitor(handle_pool_event)
            await monitor.initialize()
            
            # Start monitoring in background
            asyncio.create_task(monitor.start())
            logger.info("monitoring_started")
            
        except Exception as e:
            logger.error("monitoring_start_failed", error=str(e))

    async def run_bot() -> None:
        """Run bot with monitoring."""
        # Start monitoring
        asyncio.create_task(start_monitoring())
        
        # Start bot
        application = Application.builder().token(settings.telegram_token).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("status", status))
        application.add_handler(CommandHandler("pools", pools))
        application.add_handler(CommandHandler("signals", signals))
        application.add_handler(CommandHandler("stats", stats))

        logger.info("bot_starting", version="0.1.0")
        await application.run_polling(allowed_updates=Update.ALL_TYPES)

    # Run async main
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()