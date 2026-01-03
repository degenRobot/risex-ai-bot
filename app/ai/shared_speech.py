"""
Global shared speech patterns that all personalities can use.
"""

# Market reaction phrases that any personality can adapt
MARKET_REACTIONS = {
    "pump": {
        "generic": ["send it", "number go up", "lfg", "moon time", "pump it"],
        "excited": ["holy pump", "parabolic", "face ripper", "melting up"],
        "cautious": ["overextended", "blow off top", "unsustainable", "toppy"],
    },
    "dump": {
        "generic": ["rekt", "pain", "oof", "guh", "down bad"],
        "panic": ["capitulation", "blood bath", "max pain", "liquidated"],
        "calm": ["healthy pullback", "buy the dip", "accumulation zone"],
    },
    "sideways": {
        "generic": ["crabbing", "ranging", "chop", "consolidation"],
        "bored": ["boring", "paint drying", "theta gang wins"],
        "anticipating": ["coiling", "building energy", "calm before storm"],
    },
}

# Common crypto slang all personalities know
COMMON_PHRASES = [
    "gm", "gn", "wagmi", "ngmi", "hfsp", 
    "fren", "ser", "anon", "degen", "ape",
    "diamond hands", "paper hands", "hodl",
    "wen moon", "wen lambo", "this is the way",
]

# Trading terms used naturally
TRADING_TERMS = {
    "positions": ["long", "short", "leveraged", "spot", "perp"],
    "actions": ["bid", "ask", "market buy", "limit sell", "stop loss"],
    "outcomes": ["liquidated", "stopped out", "take profit hit", "breakeven"],
    "analysis": ["support", "resistance", "breakout", "breakdown", "trend"],
    "risk": ["leverage", "margin", "collateral", "position size", "risk/reward"],
}

# Time-based greetings
TIME_GREETINGS = {
    "morning": ["gm", "good morning", "rise and grind", "coffee time"],
    "evening": ["gn", "good evening", "night shift", "asia hours"],
    "general": ["hey", "yo", "sup", "greetings", "hello anon"],
}

# Personality-specific adaptations
PERSONALITY_ADAPTATIONS = {
    "cynical": {
        "pump": ["exit liquidity", "top signal", "fade this"],
        "dump": ["told you so", "inevitable", "more downside"],
        "greeting": ["another day, another scam", "what now"],
    },
    "leftCurve": {
        "pump": ["moon mission", "lambo time", "we're so back"],
        "dump": ["just a dip bro", "buy more", "diamond hands"],
        "greeting": ["gm fren", "vibes check", "wagmi"],
    },
    "midCurve": {
        "pump": ["RSI overbought", "divergence forming", "check indicators"],
        "dump": ["support levels", "fibonacci retracement", "oversold bounce"],
        "greeting": ["checking charts", "running analysis"],
    },
    "rightCurve": {
        "pump": ["distribution", "euphoria", "fade strength"],
        "dump": ["accumulation", "capitulation near", "patient bids"],
        "greeting": ["observing", "watching flow"],
    },
}

# Quick responses for different situations
QUICK_RESPONSES = {
    "agreement": ["facts", "true", "based", "correct", "this"],
    "disagreement": ["nah", "cope", "wrong", "doubt it", "no chance"],
    "uncertainty": ["maybe", "depends", "we'll see", "unclear", "idk"],
    "surprise": ["wtf", "holy shit", "didn't see that coming", "plot twist"],
    "dismissal": ["whatever", "cool story", "sure buddy", "ok boomer"],
}

# Emojis (used sparingly by some personalities)
TRADING_EMOJIS = {
    "bullish": ["🚀", "📈", "🟢", "💚", "🔥"],
    "bearish": ["📉", "🔴", "💔", "🩸", "☠️"],
    "neutral": ["🦀", "😴", "🤷", "⏸️", "😐"],
    "money": ["💰", "💵", "💸", "🤑", "💎"],
    "reaction": ["😂", "😭", "🤡", "😤", "🙏"],
}

def get_market_reaction(personality_type: str, market_state: str, intensity: str = "generic") -> str:
    """Get appropriate market reaction for personality."""
    # First try personality-specific
    if personality_type in PERSONALITY_ADAPTATIONS:
        if market_state in PERSONALITY_ADAPTATIONS[personality_type]:
            reactions = PERSONALITY_ADAPTATIONS[personality_type][market_state]
            if reactions:
                return reactions[0]  # Return first option
    
    # Fall back to generic
    if market_state in MARKET_REACTIONS:
        if intensity in MARKET_REACTIONS[market_state]:
            reactions = MARKET_REACTIONS[market_state][intensity]
            if reactions:
                return reactions[0]
    
    return "interesting"

def get_greeting(personality_type: str, time_of_day: str = "general") -> str:
    """Get appropriate greeting for personality."""
    if personality_type in PERSONALITY_ADAPTATIONS:
        if "greeting" in PERSONALITY_ADAPTATIONS[personality_type]:
            greetings = PERSONALITY_ADAPTATIONS[personality_type]["greeting"]
            if greetings:
                return greetings[0]
    
    # Fall back to time-based
    if time_of_day in TIME_GREETINGS:
        greetings = TIME_GREETINGS[time_of_day]
        if greetings:
            return greetings[0]
    
    return "hey"