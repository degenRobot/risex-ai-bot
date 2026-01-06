# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: RISE AI Trading Bot

An autonomous trading system where AI traders with unique personalities make decisions on RISE perpetuals DEX. Users can influence trading behavior through chat conversations.

## Bash Commands

```bash
# Install and setup
poetry install
cp .env.example .env

# Run tests
poetry run pytest                                              # All tests
poetry run python tests/trading/test_rise_market_orders.py    # Test orders
poetry run python tests/chat/test_profile_chat.py             # Test chat
poetry run pytest tests/realtime/                              # Test WebSocket infrastructure
poetry run pytest tests/realtime/test_websocket.py             # Test WebSocket endpoint
poetry run python tests/ai/test_prompt_system.py              # Test modular prompts
poetry run python tests/trading/test_action_queue.py          # Test action queue
poetry run python tests/integration/test_improved_system.py    # Test improved prompt integration

# Run bot
poetry run python scripts/run_enhanced_bot.py --interval 60   # Production bot
poetry run python scripts/run_trading_bot.py --live           # Live trading

# Development
poetry run ruff check . --fix    # Lint and fix
poetry run mypy .                # Type check
poetry run uvicorn app.api.server:app --reload  # API server

# Update markets data
poetry run python scripts/update_markets.py  # Fetch latest markets from RISE API
```

## Core Files

- `app/services/rise_client.py` - RISE API client (market order workaround here)
- `app/services/profile_chat.py` - Chat system with AI tool calling + modular prompts
- `app/services/thought_process.py` - Shared state manager
- `app/trader_profiles.py` - Immutable base personas
- `scripts/run_enhanced_bot.py` - Main trading bot runner
- `app/realtime/events.py` - WebSocket event models and types
- `app/realtime/bus.py` - Event bus for pub/sub messaging
- `app/realtime/ws.py` - WebSocket endpoint for real-time streaming
- `app/ai/prompts/` - Modular prompt system for personalities
- `app/ai/personas/` - JSON persona definitions (cynical_midwit, leftcurve_redacted, etc)
- `app/ai/prompt_loader_improved.py` - Enhanced prompt loader with persona support
- `app/ai/shared_speech.py` - Global speech patterns for all personalities
- `app/trading/actions.py` - Trading action queue for multi-market execution

## Code Style

- Use async/await for all I/O operations
- Type hints required for function signatures
- OpenRouter tool calls for all state mutations (never parse raw text)
- JSON storage for all persistence (no databases)
- Decimal handling: USDC=6 decimals, RISE internal=18 decimals

## Testing

```bash
# After changing order logic
poetry run python tests/trading/test_rise_market_orders.py

# After modifying chat system  
poetry run python tests/chat/test_profile_chat.py

# Full integration test
poetry run python tests/core/test_automated_trading.py --continuous
```

## Repository Etiquette

- Always run `poetry run ruff check . --fix` before commits
- Test market orders after any rise_client.py changes
- Update thought_processes.json atomically (read-modify-write)
- Never commit .env or private keys
- Add new personas to both trader_profiles.py AND speech_styles.py

## Environment Setup

```bash
# Required in .env
PRIVATE_KEY=0x...              # Main account key
SIGNER_PRIVATE_KEY=0x...       # Different key (MUST be different)
OPENROUTER_API_KEY=...         # For AI features
BACKEND_RPC_URL=https://indexing.testnet.riselabs.xyz
```

⚠️ **Dependencies**: Must use `eth-account==0.10.0` for EIP-712 signing compatibility

## Warnings

⚠️ **CRITICAL**: Market orders on RISE testnet MUST use `order_type="limit"` with `price=0`
- True market orders (`order_type="market"`) will revert with "status 0"
- This is handled in `place_market_order()` but be aware when debugging
- Order type mapping: `order_type=0` for limit orders (always use this)
- Market-like execution: `order_type=0, price=0, tif=3 (IOC)`

⚠️ **Decimal Precision**: USDC has 6 decimals but RISE uses 18 internally
- Always use `int(amount * 1e18)` for RISE order sizes/prices
- Position sizes from API are in 18-decimal format
- Minimum order size appears to be 0.001 BTC (smaller sizes may fail)

⚠️ **Async State**: ThoughtProcess is shared between chat and trading
- Use locks when updating to prevent race conditions
- Always read full state before modifications

## Workflow Examples

### Add New Trader Profile
```bash
# 1. Edit app/trader_profiles.py
# 2. Add speech style in app/services/speech_styles.py
# 3. Test
poetry run python tests/chat/test_profile_chat.py
```

### Debug Failed Order
```bash
# Check if using correct order type
grep -n "order_type" app/services/rise_client.py
# Test with minimal example
poetry run python tests/trading/test_rise_market_orders.py
# For detailed order placement info, see docs/ORDER_PLACEMENT.md
```

### Track Chat Influence
```bash
# View thought process entries
cat data/thought_processes.json | jq '.[] | select(.entry_type=="chat_influence")'
# Check if trading engine reads them
grep -n "get_trading_influences" app/core/trading_loop.py
```