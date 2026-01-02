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

### List Profiles
```bash
GET /api/profiles
```

**Response:**
```json
[
  {
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
- `handle`: Profile handle (e.g., "crypto_degen")

**Response:**
```json
{
  "handle": "crypto_degen",
  "name": "The Crypto Degen",
  "bio": "Aggressive day trader with a YOLO mentality",
  "trading_style": "aggressive",
  "risk_tolerance": 0.8,
  "personality_traits": ["impulsive", "overconfident"],
  "is_trading": false,
  "account_address": "0x11cDE69d5c4b5eeDb73AdaB19Afdf653060773bA",
  "positions": {},
  "pending_actions": [],
  "recent_trades": [],
  "total_pnl": 0,
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
  "profile_id": "7f673612-83ad-4e34-a323-1d77126440a8",
  "profile_name": "The Crypto Degen",
  "trading_context": {
    "current_pnl": 0,
    "open_positions": 0,
    "available_balance": 0,
    "positions": [],
    "recent_trades": []
  },
  "timestamp": "2026-01-02T07:52:00"
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

## Notes

1. **Account ID vs Handle**: Most endpoints use account UUID, profile detail endpoint uses handle
2. **Chat History**: Maintained per session, use same sessionId to continue conversation
3. **Profile Updates**: Chat can influence trader's market outlook and bias
4. **RISE Integration**: Balance/position endpoints may return 404 if account not whitelisted
5. **Order Placement**: Requires account to have USDC balance and be whitelisted on RISE