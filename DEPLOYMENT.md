# Deployment Guide

## Prerequisites

1. Install Fly CLI:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. Authenticate with Fly:
   ```bash
   fly auth login
   ```

3. Set your OpenRouter API key:
   ```bash
   export OPENROUTER_API_KEY="sk-or-v1-your-key-here"
   ```

## Deploy to Fly.io

```bash
# Run the deployment script
./scripts/deploy.sh
```

The script will:
- Create the app if it doesn't exist
- Create a persistent volume for data
- Set environment variables and secrets
- Deploy the application

## Testing the Deployment

### 1. Check Health

```bash
curl https://risex-trading-bot.fly.dev/health
```

Expected response:
```json
{
  "status": "healthy",
  "accounts": 15,
  "version": "0.1.0"
}
```

### 2. List Trading Profiles

```bash
curl https://risex-trading-bot.fly.dev/api/profiles
```

Returns array of trading profiles with their current status.

### 3. Chat with AI Trader

First, get an account ID from the profiles endpoint, then:

```bash
# Create a test message
echo '{
  "message": "Fed just cut rates by 50 basis points. What is your outlook on Bitcoin?",
  "chatHistory": ""
}' > chat_request.json

# Send chat request
curl -X POST https://risex-trading-bot.fly.dev/api/profiles/{ACCOUNT_ID}/chat \
  -H "Content-Type: application/json" \
  -d @chat_request.json
```

Example response:
```json
{
  "response": "Fed cuts are just more money printing...",
  "chatHistory": "[...]",
  "profileUpdates": ["Updated BTC outlook to Bearish: ..."],
  "sessionId": "abc123",
  "context": {
    "currentPnL": 0,
    "openPositions": 0
  }
}
```

### 4. Monitor Trading Activity

```bash
# View real-time logs
fly logs --app risex-trading-bot

# Check positions for an account
curl https://risex-trading-bot.fly.dev/api/accounts/{ADDRESS}/positions
```

## Configuration

### Environment Variables

Set via `fly secrets`:
- `OPENROUTER_API_KEY`: Required for AI chat functionality
- `RISE_API_BASE`: RISE API endpoint (default: testnet)
- `TRADING_MODE`: "dry" (simulation) or "live" (real trading)
- `TRADING_INTERVAL`: Seconds between trading cycles (default: 60)

### Persistent Storage

Data is stored in `/data` volume:
- `accounts.json`: Trading accounts and personas
- `trading_decisions.json`: Decision history
- `chat_sessions.json`: Chat conversations
- `thought_processes.json`: AI reasoning logs

## Operations

### View Logs
```bash
fly logs --app risex-trading-bot --tail
```

### SSH Access
```bash
fly ssh console --app risex-trading-bot
```

### Restart App
```bash
fly apps restart risex-trading-bot
```

### Scale Resources
```bash
# Increase memory
fly scale memory 1024 --app risex-trading-bot

# Add more instances
fly scale count 2 --app risex-trading-bot
```

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Verify secret is set: `fly secrets list --app risex-trading-bot`
   - Re-set if needed: `fly secrets set OPENROUTER_API_KEY=$OPENROUTER_API_KEY --app risex-trading-bot`

2. **Chat Not Responding**
   - Check logs for OpenRouter errors
   - Verify API key has credits
   - Ensure model supports tool calling

3. **Trading Not Executing**
   - Check TRADING_MODE (default is "dry" for safety)
   - Verify account has USDC balance
   - Check logs for specific errors

### Debug Commands

```bash
# Check app status
fly status --app risex-trading-bot

# Monitor metrics
fly monitor --app risex-trading-bot

# View configuration
fly config show --app risex-trading-bot
```