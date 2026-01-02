# Trading Tests

This directory contains comprehensive tests for the RISE AI Trading Bot's trading functionality.

## Test Files

### Core Trading Flow

1. **`test_full_trading_flow.py`** ⭐
   - Complete end-to-end test from account creation to P&L tracking
   - Steps:
     1. Create new account with keys
     2. Register signer on RISE
     3. Deposit USDC (testnet faucet)
     4. Place market orders
     5. Check positions
     6. Update local P&L tracking
   - **Run**: `python test_full_trading_flow.py`

### Signer Management

2. **`test_reregister_signer.py`**
   - Test re-registering signers (key rotation)
   - Handles expired or compromised signer keys
   - Includes bulk re-registration for multiple accounts
   - **Run**: `python test_reregister_signer.py`

### P&L Tracking

3. **`test_trading_view_pnl.py`**
   - Update P&L using TradingView-style data
   - Real-time position and P&L updates
   - Supports continuous monitoring mode
   - **Run**: `python test_trading_view_pnl.py`

### Legacy Tests

4. **`test_market_order_fixed.py`**
   - Basic market order placement test
   - Useful for quick order testing

5. **`test_rise_working_features.py`**
   - Tests various RISE API features
   - Balance checks, position queries, etc.

6. **`test_complete_trading_flow.py`**
   - Earlier version of trading flow test

## Running Tests

### Prerequisites
```bash
# Ensure you have environment variables set
export RISE_API_BASE="https://api.testnet.rise.trade"
export PYTHONPATH="/path/to/risex-ai-bot"
```

### Individual Tests
```bash
# Test full trading flow
python test_full_trading_flow.py

# Test P&L updates
python test_trading_view_pnl.py

# Test signer rotation
python test_reregister_signer.py
```

### Test Results
All tests save detailed results in JSON format:
- `full_flow_results.json` - Complete trading flow results
- `trading_view_pnl_results.json` - P&L update results

## Key Features Tested

✅ **Account Management**
- Account creation with separate main/signer keys
- Registration status tracking
- Deposit status tracking

✅ **Order Lifecycle**
- Market order placement
- Order status tracking
- Trade record management

✅ **Position Tracking**
- Real-time position queries
- Position snapshot storage
- P&L calculation

✅ **Signer Security**
- Signer registration
- Key rotation/re-registration
- Bulk key management

## Important Notes

1. **Testnet Only**: All tests use RISE testnet
2. **Account Whitelisting**: New accounts may need whitelisting for certain operations
3. **USDC Faucet**: Deposit tests use testnet faucet (may have daily limits)
4. **Gas Fees**: No ETH needed - uses gasless architecture

## Troubleshooting

### Common Issues

1. **"Account not whitelisted"**
   - New accounts need RISE testnet whitelisting
   - Use existing test accounts or contact RISE team

2. **"Signer already registered"**
   - Account/signer pair already registered
   - Use re-registration test for key rotation

3. **"Insufficient balance"**
   - Deposit USDC using deposit test
   - Check testnet faucet limits

### Debug Mode
Run tests with debug output:
```bash
LOG_LEVEL=DEBUG python test_full_trading_flow.py
```

## Next Steps

1. **Automated Testing**: Integrate with CI/CD
2. **Performance Testing**: Load test with multiple accounts
3. **Error Recovery**: Test failure scenarios and recovery
4. **Market Conditions**: Test under various market conditions