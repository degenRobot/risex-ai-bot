#!/bin/bash
# Test Docker build and run locally

set -e

echo "Testing Docker build for RISE AI Trading Bot"
echo "==========================================="

# Build the Docker image
echo "Building Docker image..."
docker build -t risex-trading-bot .

# Create local data directory for testing
mkdir -p ./test_data

# Run the container
echo ""
echo "Running Docker container..."
echo "API will be available at http://localhost:8080"
echo "Press Ctrl+C to stop"
echo ""

docker run --rm -it \
  -p 8080:8080 \
  -v $(pwd)/test_data:/data \
  -e OPENROUTER_API_KEY="${OPENROUTER_API_KEY}" \
  -e TRADING_MODE="dry" \
  -e TRADING_INTERVAL="60" \
  risex-trading-bot