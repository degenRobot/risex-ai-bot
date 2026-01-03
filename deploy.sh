#!/bin/bash
# Deploy script for Fly.io

set -e

echo "Deploying RISE AI Trading Bot to Fly.io"
echo "========================================"

# Check if fly CLI is installed
if ! command -v fly &> /dev/null; then
    echo "Error: fly CLI not found. Please install from https://fly.io/docs/flyctl/install/"
    exit 1
fi

# Check if app exists
if fly apps list | grep -q "risex-trading-bot"; then
    echo "App already exists"
else
    echo "Creating new app..."
    fly apps create risex-trading-bot --org personal
fi

# Create volume if it doesn't exist
if fly volumes list --app risex-trading-bot | grep -q "trading_data"; then
    echo "Volume already exists"
else
    echo "Creating persistent volume..."
    fly volumes create trading_data --app risex-trading-bot --size 1 --region sjc
fi

# Set secrets if provided
if [ ! -z "$OPENROUTER_API_KEY" ]; then
    echo "Setting OPENROUTER_API_KEY..."
    fly secrets set OPENROUTER_API_KEY="$OPENROUTER_API_KEY" --app risex-trading-bot
fi

# Set backend RPC URL if provided
if [ ! -z "$BACKEND_RPC_URL" ]; then
    echo "Setting BACKEND_RPC_URL..."
    fly secrets set BACKEND_RPC_URL="$BACKEND_RPC_URL" --app risex-trading-bot
fi

# Set admin API key if provided
if [ ! -z "$ADMIN_API_KEY" ]; then
    echo "Setting ADMIN_API_KEY..."
    fly secrets set ADMIN_API_KEY="$ADMIN_API_KEY" --app risex-trading-bot
fi

# Set account keys if provided (for account creation)
if [ ! -z "$PRIVATE_KEY" ]; then
    echo "Setting account keys..."
    fly secrets set PRIVATE_KEY="$PRIVATE_KEY" SIGNER_PRIVATE_KEY="$SIGNER_PRIVATE_KEY" --app risex-trading-bot
fi

# Set other environment variables via secrets (for security)
echo "Setting environment variables..."
fly secrets set \
    RISE_API_BASE="https://api.testnet.rise.trade" \
    RISE_CHAIN_ID="11155931" \
    TRADING_MODE="live" \
    PYTHONPATH="/app" \
    DATA_DIR="/data" \
    --app risex-trading-bot

# Deploy
echo "Deploying application..."
fly deploy

echo ""
echo "Deployment complete!"
echo "===================="
echo "View logs: fly logs --app risex-trading-bot"
echo "Open app: fly open --app risex-trading-bot"
echo "SSH console: fly ssh console --app risex-trading-bot"