# Test Suite Documentation

## Core Tests to Keep

### Working Tests (Verified)
- `test_tif_variations.py` - ✅ Successfully placed order with TIF=3
- `test_deposit.py` - Tests USDC deposit functionality
- `test_ai_trading.py` - AI trading decision logic
- `test_full_flow.py` - Complete profile generation flow

### Component Tests
- `test_ai_persona.py` - AI persona generation
- `test_mock_profiles.py` - Mock social media profiles
- `test_api_endpoints.py` - FastAPI endpoints

### System Tests
- `test_automated_trading.py` - Full automated trading system
- `test_enhanced_architecture.py` - Enhanced parallel architecture
- `test_rise_integration.py` - Basic RISE API connectivity

## Tests to Remove (Redundant/Outdated)
- Various order placement attempts that were superseded by test_tif_variations.py
- Debug tests that served their purpose
- Duplicate flow tests