# Order Placement Guide for RISE Trading Bot

## Overview

This document details the correct order placement structure and parameters for the RISE perpetuals DEX API. After extensive testing and debugging, we've confirmed the exact requirements for successful order placement.

## ✅ Confirmed Working Parameters

### Successful Order Example
```json
{
  "order_id": "5965786",
  "size": "0.001 BTC",
  "market_id": 1,
  "order_type": 0,
  "tif": 3,
  "status": 1
}
```

## Critical Implementation Details

### 1. Order Type Mapping

**IMPORTANT**: The RISE API uses numeric values for order types:
- `0` = Limit Order
- `1` = Market Order (but this doesn't work on testnet)

For market-like execution, use:
```python
order_type = 0  # Always use limit order type
price = 0       # Price of 0 for market-like behavior
tif = 3         # IOC (Immediate or Cancel)
```

### 2. Order Size Requirements

Based on testing:
- ❌ 0.0001 BTC - Failed (too small or RPC issue)
- ✅ 0.001 BTC - Success
- ✅ Larger sizes work

**Recommendation**: Use minimum size of 0.001 BTC for reliable execution.

### 3. API Response Structure

Successful order placement returns:
```json
{
  "data": {
    "transaction_hash": "0x...",
    "order_id": "5965786",
    "block_number": "32195710",
    "receipt": {
      "status": 1,
      "block_number": "32195710",
      "gas_used": "401929"
    },
    "order": {
      "size": "1000000000000000",  // Wei format (18 decimals)
      "filled_size": "0",
      "user": "0x2dd7F99f27EeD2Bd89E08803d9b416059589A2Db",
      "side": 0,  // 0=buy, 1=sell
      "status": 1,  // Active
      "order_type": 0,  // Limit
      "tif": 3,  // IOC
      "post_only": false,
      "reduce_only": false
    }
  }
}
```

### 4. Time-in-Force (TIF) Values

```python
TIF_GTC = 0  # Good Till Cancelled
TIF_GTT = 1  # Good Till Time
TIF_FOK = 2  # Fill Or Kill
TIF_IOC = 3  # Immediate Or Cancel (use this for market orders)
```

### 5. EIP-712 Signing Structure

Orders require EIP-712 signatures with this structure:
```python
verify_sig_data = {
    "domain": {
        "name": "RISE",
        "version": "1",
        "chainId": 11155931,
        "verifyingContract": "0x..."
    },
    "message": {
        "account": account_address,
        "target": perps_manager_address,
        "hash": order_hash,  # Keccak256 of 47-byte encoded order
        "nonce": nonce,
        "deadline": deadline
    },
    "primaryType": "VerifySignature",
    "types": {
        "EIP712Domain": [...],
        "VerifySignature": [...]
    }
}
```

## Common Issues and Solutions

### 1. "Markets show available: false"
**Issue**: API returns markets with `available: false`  
**Solution**: This is a display bug. Orders still execute successfully.

### 2. "Account balance returns 404"
**Issue**: Balance check fails with "Not Found"  
**Solution**: Account not whitelisted for reads, but can still place orders.

### 3. "PlaceOrder reverted with status 0"
**Issue**: Order transaction reverts  
**Causes**:
- Using `order_type=1` (market) instead of `0` (limit)
- Order size too small
- Insufficient USDC balance
- Signer not registered

### 4. "Invalid domain key: domain"
**Issue**: EIP-712 signing fails  
**Solution**: Use `eth-account==0.10.0` with `encode_structured_data`

## Implementation Code

### Correct Market Order Placement
```python
async def place_market_order(self, ...):
    """Place a market-like order using limit order with price=0."""
    return await self.place_order(
        account_key=account_key,
        signer_key=signer_key,
        market_id=market_id,
        size=size,
        price=0,  # Critical: price=0 for market-like
        side=side,
        order_type="limit",  # Critical: always use limit
        tif=3,  # IOC for immediate execution
        reduce_only=reduce_only
    )
```

### Order Encoding (47-byte format)
```python
# Encode order for hashing
encoded_order = encode_packed(
    ["uint64", "uint128", "uint128", "uint8", "uint8", "uint8", "uint32"],
    [market_id, size_raw, price_raw, flags, order_type_int, tif, expiry]
)
# Must be exactly 47 bytes
assert len(encoded_order) == 47
order_hash = keccak(encoded_order)
```

### Decimal Conversion
```python
# RISE uses 18 decimals internally
size_raw = int(size * 1e18)  # Convert BTC amount to wei
price_raw = int(price * 1e18) if price > 0 else 0
```

## Dependencies

**Critical**: Must use specific versions for compatibility:
```toml
[tool.poetry.dependencies]
eth-account = "0.10.0"  # Required for encode_structured_data
eth-abi = "^5.0.0"
eth-utils = "^4.0.0"
```

## Testing Orders

### Minimal Test Script
```python
# Test with known working parameters
order = await client.place_order(
    account_key=account.private_key,
    signer_key=account.signer_key,
    market_id=1,  # BTC
    side="buy",
    size=0.001,  # Minimum working size
    price=0,
    order_type="limit",
    tif=3  # IOC
)
```

## Debugging Checklist

1. ✅ Using `order_type=0` (limit) not `1` (market)?
2. ✅ Order size >= 0.001 BTC?
3. ✅ Using `eth-account==0.10.0`?
4. ✅ Signer registered on-chain?
5. ✅ Account has USDC deposited?
6. ✅ Account and signer keys are different?

## References

- RISE Testnet: https://testnet.riselabs.xyz
- Chain ID: 11155931
- PerpsManager: 0x68cAcD54a8c93A3186BF50bE6b78B761F728E1b4
- Working example: Order ID 5965786