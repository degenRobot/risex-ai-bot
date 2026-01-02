#!/usr/bin/env python3
"""Test RISE API endpoints for positions and trade history."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.storage import JSONStorage
from app.services.rise_client import RiseClient


async def test_rise_api():
    """Test RISE API endpoints for our accounts."""
    
    storage = JSONStorage()
    accounts = storage.list_accounts()
    
    print("🔍 Testing RISE API Endpoints")
    print("=" * 50)
    
    rise_client = RiseClient()
    
    try:
        for account in accounts:
            print(f"\n📊 {account.persona.name} ({account.address})")
            print("-" * 40)
            
            # Test 1: Get all positions
            print("\n1. Testing /v1/positions endpoint:")
            try:
                # Try the documented endpoint
                positions = await rise_client.get_all_positions(account.address)
                if positions and isinstance(positions, list):
                    print(f"   ✅ Found {len(positions)} positions")
                    for pos in positions[:2]:  # Show first 2
                        print(f"   - Market {pos.get('market_id')}: Size={pos.get('size')}, Entry={pos.get('entry_price')}")
                elif positions:
                    print(f"   ℹ️  Response: {positions}")
                else:
                    print("   ⚠️  No positions found")
            except Exception as e:
                print(f"   ❌ Error getting positions: {e}")
            
            # Test 2: Get positions (alternative endpoint)
            print("\n2. Testing /v1/accounts/{account}/positions:")
            try:
                response = await rise_client._request("GET", f"/v1/accounts/{account.address}/positions")
                data = response.get("data", [])
                if data:
                    print(f"   ✅ Found {len(data)} positions via account endpoint")
                    for pos in data[:2]:
                        print(f"   - {json.dumps(pos, indent=2)}")
                else:
                    print("   ⚠️  No positions via account endpoint")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Test 3: Get trade history
            print("\n3. Testing /v1/trade-history endpoint:")
            try:
                trades = await rise_client.get_account_trade_history(account.address, limit=10)
                if trades and isinstance(trades, list):
                    print(f"   ✅ Found {len(trades)} trades")
                    for trade in trades[:3]:  # Show first 3
                        print(f"   - {trade.get('side')} {trade.get('size')} @ {trade.get('price')} (ID: {trade.get('id')})")
                elif trades:
                    print(f"   ℹ️  Response: {trades}")
                else:
                    print("   ⚠️  No trades found")
            except Exception as e:
                print(f"   ❌ Error getting trade history: {e}")
            
            # Test 4: Alternative trade history endpoint
            print("\n4. Testing /v1/accounts/{account}/trade-history:")
            try:
                response = await rise_client._request("GET", f"/v1/accounts/{account.address}/trade-history", params={"limit": 10})
                data = response.get("data", [])
                if data:
                    print(f"   ✅ Found {len(data)} trades via account endpoint")
                    for trade in data[:2]:
                        print(f"   - {json.dumps(trade, indent=2)}")
                else:
                    print("   ⚠️  No trades via account endpoint")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Test 5: Get orders (might show recent orders)
            print("\n5. Testing /v1/accounts/{account}/orders:")
            try:
                response = await rise_client._request("GET", f"/v1/accounts/{account.address}/orders", params={"limit": 10})
                data = response.get("data", [])
                if data:
                    print(f"   ✅ Found {len(data)} orders")
                    for order in data[:2]:
                        print(f"   - Order {order.get('id')}: {order.get('side')} {order.get('size')} (Status: {order.get('status')})")
                else:
                    print("   ⚠️  No orders found")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Small delay between accounts
            await asyncio.sleep(1)
            
    finally:
        await rise_client.close()
    
    print("\n✅ API endpoint testing complete!")


if __name__ == "__main__":
    asyncio.run(test_rise_api())