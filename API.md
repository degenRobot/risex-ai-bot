# RISE AI Trading Bot API Documentation

## Base URL
- Production: `https://risex-trading-bot.fly.dev`
- Local: `http://localhost:8000`

## Authentication

### API Key Authentication (Admin Endpoints)
Admin endpoints require an API key in the `X-API-Key` header.

#### Generate API Key
```bash
POST /api/admin/api-keys/generate
Headers: X-Master-Key: master-secret-key
```

**Response:**
```json
{
  "api_key": "ska_...",
  "message": "Save this key - it won't be shown again",
  "usage": "Include in X-API-Key header for admin endpoints"
}
```

## Public Endpoints

### Health Check
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "accounts": 15,
  "storage": "connected"
}
```

### List Profiles (Paginated)
```bash
GET /api/profiles?page=1&limit=20
```

**Query Parameters:**
- `page`: Page number (default: 1, min: 1)
- `limit`: Items per page (default: 20, min: 1, max: 100)

**Response:**
```json
{
  "profiles": [
    {
      "account_id": "7f673612-83ad-4e34-a323-1d77126440a8",
      "handle": "crypto_degen",
      "name": "The Crypto Degen",
      "trading_style": "aggressive",
      "is_trading": false,
      "total_pnl": 0,
      "position_count": 0,
      "pending_actions": 0
    }
  ],
  "total": 15,
  "page": 1,
  "limit": 20,
  "has_more": false
}
```

### List All Profiles (No Pagination)
```bash
GET /api/profiles/all
```

**Response:**
```json
[
  {
    "account_id": "7f673612-83ad-4e34-a323-1d77126440a8",
    "handle": "crypto_degen",
    "name": "The Crypto Degen",
    "trading_style": "aggressive",
    "is_trading": false,
    "total_pnl": 0,
    "position_count": 0,
    "pending_actions": 0
  }
]
```

### Get Profile Details
```bash
GET /api/profiles/{handle}
```

**Parameters:**
- `handle`: Profile handle (e.g., "leftCurve", "midCurve", "rightCurve")

**Response:**
```json
{
  "account_id": "vXgJJCcakMbmvmq_CPXTnA",
  "handle": "leftCurve",
  "name": "Drunk Wassie",
  "bio": "wassie who drinks too much and trades on emotions and FOMO",
  "trading_style": "aggressive",
  "risk_tolerance": 0.8,
  "personality_traits": ["confident", "optimistic"],
  "is_trading": false,
  "account_address": "0x076652bc49B7818604F397f0320937248382301b",
  "positions": [
    {
      "account": "0x076652bc49B7818604F397f0320937248382301b",
      "market_id": "1",
      "side": "BUY",
      "size": "5000000000000000",
      "avg_entry_price": "90287599999999999999800",
      "quote_amount": "-451438000000000000000",
      "margin_mode": "CROSS",
      "leverage": "50000000000000000000"
    }
  ],
  "pending_actions": [
    {
      "id": "d2e4e513-e01a-4508-a60f-bba9b2de27d1",
      "type": "stop_loss",
      "condition": "price <= 85000",
      "market": "BTC",
      "created_at": "2026-01-03T01:46:30.493679",
      "description": "Stop Loss for BTC when price <= 85000"
    }
  ],
  "recent_trades": [],
  "total_pnl": -1.22,
  "win_rate": null
}
```

## Chat Endpoints

### Chat with Profile
```bash
POST /api/profiles/{account_id}/chat
```

**Parameters:**
- `account_id`: Account UUID (e.g., "7f673612-83ad-4e34-a323-1d77126440a8")

**Request Body:**
```json
{
  "message": "BTC is pumping to 100k!",
  "chatHistory": "",
  "sessionId": null
}
```

**Response:**
```json
{
  "response": "omg senpai BTC to 100k?! moon mission confirmed...",
  "chatHistory": "[{\"role\": \"user\", \"content\": \"...\"}, ...]",
  "profileUpdates": [
    "Updated BTC outlook to Bullish: ...",
    "Updated trading bias: Bullish"
  ],
  "sessionId": "cc3fbed7-c404-4f6d-a0eb-89d0bf4d328a",
  "context": {
    "currentPnL": 0,
    "openPositions": 0,
    "lastUpdate": "2026-01-02T07:50:30.931535",
    "personality": "Wassie McSmol",
    "speechStyle": "smol",
    "riskProfile": "degen"
  }
}
```

### Get Profile Summary
```bash
GET /api/profiles/{account_id}/summary
```

**Response:**
```json
{
  "account_id": "7f673612-83ad-4e34-a323-1d77126440a8",
  "name": "The Crypto Degen",
  "handle": "crypto_degen",
  "basePersona": {
    "immutableTraits": ["impulsive", "overconfident"],
    "tradingStyle": "aggressive",
    "riskTolerance": 0.8
  },
  "currentThinking": {
    "marketOutlook": {
      "BTC": "Bearish: Price dropping fast...",
      "ETH": "Neutral"
    },
    "tradingBias": "Bearish",
    "recentInfluences": [
      {
        "timestamp": "2026-01-02T07:50:30",
        "message": "Super scared me, now panicking into short position"
      }
    ]
  }
}
```

### Get Profile Context
```bash
GET /api/profiles/{account_id}/context
```

**Response:**
```json
{
  "profile_id": "vXgJJCcakMbmvmq_CPXTnA",
  "profile_name": "Drunk Wassie",
  "trading_context": {
    "current_pnl": -1.22,
    "open_positions": 1,
    "available_balance": 2989.78,
    "positions": [
      {
        "account": "0x076652bc49B7818604F397f0320937248382301b",
        "market_id": "1",
        "side": "BUY",
        "size": "5000000000000000",
        "avg_entry_price": "90287599999999999999800",
        "quote_amount": "-451438000000000000000",
        "margin_mode": "CROSS",
        "leverage": "50000000000000000000"
      }
    ],
    "recent_trades": [],
    "current_equity": 2998.78,
    "free_margin": 2989.78,
    "equity_last_updated": "2026-01-03T10:00:00Z",
    "max_btc_size": 0.016,
    "max_eth_size": 0.482,
    "orders": [
      {
        "id": "4099831",
        "market_id": "1",
        "side": "BUY",
        "type": "MARKET",
        "size": "0.001",
        "filled_size": "0.001",
        "avg_price": "87745.1",
        "status": "ORDER_STATUS_FILLED",
        "created_at": "1766889766000000000"
      }
    ],
    "orders_count": 5
  },
  "timestamp": null
}
```

## Admin Endpoints (Requires API Key)

### List All Profiles (Admin View)
```bash
GET /api/admin/profiles
Headers: X-API-Key: {your_api_key}
```

**Response:**
```json
{
  "total": 15,
  "profiles": [
    {
      "id": "7f673612-83ad-4e34-a323-1d77126440a8",
      "address": "0x11cDE69d5c4b5eeDb73AdaB19Afdf653060773bA",
      "signer_address": "0x...",
      "persona": {...},
      "is_active": true,
      "created_at": "2026-01-01T19:38:35"
    }
  ]
}
```

### Create New Profile
```bash
POST /api/admin/profiles
Headers: X-API-Key: {your_api_key}
```

**Request Body:**
```json
{
  "name": "Test Trader",
  "handle": "test_trader",
  "bio": "A test trading profile",
  "trading_style": "momentum",
  "risk_tolerance": 0.5,
  "personality_type": "midwit",
  "initial_deposit": 100.0,
  "favorite_assets": ["BTC", "ETH"],
  "personality_traits": ["analytical", "balanced"]
}
```

**Trading Styles:** `aggressive`, `conservative`, `contrarian`, `momentum`, `degen`

**Personality Types:** `cynical`, `leftCurve`, `midwit`

**Response:**
```json
{
  "profile_id": "f1a96dac-89fd-4eeb-9dc6-5612085425d0",
  "address": "0xdE3244FCBf035A374c556d3E1c1774ebA74436fD",
  "signer_address": "0x6A37D8A9213489a273bf037C20090d7804388FD8",
  "persona": {...},
  "initial_deposit": 100.0,
  "message": "Profile created and funded with 100.0 USDC"
}
```

### Delete Profile
```bash
DELETE /api/admin/profiles/{profile_id}
Headers: X-API-Key: {your_api_key}
```

**Response:**
```json
{
  "message": "Profile {profile_id} deactivated"
}
```

### Get Profile Balance
```bash
GET /api/admin/profiles/{profile_id}/balance
Headers: X-API-Key: {your_api_key}
```

**Response:**
```json
{
  "address": "0x11cDE69d5c4b5eeDb73AdaB19Afdf653060773bA",
  "balance": 100.0,
  "available": 100.0,
  "account_info": {
    "marginSummary": {
      "accountValue": 100.0,
      "freeCollateral": 100.0
    }
  }
}
```

### Get Profile Positions
```bash
GET /api/admin/profiles/{profile_id}/positions
Headers: X-API-Key: {your_api_key}
```

**Response:**
```json
{
  "positions": {
    "BTC-USD": {
      "market": "BTC-USD",
      "side": "long",
      "size": 0.001,
      "notionalValue": 95.5,
      "unrealizedPnl": -2.5
    }
  },
  "total_value": 95.5,
  "timestamp": "2026-01-02T07:55:00"
}
```

### Place Order for Profile
```bash
POST /api/admin/profiles/{profile_id}/orders
Headers: X-API-Key: {your_api_key}
```

**Request Body:**
```json
{
  "market": "BTC-USD",
  "side": "buy",
  "size": 0.001,
  "reasoning": "Admin manual order"
}
```

**Response:**
```json
{
  "success": true,
  "order_id": "123456",
  "market": "BTC-USD",
  "side": "buy",
  "size": 0.001,
  "message": "Order placed successfully"
}
```

## Position & Order Endpoints

### Get Trading Signals
```bash
GET /api/profiles/{account_id}/signals?limit=10
```

**Response:**
```json
{
  "account_id": "vXgJJCcakMbmvmq_CPXTnA",
  "signals": [
    {
      "id": "signal_123",
      "type": "trade_decision",
      "market": "BTC",
      "action": "buy",
      "confidence": 0.7,
      "size": 0.001,
      "reason": "Bullish momentum on BTC, expecting breakout above 91k",
      "created_at": "2026-01-03T10:15:00Z",
      "status": "executed",
      "result": {
        "order_id": "4099831",
        "fill_price": 87745.1
      }
    }
  ],
  "total_signals": 15
}
```

### Get Trading Activity
```bash
GET /api/profiles/{account_id}/activity?hours=24
```

**Response:**
```json
{
  "account_id": "vXgJJCcakMbmvmq_CPXTnA",
  "is_trading_active": false,
  "last_activity": "2026-01-03T09:30:00Z",
  "activities": [
    {
      "type": "trade",
      "action": "BUY 0.001 BTC at $87,745",
      "timestamp": "2026-01-03T09:30:00Z",
      "details": {
        "market": "BTC",
        "side": "BUY",
        "size": 0.001,
        "price": 87745.1,
        "status": "filled"
      }
    },
    {
      "type": "equity_update",
      "action": "Equity updated to $2,998.78",
      "timestamp": "2026-01-03T09:00:00Z",
      "details": {
        "equity": 2998.78,
        "free_margin": 2989.78,
        "positions_count": 1
      }
    }
  ],
  "total_activities": 45,
  "time_range_hours": 24
}
```

## Trading Control Endpoints

### Start Trading
```bash
POST /api/profiles/{handle}/start
```

**Response:**
```json
{
  "success": true,
  "message": "Trading started for crypto_degen",
  "data": {
    "account_id": "7f673612-83ad-4e34-a323-1d77126440a8"
  }
}
```

### Stop Trading
```bash
POST /api/profiles/{handle}/stop
```

**Response:**
```json
{
  "success": true,
  "message": "Trading stopped for crypto_degen"
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid API key"
}
```

### 404 Not Found
```json
{
  "detail": "Profile not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "type": "enum",
      "loc": ["body", "trading_style"],
      "msg": "Input should be 'aggressive', 'conservative', 'contrarian', 'momentum' or 'degen'"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to place order: {error_message}"
}
```

## Recent Updates (January 3, 2026)

### New Fields in Responses

1. **Profile Endpoints** now include:
   - `positions`: Array of open positions from RISE API with 18-decimal precision
   - `orders`: Historical order data with filled orders and status
   - `free_margin`: Available collateral for new positions
   - `margin_used`: Collateral locked in positions
   - `max_btc_size`: Maximum BTC position size (50% of free margin)
   - `max_eth_size`: Maximum ETH position size (50% of free margin)
   - `deposit_amount`: Initial deposit amount

2. **Trading Context** (`/api/profiles/{account_id}/context`):
   - `current_pnl`: Now calculated as `equity - deposit_amount`
   - `available_balance`: Shows actual free margin from blockchain
   - `free_margin`: Available collateral
   - `positions`: Live position data from RISE perpetuals DEX
   - `orders`: Historical order data with execution details
   - `orders_count`: Total number of orders for the account
   - `max_position_sizes`: Object with max sizes per asset

3. **Position Data Format** (from RISE API):
   - All values in 18-decimal format (divide by 1e18 for human-readable)
   - `market_id`: 1=BTC, 2=ETH, 3=BNB, 4=SOL, 5=DOGE
   - `side`: "BUY"=long, "SELL"=short position
   - `size`: Position size in asset units (18 decimals)
   - `avg_entry_price`: Average entry price (18 decimals)
   - `quote_amount`: Position value in USDC (18 decimals, negative for longs)

4. **Order Data Format** (from RISE API):
   - `status`: "ORDER_STATUS_FILLED", "ORDER_STATUS_CANCELLED", etc.
   - `type`: "MARKET", "LIMIT", etc.
   - `filled_size`: Actual filled amount
   - `avg_price`: Average execution price
   - `created_at`: Timestamp in nanoseconds

5. **Analytics Endpoint** (`GET /analytics`):
   ```json
   {
     "total_equity": 7001.35,
     "total_pnl": 1.35,
     "active_traders": 3,
     "total_positions": 5,
     "top_performer": {
       "name": "Drunk Wassie",
       "pnl_percent": 0.12
     }
   }
   ```

### Admin Endpoints Update

**Update Account Data**
```bash
PATCH /api/admin/accounts/{account_id}
Headers: X-API-Key: {your_api_key}
```

**Request Body:**
```json
{
  "deposit_amount": 2000.0,
  "latest_equity": 2002.32,
  "free_margin": 1985.87
}
```

## Notes

1. **Account ID vs Handle**: 
   - List and detail endpoints now include `account_id` in responses
   - Chat/context/summary endpoints require `account_id` (UUID)
   - Profile detail endpoint uses `handle` (e.g., "crypto_degen")
   - Frontend no longer needs to maintain handle→account_id mapping
   
2. **Pagination**: 
   - `/api/profiles` supports pagination with `page` and `limit` parameters
   - Use `/api/profiles/all` for backward compatibility (no pagination)
   - Default page size is 20, maximum is 100

3. **Chat History**: Maintained per session, use same sessionId to continue conversation

4. **Profile Updates**: Chat can influence trader's market outlook and bias

5. **RISE Integration**: 
   - Positions and orders now fetched from RISE perpetuals DEX API
   - Data updated every 60 seconds via equity monitor service
   - Positions: `GET /v1/positions?account={address}`
   - Orders: `GET /v1/orders?account={address}&page_size=100`
   - All RISE values use 18-decimal precision
   - Free margin fetched via `getFreeCrossMarginBalance` RPC call
   - Equity fetched via `getAccountEquity` RPC call

6. **Position & Order Data**:
   - Live position data shows current open positions with P&L
   - Order history includes all filled, cancelled, and expired orders
   - Position sizes converted from 18-decimal format for display
   - Market ID mapping: 1=BTC, 2=ETH, 3=BNB, 4=SOL, 5=DOGE
   - Orders show execution details including avg_price and filled_size

7. **Order Placement**: 
   - Requires account to have USDC balance and free margin
   - Minimum order size: 0.001 for most markets
   - Market orders use: `order_type="limit"`, `price=0`, `tif=3` (IOC)
   - Position sizing based on free margin (max 50%)

8. **Multi-Market Support**:
   - BTC, ETH, SOL, BNB, DOGE, and more
   - Each market has specific minimum sizes
   - Prices fetched from market data (index_price or last_price)

9. **Error Handling**: 
   - API automatically repairs corrupted JSON data files
   - Graceful degradation when external services are unavailable
   - Order failures due to insufficient margin return appropriate errors
   - Position/order fetching continues even if individual calls fail