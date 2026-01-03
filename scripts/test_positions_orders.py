#!/usr/bin/env python3
"""Test positions and orders fetching."""

import asyncio
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.equity_monitor import EquityMonitor
from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage


async def test_positions_orders():
    """Test fetching positions and orders."""
    print("\n🧪 Testing Positions and Orders Fetching")
    print("=" * 50)
    
    # Initialize services
    equity_monitor = EquityMonitor()
    rise_client = RiseClient()
    storage = JSONStorage()
    
    # Get accounts
    accounts = storage.get_all_accounts()
    
    if not accounts:
        print("❌ No accounts found")
        return
    
    # Test each account
    for account_id, account in accounts.items():
        print(f"\n📊 Testing {account.get('handle', 'Unknown')} ({account_id})")
        print(f"Address: {account['address']}")
        
        try:
            # Test direct API calls
            print("\n1️⃣ Direct API Calls:")
            
            # Get positions
            positions = await rise_client.get_all_positions(account['address'])
            print(f"   Positions: {len(positions)} found")
            if positions:
                for pos in positions[:2]:  # Show first 2
                    market_id = pos.get('market_id')
                    side = pos.get('side')
                    size = float(pos.get('size', 0)) / 10**18
                    print(f"   - Market {market_id}: {side} {size:.6f}")
            
            # Get orders
            orders = await rise_client.get_orders(account['address'], limit=10)
            print(f"   Orders: {len(orders)} found")
            if orders:
                for order in orders[:2]:  # Show first 2
                    market_id = order.get('market_id')
                    side = order.get('side')
                    status = order.get('status')
                    print(f"   - Market {market_id}: {side} ({status})")
            
            # Test equity monitor method
            print("\n2️⃣ Equity Monitor Method:")
            data = await equity_monitor.fetch_equity_margin_and_positions(account['address'])
            
            print(f"   Equity: ${data.get('equity', 0):,.2f}")
            print(f"   Free Margin: ${data.get('free_margin', 0):,.2f}")
            print(f"   Positions: {len(data.get('positions', []))}")
            print(f"   Orders: {len(data.get('orders', []))}")
            
            # Test update method
            print("\n3️⃣ Update Account Data:")
            success = await equity_monitor.update_account_equity(account_id, account['address'])
            if success:
                print("   ✅ Account data updated successfully")
                
                # Check stored data
                updated_accounts = storage.get_all_accounts()
                updated_account = updated_accounts.get(account_id, {})
                print(f"   Stored positions: {len(updated_account.get('positions', []))}")
                print(f"   Stored orders: {len(updated_account.get('orders', []))}")
            else:
                print("   ❌ Failed to update account data")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("-" * 50)
    
    # Test with a known account that has positions
    print("\n🔍 Testing Known Account with Position:")
    test_address = "0x2073f59c0a9323b4baeac07d6abc758987679197"
    
    try:
        positions = await rise_client.get_all_positions(test_address)
        orders = await rise_client.get_orders(test_address)
        
        print(f"Address: {test_address}")
        print(f"Positions: {len(positions)}")
        print(f"Orders: {len(orders)}")
        
        if positions:
            print("\nPosition Details:")
            for pos in positions:
                print(f"  Market ID: {pos.get('market_id')}")
                print(f"  Side: {pos.get('side')}")
                print(f"  Size: {float(pos.get('size', 0)) / 10**18}")
                print(f"  Entry Price: {float(pos.get('avg_entry_price', 0)) / 10**18}")
                
    except Exception as e:
        print(f"Error testing known account: {e}")


async def main():
    """Run tests."""
    await test_positions_orders()


if __name__ == "__main__":
    asyncio.run(main())