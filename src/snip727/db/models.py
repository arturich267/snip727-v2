"""Database models for snip727-v2."""
from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Pool(Base):
    """Uniswap pool information."""
    __tablename__ = "pools"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String(42), unique=True, index=True, nullable=False)
    token0 = Column(String(42), nullable=False)
    token1 = Column(String(42), nullable=False)
    fee = Column(Integer, nullable=True)  # V3 pools only
    version = Column(String(10), nullable=False)  # "V2" or "V3"
    factory = Column(String(42), nullable=False)
    block_number = Column(BigInteger, nullable=False)
    block_timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    trade_events = relationship("TradeEvent", back_populates="pool")
    sentiment_scores = relationship("SentimentScore", back_populates="pool")


class TradeEvent(Base):
    """Trade events (Mint/Swap) in pools."""
    __tablename__ = "trade_events"

    id = Column(Integer, primary_key=True, index=True)
    pool_address = Column(String(42), ForeignKey("pools.address"), nullable=False)
    event_type = Column(String(20), nullable=False)  # "Mint", "Swap", "Burn"
    transaction_hash = Column(String(66), nullable=False)
    block_number = Column(BigInteger, nullable=False)
    block_timestamp = Column(DateTime, nullable=False)
    log_index = Column(Integer, nullable=False)
    
    # Swap-specific fields
    amount0_in = Column(Float, nullable=True)
    amount1_in = Column(Float, nullable=True)
    amount0_out = Column(Float, nullable=True)
    amount1_out = Column(Float, nullable=True)
    
    # Mint-specific fields
    amount0 = Column(Float, nullable=True)
    amount1 = Column(Float, nullable=True)
    
    # Calculated fields
    usd_value = Column(Float, nullable=True)
    is_whale = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    pool = relationship("Pool", back_populates="trade_events")


class SentimentScore(Base):
    """Sentiment analysis scores."""
    __tablename__ = "sentiment_scores"

    id = Column(Integer, primary_key=True, index=True)
    pool_address = Column(String(42), ForeignKey("pools.address"), nullable=True)
    source = Column(String(100), nullable=False)  # "telegram", "twitter", etc.
    content = Column(Text, nullable=False)
    score = Column(Float, nullable=False)  # -1.0 to 1.0
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    pool = relationship("Pool", back_populates="sentiment_scores")


class StrategySignal(Base):
    """Strategy signals for pools."""
    __tablename__ = "strategy_signals"

    id = Column(Integer, primary_key=True, index=True)
    pool_address = Column(String(42), ForeignKey("pools.address"), nullable=False)
    signal_type = Column(String(50), nullable=False)  # "new_pool", "liquidity_spike", "whale_buy", "sentiment"
    signal_value = Column(Float, nullable=True)  # numeric value of the signal
    is_active = Column(Boolean, default=True, nullable=False)
    block_number = Column(BigInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    pool = relationship("Pool")


class Alert(Base):
    """Telegram alerts sent."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    pool_address = Column(String(42), ForeignKey("pools.address"), nullable=False)
    alert_type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    signal_count = Column(Integer, nullable=False)
    sentiment_score = Column(Float, nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    pool = relationship("Pool")