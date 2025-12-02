"""Database models for pools, events, and sentiment scores."""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Column, DateTime, Float, Integer, String, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Pool(Base):
    """Uniswap pool information."""
    __tablename__ = "pools"
    
    id = Column(Integer, primary_key=True, index=True)
    address = Column(String(42), unique=True, index=True, nullable=False)
    token0 = Column(String(42), nullable=False)
    token1 = Column(String(42), nullable=False)
    pool_type = Column(String(10), nullable=False)  # "v2" or "v3"
    fee = Column(Integer, nullable=True)  # V3 pools only
    created_at_block = Column(BigInteger, nullable=False)
    created_at_tx = Column(String(66), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Additional metadata
    token0_symbol = Column(String(20), nullable=True)
    token1_symbol = Column(String(20), nullable=True)
    token0_decimals = Column(Integer, nullable=True)
    token1_decimals = Column(Integer, nullable=True)


class TradeEvent(Base):
    """Trading events in pools."""
    __tablename__ = "trade_events"
    
    id = Column(Integer, primary_key=True, index=True)
    pool_address = Column(String(42), index=True, nullable=False)
    event_type = Column(String(20), nullable=False)  # "mint", "swap", "burn"
    block_number = Column(BigInteger, nullable=False)
    transaction_hash = Column(String(66), nullable=False)
    log_index = Column(Integer, nullable=False)
    
    # Event-specific data
    sender = Column(String(42), nullable=True)
    recipient = Column(String(42), nullable=True)
    amount0_in = Column(Float, nullable=True)
    amount1_in = Column(Float, nullable=True)
    amount0_out = Column(Float, nullable=True)
    amount1_out = Column(Float, nullable=True)
    estimated_usd = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Additional JSON data for flexible storage
    extra_data = Column(Text, nullable=True)


class SentimentScore(Base):
    """Sentiment analysis results."""
    __tablename__ = "sentiment_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    pool_address = Column(String(42), index=True, nullable=False)
    text_analyzed = Column(Text, nullable=False)
    sentiment_score = Column(Integer, nullable=False)  # -1, 0, or 1
    confidence = Column(Float, nullable=False)
    
    # Model information
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(20), nullable=True)
    
    # Context
    event_type = Column(String(20), nullable=True)
    block_number = Column(BigInteger, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Signal(Base):
    """Generated trading signals."""
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    pool_address = Column(String(42), index=True, nullable=False)
    signal_type = Column(String(20), nullable=False)  # "new_pool", "liquidity_spike", "whale_buy"
    confidence = Column(Float, nullable=False)
    
    # Strategy information
    strategy_name = Column(String(50), default="nof4")
    signal_count = Column(Integer, nullable=False)  # Number of signals contributing
    
    # Sentiment context
    sentiment_score = Column(Integer, nullable=True)
    sentiment_confidence = Column(Float, nullable=True)
    
    # Event context
    related_events = Column(Text, nullable=True)  # JSON array of related event IDs
    
    created_at = Column(DateTime, default=datetime.utcnow)
    triggered_at = Column(DateTime, nullable=True)  # When alert was sent
    is_triggered = Column(Boolean, default=False)
    
    # Additional data
    extra_data = Column(Text, nullable=True)  # JSON for additional signal data


class AlertLog(Base):
    """Log of sent alerts."""
    __tablename__ = "alert_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    pool_address = Column(String(42), index=True, nullable=False)
    signal_id = Column(Integer, nullable=True)
    alert_type = Column(String(20), nullable=False)
    
    # Alert content
    message = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    
    # Delivery information
    delivery_method = Column(String(20), default="telegram")  # "telegram", "webhook", etc.
    delivery_status = Column(String(20), default="sent")  # "sent", "failed", "pending"
    delivery_response = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)