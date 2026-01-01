"""Pydantic models for the RISE AI trading bot."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class TradingStyle(str, Enum):
    """Available trading style personas."""
    AGGRESSIVE = "aggressive"      # High leverage, frequent trades
    CONSERVATIVE = "conservative"  # Low leverage, careful entries
    CONTRARIAN = "contrarian"      # Goes against the crowd
    MOMENTUM = "momentum"          # Follows trends
    DEGEN = "degen"               # YOLO mode


class Persona(BaseModel):
    """AI trading persona derived from social profile."""
    name: str
    handle: str
    bio: str
    trading_style: TradingStyle
    risk_tolerance: float  # 0.0 to 1.0
    favorite_assets: List[str]
    personality_traits: List[str]
    sample_posts: List[str]
    created_at: datetime = datetime.now()


class Account(BaseModel):
    """Trading account with wallet and persona."""
    id: str
    address: str
    private_key: str
    signer_key: str
    persona: Optional[Persona] = None
    is_active: bool = True
    created_at: datetime = datetime.now()


class Trade(BaseModel):
    """Trade record with AI reasoning."""
    id: str
    account_id: str
    market_id: int
    side: str  # "buy" or "sell"
    size: float
    price: float
    reasoning: str  # AI explanation
    timestamp: datetime
    tx_hash: Optional[str] = None
    status: str = "pending"


class TradeDecision(BaseModel):
    """AI's trade decision with reasoning."""
    should_trade: bool
    action: Optional[str] = None  # "buy", "sell", "close"
    market: Optional[str] = None  # "BTC", "ETH"
    size_percent: Optional[float] = None  # % of available margin
    confidence: float
    reasoning: str