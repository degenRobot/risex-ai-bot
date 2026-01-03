# API Tests

This directory contains comprehensive tests for the RISE AI Trading Bot API deployed on Fly.io.

## Test Files

### 1. `test_fly_api.py`
Comprehensive test suite covering all API endpoints:
- Health check
- Profile listing and details
- Chat functionality
- Profile summaries and context
- Admin endpoints (with authentication)
- Error handling

**Run:** `python test_fly_api.py`

### 2. `test_profile_creation.py`
Tests profile creation and management:
- Creating profiles with different personalities
- Testing initial chat responses
- Verifying profile operations (balance, positions)

**Run:** `python test_profile_creation.py`

### 3. `test_chat_influence.py`
Tests how chat messages influence trader behavior:
- Bullish sentiment influence
- Bearish FUD impact
- Mixed signal handling
- Personality-specific responses

**Run:** `python test_chat_influence.py`

## Setup

1. Make sure you have the admin API key in your `.env` file:
   ```
   ADMIN_API_KEY=ska_...
   ```

2. Install dependencies:
   ```bash
   pip install httpx python-dotenv
   ```

3. Run tests:
   ```bash
   python test_fly_api.py
   ```

## API Key Generation

If you don't have an admin API key:

```bash
curl -X POST https://risex-trading-bot.fly.dev/api/admin/api-keys/generate \
  -H "X-Master-Key: master-secret-key"
```

Save the returned API key to your `.env` file.

## Test Results

Test results are saved as JSON files:
- `test_results.json` - Main API test results
- `chat_influence_results.json` - Chat influence test results

## Expected Outcomes

### Successful Tests
- ✅ Health check returns "healthy"
- ✅ Profile list contains 15+ profiles  
- ✅ Chat responds with personality-appropriate messages
- ✅ Profile updates reflect chat influence
- ✅ Admin endpoints work with valid API key

### Known Issues
- ⚠️ Balance/position endpoints may return 404 if accounts not whitelisted
- ⚠️ Order placement requires whitelisted account with USDC balance