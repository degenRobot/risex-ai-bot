#!/usr/bin/env python3
"""Simple test to place an order with a fresh account."""

import asyncio
import sys
from pathlib import Path
from eth_account import Account as EthAccount

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rise_client import RiseClient


async def test_place_order():
    """Test placing a simple order."""
    rise_client = RiseClient()
    
    print("RISE Simple Order Test")
    print("=" * 50)
    
    # Generate fresh keys
    main_account = EthAccount.create()
    signer_account = EthAccount.create()
    
    print(f"\nAccount: {main_account.address}")
    print(f"Signer: {signer_account.address}")
    
    try:
        # 1. Register signer
        print("\n1. Registering signer...")
        result = await rise_client.register_signer(
            main_account.key.hex(),
            signer_account.key.hex()
        )
        print(f"   ✓ Registration successful")
    except Exception as e:
        print(f"   ✗ Registration error: {e}")
        return
    
    # 2. Deposit USDC
    print("\n2. Depositing USDC...")
    try:
        deposit_result = await rise_client.deposit_usdc(
            main_account.key.hex(),
            amount=100.0
        )
        print(f"   ✓ Deposit submitted")
    except Exception as e:
        print(f"   ✗ Deposit error: {e}")
    
    # 3. Wait for faucet
    print("\n3. Waiting 10 seconds for faucet...")
    await asyncio.sleep(10)
    
    # 4. Get market price
    print("\n4. Getting BTC market price...")
    try:
        markets = await rise_client.get_markets()
        btc_market = next((m for m in markets if "BTC" in m.get("base_asset_symbol", "")), None)
        
        if btc_market:
            btc_price = float(btc_market.get("last_price", 90000))
            btc_id = int(btc_market.get("market_id", 1))
            print(f"   BTC Price: ${btc_price:,.0f}")
            print(f"   Market ID: {btc_id}")
        else:
            btc_price = 90000
            btc_id = 1
            print(f"   Using default BTC price: ${btc_price:,.0f}")
    except Exception as e:
        print(f"   Market error: {e}")
        btc_price = 90000
        btc_id = 1
    
    # 5. Place order
    print("\n5. Placing BTC buy order...")
    try:
        order_result = await rise_client.place_order(
            account_key=main_account.key.hex(),
            signer_key=signer_account.key.hex(),
            market_id=btc_id,
            size=0.001,  # Small amount
            price=btc_price * 0.99,  # 1% below market
            side="buy",
            order_type="limit"
        )
        
        if order_result.get('success'):
            order_data = order_result.get('data', {})
            print(f"   ✓ Order placed successfully!")
            print(f"   Order ID: {order_data.get('order_id')}")
            print(f"   Tx Hash: {order_data.get('transaction_hash')}")
        else:
            print(f"   ✗ Order failed: {order_result.get('message')}")
            
    except Exception as e:
        print(f"   ✗ Order error: {e}")
    
    await rise_client.close()
    
    print("\n" + "=" * 50)
    print("Test complete!")


if __name__ == "__main__":
    asyncio.run(test_place_order())