# RISE AI Trading Bot

An AI-powered trading bot for RISE testnet that creates unique trading personas and makes autonomous trading decisions. Each persona has distinct characteristics derived from social media analysis and makes trades based on its personality and risk tolerance.

## 🎯 Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Social Posts  │────▶│  AI Persona     │────▶│   RISE API      │
│   & Profile     │     │  (OpenRouter)   │     │   Trading       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
   Profile Analysis      Trade Decisions         Execute Trades
```

**Key Features:**
- 🤖 AI-generated trading personas with unique personalities
- 🔐 Gasless trading using RISE's gasless architecture
- 💰 Automatic USDC faucet integration for testnet
- 📊 Real-time market analysis and decision making
- 🎮 Simple REST API for bot management

## 🚀 Quick Start

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
# Test RISE API integration
poetry run python test_complete_flow.py

# Test AI persona generation
poetry run python test_ai_persona.py

# Basic integration check
poetry run python test_rise_integration.py
```

## 🏗️ Project Structure

```
risex-ai-bot/
├── app/
│   ├── core/
│   │   └── account_manager.py    # Account & persona management
│   ├── services/
│   │   ├── rise_client.py        # RISE API client (gasless trading)
│   │   ├── ai_client.py          # OpenRouter AI client
│   │   └── storage.py            # JSON file storage
│   ├── config.py                 # Configuration management
│   └── models.py                 # Pydantic data models
├── data/                         # Persistent storage
├── test_*.py                     # Test scripts
└── pyproject.toml               # Poetry configuration
```

## 🔧 Core Components

### RISE Client (`app/services/rise_client.py`)

Handles all RISE API interactions with gasless trading support:

```python
from app.services.rise_client import RiseClient

async with RiseClient() as client:
    # Register signer for gasless trading
    await client.register_signer(account_key, signer_key)
    
    # Deposit USDC (triggers faucet)
    await client.deposit_usdc(account_key, amount=100.0)
    
    # Place gasless order
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

## 🧪 Testing

### Complete Flow Test

Tests the entire pipeline with fresh generated keys:

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

### Basic Integration Test

Quick check of RISE API connectivity:

```bash
poetry run python test_rise_integration.py
```

## 🤖 Automated Trading

### Quick Start - Run the Bot

```bash
# Create demo accounts (first time setup)
poetry run python run_trading_bot.py --create-accounts

# Run in dry-run mode (safe testing)
poetry run python run_trading_bot.py --interval 60

# Run with live trading (requires confirmation)
poetry run python run_trading_bot.py --live --interval 300 --max-position 50
```

### Automated Trading Features

🔄 **Every X seconds, each AI trader:**
1. 📱 Checks for new social media activity (simulated)
2. 📊 Fetches real market data from RISE API
3. 💰 Calculates P&L on open positions  
4. 🤖 Makes AI trading decision based on personality
5. 📈 Executes trades if confidence > 60%

🎭 **5 AI Trader Personalities:**
- **crypto_degen** - Aggressive YOLO trader
- **btc_hodler** - Conservative Bitcoin maximalist  
- **trend_master** - Technical momentum trader
- **market_contrarian** - Contrarian value investor
- **yolo_king** - Ultimate degen with 100x mentality

## 🎮 Usage Examples

### Run Automated Trading Test

```bash
# Test the complete automated system (3 iterations)
poetry run python test_automated_trading.py

# Test specific components
poetry run python test_mock_profiles.py      # Mock social profiles
poetry run python test_end_to_end.py         # Full pipeline
poetry run python test_complete_flow.py      # RISE API integration
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

## 🔐 Security Notes

- **Different Keys Required**: Account and signer keys MUST be different for security
- **Gasless Trading**: All transactions are sponsored by RISE API - no ETH needed
- **Testnet Only**: This implementation is designed for RISE testnet
- **Private Keys**: Never commit real private keys to version control

## 🌐 RISE Testnet Info

- **Network**: RISE Testnet
- **Chain ID**: 11155931
- **RPC**: https://testnet.riselabs.xyz
- **Explorer**: https://explorer.testnet.riselabs.xyz
- **API**: https://api.testnet.rise.trade
- **Faucet**: Automatically triggered by deposit calls

## 📚 API Reference

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

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `poetry run pytest`
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Troubleshooting

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

---

Built with ❤️ for the RISE ecosystem