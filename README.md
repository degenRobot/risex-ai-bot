# RISE AI Trading Bot

An AI-powered trading bot for RISE testnet that creates unique trading personas and makes autonomous trading decisions. Each persona has distinct characteristics derived from social media analysis and makes trades based on its personality and risk tolerance.

## Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          AI Trader Profile                           │
├─────────────────────┬───────────────────────────────────────────────┤
│  Immutable Base     │           Mutable Current State               │
│  ├─ Personality     │  ├─ Shared Thought Process                    │
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

**Key Features:**
- **Immutable Base Personas**: Core personality traits that never change
- **Mutable Thought Process**: Shared state that evolves through chat and trading
- **Chat with AI Traders**: Influence trading decisions through conversations
- **Async Architecture**: Clean separation of chat and trading with shared state
- Gasless trading using RISE's gasless architecture
- Automatic USDC faucet integration for testnet
- Real-time market analysis and decision making
- REST API for bot management and profile chat

## Quick Start

### 1. Installation

```bash
# Clone and setup
git clone <your-repo>
cd risex-ai-bot

# Install dependencies
poetry install

# Create environment file
cp .env.example .env
```

### 2. Configuration

Edit `.env` with your keys:

```bash
# Required: Ethereum private keys (MUST be different for security)
PRIVATE_KEY=0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
SIGNER_PRIVATE_KEY=0xfedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321

# Required for AI features
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### 3. Test the Integration

```bash
# Test order placement with TIF variations (RECOMMENDED)
poetry run python tests/test_tif_variations.py

# Test profile generation and full flow
poetry run python tests/test_full_flow.py

# Test AI trading logic
poetry run python tests/test_ai_trading.py

# Test profile chat system (NEW)
poetry run python tests/test_profile_chat.py

# Test deposits
poetry run python tests/test_deposit.py
```

## Project Structure

```
risex-ai-bot/
├── app/                          # Main application code
│   ├── core/
│   │   ├── account_manager.py    # Account & persona management
│   │   ├── trading_loop.py       # Automated trading bot with decision logging
│   │   ├── market_manager.py     # Global market data manager
│   │   └── parallel_executor.py  # Parallel profile executor
│   ├── services/
│   │   ├── rise_client.py        # RISE API client (gasless trading) ✅
│   │   ├── ai_client.py          # OpenRouter AI client with tool support
│   │   ├── ai_tools.py           # AI tool definitions
│   │   ├── profile_chat.py       # Chat with AI traders 💬
│   │   ├── thought_process.py    # Shared thought process manager 🧠
│   │   ├── prompt_builders.py    # Consistent prompt generation 📝
│   │   ├── speech_styles.py      # Personality speech patterns 🗣️
│   │   ├── mock_social.py        # Mock social media profiles
│   │   └── storage.py            # JSON storage
│   ├── utils/
│   │   └── profile_generator.py  # Profile creation helper 🎯
│   ├── api/                      # FastAPI endpoints
│   ├── trader_profiles.py        # Trader personality definitions 👥
│   ├── config.py                 # Configuration management
│   └── models.py                 # Pydantic models
├── scripts/                      # Production scripts
│   ├── run_trading_bot.py        # Original trading bot runner
│   └── run_enhanced_bot.py       # Enhanced parallel bot 🚀
├── tests/                        # Comprehensive test suite
│   ├── test_chat_influence.py    # Test chat → trading influence
│   ├── test_enhanced_system.py   # Test decision logging & history
│   ├── test_automated_trading.py # Complete system test
│   └── test_*.py                 # Component tests
├── data/                         # Persistent storage & trading logs
│   ├── accounts.json             # Trading accounts
│   ├── thought_processes.json    # Shared thought process entries 🧠
│   ├── chat_sessions.json        # Chat conversation history
│   ├── trading_decisions.json    # Decision logs with reasoning
│   ├── trading_sessions.json     # Trading sessions and outcomes
│   └── pending_actions.json      # Pending conditional actions
├── ARCHITECTURE.md               # System architecture & async flow 📚
└── pyproject.toml                # Poetry configuration
```

## Core Components

### Profile Generator (`app/utils/profile_generator.py`)

Quick profile creation with full setup:

```python
from app.utils.profile_generator import quick_setup_profile

# Create new AI trader with one function call
profile = await quick_setup_profile(
    name="AI Alpha Trader",
    deposit=1000.0,  # Initial USDC deposit
    profile_type="moderate"  # conservative, moderate, aggressive
)

print(f"Account: {profile['profile']['address']}")
print(f"Signer: {profile['profile']['signer_address']}")
```

### RISE Client (`app/services/rise_client.py`)

Handles all RISE API interactions with gasless trading support:

```python
from app.services.rise_client import RiseClient

async with RiseClient() as client:
    # Register signer for gasless trading
    await client.register_signer(account_key, signer_key)
    
    # Deposit USDC (6 decimals!)
    await client.deposit_usdc(account_key, amount=100.0)
    
    # Place gasless order (use TIF=3 for IOC)
    await client.place_order(
        account_key, signer_key,
        market_id=1, size=0.01, price=95000,
        side="buy", order_type="limit"
    )
```

### AI Client (`app/services/ai_client.py`)

Generates personas and trading decisions using OpenRouter:

```python
from app.services.ai_client import AIClient

ai = AIClient()

# Generate persona from social posts
persona = await ai.create_persona_from_posts(
    handle="trader123",
    posts=["Buying the dip!", "Diamond hands 💎"],
    bio="Crypto enthusiast"
)

# Get trading decision
decision = await ai.get_trade_decision(
    persona, market_data, positions, balance
)
```

### Account Manager (`app/core/account_manager.py`)

Orchestrates account creation and management:

```python
from app.core.account_manager import AccountManager

async with AccountManager() as manager:
    # Create account with AI persona
    account = await manager.create_account_with_persona(
        handle="crypto_trader",
        posts=social_media_posts,
        bio="Day trader focused on BTC/ETH"
    )
    
    # Check account status
    status = await manager.check_account_status(account.id)
```

### Thought Process Manager (`app/services/thought_process.py`)

Manages shared thought process that evolves through chat and trading:

```python
from app.services.thought_process import ThoughtProcessManager

manager = ThoughtProcessManager()

# Add chat influence
await manager.add_entry(
    account_id="trader-123",
    entry_type="chat_influence",
    source="user_message",
    content="User shared Fed rate cut news",
    impact="Reconsidering bearish BTC stance",
    confidence=0.7
)

# Add trading decision
await manager.add_entry(
    account_id="trader-123",
    entry_type="trading_decision",
    source="market_analysis",
    content="Opened BTC long based on Fed news",
    impact="Committed to bullish thesis",
    details={"action": "buy", "size": 0.1, "price": 95000}
)

# Get thoughts for trading context
thoughts = await manager.summarize_thoughts(
    account_id="trader-123",
    for_purpose="trading_decision"
)
```

### Profile Chat (`app/services/profile_chat.py`)

Chat with AI traders using their unique personalities:

```python
from app.services.profile_chat import ProfileChatService

chat = ProfileChatService()

# Chat with trader
result = await chat.chat_with_profile(
    account_id="trader-123",
    user_message="Fed is cutting rates, BTC to moon!",
    chat_history=""  # or previous chat JSON
)

print(result['response'])  # AI's in-character response
print(result['profileUpdates'])  # How their thinking changed
```

### Trader Profiles (`app/trader_profiles.py`)

Pre-defined personalities with immutable base traits:

- **cynicalUser**: Extremely skeptical, uses "financialAdvisor" speech
- **leftCurve**: Easily influenced, uses "smol" (WassieSpeak) speech  
- **midwit**: Overconfident analyst, uses crypto slang

```python
from app.trader_profiles import create_trader_profile

# Create a cynical trader
profile = create_trader_profile("cynical", account_id="123")
print(profile.base_persona.core_beliefs)
# {'crypto': 'All ponzis go to zero eventually', ...}
```

## Testing

### Automated Trading System Test

Test the complete automated trading system (recommended):

```bash
# Quick test (3 iterations) - validates complete system
poetry run python test_automated_trading.py

# Continuous mode (manual stop with Ctrl+C)
poetry run python test_automated_trading.py --continuous
```

**What it tests:**
- ✅ AI persona generation from mock profiles
- ✅ Market data integration from RISE API  
- ✅ Social activity simulation
- ✅ Trading decision engine with AI
- ✅ Position tracking and P&L calculation
- ✅ Dry-run mode safety features

### Complete Flow Test

Tests the core RISE API integration:

```bash
poetry run python test_complete_flow.py
```

This will:
1. Generate fresh wallet + signer keys
2. Register signer with RISE
3. Deposit USDC (triggers testnet faucet)
4. Attempt to place a test order

### AI Persona Test

Tests AI persona generation and trading decisions:

```bash
poetry run python test_ai_persona.py
```

Requires `OPENROUTER_API_KEY` in `.env` for full functionality.

### Component Tests

```bash
# Test mock social profiles
poetry run python test_mock_profiles.py

# Basic RISE API connectivity
poetry run python test_rise_integration.py

# End-to-end pipeline test
poetry run python test_end_to_end.py
```

## Chat & Thought Process System

### How It Works

1. **Chat influences trading**: Users can chat with AI traders to influence their market outlook
2. **Shared thought process**: Both chat and trading update a shared thought log
3. **Async architecture**: Chat and trading run independently but share state
4. **Tool-based updates**: AI uses tools to update their thinking

### Example Flow

```python
# 1. User chats with trader
POST /api/profiles/{account_id}/chat
{
    "message": "Fed is cutting rates tomorrow, BTC will pump!",
    "chatHistory": ""
}

# 2. AI responds and updates thinking
Response: "Hmm, Fed rate cuts could be bullish..."
Tool Call: update_thought_process(
    thought_type="opinion_change",
    content="Considering bullish BTC stance due to Fed policy",
    impact="May look for long entries",
    confidence=0.7
)

# 3. Trading engine reads thoughts (5 min later)
thoughts = await thought_manager.get_trading_influences(account_id)
# Sees recent bullish influence from chat

# 4. Makes influenced decision
Decision: Buy 0.1 BTC at $95k
Tool Call: update_thought_process(
    content="Executed BTC long based on Fed news from chat",
    impact="Testing thesis about macro influences"
)
```

### API Endpoints

```bash
# Chat with AI trader
POST /api/profiles/{account_id}/chat
POST /api/v2/profiles/{account_id}/chat  # Enhanced version

# Get profile summary with current thinking  
GET /api/profiles/{account_id}/summary
GET /api/v2/profiles/{account_id}/summary

# Get trading context
GET /api/profiles/{account_id}/context
```

## Automated Trading

### Quick Start - Run the Bot

```bash
# Create demo accounts (first time setup)
poetry run python scripts/run_trading_bot.py --create-accounts

# Run ORIGINAL bot (sequential processing)
poetry run python scripts/run_trading_bot.py --interval 60

# Run ENHANCED bot (parallel + tool calling) 🚀
poetry run python scripts/run_enhanced_bot.py --interval 60

# Run with live trading (requires confirmation)
poetry run python scripts/run_enhanced_bot.py --live --interval 300
```

### 🚀 Enhanced Architecture (NEW)

**Parallel Execution + OpenRouter Tool Calling:**

```bash
# Run enhanced bot with parallel profile processing
poetry run python scripts/run_enhanced_bot.py

# Test enhanced architecture
poetry run python tests/test_enhanced_architecture.py
```

**Key Improvements:**
- **Parallel Processing**: All profiles execute simultaneously
- **Tool Calling**: Structured AI actions via OpenRouter tools
- **Global Market Data**: Shared data manager (30s updates)
- **Pending Actions**: Stop loss, take profit, conditional orders
- **Action Queue**: Automated execution when conditions are met

**Available AI Tools:**
- `place_market_order` - Immediate market execution
- `place_limit_order` - Limit order at specific price
- `close_position` - Close position (full or partial)
- `set_stop_loss` - Automatic stop loss trigger
- `set_take_profit` - Take profit at target price
- `schedule_limit_order` - Conditional future order
- `cancel_pending_action` - Cancel pending action

**Enhanced Features:**
- **Decision Logging**: Every trading decision is saved with full context
- **Historical Learning**: AI learns from past successful/failed trades  
- **Outcome Tracking**: Track P&L and success rates over time
- **Analytics Dashboard**: View win rates, execution rates, confidence levels

### Automated Trading Features

**Every X seconds, each AI trader:**
1. Checks for new social media activity (simulated)
2. Fetches real market data from RISE API
3. Calculates P&L on open positions  
4. Makes AI trading decision based on personality
5. Executes trades if confidence > 60%

**AI Trader Personalities:**

**Immutable Base Personas** (3 main types):
- **cynicalUser** - Extremely cynical, thinks everything goes to 0
  - Speech: "financialAdvisor" (calls things ponzis, says NGMI/HFSP)
  - Very hard to convince of anything bullish
  - Conservative risk profile
  
- **leftCurve** - Easily persuaded, makes terrible decisions
  - Speech: "smol" (wassie speak - "henlo fren", "numba go up")
  - Believes any exciting rumor, FOMOs into everything
  - Degen risk profile
  
- **midwit** - Overconfident technical analyst
  - Speech: "ct" (crypto slang)
  - Overanalyzes with too many indicators
  - Moderate risk profile

**Legacy Personas** (from social profiles):
- **crypto_degen** - Aggressive YOLO trader
- **btc_hodler** - Conservative Bitcoin maximalist  
- **trend_master** - Technical momentum trader
- **market_contrarian** - Contrarian value investor
- **yolo_king** - Ultimate degen with 100x mentality

## 🎮 Usage Examples

### System Status ✅ 

**Current Implementation Status:**

🟢 **Core Features - COMPLETE**
- ✅ RISE API client with gasless trading
- ✅ Account & signer management
- ✅ AI persona generation (5 trader types)
- ✅ Mock social media profiles with market responsiveness
- ✅ Market data integration (live RISE API)
- ✅ Automated trading loop with configurable intervals
- ✅ P&L calculation and position tracking
- ✅ JSON file storage system
- ✅ Comprehensive test suite

🟡 **Production Ready Features**
- ✅ Dry-run mode for safe testing
- ✅ Live trading mode (manual confirmation required)
- ✅ Error handling and recovery
- ✅ Logging and monitoring
- ✅ Graceful shutdown handling

**Test Results (Last Run):**
- ✅ 3 trading loop iterations completed
- ✅ 4 AI traders processed successfully  
- ✅ Market data integration working
- ✅ AI decision making operational
- ✅ All safety features validated

### Run Complete System Test

```bash
# Test the complete automated system (recommended)
poetry run python tests/test_automated_trading.py

# Test enhanced features
poetry run python tests/test_enhanced_system.py  # Decision logging & history

# Component tests
poetry run python tests/test_complete_flow.py      # RISE API integration
poetry run python tests/test_mock_profiles.py      # Mock social profiles
poetry run python tests/test_ai_persona.py         # AI decision making
```

### Create and Test Trading Account

```python
import asyncio
from app.core.account_manager import AccountManager

async def create_trader():
    async with AccountManager() as manager:
        # Create account from mock social profile
        account = await manager.create_account_from_mock_profile("crypto_degen")
        
        # Check status
        status = await manager.check_account_status(account.id)
        print(f"Account: {status['address']}")
        print(f"Persona: {status['persona']}")

asyncio.run(create_trader())
```

### Generate AI Trading Decision

```python
from app.services.ai_client import AIClient
from app.models import Persona, TradingStyle

async def get_decision():
    ai = AIClient()
    
    # Sample persona
    persona = Persona(
        name="Degen Trader",
        handle="crypto_degen",
        bio="YOLO trader going for big gains",
        trading_style=TradingStyle.DEGEN,
        risk_tolerance=0.9,
        favorite_assets=["BTC", "ETH"],
        personality_traits=["risk-taker", "optimistic", "impatient"],
        sample_posts=["To the moon! 🚀", "Buy the dip!"]
    )
    
    # Market conditions
    market_data = {
        "btc_price": 95000,
        "eth_price": 3500,
        "btc_change": 0.05,  # 5% up
        "eth_change": -0.02  # 2% down
    }
    
    decision = await ai.get_trade_decision(
        persona, market_data, {}, 1000.0
    )
    
    print(f"Should trade: {decision.should_trade}")
    print(f"Action: {decision.action}")
    print(f"Reasoning: {decision.reasoning}")

asyncio.run(get_decision())
```

## Security Notes

- **Different Keys Required**: Account and signer keys MUST be different for security
- **Gasless Trading**: All transactions are sponsored by RISE API - no ETH needed
- **Testnet Only**: This implementation is designed for RISE testnet
- **Private Keys**: Never commit real private keys to version control

## RISE Testnet Info

- **Network**: RISE Testnet
- **Chain ID**: 11155931
- **RPC**: https://testnet.riselabs.xyz
- **Explorer**: https://explorer.testnet.riselabs.xyz
- **API**: https://api.testnet.rise.trade
- **Faucet**: Automatically triggered by deposit calls

## API Reference

### Configuration

Environment variables in `.env`:

- `PRIVATE_KEY`: Main account private key (required)
- `SIGNER_PRIVATE_KEY`: Signer key for orders (required, must be different)
- `OPENROUTER_API_KEY`: OpenRouter API key for AI features
- `RISE_API_BASE`: RISE API base URL (default: testnet)
- `DEBUG`: Enable debug logging (default: false)

### Models

**Persona**: AI-generated trading personality
- `name`: Trading nickname
- `trading_style`: aggressive, conservative, contrarian, momentum, degen
- `risk_tolerance`: 0.0 - 1.0
- `favorite_assets`: Preferred crypto assets
- `personality_traits`: Character traits affecting decisions

**TradeDecision**: AI trading recommendation
- `should_trade`: Boolean recommendation
- `action`: buy, sell, or close
- `market`: BTC or ETH
- `size_percent`: Percentage of balance to use
- `confidence`: Decision confidence level
- `reasoning`: AI explanation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `poetry run pytest`
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Current Status (January 2025)

### ✅ Working Implementation

We have successfully implemented and tested all core features:

1. **RISE API Integration** - Complete with proper EIP-712 signing
2. **Order Placement** - Successfully placed orders with TIF=IOC (Order ID: 5766369)
3. **Profile Generation** - Automated account/signer key creation and setup
4. **AI Trading Logic** - Market analysis and decision making
5. **Gasless Trading** - Working with proper signer registration
6. **Chat System** - Users can influence AI traders through natural conversation
7. **Thought Process** - Shared state that evolves from both chat and trading
8. **Immutable Personas** - Base personalities that stay consistent
9. **Tool Calling** - AI updates thinking through structured tool calls

### 🎯 Key Discoveries

**Critical for Order Success:**
- Use TIF=3 (IOC) for orders - GTC orders fail on testnet
- USDC uses 6 decimals (not 18)
- Order sizes/prices use 18 decimals
- 47-byte order encoding is working correctly

**Successful Test Results:**
```bash
✅ Deposited 1000 USDC (TX: 0x7674749131f423b0820a62e9096380012724f5dfae5b93ceccd6db51f44c8049)
✅ Registered signer for gasless trading
✅ Placed order successfully (Order ID: 5766369, TX: 0x96e552b3b076d8c424722cf304346f35afd585271d85f432ba5cd51818a40f00)
```

### 🚧 Known Limitations

- New accounts may need initial ETH or activity before deposits work
- Some accounts show "missing nonce or insufficient funds" errors
- Markets show `available: false` but orders still execute

## Troubleshooting

### Common Issues

**"Account and signer must be different addresses"**
- Ensure PRIVATE_KEY and SIGNER_PRIVATE_KEY are different in .env

**"OpenRouter API key not configured"**
- Add OPENROUTER_API_KEY to .env for AI features

**"Insufficient balance" errors**
- Normal for fresh accounts - faucet deposits may take time
- Check account balance with test scripts

**"Market unavailable" errors**
- RISE testnet markets may be temporarily disabled
- Check market status with `test_rise_integration.py`

### Getting Help

1. Check the test scripts output for detailed error information
2. Review the RISE API documentation: https://developer.rise.trade
3. Ensure you're using RISE testnet (not Ethereum mainnet/Sepolia)
