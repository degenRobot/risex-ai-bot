#!/usr/bin/env python3
"""Test fixed RISE API methods."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.storage import JSONStorage
from app.services.rise_client import RiseClient


async def test_fixed_api():
    """Test the fixed RISE API methods."""
    
    storage = JSONStorage()
    accounts = storage.list_accounts()
    
    print("🔍 Testing Fixed RISE API Methods")
    print("=" * 50)
    
    rise_client = RiseClient()
    
    try:
        for account in accounts:
            print(f"\n📊 {account.persona.name} ({account.address})")
            print("-" * 40)
            
            # Test 1: Get positions with fixed endpoint
            print("\n1. Getting positions:")
            try:
                positions = await rise_client.get_all_positions(account.address)
                if positions:
                    print(f"   ✅ Found {len(positions)} positions")
                    for pos in positions:
                        market_id = pos.get("market_id")
                        size = pos.get("size", "0")
                        entry_price = pos.get("entry_price", "0")
                        # Convert size from raw format
                        size_btc = float(size) / 1e18
                        if size_btc != 0:
                            side = "LONG" if size_btc > 0 else "SHORT"
                            print(f"   - Market {market_id}: {side} {abs(size_btc):.6f} BTC @ ${entry_price}")
                else:
                    print("   ⚠️  No open positions")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Test 2: Get trade history with fixed endpoint
            print("\n2. Getting trade history:")
            try:
                trades = await rise_client.get_account_trade_history(account.address, limit=5)
                if trades:
                    print(f"   ✅ Found {len(trades)} trades")
                    for trade in trades[:3]:
                        order_id = trade.get("order_id")
                        side = trade.get("side", "").upper()
                        size = trade.get("size", "0")
                        price = trade.get("price", "0")
                        # Convert size
                        size_btc = float(size) / 1e18
                        print(f"   - Order {order_id}: {side} {size_btc:.6f} BTC @ ${price}")
                else:
                    print("   ⚠️  No trades found")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Test 3: Get orders with query params
            print("\n3. Getting recent orders:")
            try:
                # Direct API call for orders
                response = await rise_client._request(
                    "GET", "/v1/orders",
                    params={"account": account.address, "limit": 5}
                )
                orders = response.get("orders", [])
                if orders:
                    print(f"   ✅ Found {len(orders)} orders")
                    for order in orders[:3]:
                        order_id = order.get("id")
                        side = order.get("side", "").upper()
                        size = order.get("size", "0")
                        status = order.get("status", "")
                        order_type = order.get("type", "")
                        print(f"   - Order {order_id}: {side} {size} ({order_type}/{status})")
                else:
                    print("   ⚠️  No orders found")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            await asyncio.sleep(1)
            
    finally:
        await rise_client.close()
    
    print("\n✅ API testing complete!")


if __name__ == "__main__":
    asyncio.run(test_fixed_api())