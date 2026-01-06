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
  "chatHistory": "",  // Deprecated - server uses persistent history
  "sessionId": null,
  "user_id": "user-123",  // For message deduplication
  "stream": false  // Set to true for streaming responses
}
```

**New Features:**
- **Server-side chat history**: No need to send chatHistory anymore
- **Streaming responses**: Set `stream: true` for chunk-by-chunk delivery
- **Message deduplication**: Provide `user_id` to avoid echo in WebSocket

**Response:**
```json
{
  "response": "omg senpai BTC to 100k?! moon mission confirmed...",
  "chatHistory": "[{\"role\": \"user\", \"content\": \"...\"}, ...]",
  "message_id": null,
  "profileUpdates": [],
  "sessionId": "cc3fbed7-c404-4f6d-a0eb-89d0bf4d328a",
  "context": {
    "message_count": 15
  }
}
```

### Get Chat History
```bash
GET /api/profiles/{account_id}/chat/history?limit=50&after_id={message_id}
```

**Query Parameters:**
- `limit`: Maximum messages to return (1-200, default: 50)
- `after_id`: Return messages after this ID (for pagination)

**Response:**
```json
{
  "messages": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "role": "user",
      "content": "What's your take on the market?",
      "author": "user-123",
      "timestamp": "2025-01-03T10:30:00Z",
      "metadata": {}
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "role": "assistant",
      "content": "The market looks bullish to me...",
      "author": "ai",
      "timestamp": "2025-01-03T10:30:15Z",
      "metadata": {"model": "x-ai/grok-beta", "temperature": 0.7}
    }
  ],
  "total": 150,
  "has_more": true
}
```

### Clear Chat History
```bash
DELETE /api/profiles/{account_id}/chat/history
```

**Response:**
```json
{
  "message": "Chat history cleared for profile {account_id}"
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
POST /api/admin/profiles  (Currently Disabled - Returns 501)
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

### Get Profile Details (Admin)
```bash
GET /api/admin/profiles/{profile_id}
Headers: X-API-Key: {your_api_key}
```

**Response:**
```json
{
  "profile_id": "f1a96dac-89fd-4eeb-9dc6-5612085425d0",
  "address": "0xdE3244FCBf035A374c556d3E1c1774ebA74436fD",
  "signer_address": "0x6A37D8A9213489a273bf037C20090d7804388FD8",
  "persona": {
    "name": "Test Trader",
    "handle": "test_trader",
    "bio": "A test trading profile",
    "trading_style": "momentum",
    "risk_tolerance": 0.5,
    "favorite_assets": ["BTC", "ETH"],
    "personality_traits": ["analytical", "balanced"]
  },
  "is_active": true,
  "is_registered": true,
  "has_deposited": true,
  "deposit_amount": 100.0,
  "initial_equity": 100.0,
  "current_equity": 105.32,
  "created_at": "2025-01-03T10:30:00Z",
  "registered_at": "2025-01-03T10:30:15Z",
  "deposited_at": "2025-01-03T10:30:30Z"
}
```

### Update Profile
```bash
PUT /api/admin/profiles/{profile_id}
Headers: X-API-Key: {your_api_key}
```

**Request Body:**
```json
{
  "persona_update": {
    "bio": "Updated bio - now more aggressive",
    "trading_style": "aggressive",
    "risk_tolerance": 0.8,
    "favorite_assets": ["BTC", "ETH", "SOL", "LINK"],
    "personality_traits": ["bold", "risk-taker", "opportunistic"]
  },
  "is_active": true,
  "deposit_amount": 200.0
}
```

**Editable Fields:**
- **Persona fields:** `name`, `bio`, `trading_style`, `risk_tolerance`, `favorite_assets`, `personality_traits`
- **Account fields:** `is_active`, `deposit_amount` (tracking only)

**Non-editable fields** (for security):
- Address, private keys, signer key
- Profile ID
- Registration status

**Response:**
```json
{
  "message": "Profile f1a96dac-89fd-4eeb-9dc6-5612085425d0 updated successfully",
  "profile_id": "f1a96dac-89fd-4eeb-9dc6-5612085425d0",
  "updated_fields": ["persona_update", "is_active", "deposit_amount"]
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

## WebSocket Endpoint

### Connect to WebSocket
```
ws://localhost:8000/ws?profile_id={profile_id}&user_id={user_id}&subscribe_global={bool}
```

**Query Parameters:**
- `profile_id`: Subscribe to events for a specific profile (optional)
- `user_id`: User identifier for message deduplication (optional)
- `subscribe_global`: Subscribe to all events (default: false)
- `last_event_id`: Resume from specific event ID (optional)

**Connection Example:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws?profile_id=abc-123&user_id=user-456');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type, data.payload);
};
```

**Event Types:**
- `market.update` - Market price updates
- `trade.decision` - AI trading decisions
- `trade.order_*` - Order lifecycle events
- `account.update` - Account equity changes
- `chat.user_message` - New user messages
- `chat.assistant_start` - AI starts responding
- `chat.assistant_chunk` - Streaming AI response chunk
- `chat.assistant_final` - Complete AI message
- `profile.updated` - Profile configuration changes
- `bot.connected` - WebSocket connection confirmed
- `bot.disconnected` - Connection closed

**Example Events:**
```json
// Connection confirmed
{
  "type": "bot.connected",
  "payload": {
    "connection_id": "123e4567-e89b-12d3-a456-426614174000",
    "profile_id": "abc-123",
    "user_id": "user-456",
    "subscribed": true
  }
}

// Chat streaming chunk
{
  "type": "chat.assistant_chunk",
  "profile_id": "abc-123",
  "payload": {
    "content": "I think BTC is",
    "chunk_index": 0
  },
  "metadata": {
    "message_id": "msg-789",
    "chunk_index": 0,
    "correlation_id": "corr-123"
  }
}

// Profile update
{
  "type": "profile.updated",
  "profile_id": "abc-123",
  "payload": {
    "profile_id": "abc-123",
    "updated_fields": ["bio", "trading_style", "risk_tolerance"],
    "is_active": true
  }
}
```

### WebSocket Status
```bash
GET /ws/status
```

**Response:**
```json
{
  "active_connections": 5,
  "subscribers": {
    "global": 1,
    "profile_specific": 4
  },
  "event_bus": "active",
  "timestamp": "2025-01-03T10:30:00Z"
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

## Recent Updates

### Phase A-C Enhancements (January 2025)

1. **WebSocket Support** (`/ws`):
   - Real-time event streaming for all system activities
   - Profile-specific and global subscriptions
   - Message deduplication with user_id
   - Reconnection support with last_event_id
   - Event types for market, trading, chat, and profile updates

2. **Enhanced Chat System**:
   - **Server-side chat history**: All conversations now persisted in JSONL format
   - **Streaming responses**: Set `stream: true` for chunk-by-chunk AI responses
   - **Chat history endpoint**: `GET /api/profiles/{id}/chat/history` with pagination
   - **Clear history**: `DELETE /api/profiles/{id}/chat/history`
   - **Message deduplication**: Provide user_id to prevent echo

3. **Profile Management Enhancements**:
   - **Update profiles**: `PUT /api/admin/profiles/{id}` for editing personas
   - **Detailed admin view**: `GET /api/admin/profiles/{id}` with all fields
   - **Initial equity tracking**: Profiles now track starting equity for P&L
   - **Validation**: Asset symbols, risk tolerance, and field constraints
   - **Event publishing**: Profile updates trigger WebSocket events

4. **Profile Factory**:
   - Centralized profile creation with error handling
   - Automated RISE registration and USDC deposits
   - Retry logic for failed deposits
   - Initial equity fetching for P&L baseline

### Original Updates (January 3, 2026)

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