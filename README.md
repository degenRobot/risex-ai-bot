# RISE AI Trading Bot

AI-powered trading bot for RISE that uses personality-driven decision making and chat-based influence.

## Overview

The bot creates AI traders with distinct personalities that make autonomous trading decisions. Users can chat with these traders to influence their market outlook and trading behavior.

```
    User Chat                    Trading Engine
        |                              |
        v                              v
    Chat API -----> Shared <------ Market Data
                 Thought Process
                       |
                       v
                 Trading Decisions
```

## Quick Start

### Install

```bash
# Clone repository
git clone <repository>
cd risex-ai-bot

# Install dependencies
poetry install

# Set up environment
cp .env.example .env
# Edit .env with your OPENROUTER_API_KEY
```

### Run Locally

```bash
# Start API server
poetry run uvicorn app.api.server:app --reload

# Access API docs
open http://localhost:8000/docs
```

### Deploy to Production

```bash
# Set API key
export OPENROUTER_API_KEY="sk-or-v1-..."

# Deploy to Fly.io
./scripts/deploy.sh
```

## Core Features

### AI Trading Personalities

Three base personality types with immutable core traits:

1. **Cynical** - Extremely bearish, thinks everything goes to zero
   - Uses financial advisor speech style
   - Very hard to convince of bullish ideas
   - Conservative risk profile

2. **Left Curve** - Easily influenced, makes impulsive decisions
   - Uses "smol" speech style (wassie speak)
   - Gets excited by any market rumor
   - Degen risk profile

3. **Midwit** - Overconfident technical analyst
   - Uses crypto Twitter slang
   - Overanalyzes with indicators
   - Moderate risk profile

### Chat Influence System

Users can chat with AI traders to influence their thinking:

```bash
# Chat with a trader
curl -X POST http://localhost:8000/api/profiles/{id}/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Fed cut rates by 50bps!", "chatHistory": ""}'
```

The AI will:
- Respond in character based on personality
- Update market outlook using tools
- Record influences for future trading decisions

### Shared Thought Process

Both chat and trading systems update a shared thought log that tracks:
- Market outlooks and biases
- User influences and their impact
- Trading decisions and reasoning
- Confidence levels and timeframes

## API Endpoints

### Trading Profiles

```bash
# List all profiles
GET /api/profiles

# Get profile details
GET /api/profiles/{id}/summary

# Get trading context
GET /api/profiles/{id}/context
```

### Chat Interface

```bash
# Chat with AI trader
POST /api/profiles/{id}/chat
{
  "message": "Your message here",
  "chatHistory": ""  # Optional previous conversation
}
```

### Trading Control

```bash
# Start trading
POST /api/profiles/{id}/start

# Stop trading
POST /api/profiles/{id}/stop

# Get positions
GET /api/accounts/{address}/positions
```

## Architecture

### Directory Structure

```
app/
├── api/              # REST API endpoints
├── core/             # Trading engine and account management
├── services/         # AI, chat, and RISE integration
│   ├── ai_client.py         # OpenRouter AI integration
│   ├── profile_chat.py      # Chat service with tool calling
│   ├── rise_client.py       # RISE API client
│   ├── thought_process.py   # Shared thought management
│   └── storage.py           # JSON persistence
├── trader_profiles.py       # Base personality definitions
└── models.py               # Data models
```

### Key Components

**AI Client**: Integrates with OpenRouter for chat completions and tool calling

**Profile Chat Service**: Manages conversations and personality-based responses

**Thought Process Manager**: Maintains shared state between chat and trading

**RISE Client**: Handles all trading operations on RISE testnet

**Storage**: JSON-based persistence for accounts, decisions, and chat history

## Deployment

### Prerequisites

- Fly.io CLI installed
- OpenRouter API key

### Deploy Steps

1. Set environment variable:
   ```bash
   export OPENROUTER_API_KEY="your-key"
   ```

2. Run deployment:
   ```bash
   ./scripts/deploy.sh
   ```

3. Verify deployment:
   ```bash
   fly status --app risex-trading-bot
   ```

### Configuration

Environment variables (set via `fly secrets`):
- `OPENROUTER_API_KEY` - Required for AI features
- `TRADING_MODE` - "dry" (default) or "live"
- `TRADING_INTERVAL` - Seconds between trades (default: 60)

## Testing

### Run Tests

```bash
# Test chat system
poetry run python tests/core/test_chat_with_grok.py

# Test trading flow
poetry run python tests/trading/test_complete_trading_flow.py

# Test full system
poetry run python tests/core/test_full_system_live.py
```

### Manual Testing

1. Start local server
2. Get account ID from `/api/profiles`
3. Send chat message to influence trader
4. Monitor thought process updates
5. Observe trading decisions

## Development

### Adding New Personalities

Edit `app/trader_profiles.py`:

```python
NEW_PERSONA = BasePersona(
    name="Your Trader Name",
    handle="unique_handle",
    core_personality="Description of unchanging traits",
    speech_style="speechStyleKey",
    risk_profile=RiskProfile.MODERATE,
    # ... other traits
)
```

### Custom Speech Styles

Add to `app/services/speech_styles.py`:

```python
speechDict["newStyle"] = """
Instructions for how this personality speaks.
Include examples and key phrases.
"""
```

## Monitoring

### View Logs

```bash
# Local development
tail -f data/trading_decisions.json

# Production
fly logs --app risex-trading-bot
```

### Check Data Files

- `accounts.json` - Trading accounts
- `thought_processes.json` - Shared thoughts
- `chat_sessions.json` - Conversation history
- `trading_decisions.json` - Trade history

## Support

- RISE API Docs: https://developer.rise.trade/reference/general-information
- OpenRouter Docs: https://openrouter.ai/docs

## License

MIT