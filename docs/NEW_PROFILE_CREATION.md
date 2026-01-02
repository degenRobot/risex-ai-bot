# New Profile Creation Guide

## Overview

Creating a new AI trading profile involves generating cryptographic keys, registering for gasless trading, depositing funds, and integrating with our chat/trading systems.

## Complete Flow

### 1. Key Generation
```python
from web3 import Web3
w3 = Web3()

# Generate main account key (holds funds)
main_account = w3.eth.account.create()
main_address = main_account.address
main_private_key = main_account.key.hex()

# Generate separate signer key (for gasless trades) 
signer_account = w3.eth.account.create()
signer_address = signer_account.address
signer_private_key = signer_account.key.hex()

# CRITICAL: Keys must be different for security
assert main_address != signer_address
```

### 2. Signer Registration

**API Endpoint**: `POST /v1/auth/register-signer`  
**Purpose**: Enable gasless trading by registering the signer key with RISE

```python
registration_result = await rise_client.register_signer(
    account_key=main_private_key,
    signer_key=signer_private_key
)

# Expected response:
{
  "data": {
    "transaction_hash": "0x6ec6c13716f9d80a7c21bec8b2fdb5ea2a5d6edd9c9eae01acec65c00dc42283",
    "success": True,
    "status": 1,
    "block_number": "32259643"
  }
}
```

**What happens**:
- Main account signs a `RegisterSigner` message
- Signer account signs a `VerifySigner` message  
- RISE API validates both signatures
- Transaction is submitted to register the signer on-chain

### 3. USDC Deposit 

**API Endpoint**: `POST /v1/account/deposit-usdc`  
**Purpose**: Mint testnet USDC and deposit to trading account

```python
deposit_result = await rise_client.deposit_usdc(
    account_key=main_private_key,
    amount=100.0  # Amount in USDC
)

# Expected response:
{
  "data": {
    "transaction_hash": "0xbd91ab62598872628b29d6a9b4af545435bf17452cb494001a73135733ee197b",
    "block_number": "32259643", 
    "success": True
  }
}
```

**What happens**:
- Main account signs a `Deposit` message
- RISE backend mints testnet USDC to the account
- Funds are deposited into the trading balance
- Transaction is submitted on-chain

### 4. Verification

After registration and deposit, verify the account status:

```python
# Check on-chain equity
equity = await equity_monitor.fetch_equity(main_address)
# Should show deposited amount (e.g., $100.00)

# Check trading balance  
balance = await rise_client.get_balance(main_address)
# Should show available margin balance

# Check account info
account_info = await rise_client.get_account(main_address) 
# Should show registered status
```

## Integration with AI System

### 5. Profile Creation

```python
from app.models import Account, Persona
from app.trader_profiles import create_trader_profile

# Create trader profile with personality
trader_profile = create_trader_profile("cynical")  # or "leftCurve", "midwit"

# Create Account model
account = Account(
    id=f"profile_{timestamp}",
    address=main_address,
    private_key=main_private_key,
    signer_key=signer_private_key,
    persona=Persona(
        name=trader_profile.base_persona.name,
        handle=f"{trader_profile.base_persona.handle}_{timestamp}",
        bio=trader_profile.base_persona.core_personality,
        trading_style="conservative",  # Map from risk_profile
        risk_tolerance=0.5,
        favorite_assets=["BTC", "ETH"],
        personality_traits=trader_profile.base_persona.base_traits,
        sample_posts=["Ready to trade!"]
    ),
    is_active=True,
    is_registered=True,
    registered_at=datetime.now(),
    has_deposited=True, 
    deposited_at=datetime.now(),
    deposit_amount=100.0
)

# Save to storage
storage.save_account(account)
```

### 6. Enable Services

The profile is now ready for:

- **🤖 AI Chat**: Users can chat with the personality 
- **📈 Trading**: AI makes autonomous trading decisions
- **💰 Equity Tracking**: Real-time on-chain balance monitoring
- **📊 Analytics**: P&L tracking and performance metrics

## Key Security Requirements

### Address Separation
- **Main Address**: Holds funds, signs deposits, owns account
- **Signer Address**: Signs trading orders, must be different from main

### EIP-712 Signatures
All operations use typed signatures:
- `RegisterSigner`: Links signer to main account
- `VerifySigner`: Proves signer key ownership  
- `Deposit`: Authorizes USDC minting/deposit
- `PlaceOrder`: Gasless trading orders

### Testnet Environment
- Uses RISE Sepolia testnet
- USDC is minted, not real
- Trades are gasless (no ETH fees)
- Accounts must be whitelisted for full functionality

## Common Issues & Solutions

### ❌ Registration Fails
```
Error: "Signer already registered" 
```
**Solution**: Each signer can only be used once. Generate new keys.

### ❌ Deposit Fails  
```
Error: "insufficient funds" or "missing nonce"
```
**Solution**: 
- Account may not be whitelisted
- Try smaller amounts (start with $1)
- Ensure main account has some ETH for gas

### ❌ Zero Equity
If on-chain equity shows $0 after deposit:
- Wait for block confirmations
- Check transaction was successful
- Verify correct contract address

### ❌ Trading Disabled
```
Error: "Account not registered"
```
**Solution**: Ensure both registration and deposit completed successfully.

## Testing Checklist

For new profiles, verify:

- [ ] ✅ **Keys Generated**: Two different addresses created
- [ ] ✅ **Signer Registered**: Transaction hash received
- [ ] ✅ **Funds Deposited**: Transaction hash received  
- [ ] ✅ **Equity Visible**: On-chain balance shows deposit amount
- [ ] ✅ **Profile Saved**: Account exists in `data/accounts.json`
- [ ] ✅ **Chat Works**: AI responds with context
- [ ] ✅ **Trading Active**: Profile participates in trading cycles

## API References

- **Signer Registration**: [RISE Docs](https://docs.risechain.com/docs/risex/api/register-signer)
- **Deposit USDC**: [API Reference](https://developer.rise.trade/reference/accountservice_depositusdc)
- **Account Management**: [API Docs](https://developer.rise.trade/reference/accountservice_getaccount)

## File Locations

- **Models**: `app/models.py` - Account, Persona definitions
- **Profiles**: `app/trader_profiles.py` - Base personalities  
- **Client**: `app/services/rise_client.py` - API interactions
- **Storage**: `data/accounts.json` - Profile persistence
- **Tests**: `scripts/test_fresh_account_flow.py` - End-to-end testing