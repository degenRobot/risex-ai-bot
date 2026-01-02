#!/usr/bin/env python3
"""Test order placement with parameters matching the successful order."""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Account
from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage


async def test_order_placement():
    """Test order placement with correct parameters."""
    print("🔧 Testing Order Placement with Correct Parameters")
    print("=" * 60)
    
    storage = JSONStorage()
    
    # Use the test account that has deposits
    account_id = "test-1767342488"
    account = storage.get_account(account_id)
    
    if not account:
        print("❌ Test account not found")
        return
    
    print(f"Account: {account.persona.name if account.persona else account.address}")
    print(f"Address: {account.address}")
    print(f"Has deposited: {account.has_deposited}")
    
    async with RiseClient() as client:
        # 1. Check current balance
        print("\n💰 Checking Balance")
        print("-" * 40)
        
        try:
            balance_info = await client.get_balance(account.address)
            margin_summary = balance_info.get("marginSummary", {})
            free_collateral = margin_summary.get("freeCollateral", 0)
            print(f"Free Collateral: ${free_collateral:,.2f}")
        except Exception as e:
            print(f"⚠️  Balance check failed: {e}")
            free_collateral = 0
        
        # 2. Check market status
        print("\n🏪 Market Status")
        print("-" * 40)
        
        markets = await client.get_markets()
        btc_market = next((m for m in markets if int(m.get("market_id", 0)) == 1), None)
        
        if btc_market:
            print(f"BTC Market:")
            print(f"  Symbol: {btc_market.get('symbol', 'BTC-USD')}")
            print(f"  Last Price: ${float(btc_market.get('last_price', 0)):,.2f}")
            print(f"  Available: {btc_market.get('available', False)}")
            
        # 3. Attempt order with correct parameters
        print("\n📈 Attempting Order (Matching Successful Format)")
        print("-" * 40)
        
        # Parameters matching the successful order:
        # - Use limit order (order_type=0)
        # - Use TIF=3 (IOC)
        # - Very small size
        
        try:
            print("Parameters:")
            print("  Market ID: 1 (BTC)")
            print("  Order Type: limit (0)")
            print("  Size: 0.0001 BTC")
            print("  Price: 0 (for market-like execution)")
            print("  Side: buy")
            print("  TIF: 3 (IOC)")
            
            order = await client.place_order(
                account_key=account.private_key,
                signer_key=account.signer_key,
                market_id=1,  # BTC
                side="buy",
                size=0.0001,  # Very small order
                price=0,  # Price=0 for market-like
                order_type="limit",  # Use limit order type
                tif=3,  # IOC
                reduce_only=False,
                max_retries=1
            )
            
            print(f"\n✅ Order Response:")
            print(json.dumps(order, indent=2))
            
            if "data" in order:
                data = order["data"]
                print(f"\nOrder Details:")
                print(f"  Order ID: {data.get('order_id')}")
                print(f"  TX Hash: {data.get('transaction_hash')}")
                print(f"  Status: {data.get('order', {}).get('status')}")
                
        except Exception as e:
            print(f"\n❌ Order failed: {e}")
            
            # Extract tx hash if available
            error_str = str(e)
            if "tx=" in error_str:
                start = error_str.find("tx=") + 3
                end = error_str.find(" ", start)
                if end == -1:
                    end = error_str.find(":", start)
                if end > start:
                    tx_hash = error_str[start:end]
                    print(f"Transaction: https://explorer.testnet.riselabs.xyz/tx/{tx_hash}")
        
        # 4. Try with different variations
        print("\n🔄 Testing Variations")
        print("-" * 40)
        
        variations = [
            # (size, price, description)
            (0.00001, 0, "Smaller size (0.00001 BTC)"),
            (0.001, 0, "Larger size (0.001 BTC)"),
            (0.0001, 100000, "With high limit price"),
        ]
        
        for size, price, desc in variations:
            print(f"\nTrying: {desc}")
            
            try:
                order = await client.place_order(
                    account_key=account.private_key,
                    signer_key=account.signer_key,
                    market_id=1,
                    side="buy",
                    size=size,
                    price=price,
                    order_type="limit",
                    tif=3,
                    reduce_only=False,
                    max_retries=1
                )
                
                if "data" in order and order["data"].get("order_id"):
                    print(f"✅ Success! Order ID: {order['data']['order_id']}")
                    break
                else:
                    print("❌ Failed - no order ID returned")
                    
            except Exception as e:
                print(f"❌ Failed: {str(e)[:100]}...")
            
            await asyncio.sleep(1)


async def main():
    """Run the test."""
    await test_order_placement()


if __name__ == "__main__":
    asyncio.run(main())