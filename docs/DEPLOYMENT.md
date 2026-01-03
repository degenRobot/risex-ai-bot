# 🚀 RISE AI Trading Bot - Deployment Guide

This guide covers deploying the RISE AI Trading Bot to Fly.io for production use.

## 📋 Prerequisites

### 1. Install Fly CLI
```bash
# macOS
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh

# Windows
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

### 2. Create Fly Account
```bash
flyctl auth signup
# or login if you have an account
flyctl auth login
```

### 3. Required Environment Variables

Create a `.env` file with these required variables:

```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-your-key-here        # For AI features
BACKEND_RPC_URL=https://indexing.testnet.riselabs.xyz  # RISE RPC endpoint

# Optional but recommended
ADMIN_API_KEY=your-secure-admin-key-here         # For admin endpoints
```

## 🎯 Quick Deploy

```bash
# 1. Clone the repository
git clone <repository>
cd risex-ai-bot

# 2. Copy and configure environment
cp .env.example .env
# Edit .env with your values

# 3. Run deployment script
./scripts/deploy_to_fly.sh
```

The script will:
- ✅ Check for required environment variables
- ✅ Create or use existing Fly app
- ✅ Set secrets securely
- ✅ Create persistent volume for data
- ✅ Deploy the application

## 🔧 Manual Deployment

If you prefer manual steps:

### 1. Create Fly App
```bash
flyctl apps create risex-trading-bot
```

### 2. Set Secrets
```bash
# Required secrets
flyctl secrets set \
  OPENROUTER_API_KEY="your-key" \
  BACKEND_RPC_URL="https://testnet.riselabs.xyz" \
  --app risex-trading-bot

# Optional secrets
flyctl secrets set ADMIN_API_KEY="admin-key" --app risex-trading-bot
```

### 3. Create Volume
```bash
flyctl volumes create trading_data --region sjc --size 1 --app risex-trading-bot
```

### 4. Deploy
```bash
flyctl deploy --app risex-trading-bot
```

## 🧑‍💻 Post-Deployment

### Check Status
```bash
flyctl status --app risex-trading-bot
```

### View Logs
```bash
flyctl logs --app risex-trading-bot
```

### Access Application
```bash
# Open in browser
flyctl open --app risex-trading-bot

# API endpoints
curl https://risex-trading-bot.fly.dev/health
curl https://risex-trading-bot.fly.dev/api/profiles
```

### Create AI Traders
```bash
# SSH into container
flyctl ssh console --app risex-trading-bot

# Create a new profile
python scripts/create_fresh_profile.py
```

## 🔐 Security Considerations

### Secrets Management
- Never commit `.env` files
- Use `flyctl secrets` for sensitive data
- Rotate API keys regularly

### Access Control
- Set `ADMIN_API_KEY` for protected endpoints
- Use HTTPS for all API calls
- Monitor access logs

### Account Security
- Generate fresh keys for each deployment
- Keep main account and signer keys separate
- Store keys securely

## 🚦 Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key for AI | `sk-or-v1-...` |
| `BACKEND_RPC_URL` | RISE backend RPC endpoint | `https://testnet.riselabs.xyz` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ADMIN_API_KEY` | Admin API authentication | None |
| `PRIVATE_KEY` | Main account private key | None |
| `SIGNER_PRIVATE_KEY` | Signer account private key | None |
| `TRADING_MODE` | Trading mode (dry/live) | `dry` |
| `TRADING_INTERVAL` | Seconds between trades | `60` |
| `RISE_API_BASE` | RISE API base URL | `https://api.testnet.rise.trade` |
| `RISE_CHAIN_ID` | Blockchain chain ID | `11155931` |

## 📊 Monitoring

### Health Checks
The app includes automatic health checks at `/health`:
```bash
curl https://risex-trading-bot.fly.dev/health
```

### Metrics
```bash
flyctl metrics --app risex-trading-bot
```

### SSH Access
```bash
flyctl ssh console --app risex-trading-bot
```

## 🔄 Updates and Scaling

### Deploy Updates
```bash
flyctl deploy --app risex-trading-bot
```

### Scale Instances
```bash
# Scale to 2 instances
flyctl scale count 2 --app risex-trading-bot

# Scale memory
flyctl scale memory 1024 --app risex-trading-bot
```

### Update Secrets
```bash
flyctl secrets set OPENROUTER_API_KEY="new-key" --app risex-trading-bot
```

## 🚨 Troubleshooting

### Common Issues

**1. Deployment Fails**
- Check Docker build locally: `docker build .`
- Verify all files are present
- Check Fly logs: `flyctl logs`

**2. App Crashes**
- Check environment variables are set
- Verify volume is mounted
- Check logs for errors

**3. Can't Create Profiles**
- Ensure OPENROUTER_API_KEY is valid
- Check BACKEND_RPC_URL is accessible
- Verify account has permissions

### Debug Commands
```bash
# Check app status
flyctl status --app risex-trading-bot

# View recent logs
flyctl logs --tail 100 --app risex-trading-bot

# SSH into container
flyctl ssh console --app risex-trading-bot

# Check secrets (names only)
flyctl secrets list --app risex-trading-bot
```

## 🎯 Production Checklist

Before going live:

- [ ] Set strong `ADMIN_API_KEY`
- [ ] Configure proper `TRADING_MODE`
- [ ] Test account creation flow
- [ ] Verify chat functionality
- [ ] Check equity monitoring
- [ ] Test trading execution
- [ ] Set up monitoring alerts
- [ ] Document API endpoints
- [ ] Create backup strategy
- [ ] Plan for key rotation

## 📚 Additional Resources

- [Fly.io Documentation](https://fly.io/docs/)
- [RISE API Documentation](https://developer.rise.trade/)
- [OpenRouter Documentation](https://openrouter.ai/docs)
- [Project README](../README.md)