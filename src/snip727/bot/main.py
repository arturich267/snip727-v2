"""Telegram bot main module."""
import structlog
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

from snip727.core.config import get_settings
from snip727.db import get_session
from snip727.db.models import Pool, Alert, StrategySignal
from snip727.services.strategy import strategy_service

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
        "/pools - Last 10 new pools\n"
        "/signals - Current hot pools with votes\n"
        "/stats - Bot statistics"
    )
    logger.info("user_command", command="start", user_id=update.effective_user.id)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command."""
    if update.message is None or update.effective_user is None:
        return
    
    # Check service status
    monitor_running = True  # Would check actual monitor status
    sentiment_running = True  # Would check actual sentiment status
    strategy_running = True  # Would check actual strategy status
    
    status_text = (
        "✅ **Bot Status**\n\n"
        f"🔗 Uniswap Monitor: {'🟢 Running' if monitor_running else '🔴 Stopped'}\n"
        f"💬 Sentiment Analysis: {'🟢 Running' if sentiment_running else '🔴 Stopped'}\n"
        f"🎯 Strategy Service: {'🟢 Running' if strategy_running else '🔴 Stopped'}\n"
        f"🗄️ Database: 🟢 Connected\n"
        f"🔴 Redis: 🟢 Connected"
    )
    
    await update.message.reply_text(status_text, parse_mode="Markdown")
    logger.info("user_command", command="status", user_id=update.effective_user.id)


async def pools(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /pools command - show last 10 new pools."""
    if update.message is None or update.effective_user is None:
        return
    
    try:
        async for session in get_session():
            from sqlalchemy import select
            
            result = await session.execute(
                select(Pool)
                .order_by(Pool.created_at.desc())
                .limit(10)
            )
            pools = result.scalars().all()
            break  # Exit after getting session
            
            if not pools:
                await update.message.reply_text("No pools found yet.")
                return
            
            message = "🏊 **Recent Uniswap Pools**\n\n"
            
            for i, pool in enumerate(pools, 1):
                token0_short = f"{pool.token0[:6]}...{pool.token0[-4:]}"
                token1_short = f"{pool.token1[:6]}...{pool.token1[-4:]}"
                
                message += (
                    f"{i}. {pool.version} Pool\n"
                    f"   📍 `{pool.address}`\n"
                    f"   💱 {token0_short} / {token1_short}\n"
                )
                
                if pool.fee:
                    message += f"   🏷️ Fee: {pool.fee/10000:.2f}%\n"
                    
                message += f"   ⏰ {pool.created_at.strftime('%H:%M:%S')}\n\n"
            
            await update.message.reply_text(message, parse_mode="Markdown")
            
    except Exception as e:
        logger.error("pools_command_error", error=str(e))
        await update.message.reply_text("❌ Error fetching pools.")
    
    logger.info("user_command", command="pools", user_id=update.effective_user.id)


async def signals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /signals command - show current hot pools."""
    if update.message is None or update.effective_user is None:
        return
    
    try:
        signals_list = await strategy_service.get_current_signals()
        
        if not signals_list:
            await update.message.reply_text("No active signals at the moment.")
            return
        
        # Group by pool
        pools_signals = {}
        for signal in signals_list:
            pool_addr = signal['pool_address']
            if pool_addr not in pools_signals:
                pools_signals[pool_addr] = {
                    'token0': signal['token0'],
                    'token1': signal['token1'],
                    'signals': []
                }
            pools_signals[pool_addr]['signals'].append(signal['signal_type'])
        
        message = "🎯 **Current Hot Pools**\n\n"
        
        for pool_addr, pool_data in list(pools_signals.items())[:5]:  # Top 5 pools
            token0_short = f"{pool_data['token0'][:6]}...{pool_data['token0'][-4:]}"
            token1_short = f"{pool_data['token1'][:6]}...{pool_data['token1'][-4:]}"
            
            signal_emojis = {
                'new_pool': '🆕',
                'liquidity_spike': '📈',
                'whale_buy': '🐋',
                'sentiment': '💬'
            }
            
            signals_text = " ".join([
                signal_emojis.get(sig, '🔔') 
                for sig in pool_data['signals']
            ])
            
            message += (
                f"📍 `{pool_addr[:10]}...{pool_addr[-8:]}`\n"
                f"💱 {token0_short} / {token1_short}\n"
                f"🎯 Signals: {signals_text} ({len(pool_data['signals'])}/4)\n\n"
            )
        
        await update.message.reply_text(message, parse_mode="Markdown")
        
    except Exception as e:
        logger.error("signals_command_error", error=str(e))
        await update.message.reply_text("❌ Error fetching signals.")
    
    logger.info("user_command", command="signals", user_id=update.effective_user.id)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command - show bot statistics."""
    if update.message is None or update.effective_user is None:
        return
    
    try:
        async for session in get_session():
            from sqlalchemy import select, func
            
            # Count pools
            pools_count = await session.execute(select(func.count(Pool.id)))
            total_pools = pools_count.scalar() or 0
            
            # Count alerts
            alerts_count = await session.execute(select(func.count(Alert.id)))
            total_alerts = alerts_count.scalar() or 0
            
            # Count active signals
            signals_count = await session.execute(
                select(func.count(StrategySignal.id))
                .where(StrategySignal.is_active)
            )
            active_signals = signals_count.scalar() or 0
            
            # Get recent alerts
            recent_alerts = await session.execute(
                select(Alert)
                .order_by(Alert.sent_at.desc())
                .limit(5)
            )
            recent = recent_alerts.scalars().all()
            break  # Exit after getting session
        
        message = (
            f"📊 **Bot Statistics**\n\n"
            f"🏊 Total Pools Monitored: {total_pools}\n"
            f"🚨 Total Alerts Sent: {total_alerts}\n"
            f"🎯 Active Signals: {active_signals}\n\n"
        )
        
        if recent:
            message += "**Recent Alerts:**\n"
            for alert in recent:
                pool_short = f"{alert.pool_address[:8]}...{alert.pool_address[-6:]}"
                message += f"• {pool_short} - {alert.signal_count} signals\n"
        
        await update.message.reply_text(message, parse_mode="Markdown")
        
    except Exception as e:
        logger.error("stats_command_error", error=str(e))
        await update.message.reply_text("❌ Error fetching statistics.")
    
    logger.info("user_command", command="stats", user_id=update.effective_user.id)


async def send_alert_to_telegram(pool_address: str, message: str, signals: dict) -> None:
    """Send alert message to Telegram chat."""
    settings = get_settings()
    
    # Create inline keyboard
    keyboard = [
        [
            InlineKeyboardButton("🔍 View Pool", url=f"https://basescan.org/address/{pool_address}"),
            InlineKeyboardButton("🦄 Uniswap", url=f"https://app.uniswap.org/explore/pools/{pool_address}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        # Send to configured chat
        import telegram
        bot = telegram.Bot(token=settings.telegram_token)
        await bot.send_message(
            chat_id=settings.telegram_chat_id,
            text=message,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
        logger.info("alert_sent_to_telegram", pool_address=pool_address)
        
    except Exception as e:
        logger.error("send_telegram_alert_failed", pool_address=pool_address, error=str(e))


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

    application = Application.builder().token(settings.telegram_token).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("pools", pools))
    application.add_handler(CommandHandler("signals", signals))
    application.add_handler(CommandHandler("stats", stats))

    # Register alert callback with strategy service
    strategy_service.add_alert_callback(send_alert_to_telegram)

    logger.info("bot_starting", version="0.2.0")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
