# RISE AI Trading Bot Architecture

## Overview

The RISE AI Trading Bot uses a modular architecture with immutable base personalities and mutable "thought processes" that evolve through both user interactions and trading experiences.

## Core Architecture Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                          AI Trader Profile                           │
├─────────────────────┬───────────────────────────────────────────────┤
│  Immutable Base     │           Mutable Current State               │
│  ├─ Personality     │  ├─ Thought Process (shared, async)          │
│  ├─ Core Beliefs    │  ├─ Market Outlooks                          │
│  ├─ Speech Style    │  ├─ Recent Influences                        │
│  └─ Risk Profile    │  └─ Trading Decisions                        │
└─────────────────────┴───────────────────────────────────────────────┘
                ↑                           ↑
                │                           │
    ┌───────────┴────────┐       ┌─────────┴──────────┐
    │   Chat Interface   │       │  Trading Engine    │
    │  - User messages   │       │  - Market data     │
    │  - AI responses    │       │  - Position calc   │
    │  - Tool calls      │       │  - Order placement │
    └────────────────────┘       └────────────────────┘
```

## Thought Process Management

### Structure
The thought process is a chronological log of decisions, influences, and reasoning:

```json
{
  "thought_process": [
    {
      "timestamp": "2026-01-02T10:30:00Z",
      "type": "chat_influence",
      "source": "user_message",
      "content": "User convinced me Fed rate cuts are bullish for BTC",
      "impact": "Changed BTC outlook from bearish to neutral",
      "confidence": 0.6
    },
    {
      "timestamp": "2026-01-02T10:35:00Z", 
      "type": "trading_decision",
      "source": "market_analysis",
      "content": "Placed long BTC order based on rate cut news and technical breakout",
      "action": "buy_btc",
      "details": {
        "size": 0.1,
        "price": 95000,
        "reasoning": "Combining user insight about Fed with bullish technicals"
      }
    },
    {
      "timestamp": "2026-01-02T11:00:00Z",
      "type": "market_observation",
      "source": "price_action",
      "content": "BTC pumped 5% after Fed announcement, validating decision",
      "impact": "Increased confidence in macro-driven trades"
    }
  ]
}
```

### Async Update Flow

1. **Chat Updates** (User → AI):
   ```
   User Message → ProfileChatService → AI Response with Tool Calls
        ↓                                      ↓
   Update Thought Process ←──────── Tool: update_thought_process
   ```

2. **Trading Updates** (Market → AI):
   ```
   Market Data → TradingEngine → AI Decision with Tool Calls
        ↓                               ↓
   Execute Trade ←─────────── Tool: execute_trade_decision
        ↓                               ↓
   Update Thought Process ←─── Tool: update_thought_process
   ```

## Component Details

### 1. ProfileChatService
- Manages chat sessions with AI traders
- Updates thought process through tool calls
- Maintains conversation history
- Uses immutable base persona + current thinking

### 2. TradingEngine
- Runs on configurable intervals (e.g., every 5 minutes)
- Reads current thought process before decisions
- Updates thought process after trades
- Considers recent chat influences

### 3. ThoughtProcessManager (New Component)
```python
class ThoughtProcessManager:
    """Manages shared thought process across chat and trading."""
    
    async def add_entry(
        self,
        account_id: str,
        entry_type: str,  # chat_influence, trading_decision, market_observation
        source: str,      # user_message, market_analysis, price_action
        content: str,     # What happened
        impact: Optional[str] = None,  # How it affects thinking
        details: Optional[Dict] = None  # Additional context
    ) -> ThoughtEntry:
        """Add new thought process entry."""
    
    async def get_recent_thoughts(
        self,
        account_id: str,
        hours: int = 24,
        entry_types: Optional[List[str]] = None
    ) -> List[ThoughtEntry]:
        """Get recent thought process entries."""
    
    async def summarize_thoughts(
        self,
        account_id: str,
        for_purpose: str  # "trading_decision" or "chat_response"
    ) -> str:
        """Summarize recent thoughts for AI context."""
```

### 4. Prompt Builders

#### ChatPromptBuilder
```python
class ChatPromptBuilder:
    """Builds prompts for chat interactions."""
    
    def build_chat_prompt(
        self,
        profile: TraderProfile,
        thought_summary: str,
        market_context: Dict,
        conversation_history: List[Dict]
    ) -> str:
        """Build system prompt for chat."""
        return f"""
        You are {profile.base_persona.name}.
        
        IMMUTABLE TRAITS:
        {profile.base_persona.core_personality}
        
        RECENT THOUGHTS:
        {thought_summary}
        
        CURRENT MARKET:
        {self._format_market_context(market_context)}
        
        Remember to update your thought process when users share valuable insights.
        """
```

#### TradingPromptBuilder  
```python
class TradingPromptBuilder:
    """Builds prompts for trading decisions."""
    
    def build_trading_prompt(
        self,
        profile: TraderProfile,
        thought_summary: str,
        market_data: Dict,
        positions: Dict,
        recent_trades: List[Trade]
    ) -> str:
        """Build prompt for trading decision."""
        return f"""
        Analyze market and make trading decision.
        
        YOUR PERSONALITY:
        {profile.base_persona.decision_style}
        
        RECENT THOUGHTS & INFLUENCES:
        {thought_summary}
        
        MARKET DATA:
        {self._format_market_data(market_data)}
        
        CURRENT POSITIONS:
        {self._format_positions(positions)}
        
        Update thought process with your reasoning and decision.
        """
```

## Data Flow Examples

### Example 1: Chat Influence → Trade
```
1. User: "Fed is cutting rates, BTC will moon!"
2. AI Chat Response: "Interesting point about Fed policy..."
   → Tool Call: update_thought_process
   → Entry: "User shared bullish Fed insight, reconsidering bearish stance"
3. Trading Engine (5 min later):
   → Reads thought process including Fed insight
   → Decision: Place long BTC position
   → Tool Call: update_thought_process  
   → Entry: "Executing long BTC based on Fed policy shift discussed in chat"
```

### Example 2: Trade Result → Future Decisions
```
1. Trading Engine: Places BTC long at $95k
   → Tool Call: update_thought_process
   → Entry: "Opened BTC long based on technical + fundamental alignment"
2. Market pumps 5%
3. Trading Engine (next cycle):
   → Reads thought process showing successful Fed-based trade
   → Decision: Increase position size on macro-driven trades
   → Entry: "Previous Fed trade successful, increasing confidence in macro plays"
```

## Storage Structure

```
data/
├── accounts.json                 # Account data with base personas
├── thought_processes.json        # Shared thought process entries
├── chat_sessions.json           # Chat conversation history  
├── trading_decisions.json       # Detailed trading decisions
├── trade_history.json          # Executed trades with outcomes
└── market_snapshots.json       # Historical market data
```

## Async Considerations

1. **Thread Safety**: Use asyncio locks for thought process updates
2. **Event Broadcasting**: Notify components of thought updates
3. **Read Consistency**: Snapshot thoughts at decision time
4. **Write Ordering**: Timestamp all entries, handle concurrent writes

## Tool Definitions

### For Chat
```python
tools = [
    {
        "name": "update_thought_process",
        "description": "Record a new thought or realization",
        "parameters": {
            "thought_type": "insight|opinion_change|observation",
            "content": "What you realized or changed your mind about",
            "impact": "How this affects your trading approach",
            "confidence": "0-1 confidence in this thought"
        }
    }
]
```

### For Trading
```python
tools = [
    {
        "name": "execute_trade_decision",
        "description": "Execute a trading decision",
        "parameters": {
            "action": "buy|sell|hold",
            "asset": "BTC|ETH",
            "size": "Position size",
            "reasoning": "Why this trade makes sense"
        }
    },
    {
        "name": "update_thought_process",
        "description": "Record trading decision reasoning",
        "parameters": {
            "content": "Trading rationale and market observation",
            "trade_id": "Associated trade ID"
        }
    }
]
```

## Benefits

1. **Continuity**: Decisions build on previous thoughts and experiences
2. **Explainability**: Clear audit trail of why trades were made
3. **Learning**: AI can reference successful/failed decisions
4. **Personality**: Thoughts remain consistent with base personality
5. **Influence Tracking**: See how user chats affect trading

## Next Steps

1. Implement ThoughtProcessManager service
2. Add thought process integration to ProfileChatService
3. Update TradingEngine to read/write thoughts
4. Create visualization tools for thought timeline
5. Add thought decay (older thoughts less influential)