# Architecture Overview

## System Design

The RISE AI Trading Bot is an autonomous trading system where AI traders with unique personalities make decisions on RISE perpetuals DEX. Users can influence trading behavior through chat conversations.

**Key Innovation**: Chat-driven AI personality influence system with real-time trading integration and dynamic position sizing based on blockchain free margin.

### Component Overview

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│    Chat API         │     │   Trading Engine    │     │  Account Manager    │
│  (User Influence)   │     │ (Parallel Executor) │     │  (Fresh Creation)   │
└──────────┬──────────┘     └──────────┬──────────┘     └──────────┬──────────┘
           │                           │                           │
           │                           │                           │
           ▼                           ▼                           ▼
    ┌───────────────────────────────────────────────────────────────────────┐
    │                    Shared Profile System                              │
    │              (AI Personalities + Tool Calling)                       │
    └───────────────────────────────────────────────────────────────────────┘
                       │                           │
                       ▼                           ▼
    ┌──────────────────────────────────┐    ┌──────────────────────────────────┐
    │        Equity Monitor            │    │         Market Manager          │
    │   (RPC: equity + free margin)    │    │    (Live RISE API Data)        │
    └──────────────────────────────────┘    └──────────────────────────────────┘
                       │                           │
                       ▼                           ▼
    ┌───────────────────────────────────────────────────────────────────────┐
    │                         JSON Storage                                  │
    │  (accounts, equity, markets, chat, thoughts, trades, free margin)     │
    └───────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Fresh Account Creation:
Keys Generated → Signer Registration → USDC Deposit → Profile Creation → Ready for Trading

Chat Influence Flow:
User Message → Chat API → AI Processing → Tool Calls → Profile Updates → Trading Context

Trading Decision Flow:
Market Data + Free Margin → Position Sizing → AI Decision → Market Order → Equity Update → Feedback Loop

Real-time Monitoring:
RPC Calls (getAccountEquity + getFreeCrossMarginBalance) → Storage → Trading Context → Position Limits
```

## Core Components

### 1. API Server (app/api/server.py)

FastAPI application providing REST endpoints:

- /health - Health check
- /api/profiles - List trading profiles
- /api/profiles/{id}/chat - Chat with AI trader
- /api/profiles/{id}/context - Get trading context
- /api/profiles/{id}/start - Start trading
- /api/profiles/{id}/stop - Stop trading

### 2. Trading Engine (app/core/parallel_executor.py)

Parallel execution system that:
- Runs trading cycles every N seconds (300s in production)
- Processes all profiles concurrently
- Reads shared thought process for context
- Calculates position sizes based on free margin
- Makes trading decisions based on personality + thoughts + risk limits
- Updates thought process with decisions

### 3. AI Integration (app/services/ai_client.py)

OpenRouter integration using OpenAI SDK:
- Chat completions with streaming
- Tool calling for structured actions
- JSON mode for reliable parsing
- Personality-based prompting

### 4. Profile Chat Service (app/services/profile_chat.py)

Manages conversations with AI traders:
- Maintains chat history
- Handles tool calls
- Updates market outlooks
- Records influences
- Provides real-time P&L and free margin

Available tools:
- update_market_outlook - Change view on specific asset
- update_trading_bias - Adjust overall trading approach
- add_influence - Record what influenced thinking
- place_market_order - Execute trades with position sizing

### 5. Thought Process Manager (app/services/thought_process.py)

Shared state management:
- Thread-safe async operations
- Entry types: chat_influence, market_analysis, trading_decision
- Summarization for different purposes
- Time-based filtering

### 6. Storage Layer (app/services/storage.py)

JSON-based persistence:
- Atomic file operations
- Backup on write
- Schema validation
- Query methods for each data type

## Personality System

### Base Personas (Immutable)

```
BasePersona
├── name: str
├── handle: str
├── core_personality: str
├── speech_style: str
├── risk_profile: RiskProfile
├── core_beliefs: dict
├── decision_style: str
└── emotional_triggers: list
```

### Current Thinking (Mutable)

```
CurrentThinking
├── market_outlooks: dict[asset, outlook]
├── recent_influences: list[influence]
├── trading_biases: list[bias]
├── confidence_levels: dict
└── last_updated: datetime
```

## Async Architecture

### Chat Flow

```python
async def chat_flow():
    # 1. Receive user message
    message = await request.json()
    
    # 2. Load profile and context
    profile = load_trader_profile(account_id)
    context = await get_trading_context(account_id)
    
    # 3. AI processes with tools
    response = await ai.chat_with_tools(
        messages=[system, user],
        tools=[update_outlook, add_influence]
    )
    
    # 4. Handle tool calls
    for tool_call in response.tool_calls:
        await process_tool_call(tool_call)
    
    # 5. Update thought process
    await thought_manager.add_entry(
        account_id=account_id,
        entry_type="chat_influence",
        content=tool_call.arguments
    )
    
    # 6. Return response
    return {"response": ai_message, "updates": profile_updates}
```

### Trading Flow

```python
async def trading_flow():
    # 1. Get market data and account equity/margin
    markets = await rise_client.get_markets()
    equity_data = await equity_monitor.fetch_all_equity()
    
    # 2. For each profile (parallel)
    async def process_profile(profile):
        # Get free margin for position sizing
        free_margin = equity_data[profile.address]['free_margin']
        
        # Read recent thoughts
        thoughts = await thought_manager.get_recent(
            account_id=profile.id,
            purpose="trading_decision"
        )
        
        # Calculate max position sizes
        max_sizes = calculate_position_limits(
            free_margin=free_margin,
            risk_profile=profile.risk_profile
        )
        
        # Get AI decision with context
        decision = await ai.get_trade_decision(
            persona=profile.persona,
            market_data=markets,
            thoughts=thoughts,
            max_sizes=max_sizes
        )
        
        # Execute if confident
        if decision.confidence > 0.6:
            await rise_client.place_market_order(...)
            
            # Record decision
            await thought_manager.add_entry(
                entry_type="trading_decision",
                content=decision
            )
    
    # 3. Process all profiles concurrently
    await asyncio.gather(*[
        process_profile(p) for p in profiles
    ])
```

## Security Considerations

### API Security
- No authentication (testnet only)
- HTTPS enforced in production
- Input validation on all endpoints
- Rate limiting via Fly.io

### Key Management
- API keys stored as environment variables
- No private keys in trading bot
- Gasless trading via RISE API
- Keys never logged or exposed

### Data Protection
- JSON files in persistent volume
- Atomic writes prevent corruption
- Backup before modifications
- No sensitive data in responses

## Deployment Architecture

### Fly.io Configuration

```
┌─────────────────────────────────┐
│         Fly.io Edge             │
│     (Global Load Balancer)      │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│      App Instance (sjc)         │
│  ┌─────────────────────────┐    │
│  │   FastAPI (port 8080)   │    │
│  └─────────────────────────┘    │
│  ┌─────────────────────────┐    │
│  │   Trading Engine        │    │
│  │  (5 min intervals)      │    │
│  └─────────────────────────┘    │
│  ┌─────────────────────────┐    │
│  │   Equity Monitor        │    │
│  │  (60s RPC updates)      │    │
│  └─────────────────────────┘    │
│  ┌─────────────────────────┐    │
│  │  Persistent Volume      │    │
│  │      /data (1GB)        │    │
│  └─────────────────────────┘    │
└─────────────────────────────────┘
```

### Scaling Strategy

- Horizontal: Add more instances (profiles distributed)
- Vertical: Increase CPU/memory for more profiles
- Storage: Expand volume as needed

## Performance Optimizations

### Parallel Processing
- All profiles execute concurrently
- Async I/O for all external calls
- Shared market data updates
- Combined equity/margin RPC calls

### Caching
- Market data cached for 30 seconds
- Thought summaries cached
- Profile data loaded once per cycle
- Equity/margin data refreshed every 60s

### Resource Management
- Connection pooling for HTTP clients
- Graceful shutdown handling
- Memory-efficient JSON storage
- Atomic file operations prevent corruption

## Monitoring and Observability

### Logging
- Structured JSON logs
- Log levels: DEBUG, INFO, WARNING, ERROR
- Contextual information (account_id, action)
- Trading decisions with reasoning
- Equity/margin updates with timestamps

### Metrics
- Trading decisions per cycle
- API response times
- Error rates by component
- P&L tracking (equity - deposit)
- Free margin utilization
- Position sizing adherence

### Health Checks
- /health endpoint
- Storage accessibility
- API connectivity
- RPC node responsiveness

### Analytics
- /analytics endpoint provides:
  - Total equity across all traders
  - Aggregate P&L
  - Active trader count
  - Top performer identification
  - Position distribution

## Technical Details

### RISE Market Orders
- Market orders use `order_type="limit"` with `price=0`
- Time-in-force: IOC (Immediate or Cancel)
- Minimum sizes: 0.001 for most markets
- Orders placed via EIP-712 gasless signing

### RPC Integration
- Contract: PerpsManager (0x68cAcD54a8c93A3186BF50bE6b78B761F728E1b4)
- Methods: getAccountEquity, getFreeCrossMarginBalance
- Network: RISE testnet via indexing RPC
- Update frequency: 60 seconds

### Position Sizing Rules
- Conservative (cynical): 10-20% of free margin
- Moderate (midwit): 20-35% of free margin
- Aggressive (left curve): 35-50% of free margin
- Maximum single position: 50% of free margin

## Recent Improvements (January 2026)

1. **P&L Calculation**: Fixed to use equity - deposit instead of unrealized P&L
2. **Free Margin Display**: Added RPC call to show available collateral
3. **Position Sizing**: Dynamic calculation based on risk profile and free margin
4. **Order Execution**: Fixed async/await issues and success detection
5. **Multi-Market Support**: Expanded beyond BTC/ETH to all RISE markets
6. **API Enhancements**: Added analytics, admin endpoints, and improved data consistency