#!/usr/bin/env python3
"""Test order success detection with the new tracker."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.storage import JSONStorage
from app.services.rise_client import RiseClient
from app.services.equity_monitor import get_equity_monitor
from app.services.order_tracker import OrderTracker


async def test_order_success():
    """Test order placement with success detection."""
    
    storage = JSONStorage()
    accounts = storage.list_accounts()
    
    print("🎯 Testing Order Success Detection")
    print("=" * 50)
    
    # Test with one account
    test_account = accounts[0]  # Use Drunk Wassie
    
    print(f"\n📊 Testing with {test_account.persona.name}")
    print(f"   Address: {test_account.address}")
    
    # Get initial state
    equity_monitor = get_equity_monitor()
    initial_equity = await equity_monitor.fetch_equity(test_account.address)
    print(f"   Initial equity: ${initial_equity:.2f}")
    
    # Check current positions
    tracker = OrderTracker()
    positions = await tracker.get_account_positions_summary(test_account.address)
    print(f"   Current positions: {positions['total_positions']}")
    for pos in positions['positions']:
        print(f"     - Market {pos['market_id']}: {pos['side']} {pos['size']:.6f} BTC")
    
    # Place a small test order
    rise_client = RiseClient()
    
    try:
        print(f"\n🎲 Placing test order...")
        
        # Place order with success detection
        result = await rise_client.place_market_order(
            account_key=test_account.private_key,
            signer_key=test_account.signer_key,
            market_id=1,  # BTC
            side="buy",
            size=0.001,  # Small test trade
            check_success=True  # Enable success detection
        )
        
        # Check result
        if result and "data" in result:
            order_id = result["data"].get("order_id")
            print(f"   ✅ Order placed: ID {order_id}")
            
            # Check if filled
            if result.get("order_filled"):
                print(f"   ✅ Order FILLED successfully!")
                fill_details = result.get("fill_details", {})
                print(f"   - Fill price: ${fill_details.get('price', 0):.2f}")
                print(f"   - Size: {fill_details.get('size', 0)}")
                print(f"   - TX: {fill_details.get('tx_hash', 'N/A')[:20]}...")
            else:
                print(f"   ⚠️  Order placed but fill status unknown")
        else:
            print(f"   ❌ Order placement failed: {result}")
        
        # Wait a bit and check positions again
        await asyncio.sleep(3)
        
        print(f"\n📊 After trade:")
        final_equity = await equity_monitor.fetch_equity(test_account.address)
        print(f"   Final equity: ${final_equity:.2f}")
        print(f"   Change: ${final_equity - initial_equity:.2f}")
        
        # Get updated positions
        positions = await tracker.get_account_positions_summary(test_account.address)
        print(f"   Positions: {positions['total_positions']}")
        for pos in positions['positions']:
            print(f"     - Market {pos['market_id']}: {pos['side']} {pos['size']:.6f} BTC @ ${pos['entry_price']:.2f}")
        
        # Get trading data update
        print(f"\n📝 Updating account trading data...")
        trading_data = await tracker.update_account_trading_data(
            account_id=test_account.id,
            account_address=test_account.address
        )
        
        print(f"   Recent trades: {len(trading_data['recent_trades'])}")
        for trade in trading_data['recent_trades'][:3]:
            print(f"     - Order {trade['order_id']}: {trade['side']} {trade['size']} @ ${trade['price']:.2f}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    finally:
        await rise_client.close()
        await tracker.close()
    
    print("\n✅ Order success detection test complete!")


if __name__ == "__main__":
    asyncio.run(test_order_success())