from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class Pair(Base):
    """Uniswap pair model."""

    __tablename__ = "pairs"

    id: Mapped[int] = mapped_column(primary_key=True)
    pair_address: Mapped[str] = mapped_column(String(42), unique=True, index=True)
    token0: Mapped[str] = mapped_column(String(42), index=True)
    token1: Mapped[str] = mapped_column(String(42), index=True)
    pool_type: Mapped[str] = mapped_column(String(10))  # V2 or V3
    fee: Mapped[int | None] = mapped_column(nullable=True)
    liquidity: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Trade(Base):
    """Trade execution model."""

    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(primary_key=True)
    pair_address: Mapped[str] = mapped_column(String(42), index=True)
    tx_hash: Mapped[str] = mapped_column(String(66), unique=True, index=True)
    amount_in: Mapped[float] = mapped_column(Float)
    amount_out: Mapped[float] = mapped_column(Float)
    slippage: Mapped[float] = mapped_column(Float)
    gas_used: Mapped[float | None] = mapped_column(Float, nullable=True)
    profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20))  # pending, completed, failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Sentiment(Base):
    """Sentiment analysis model."""

    __tablename__ = "sentiments"

    id: Mapped[int] = mapped_column(primary_key=True)
    pair_address: Mapped[str] = mapped_column(String(42), index=True)
    score: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(50))
    data: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
