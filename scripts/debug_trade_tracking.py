#!/usr/bin/env python3
"""Debug trade tracking issue."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.storage import JSONStorage
from app.services.rise_client import RiseClient


async def debug_trades():
    """Debug trade tracking."""
    
    storage = JSONStorage()
    accounts = storage.list_accounts()
    
    test_account = accounts[1]  # Midwit McGee
    print(f"🔍 Debugging trades for {test_account.persona.name}")
    print(f"Address: {test_account.address}")
    print("=" * 50)
    
    rise_client = RiseClient()
    
    try:
        # Place an order without success check
        print("\n1. Placing order...")
        result = await rise_client.place_market_order(
            account_key=test_account.private_key,
            signer_key=test_account.signer_key,
            market_id=1,
            side="sell",
            size=0.001,
            check_success=False  # Disable check
        )
        
        if result and "data" in result:
            order_id = result["data"].get("order_id")
            print(f"   Order ID: {order_id}")
        else:
            print(f"   Failed: {result}")
            return
        
        # Wait and check trades multiple times
        for i in range(5):
            await asyncio.sleep(2)
            print(f"\n2. Checking trades (attempt {i+1})...")
            
            # Get trade history
            trades = await rise_client.get_account_trade_history(test_account.address, limit=20)
            print(f"   Found {len(trades)} trades")
            
            # Show all recent order IDs
            if trades:
                print("   Recent order IDs:")
                for trade in trades[:5]:
                    print(f"     - Order {trade.get('order_id')}: {trade.get('side')} {trade.get('size')} @ {trade.get('price')}")
                    if str(trade.get('order_id')) == str(order_id):
                        print(f"   ✅ FOUND OUR TRADE!")
                        return
        
        # Check orders endpoint too
        print("\n3. Checking orders endpoint...")
        response = await rise_client._request(
            "GET", "/v1/orders",
            params={"account": test_account.address, "limit": 20}
        )
        orders = response.get("orders", [])
        print(f"   Found {len(orders)} orders")
        
        for order in orders[:5]:
            print(f"     - Order {order.get('id')}: {order.get('status')} / {order.get('cancel_reason', 'N/A')}")
            if str(order.get('id')) == str(order_id):
                print(f"   ✅ Found our order: {order.get('status')}")
                
    finally:
        await rise_client.close()


if __name__ == "__main__":
    asyncio.run(debug_trades())