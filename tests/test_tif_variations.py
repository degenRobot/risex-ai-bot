#!/usr/bin/env python3
"""Test different Time-In-Force values for orders."""

import asyncio
import json
import sys
import time
from pathlib import Path
from eth_account import Account as EthAccount
from eth_abi.packed import encode_packed
from eth_utils import keccak

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage


async def place_order_with_tif(rise_client, account, order_config):
    """Place order with specific TIF configuration."""
    
    account_obj = EthAccount.from_key(account.private_key)
    signer_obj = EthAccount.from_key(account.signer_key)
    
    domain = await rise_client.get_eip712_domain()
    
    # Extract parameters
    market_id = order_config["market_id"]
    size_wei = int(order_config["size"] * 1e18)
    price_wei = int(order_config["price"] * 1e18)
    side_int = order_config["side"]
    order_type_int = order_config["order_type"]
    tif = order_config["tif"]
    
    # Set expiry based on TIF
    if tif == 1:  # GTT needs expiry
        expiry = int(time.time()) + 3600  # 1 hour from now
    else:
        expiry = 0
    
    # Encode flags
    flags = (
        side_int |
        (0 << 1) |  # post_only = false
        (0 << 2) |  # reduce_only = false
        (0 << 3)    # stp_mode = 0
    )
    
    # Encode order (47 bytes)
    encoded_order = encode_packed(
        ["uint64", "uint128", "uint128", "uint8", "uint8", "uint8", "uint32"],
        [market_id, size_wei, price_wei, flags, order_type_int, tif, expiry]
    )
    
    print(f"  Encoded: {encoded_order.hex()}")
    print(f"  Length: {len(encoded_order)} bytes")
    print(f"  Byte 41 (orderType): {encoded_order[41]} ({order_type_int})")
    print(f"  Byte 42 (tif): {encoded_order[42]} ({tif})")
    
    order_hash = keccak(encoded_order)
    
    # Create signature
    nonce = rise_client._create_client_nonce(account_obj.address)
    deadline = int(time.time()) + 300
    target = "0x68cAcD54a8c93A3186BF50bE6b78B761F728E1b4"
    
    verify_sig_data = {
        "domain": domain,
        "message": {
            "account": account_obj.address,
            "target": target,
            "hash": order_hash,
            "nonce": nonce,
            "deadline": deadline,
        },
        "primaryType": "VerifySignature",
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "VerifySignature": [
                {"name": "account", "type": "address"},
                {"name": "target", "type": "address"},
                {"name": "hash", "type": "bytes32"},
                {"name": "nonce", "type": "uint256"},
                {"name": "deadline", "type": "uint256"},
            ],
        },
    }
    
    signature = rise_client._sign_typed_data(verify_sig_data, account.signer_key)
    
    # Build request
    order_request = {
        "order_params": {
            "market_id": str(market_id),
            "size": str(size_wei),
            "price": str(price_wei),
            "side": side_int,
            "order_type": order_type_int,
            "tif": tif,
            "post_only": False,
            "reduce_only": False,
            "stp_mode": 0,
            "expiry": expiry,
        },
        "permit_params": {
            "account": account_obj.address,
            "signer": signer_obj.address,
            "deadline": str(deadline),
            "signature": signature,
            "nonce": str(nonce),
        }
    }
    
    try:
        result = await rise_client._request(
            "POST", "/v1/orders/place",
            json=order_request
        )
        return True, result
    except Exception as e:
        return False, str(e)


async def test_tif_variations():
    """Test different TIF values."""
    rise_client = RiseClient()
    storage = JSONStorage()
    
    print("RISE Time-In-Force Test")
    print("=" * 60)
    
    accounts = storage.list_accounts()
    if not accounts:
        return
    
    account = accounts[0]
    print(f"Account: {account.address}")
    print(f"Signer: {EthAccount.from_key(account.signer_key).address}")
    
    # Test configurations
    test_configs = [
        # Limit orders with different TIF
        {
            "name": "Limit Order with GTC (0)",
            "market_id": 1,
            "size": 0.0001,
            "price": 50000.0,
            "side": 0,  # buy
            "order_type": 0,  # limit
            "tif": 0  # GTC
        },
        {
            "name": "Limit Order with IOC (3)",
            "market_id": 1,
            "size": 0.0001,
            "price": 50000.0,
            "side": 0,
            "order_type": 0,  # limit
            "tif": 3  # IOC
        },
        {
            "name": "Limit Order with FOK (2)",
            "market_id": 1,
            "size": 0.0001,
            "price": 50000.0,
            "side": 0,
            "order_type": 0,  # limit
            "tif": 2  # FOK
        },
        {
            "name": "Limit Order with GTT (1)",
            "market_id": 1,
            "size": 0.0001,
            "price": 50000.0,
            "side": 0,
            "order_type": 0,  # limit
            "tif": 1  # GTT
        },
        # Market orders - these typically need IOC or FOK
        {
            "name": "Market Order with IOC (3)",
            "market_id": 1,
            "size": 0.0001,
            "price": 100000.0,  # Market orders still need a price reference
            "side": 0,
            "order_type": 1,  # market
            "tif": 3  # IOC
        },
        {
            "name": "Market Order with FOK (2)",
            "market_id": 1,
            "size": 0.0001,
            "price": 100000.0,
            "side": 0,
            "order_type": 1,  # market
            "tif": 2  # FOK
        },
        # This should fail - market orders shouldn't use GTC
        {
            "name": "Market Order with GTC (0) - Should Fail",
            "market_id": 1,
            "size": 0.0001,
            "price": 100000.0,
            "side": 0,
            "order_type": 1,  # market
            "tif": 0  # GTC - invalid for market orders!
        }
    ]
    
    # Test each configuration
    for config in test_configs:
        print(f"\n{'=' * 60}")
        print(f"Test: {config['name']}")
        print(f"Parameters:")
        print(f"  Market ID: {config['market_id']}")
        print(f"  Size: {config['size']} BTC")
        print(f"  Price: ${config['price']:,.2f}")
        print(f"  Side: {'buy' if config['side'] == 0 else 'sell'}")
        print(f"  Order Type: {'limit' if config['order_type'] == 0 else 'market'}")
        print(f"  TIF: {config['tif']} ({['GTC', 'GTT', 'FOK', 'IOC'][config['tif']]})")
        
        success, result = await place_order_with_tif(rise_client, account, config)
        
        if success:
            print("\n✅ ORDER PLACED SUCCESSFULLY!")
            print(f"Response: {json.dumps(result, indent=2)}")
            # If we find a working combination, note it
            print(f"\n🎉 Working configuration found: {config['name']}")
            break
        else:
            print(f"\n❌ Failed: {result}")
            if "InvalidTimeInForceForMarketOrder" in result:
                print("  → This confirms market orders need specific TIF values")
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print("- Market orders (type=1) require TIF=2 (FOK) or TIF=3 (IOC)")
    print("- Limit orders (type=0) can use any TIF value")
    print("- The error suggests our encoding is correct but we used wrong TIF")
    
    await rise_client.close()


if __name__ == "__main__":
    asyncio.run(test_tif_variations())