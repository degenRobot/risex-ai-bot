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

# Deploy
echo "Deploying application..."
fly deploy

echo ""
echo "Deployment complete!"
echo "===================="
echo "View logs: fly logs --app risex-trading-bot"
echo "Open app: fly open --app risex-trading-bot"
echo "SSH console: fly ssh console --app risex-trading-bot"