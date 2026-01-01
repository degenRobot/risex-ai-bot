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


class MarketContext(BaseModel):
    """Market context at the time of decision."""
    btc_price: float
    eth_price: float
    btc_change: float
    eth_change: float
    timestamp: datetime = datetime.now()


class TradingDecisionLog(BaseModel):
    """Comprehensive log of trading decision with full context."""
    id: str
    account_id: str
    persona_name: str
    
    # Market context
    market_context: MarketContext
    
    # Account state
    available_balance: float
    current_positions: dict  # {"BTC": 0.01, "ETH": 0.0}
    total_pnl: float
    
    # Recent social activity
    recent_posts: List[str]
    
    # AI Decision
    decision: TradeDecision
    
    # Execution result
    executed: bool
    execution_details: Optional[dict] = None  # Trade result if executed
    
    # Outcome tracking (to be filled later)
    outcome_tracked: bool = False
    outcome_pnl: Optional[float] = None
    outcome_reasoning: Optional[str] = None
    
    timestamp: datetime = datetime.now()


class TradingSession(BaseModel):
    """A complete trading session with decisions and outcomes."""
    id: str
    account_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    decisions: List[TradingDecisionLog] = []
    session_pnl: float = 0.0
    total_trades: int = 0
    successful_trades: int = 0