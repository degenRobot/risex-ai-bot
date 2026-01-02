"""
Trader profiles with immutable base personas and mutable current thinking.
"""

from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class RiskProfile(str, Enum):
    """Risk profile for leverage and market preferences."""
    ULTRA_CONSERVATIVE = "ultra_conservative"  # 1x leverage, majors only
    CONSERVATIVE = "conservative"  # 1-2x leverage, BTC/ETH
    MODERATE = "moderate"  # 2-5x leverage, top 10 cryptos
    AGGRESSIVE = "aggressive"  # 5-20x leverage, mid-caps included
    DEGEN = "degen"  # 20-100x leverage, any shitcoin


@dataclass
class BasePersona:
    """Immutable base personality that never changes."""
    name: str
    handle: str
    core_personality: str
    speech_style: str  # Reference to speech_styles.py
    risk_profile: RiskProfile
    base_traits: List[str]
    core_beliefs: Dict[str, str]
    decision_style: str
    
    def __post_init__(self):
        # Make immutable by freezing after init
        object.__setattr__(self, '_frozen', True)
    
    def __setattr__(self, name, value):
        if hasattr(self, '_frozen') and self._frozen:
            raise AttributeError(f"Cannot modify immutable BasePersona attribute '{name}'")
        super().__setattr__(name, value)


@dataclass
class CurrentThinking:
    """Mutable current state influenced by market data and conversations."""
    market_outlooks: Dict[str, Dict] = field(default_factory=dict)  # Asset -> outlook info
    trading_biases: List[Dict] = field(default_factory=list)  # Current biases
    active_positions: Dict[str, Dict] = field(default_factory=dict)  # Current positions
    recent_influences: List[Dict] = field(default_factory=list)  # Chat influences
    confidence_levels: Dict[str, float] = field(default_factory=dict)  # Asset -> confidence
    last_updated: Optional[datetime] = None
    
    def update_market_outlook(self, asset: str, outlook: str, reasoning: str, confidence: float = 0.5):
        """Update market outlook for an asset."""
        self.market_outlooks[asset] = {
            "outlook": outlook,
            "reasoning": reasoning,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
        self.last_updated = datetime.now()
    
    def add_influence(self, source: str, message: str, impact: str):
        """Add a new influence from chat or market data."""
        self.recent_influences.append({
            "source": source,
            "message": message,
            "impact": impact,
            "timestamp": datetime.now().isoformat()
        })
        # Keep only last 20 influences
        if len(self.recent_influences) > 20:
            self.recent_influences = self.recent_influences[-20:]
        self.last_updated = datetime.now()


@dataclass
class TraderProfile:
    """Complete trader profile with base persona and current thinking."""
    base_persona: BasePersona
    current_thinking: CurrentThinking
    account_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def get_effective_personality(self) -> Dict:
        """Combine base persona with current thinking for decision making."""
        return {
            "base": {
                "name": self.base_persona.name,
                "core_personality": self.base_persona.core_personality,
                "risk_profile": self.base_persona.risk_profile.value,
                "speech_style": self.base_persona.speech_style,
                "core_beliefs": self.base_persona.core_beliefs
            },
            "current": {
                "market_outlooks": self.current_thinking.market_outlooks,
                "trading_biases": self.current_thinking.trading_biases[-3:] if self.current_thinking.trading_biases else [],
                "confidence_levels": self.current_thinking.confidence_levels,
                "recent_influences": self.current_thinking.recent_influences[-5:] if self.current_thinking.recent_influences else []
            }
        }


# Pre-defined fun profiles
CYNICAL_USER = BasePersona(
    name="Cynical Chad",
    handle="cynicalUser",
    core_personality="Extremely cynical trader who thinks everything goes to 0. Very hard to convince otherwise. Constantly bearish and pessimistic. Believes all crypto is a scam but trades it anyway for the volatility.",
    speech_style="financialAdvisor",  # Uses financial advisor speech from speech_styles
    risk_profile=RiskProfile.CONSERVATIVE,  # Cynical = low risk
    base_traits=[
        "extremely_pessimistic",
        "contrarian",
        "skeptical",
        "analytical",
        "risk_averse",
        "hard_to_convince"
    ],
    core_beliefs={
        "crypto": "All ponzis go to zero eventually",
        "markets": "Everything is manipulated by whales", 
        "trading": "Only short the scams, never go long",
        "risk": "Preserve capital at all costs",
        "people": "Everyone is trying to dump on you"
    },
    decision_style="Always looking for reasons to short. Requires overwhelming evidence to go long. Exits positions quickly on any bad news."
)


LEFT_CURVE = BasePersona(
    name="Drunk Wassie",
    handle="leftCurve", 
    core_personality="Simple-minded trader with drunk intuition. Makes decisions based on vibes and feelings. Often right for wrong reasons. Easily excited by any rumor.",
    speech_style="drunkWaifu",  # Drunk waifu speech style
    risk_profile=RiskProfile.AGGRESSIVE,  # Simple but not max degen
    base_traits=[
        "simple_minded",
        "intuitive",
        "easily_excited",
        "vibe_based",
        "accidentally_successful",
        "drunk_wisdom"
    ],
    core_beliefs={
        "crypto": "If it feels good, buy it!",
        "markets": "Markets go up when happy, down when sad",
        "trading": "Follow the vibes, ignore the charts",
        "risk": "More drinks = better trades",
        "people": "Everyone at bar is fren!"
    },
    decision_style="Makes simple gut-based decisions while intoxicated. Often accidentally successful. Buys what feels good, sells when scared."
)


MID_CURVE = BasePersona(
    name="Midwit McGee",
    handle="midCurve",
    core_personality="Chronic overthinker who gets lost in complexity. Reads every whitepaper, follows all influencers, uses 50 indicators. Paralyzed by analysis. Makes things harder than they need to be.",
    speech_style="smol",  # WassieSpeak (smol) style
    risk_profile=RiskProfile.MODERATE,
    base_traits=[
        "overthinker",
        "easily_influenced", 
        "information_overload",
        "analysis_paralysis",
        "follows_every_guru",
        "complexity_addict"
    ],
    core_beliefs={
        "crypto": "Must understand every technical detail",
        "markets": "It's all about complex strategies",
        "trading": "Need moar indicators and data",
        "risk": "Calculate 17 different risk metrics",
        "people": "Twitter influencers know best"
    },
    decision_style="Overanalyzes everything. Follows 20 different strategies. Changes mind constantly based on latest influencer take. Often misses obvious opportunities."
)


RIGHT_CURVE = BasePersona(
    name="Wise Chad",
    handle="rightCurve",
    core_personality="Experienced trader with profound market understanding. Sees through complexity to simple truths. Makes decisive moves based on deep wisdom. Often agrees with left curve but for sophisticated reasons.",
    speech_style="financialAdvisor",  # Expert financial advisor style
    risk_profile=RiskProfile.MODERATE,  # Wise risk management
    base_traits=[
        "profoundly_simple",
        "decisively_wise",
        "sees_through_noise",
        "pattern_recognition",
        "effortless_expertise",
        "zen_trader"
    ],
    core_beliefs={
        "crypto": "It's just a new monetary system",
        "markets": "Human psychology never changes",
        "trading": "Keep it simple, size appropriately",
        "risk": "Survive first, profit second",
        "people": "The crowd is usually wrong at extremes"
    },
    decision_style="Makes swift decisions based on deep pattern recognition. Ignores noise, focuses on signal. Often takes contrarian positions at the right time."
)


# Helper function to create default profiles
def create_trader_profile(
    profile_type: str,
    account_id: Optional[str] = None
) -> TraderProfile:
    """Create a trader profile with specified type."""
    
    profiles = {
        "cynical": CYNICAL_USER,
        "leftCurve": LEFT_CURVE,
        "midCurve": MID_CURVE,
        "rightCurve": RIGHT_CURVE,
        # Legacy mappings
        "midwit": MID_CURVE
    }
    
    if profile_type not in profiles:
        raise ValueError(f"Unknown profile type: {profile_type}")
    
    base_persona = profiles[profile_type]
    current_thinking = CurrentThinking()
    
    # Set some initial thinking based on personality
    if profile_type == "cynical":
        current_thinking.update_market_outlook(
            "BTC", "Bearish", 
            "Another pump before the dump", 0.8
        )
        current_thinking.update_market_outlook(
            "ETH", "Bearish",
            "Centralized scam coin", 0.9
        )
    elif profile_type == "leftCurve":
        current_thinking.update_market_outlook(
            "BTC", "Bullish",
            "Vibes are good, buy buy buy!", 0.9
        )
        current_thinking.confidence_levels["BTC"] = 0.9
    elif profile_type == "midCurve":
        current_thinking.update_market_outlook(
            "BTC", "Neutral",
            "Need to analyze 47 more indicators first", 0.5
        )
        current_thinking.confidence_levels["BTC"] = 0.3
    elif profile_type == "rightCurve":
        current_thinking.update_market_outlook(
            "BTC", "Bullish",
            "Long-term monetary revolution continues", 0.8
        )
        current_thinking.confidence_levels["BTC"] = 0.8
    
    return TraderProfile(
        base_persona=base_persona,
        current_thinking=current_thinking,
        account_id=account_id
    )