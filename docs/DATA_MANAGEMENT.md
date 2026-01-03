# Data Management Architecture

## Overview

The RISE AI Trading Bot manages data from multiple sources to create a comprehensive view of trading activity, market conditions, and account performance. This document explains our data architecture, sources, storage strategies, and synchronization methods.

## Data Sources

### 1. RISE API (Primary Trading Data)
**Endpoint**: `https://api.testnet.rise.trade`
- **Markets**: Real-time prices, funding rates, open interest
- **Positions**: Open positions, leverage, unrealized P&L
- **Orders**: Order status, fills, trade history
- **Account Info**: Available balance, margin requirements
- **Update Frequency**: On-demand for trading, 30s for market data

### 2. RPC Blockchain Data (On-chain Truth)
**Endpoint**: `https://indexing.testnet.riselabs.xyz`
- **Account Equity**: Direct from PerpsManager contract (0x68cAcD54a8c93A3186BF50bE6b78B761F728E1b4)
- **Update Frequency**: Every 60 seconds (configurable)
- **Purpose**: Ground truth for account value, reconciliation

### 3. Local Storage (JSON Files)
**Directory**: `data/`
- **accounts.json**: Account details, keys, personas, registration status
- **trades.json**: Trade history with AI reasoning
- **positions.json**: Position snapshots for P&L tracking
- **equity_snapshots.json**: Historical equity data (200 entries per account)
- **chat_sessions.json**: Conversation history and context (deprecated - see chat/)
- **trading_decisions.json**: AI decision logs with outcomes
- **markets.json**: Cached market metadata
- **thought_processes.json**: Shared state between chat and trading
- **chat/{profile_id}.jsonl**: Persistent chat history (JSONL format, one file per profile)
- **api_keys.json**: API key storage for admin authentication

### 4. In-Memory Caches
- **GlobalMarketManager**: Singleton for market prices/changes
- **EquityMonitor**: Recent equity values with 1h/24h deltas
- **ThoughtProcess**: Active trading influences from chat
- **EventBus**: Real-time event distribution for WebSocket connections
- **ChatContextCache**: Token-counted message windows per profile

## Data Flow Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   RISE API      │     │   RPC Node      │     │  User Input     │
│  (Trading)      │     │  (Equity)       │     │  (Chat/API)     │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                         │
         ▼                       ▼                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Service Layer                             │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ RiseClient  │  │EquityMonitor │  │ ProfileChat        │    │
│  │             │  │              │  │                    │    │
│  └─────────────┘  └──────────────┘  └────────────────────┘    │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ EventBus    │  │ WebSocket    │  │ ProfileFactory     │    │
│  │             │  │              │  │                    │    │
│  └─────────────┘  └──────────────┘  └────────────────────┘    │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Storage Layer                               │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ JSONStorage │  │ Memory Cache │  │ ThoughtProcess     │    │
│  │ (Files)     │  │ (Transient)  │  │ (Shared State)    │    │
│  └─────────────┘  └──────────────┘  └────────────────────┘    │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ ChatStore   │  │ EventQueue   │  │ APIKeys           │    │
│  │ (JSONL)     │  │ (AsyncQueue) │  │ (Hashed)          │    │
│  └─────────────┘  └──────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Decision Layer                              │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ TradingLoop │  │ ParallelExec │  │ API Server        │    │
│  │             │  │              │  │                    │    │
│  └─────────────┘  └──────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Storage Strategies

### JSON File Storage
**Why JSON?**
- Human-readable for debugging
- Simple atomic writes
- No database dependencies
- Easy backup/restore
- Git-friendly for tracking changes

**Write Strategy**:
```python
# Atomic write pattern
def _save_json(self, file_path: Path, data: Dict) -> None:
    # Read-modify-write pattern
    existing = self._load_json(file_path)
    existing.update(data)
    
    # Atomic write with temp file
    temp_path = file_path.with_suffix('.tmp')
    with open(temp_path, 'w') as f:
        json.dump(existing, f, indent=2)
    temp_path.replace(file_path)
```

### Memory Caching
**Market Data Cache**:
- 30-second TTL
- Shared across all profiles via singleton
- Reduces API calls significantly

**Equity Cache**:
- Updates every 60 seconds
- Stores latest + historical deltas
- Enables quick P&L calculations

### Historical Data Management
**Equity Snapshots**:
- Rolling window of 200 entries per account
- Enables 1h/24h change calculations
- Automatic trimming on save

**Trading Decisions**:
- Full history retained
- Outcome tracking for ML training
- Success rate calculations

## Data Synchronization

### 1. Background Tasks
**Market Manager** (`GlobalMarketManager`):
```python
async def start_background_updates(self):
    # Updates every 30 seconds
    # Refreshes markets.json every 15 minutes
```

**Equity Monitor** (`EquityMonitor`):
```python
async def start_polling(self, interval=60):
    # Polls all account equity
    # Updates snapshots and deltas
```

### 2. Event-Driven Updates
- **On Trade Execution**: Update positions, calculate P&L, publish trade events
- **On Chat Message**: Update thought processes, influences, stream via WebSocket
- **On Order Fill**: Check and update decision outcomes, publish order events
- **On Equity Change**: Publish account.update events
- **On Profile Update**: Publish profile.updated events

### 3. Reconciliation
- **Equity vs Positions**: RPC equity is ground truth
- **Order Status**: Poll RISE API for fills
- **Market Prices**: Cross-check multiple sources

## Data Consistency

### Atomic Operations
All file writes use atomic patterns:
1. Read existing data
2. Modify in memory
3. Write to temp file
4. Atomic rename

### Locking Strategy
- File-level locks for JSON writes
- AsyncLock for background tasks
- No cross-file transactions

### Error Recovery
- Keep last known good values in cache
- Circuit breaker for repeated failures
- Graceful degradation (use stale data)

## Performance Optimizations

### 1. Batch Operations
```python
# Fetch equity for multiple accounts in one call
async def fetch_equity_batch(self, addresses: List[str])
```

### 2. Caching Strategy
- Hot data in memory (prices, recent equity)
- Warm data in JSON files
- Cold data can be pruned (old snapshots)

### 3. Parallel Execution
- Concurrent API calls where possible
- Background tasks don't block trading
- Separate threads for I/O operations

## Monitoring & Debugging

### Health Checks
```python
GET /health
{
    "equity_monitor": {
        "last_update": "2024-01-02T10:00:00Z",
        "consecutive_failures": 0
    },
    "market_manager": {
        "cache_age_seconds": 15,
        "markets_tracked": 12
    }
}
```

### Debug Endpoints
- `/api/debug/equity/{account_id}` - Raw equity data
- `/api/debug/cache` - Current cache contents
- `/api/debug/storage` - File sizes and timestamps

### Logging
- Structured logs with context
- Separate log levels per component
- Performance metrics (update times)

## Recent Enhancements (Phase A-C)

### WebSocket Real-Time Events
- **EventBus**: Pub/sub system for real-time updates
- **Event Types**: market.update, trade.*, account.update, chat.*, profile.*
- **Deduplication**: Prevents echo of user's own messages via sender_id
- **Subscriptions**: Global or profile-specific event streams

### Chat Persistence
- **JSONL Storage**: One file per profile for scalable chat history
- **Token Management**: Context windows with tiktoken counting
- **Streaming Support**: OpenRouter integration for chunk-by-chunk responses
- **Message IDs**: Unique identifiers for deduplication and correlation

### Profile Management
- **ProfileFactory**: Centralized creation with RISE setup automation
- **Initial Equity**: Baseline tracking for accurate P&L calculations
- **Update API**: PUT endpoint for persona modifications
- **Event Publishing**: Real-time notifications of profile changes

## Future Enhancements

### Near Term
1. **Redis Cache**: For multi-instance deployments
2. **Webhook Support**: Real-time order fill notifications
3. **Data Export**: CSV/Parquet for analysis

### Long Term
1. **TimescaleDB**: For time-series data
2. **GraphQL API**: Flexible data queries
3. **ML Pipeline**: Feature store for predictions

## Configuration

### Environment Variables
```bash
# RPC Configuration
BACKEND_RPC_URL=https://indexing.testnet.riselabs.xyz
RPC_URL=https://testnet.riselabs.xyz

# Polling Intervals
EQUITY_POLL_INTERVAL=60
MARKET_UPDATE_INTERVAL=30

# Storage Limits
EQUITY_HISTORY_LIMIT=200
TRADE_HISTORY_DAYS=30

# Performance
EQUITY_BATCH_SIZE=10
API_TIMEOUT=30
```

### File Structure
```
data/
├── accounts.json           # Account registry with personas
├── equity_snapshots.json   # Historical equity (200 entries/account)
├── markets.json           # Market metadata cache
├── positions.json         # Position snapshots
├── trades.json            # Trade history
├── trading_decisions.json # AI decision log with outcomes
├── chat_sessions.json     # Legacy chat history (deprecated)
├── thought_processes.json # Shared state between chat/trading
├── pending_actions.json   # Action queue for trading
├── api_keys.json         # Admin API key storage
├── chat/                 # Chat persistence directory
│   ├── {profile_id}.jsonl # Per-profile chat history (JSONL)
│   └── ...              # One file per profile
└── tmp/                  # Temporary files for atomic writes
```

## Best Practices

1. **Always use checksummed addresses** for RPC calls
2. **Handle None values** in equity calculations
3. **Validate data types** when loading from JSON
4. **Log all data source errors** with context
5. **Test with empty/corrupted files** 
6. **Monitor file sizes** to prevent unbounded growth
7. **Use UTC timestamps** everywhere
8. **Keep sensitive data encrypted** (private keys)

## Troubleshooting

### Common Issues

**"Market not found"**
- Run `scripts/update_markets.py` to refresh
- Check markets.json for corruption

**"Equity fetch failed"**
- Verify RPC endpoint is accessible
- Check account address checksum
- Review rate limits

**"Storage corrupted"**
- Look for .tmp files (incomplete writes)
- Validate JSON syntax
- Check file permissions

### Recovery Procedures

1. **Corrupted JSON File**:
   ```bash
   mv data/file.json data/file.json.backup
   echo "{}" > data/file.json
   ```

2. **Stale Cache**:
   ```python
   manager = GlobalMarketManager()
   await manager.get_latest_data(force_update=True)
   ```

3. **Missing Equity Data**:
   ```python
   monitor = get_equity_monitor()
   await monitor.update_all_accounts()
   ```