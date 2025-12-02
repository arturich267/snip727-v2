from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PairSchema(BaseModel):
    """Uniswap pair schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    pair_address: str = Field(..., description="Pair contract address")
    token0: str = Field(..., description="First token address")
    token1: str = Field(..., description="Second token address")
    pool_type: str = Field(..., description="V2 or V3")
    fee: int | None = Field(None, description="Pool fee for V3")
    liquidity: float | None = Field(None, description="Current liquidity")
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TradeSchema(BaseModel):
    """Trade execution schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    pair_address: str
    tx_hash: str
    amount_in: float
    amount_out: float
    slippage: float
    gas_used: float | None = None
    profit: float | None = None
    status: str = Field(..., description="pending, completed, failed")
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SentimentSchema(BaseModel):
    """Sentiment analysis schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    pair_address: str
    score: float = Field(..., ge=-1.0, le=1.0)
    source: str
    data: str | None = None
    created_at: datetime | None = None
