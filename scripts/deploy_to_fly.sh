#!/bin/bash
set -euo pipefail

echo "🚀 RISE AI Trading Bot - Fly.io Deployment"
echo "=========================================="

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if fly CLI is installed
if ! command -v flyctl &> /dev/null; then
    echo -e "${RED}❌ Fly CLI not found. Install it from https://fly.io/docs/flyctl/install/${NC}"
    exit 1
fi

# Check if logged in to Fly
if ! flyctl auth whoami &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Fly. Running 'flyctl auth login'...${NC}"
    flyctl auth login
fi

# Load environment variables
if [ -f .env ]; then
    echo -e "${GREEN}✅ Loading .env file${NC}"
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${RED}❌ .env file not found. Copy .env.example to .env and configure it.${NC}"
    exit 1
fi

# Required environment variables
REQUIRED_VARS=(
    "OPENROUTER_API_KEY"
    "BACKEND_RPC_URL"
)

# Optional but recommended
OPTIONAL_VARS=(
    "ADMIN_API_KEY"
    "PRIVATE_KEY"
    "SIGNER_PRIVATE_KEY"
)

echo -e "\n${YELLOW}Checking required environment variables...${NC}"

# Check required variables
missing_vars=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        missing_vars+=($var)
        echo -e "${RED}❌ Missing required: $var${NC}"
    else
        echo -e "${GREEN}✅ Found: $var${NC}"
    fi
done

# Check optional variables
echo -e "\n${YELLOW}Checking optional environment variables...${NC}"
for var in "${OPTIONAL_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo -e "${YELLOW}⚠️  Missing optional: $var${NC}"
    else
        echo -e "${GREEN}✅ Found: $var${NC}"
    fi
done

# Exit if missing required vars
if [ ${#missing_vars[@]} -ne 0 ]; then
    echo -e "\n${RED}❌ Missing required environment variables. Please set them in .env${NC}"
    exit 1
fi

# Ask for app name
echo -e "\n${YELLOW}Fly app configuration:${NC}"
FLY_APP_NAME="risex-trading-bot"
read -p "App name (default: $FLY_APP_NAME): " input_app_name
if [ ! -z "$input_app_name" ]; then
    FLY_APP_NAME=$input_app_name
fi

# Check if app exists
if flyctl apps list | grep -q "$FLY_APP_NAME"; then
    echo -e "${GREEN}✅ App '$FLY_APP_NAME' exists${NC}"
else
    echo -e "${YELLOW}⚠️  App '$FLY_APP_NAME' not found. Creating...${NC}"
    flyctl apps create $FLY_APP_NAME
fi

# Set secrets
echo -e "\n${YELLOW}Setting Fly secrets...${NC}"

# Required secrets
flyctl secrets set OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
    BACKEND_RPC_URL="$BACKEND_RPC_URL" \
    --app $FLY_APP_NAME

# Optional secrets if present
if [ ! -z "${ADMIN_API_KEY:-}" ]; then
    flyctl secrets set ADMIN_API_KEY="$ADMIN_API_KEY" --app $FLY_APP_NAME
fi

if [ ! -z "${PRIVATE_KEY:-}" ] && [ ! -z "${SIGNER_PRIVATE_KEY:-}" ]; then
    flyctl secrets set PRIVATE_KEY="$PRIVATE_KEY" \
        SIGNER_PRIVATE_KEY="$SIGNER_PRIVATE_KEY" \
        --app $FLY_APP_NAME
fi

# Create or verify volume for persistent data
echo -e "\n${YELLOW}Checking persistent volume...${NC}"
if ! flyctl volumes list --app $FLY_APP_NAME | grep -q "trading_data"; then
    echo -e "${YELLOW}Creating volume for persistent data...${NC}"
    flyctl volumes create trading_data --region sjc --size 1 --app $FLY_APP_NAME
else
    echo -e "${GREEN}✅ Volume 'trading_data' exists${NC}"
fi

# Deploy
echo -e "\n${YELLOW}Deploying to Fly...${NC}"
echo "This will build and deploy the Docker image..."

flyctl deploy --app $FLY_APP_NAME

echo -e "\n${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Check app status: flyctl status --app $FLY_APP_NAME"
echo "2. View logs: flyctl logs --app $FLY_APP_NAME"
echo "3. Open app: flyctl open --app $FLY_APP_NAME"
echo "4. Create AI traders: flyctl ssh console --app $FLY_APP_NAME -C 'python scripts/create_fresh_profile.py'"
echo ""
echo "API endpoints:"
echo "- Health: https://$FLY_APP_NAME.fly.dev/health"
echo "- Docs: https://$FLY_APP_NAME.fly.dev/docs"
echo "- Profiles: https://$FLY_APP_NAME.fly.dev/api/profiles"