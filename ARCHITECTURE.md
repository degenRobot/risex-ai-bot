# Architecture Overview

## System Design

The RISE AI Trading Bot uses an asynchronous architecture with shared state management between chat and trading systems.

### Component Overview

```
┌─────────────────────┐     ┌─────────────────────┐
│    REST API         │     │   Trading Engine    │
│  (FastAPI/Uvicorn)  │     │  (Async Executor)   │
└──────────┬──────────┘     └──────────┬──────────┘
           │                           │
           │                           │
           ▼                           ▼
    ┌──────────────────────────────────────────┐
    │         Shared Thought Process           │
    │     (Async State Management)             │
    └──────────────────────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────┐
    │          JSON Storage Layer              │
    │  (accounts, decisions, chat, thoughts)   │
    └──────────────────────────────────────────┘
```

### Data Flow

```
User Input --> Chat API --> AI Processing --> Tool Calls
                                   │
                                   ▼
                          Update Thought Process
                                   │
                                   ▼
Market Data --> Trading Engine --> Read Thoughts --> Decision
                                                       │
                                                       ▼
                                                 Execute Trade
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
- Runs trading cycles every N seconds
- Processes all profiles concurrently
- Reads shared thought process for context
- Makes trading decisions based on personality + thoughts
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

Available tools:
- update_market_outlook - Change view on specific asset
- update_trading_bias - Adjust overall trading approach
- add_influence - Record what influenced thinking

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
    # 1. Get market data
    markets = await rise_client.get_markets()
    
    # 2. For each profile (parallel)
    async def process_profile(profile):
        # Read recent thoughts
        thoughts = await thought_manager.get_recent(
            account_id=profile.id,
            purpose="trading_decision"
        )
        
        # Get AI decision with context
        decision = await ai.get_trade_decision(
            persona=profile.persona,
            market_data=markets,
            thoughts=thoughts
        )
        
        # Execute if confident
        if decision.confidence > 0.6:
            await rise_client.place_order(...)
            
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

### Caching
- Market data cached for 30 seconds
- Thought summaries cached
- Profile data loaded once per cycle

### Resource Management
- Connection pooling for HTTP clients
- Graceful shutdown handling
- Memory-efficient JSON storage

## Monitoring and Observability

### Logging
- Structured JSON logs
- Log levels: DEBUG, INFO, WARNING, ERROR
- Contextual information (account_id, action)

### Metrics
- Trading decisions per cycle
- API response times
- Error rates by component

### Health Checks
- /health endpoint
- Storage accessibility
- API connectivity