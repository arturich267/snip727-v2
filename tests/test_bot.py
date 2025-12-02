"""Tests for Telegram bot commands."""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from telegram import Update, Message, User
from telegram.ext import ContextTypes

from snip727.bot.main import start, status, pools, signals, stats


@pytest.fixture
def mock_update():
    """Create mock Telegram update."""
    user = User(id=123, is_bot=False, first_name="Test")
    message = Message(message_id=1, date=None, chat=Mock(id=456), from_user=user, text="/test")
    update = Update(update_id=1, message=message)
    return update


@pytest.fixture
def mock_context():
    """Create mock Telegram context."""
    return Mock(spec=ContextTypes.DEFAULT_TYPE)


@pytest.mark.asyncio
async def test_start_command(mock_update, mock_context):
    """Test /start command."""
    mock_update.message.reply_text = AsyncMock()
    
    await start(mock_update, mock_context)
    
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "snip727-v2" in call_args
    assert "/start" in call_args
    assert "/status" in call_args
    assert "/pools" in call_args
    assert "/signals" in call_args
    assert "/stats" in call_args


@pytest.mark.asyncio
async def test_start_command_no_message(mock_context):
    """Test /start command with no message."""
    update = Mock(update_id=1, message=None)
    
    # Should not raise exception
    await start(update, mock_context)


@pytest.mark.asyncio
async def test_status_command(mock_update, mock_context):
    """Test /status command."""
    mock_update.message.reply_text = AsyncMock()
    
    with patch('snip727.bot.main.get_strategy') as mock_get_strategy:
        mock_strategy = Mock()
        mock_strategy.get_pool_stats.return_value = {
            'monitored_pools': 5,
            'total_events': 100,
            'total_signals': 25,
            'recent_signals_last_hour': 3,
            'active_pools_last_hour': 2,
            'signal_breakdown': {'new_pool': 5, 'liquidity_spike': 15, 'whale_buy': 5}
        }
        mock_get_strategy.return_value = mock_strategy
        
        await status(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "✅ Bot is running" in call_args
        assert "5" in call_args  # monitored pools
        assert "100" in call_args  # total events
        assert "25" in call_args  # total signals


@pytest.mark.asyncio
async def test_status_command_error(mock_update, mock_context):
    """Test /status command with error."""
    mock_update.message.reply_text = AsyncMock()
    
    with patch('snip727.bot.main.get_strategy') as mock_get_strategy:
        mock_get_strategy.side_effect = Exception("Test error")
        
        await status(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once_with("❌ Error getting status")


@pytest.mark.asyncio
async def test_pools_command_no_pools(mock_update, mock_context):
    """Test /pools command with no pools."""
    mock_update.message.reply_text = AsyncMock()
    
    with patch('snip727.bot.main.get_strategy') as mock_get_strategy:
        mock_strategy = Mock()
        mock_strategy.get_pool_stats.return_value = {
            'monitored_pools': 0,
            'active_pools_last_hour': 0,
            'signal_breakdown': {}
        }
        mock_get_strategy.return_value = mock_strategy
        
        await pools(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once_with("🏊 No pools being monitored yet")


@pytest.mark.asyncio
async def test_pools_command_with_pools(mock_update, mock_context):
    """Test /pools command with pools."""
    mock_update.message.reply_text = AsyncMock()
    
    with patch('snip727.bot.main.get_strategy') as mock_get_strategy:
        mock_strategy = Mock()
        mock_strategy.get_pool_stats.return_value = {
            'monitored_pools': 3,
            'active_pools_last_hour': 2,
            'signal_breakdown': {'new_pool': 1, 'liquidity_spike': 4, 'whale_buy': 2}
        }
        mock_get_strategy.return_value = mock_strategy
        
        await pools(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "🏊 Monitoring 3 pools" in call_args
        assert "2 pools active in last hour" in call_args
        assert "new_pool: 1" in call_args
        assert "liquidity_spike: 4" in call_args


@pytest.mark.asyncio
async def test_signals_command_no_signals(mock_update, mock_context):
    """Test /signals command with no signals."""
    mock_update.message.reply_text = AsyncMock()
    
    with patch('snip727.bot.main.get_strategy') as mock_get_strategy:
        mock_strategy = Mock()
        mock_strategy.get_recent_signals.return_value = []
        mock_get_strategy.return_value = mock_strategy
        
        await signals(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once_with("📡 No recent signals")


@pytest.mark.asyncio
async def test_signals_command_with_signals(mock_update, mock_context):
    """Test /signals command with signals."""
    mock_update.message.reply_text = AsyncMock()
    
    with patch('snip727.bot.main.get_strategy') as mock_get_strategy:
        mock_strategy = Mock()
        mock_strategy.get_recent_signals.return_value = [
            {
                'type': 'liquidity_spike',
                'pool': '0x123456789012345678901234567890',
                'confidence': 0.85,
                'timestamp': '2024-12-02T17:40:00',
                'data': {}
            },
            {
                'type': 'whale_buy',
                'pool': '0x0987654321098765432109876543210987654321',
                'confidence': 0.90,
                'timestamp': '2024-12-02T17:35:00',
                'data': {}
            }
        ]
        mock_get_strategy.return_value = mock_strategy
        
        await signals(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "📡 Recent Signals" in call_args
        assert "LIQUIDITY_SPIKE" in call_args
        assert "WHALE_BUY" in call_args
        assert "0x1234...7890" in call_args
        assert "0x0987...4321" in call_args


@pytest.mark.asyncio
async def test_stats_command(mock_update, mock_context):
    """Test /stats command."""
    mock_update.message.reply_text = AsyncMock()
    
    with patch('snip727.bot.main.get_strategy') as mock_get_strategy:
        mock_strategy = Mock()
        mock_strategy.get_pool_stats.return_value = {
            'monitored_pools': 10,
            'total_events': 500,
            'total_signals': 75,
            'recent_signals_last_hour': 8,
            'active_pools_last_hour': 4,
            'signal_breakdown': {'new_pool': 10, 'liquidity_spike': 40, 'whale_buy': 25}
        }
        mock_get_strategy.return_value = mock_strategy
        
        await stats(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "📊 Bot Statistics" in call_args
        assert "10" in call_args  # monitored pools
        assert "500" in call_args  # total events
        assert "75" in call_args  # total signals
        assert "8" in call_args  # recent signals last hour
        assert "4" in call_args  # active pools last hour