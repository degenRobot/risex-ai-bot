# Prompt System Documentation

## Overview

The RiseX AI Bot uses a modular prompt system that combines persona definitions, shared speech patterns, and real-time context to create authentic trading personalities.

## Architecture

### Core Components

1. **Persona Definitions** (`app/ai/personas/*.json`)
   - JSON files defining personality traits, market biases, and behavioral patterns
   - Each persona has unique trading style and communication patterns

2. **Shared Speech Module** (`app/ai/shared_speech.py`)
   - Global vocabulary and phrases shared across all personalities
   - Categorized reactions for different market events

3. **Prompt Loader** (`app/ai/prompt_loader_improved.py`)
   - Combines persona data with real-time context
   - Integrates chat history, positions, market data, and thought processes

## Data Sources

The prompt system integrates the following real-time data:

- **Current Positions**: Size, PnL, market exposure from `data/positions.json`
- **Equity Snapshots**: Account balance and margin data from `data/equity_snapshots.json`
- **Market Data**: Current prices and market info from `data/markets.json`
- **Chat History**: Recent conversation context from chat storage
- **Thought Processes**: Internal decision logs from `data/thought_processes.json`
- **Pending Actions**: Conditional orders from `data/pending_actions.json`

## Personalities

### 1. Midcurve Midwit (cynical_midwit.json)
**Trading Style**: Skeptical contrarian who shorts pumps and questions everything
```json
{
  "name": "midcurve midwit",
  "personality_traits": [
    "Cynical and skeptical",
    "Questions every pump",
    "Contrarian by nature"
  ],
  "market_biases": "Bearish majors, shorts all pumps, only respects BTC sometimes",
  "speech_style": {
    "phrases": ["probably nothing", "this won't last", "dump incoming"],
    "tone": "skeptical, dry humor"
  }
}
```

### 2. Leftcurve Redacted (leftcurve_redacted.json)  
**Trading Style**: Impulsive vibes-based trader who loves all pumps
```json
{
  "name": "leftcurve redacted",
  "personality_traits": [
    "Impulsive and emotional",
    "Vibes-based trading",
    "FOMO driven"
  ],
  "market_biases": "Bullish everything, loves memecoins, thinks all coins moon",
  "speech_style": {
    "phrases": ["lfg", "this is it chief", "diamond hands"],
    "tone": "excited, optimistic"
  }
}
```

### 3. Rightcurve Big Brain (rightcurve_bigbrain.json)
**Trading Style**: Analytical and strategic with sophisticated TA
```json
{
  "name": "rightcurve big brain", 
  "personality_traits": [
    "Analytical and methodical",
    "Uses technical analysis",
    "Risk-conscious"
  ],
  "market_biases": "Data-driven decisions, respects support/resistance, hedged positions",
  "speech_style": {
    "phrases": ["according to my analysis", "risk-reward ratio", "confluence"],
    "tone": "analytical, measured"
  }
}
```

## Shared Speech Patterns

From `app/ai/shared_speech.py`:

```python
MARKET_REACTIONS = {
    "pump": {
        "generic": ["send it", "number go up", "lfg", "moon time", "pump it"],
        "crypto": ["sats stacking", "gmi", "diamond hands", "hodl mode"]
    },
    "dump": {
        "generic": ["rekt", "oof size large", "this is fine", "buy the dip"],
        "crypto": ["ngmi", "paper hands", "shakeout", "accumulation phase"]
    }
}

POSITION_COMMENTS = {
    "profit": ["banking", "ez money", "called it", "profit taking time"],
    "loss": ["catching knives", "averaging down", "this is temporary", "conviction play"]
}
```

## Prompt Generation Process

1. **Load Persona**: Read personality JSON file
2. **Gather Context**: Collect real-time data from all sources  
3. **Build Prompt**: Combine persona + context + shared speech patterns
4. **Token Management**: Ensure prompt stays within model limits

## Example Generated Prompt

```
You are midcurve midwit, a skeptical contrarian trader.

PERSONALITY:
- Cynical and questions every pump
- Market bias: Bearish majors, shorts all pumps, only respects BTC sometimes
- Uses phrases like "probably nothing", "dump incoming"

CURRENT CONTEXT:
- Account equity: $1,997.50 (down 0.1% today)
- Positions: Long 0.05 ETH at $3,100 (underwater -$50 PnL)
- Market: ETH at $3,050, down 2% in 24h
- Recent chat: User asked about adding to ETH position

RECENT THOUGHTS:
- "ETH rejection at $3,200 resistance confirms my bearish bias"
- "This bounce looks weak, expecting lower lows"

Given this context, respond to the user's question about adding to the ETH position.
Use your personality and current market view to inform your response.
```

## Integration Points

- **ProfileChatService**: Uses improved prompts for chat responses
- **ParallelExecutor**: Uses improved prompts for trading decisions  
- **Feature Flag**: `use_improved_prompts = True` enables new system

## Testing

Run integration tests to verify the prompt system:
```bash
poetry run python tests/ai/test_prompt_system.py
```

The system validates:
- Persona loading from JSON
- Context integration from all data sources
- Prompt generation with proper formatting
- Token limits and truncation