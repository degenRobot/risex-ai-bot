# 🤖 RISE AI Trading Bot

An autonomous trading system where AI traders with unique personalities make decisions on RISE perpetuals DEX. Users can influence trading behavior through chat conversations.

## ✨ Overview

Create AI traders with distinct personalities that:
- 🎭 **Respond in character** to market events and user messages
- 📈 **Make autonomous trading decisions** based on personality and influences
- 💬 **Learn from chat interactions** and adjust market outlook
- 💰 **Trade real assets** on RISE testnet with gasless transactions
- 📊 **Monitor equity in real-time** via on-chain RPC calls

```
🗣️  User Chat → 🤖 AI Personality → 📊 Market Analysis → 💸 Trading Decision
                        ↓                    ↑
                 📝 Profile Updates ← 💰 Live Equity Monitor
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Poetry package manager
- OpenRouter API key for AI features

### Install & Setup

```bash
# Clone repository
git clone <repository>
cd risex-ai-bot

# Install dependencies
poetry install

# Set up environment
cp .env.example .env

# Configure your .env file with:
# PRIVATE_KEY=0x...              # Main account key
# SIGNER_PRIVATE_KEY=0x...       # Different key (MUST be different)
# OPENROUTER_API_KEY=...         # For AI features
# BACKEND_RPC_URL=https://indexing.testnet.riselabs.xyz
```

### Create Your First AI Trader

```bash
# Interactive profile creation
poetry run python scripts/create_fresh_profile.py

# Or specify personality and deposit
poetry run python scripts/create_fresh_profile.py cynical 1000
```

This creates a fresh account with:
- ✅ Cryptographic keys generated  
- ✅ Signer registered for gasless trading
- ✅ USDC deposited (minted on testnet)
- ✅ AI personality configured
- ✅ Ready for chat and trading

### Run Locally

```bash
# Start both API server and trading bot
poetry run python start_bot.py

# Or run separately:
# Start API server
poetry run uvicorn app.api.server:app --reload

# Start trading bot (in another terminal)
poetry run python scripts/run_enhanced_bot.py --interval 60

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
   - Conservative risk profile (10-20% of free margin)

2. **Left Curve** - Easily influenced, makes impulsive decisions
   - Uses "smol" speech style (wassie speak)
   - Gets excited by any market rumor
   - Degen risk profile (35-50% of free margin)

3. **Midwit** - Overconfident technical analyst
   - Uses crypto Twitter slang
   - Overanalyzes with indicators
   - Moderate risk profile (20-35% of free margin)

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

### Real-time Equity Monitoring

On-chain RPC monitoring fetches:
- Account equity via `getAccountEquity`
- Free margin via `getFreeCrossMarginBalance`
- Updates every 60 seconds in production
- Combined fetching for efficiency

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
POST /api/profiles/{handle}/start

# Stop trading
POST /api/profiles/{handle}/stop

# Get trading context with P&L
GET /api/profiles/{account_id}/context

# Get analytics
GET /analytics
```

## Architecture

### Directory Structure

```
app/
├── ai/               # Prompt system and personas
│   ├── prompt_loader_improved.py  # Modular prompt loader
│   ├── shared_speech.py          # Global speech patterns
│   ├── prompts/                  # Prompt templates
│   └── personas/                 # JSON persona definitions
├── api/              # REST API endpoints
├── core/             # Trading engine and account management
│   ├── parallel_executor.py      # Parallel trading execution
│   ├── market_manager.py         # Market data management
│   └── trading_loop.py           # Main trading loop
├── realtime/         # WebSocket and event system
│   ├── events.py            # Event models and types
│   ├── bus.py               # Event bus for pub/sub
│   └── ws.py                # WebSocket endpoint
├── services/         # AI, chat, and RISE integration
│   ├── ai_client.py         # OpenRouter AI integration
│   ├── equity_monitor.py    # Real-time RPC equity/margin tracking
│   ├── profile_chat.py      # Chat service with tool calling
│   ├── ai_tools.py          # Trading tools for AI function calling
│   ├── rise_client.py       # RISE API client (market orders)
│   ├── thought_process.py   # Shared thought management
│   └── storage.py           # JSON persistence
├── trading/          # Trading execution system
│   └── actions.py           # Action queue for multi-market execution
├── trader_profiles.py       # Base personality definitions
└── models.py               # Data models
```

### Key Components

**AI Client**: Integrates with OpenRouter for chat completions and tool calling

**Profile Chat Service**: Manages conversations and personality-based responses with dynamic position sizing

**Thought Process Manager**: Maintains shared state between chat and trading

**RISE Client**: Handles all trading operations on RISE testnet using market orders (limit orders with price=0)

**Equity Monitor**: Real-time RPC calls to track account equity and free margin

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
- `TRADING_MODE` - "live" (production) or "dry" (testing)
- `TRADING_INTERVAL` - Seconds between trades (default: 300)
- `PRIVATE_KEY` - Main account key for deployment
- `SIGNER_PRIVATE_KEY` - Different key for gasless signing

## Testing

### Run Tests

```bash
# Test market orders
poetry run python tests/trading/test_rise_market_orders.py

# Test chat system
poetry run python tests/chat/test_profile_chat.py

# Test equity monitoring
poetry run python scripts/test_equity_monitor.py

# Full integration test
poetry run python tests/core/test_automated_trading.py --continuous
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

- `accounts.json` - Trading accounts with deposit amounts
- `thought_processes.json` - Shared thoughts and influences
- `chat_sessions.json` - Conversation history
- `trading_decisions.json` - Trade history with reasoning
- `equity_snapshots.json` - Historical equity and margin data
- `markets.json` - Market data with minimum sizes

## Recent Updates (January 2026)

### New Features
- ✅ Real-time P&L calculation (equity - deposit)
- ✅ Free margin display from blockchain RPC
- ✅ Dynamic position sizing based on risk profile
- ✅ Multi-market support (BTC, ETH, SOL, BNB, DOGE)
- ✅ Market orders via limit orders with price=0
- ✅ Combined equity/margin fetching for efficiency

### API Improvements
- New analytics endpoint with top performer tracking
- Enhanced profile context with free margin and max position sizes
- Admin endpoint for updating account data
- Improved error handling for insufficient margin

## Support

- RISE API Docs: https://developer.rise.trade/reference/general-information
- OpenRouter Docs: https://openrouter.ai/docs
- API Documentation: [API.md](./API.md)
- Architecture Guide: [ARCHITECTURE.md](./ARCHITECTURE.md)

## License

MIT