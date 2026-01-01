#!/usr/bin/env python3
"""Test with existing accounts that might have balance."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.storage import JSONStorage
from app.services.rise_client import RiseClient
from app.core.market_manager import get_market_manager


async def test_existing_accounts():
    """Check existing accounts and try to place order."""
    storage = JSONStorage()
    rise_client = RiseClient()
    market_manager = get_market_manager()
    
    print("Testing Existing Accounts")
    print("=" * 50)
    
    # Get all accounts
    accounts = storage.list_accounts()
    print(f"\nFound {len(accounts)} accounts in storage\n")
    
    # Get market data
    await market_manager.get_latest_data(force_update=True)
    btc_price = market_manager.market_cache.get("btc_price", 90000)
    btc_id = market_manager.market_cache.get("btc_market_id", 1)
    
    print(f"Market Data:")
    print(f"BTC Price: ${btc_price:,.0f}")
    print(f"BTC Market ID: {btc_id}\n")
    
    # Check each account
    for account in accounts[-3:]:  # Check last 3 accounts
        if not account.persona:
            continue
            
        print(f"\nChecking {account.persona.handle} ({account.persona.name})")
        print(f"Address: {account.address}")
        
        try:
            # Check balance
            balance_data = await rise_client.get_balance(account.address)
            balance = float(balance_data.get('cross_margin_balance', 0))
            available = float(balance_data.get('available_balance', 0))
            
            print(f"Balance: ${balance:.2f} (available: ${available:.2f})")
            
            # Check positions
            positions = await rise_client.get_all_positions(account.address)
            open_positions = [p for p in positions if float(p.get('size', 0)) != 0]
            print(f"Open positions: {len(open_positions)}")
            
            # If has balance and no positions, try to place order
            if balance > 10 and len(open_positions) == 0:
                print("\nPlacing test order...")
                
                size = 0.0001  # Small BTC amount
                price = btc_price * 0.99  # 1% below market
                
                try:
                    order_result = await rise_client.place_order(
                        account_key=account.private_key,
                        signer_key=account.signer_key,
                        market_id=btc_id,
                        size=size,
                        price=price,
                        side="buy",
                        order_type="limit"
                    )
                    
                    if order_result.get('success'):
                        print(f"✓ Order placed successfully!")
                        print(f"  Order ID: {order_result.get('data', {}).get('order_id')}")
                    else:
                        print(f"✗ Order failed: {order_result.get('message')}")
                        
                except Exception as e:
                    print(f"✗ Order error: {e}")
                    
        except Exception as e:
            print(f"Error checking account: {e}")
    
    await rise_client.close()
    await market_manager.close()
    
    print("\n" + "=" * 50)
    print("Test complete!")


if __name__ == "__main__":
    asyncio.run(test_existing_accounts())