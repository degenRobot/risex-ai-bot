#!/usr/bin/env python3
"""Test fixed market order implementation."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage


async def test_fixed_market_order():
    """Test market order with the fix (limit order with price=0)."""
    
    print("✅ Testing Fixed Market Order Implementation")
    print("=" * 60)
    
    # Get test account
    storage = JSONStorage()
    test_account = next((acc for acc in storage.list_accounts() 
                        if acc.signer_key and acc.signer_key != acc.private_key), None)
    
    if not test_account:
        print("❌ No valid test account found")
        return
    
    print(f"\n📊 Test Account: {test_account.address}")
    
    async with RiseClient() as client:
        # Test 1: Buy order
        print("\n1️⃣ Testing Market Buy Order...")
        print("   Using: order_type='limit', price=0, tif=3")
        
        try:
            result = await client.place_market_order(
                account_key=test_account.private_key,
                signer_key=test_account.signer_key,
                market_id=1,  # BTC
                size=0.0001,
                side="buy"
            )
            
            print(f"\n✅ BUY ORDER SUCCESSFUL!")
            data = result.get('data', {})
            print(f"   Order ID: {data.get('order_id')}")
            print(f"   TX Hash: {data.get('transaction_hash')}")
            
            # Wait for execution
            await asyncio.sleep(3)
            
        except Exception as e:
            print(f"❌ Buy order failed: {e}")
        
        # Test 2: Sell order
        print("\n2️⃣ Testing Market Sell Order...")
        
        try:
            result = await client.place_market_order(
                account_key=test_account.private_key,
                signer_key=test_account.signer_key,
                market_id=1,
                size=0.00005,  # Sell half
                side="sell"
            )
            
            print(f"\n✅ SELL ORDER SUCCESSFUL!")
            print(f"   Order ID: {result.get('data', {}).get('order_id')}")
            
        except Exception as e:
            print(f"❌ Sell order failed: {e}")
        
        # Check final position
        print("\n3️⃣ Checking Final Position...")
        response = await client._request(
            "GET", "/v1/account/position",
            params={"account": test_account.address, "market_id": 1}
        )
        
        position = response.get("data", {}).get("position", {})
        size_raw = int(position.get("size", 0))
        
        if size_raw != 0:
            size_human = abs(size_raw / 1e18)
            side = "Long" if size_raw > 0 else "Short"
            print(f"   Position: {side} {size_human:.6f} BTC")
        else:
            print("   No open position")


if __name__ == "__main__":
    asyncio.run(test_fixed_market_order())