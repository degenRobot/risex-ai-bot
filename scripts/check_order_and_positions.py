#!/usr/bin/env python3
"""Check order details and current positions."""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage


async def check_order(order_id: str, account_address: str):
    """Check order details."""
    print(f"\n=== Checking Order {order_id} ===")
    
    rise_client = RiseClient()
    
    try:
        # Get order details
        order_response = await rise_client._request(
            "GET", 
            f"/v1/orders/{order_id}"
        )
        
        print(f"\nOrder Response:")
        print(json.dumps(order_response, indent=2))
        
        # Also check trade history
        trades_response = await rise_client._request(
            "GET",
            "/v1/trade-history",
            params={"account": account_address}
        )
        
        # Find trades for this order
        if trades_response.get("data"):
            order_trades = [
                trade for trade in trades_response["data"] 
                if trade.get("order_id") == order_id
            ]
            
            if order_trades:
                print(f"\nTrades for order {order_id}:")
                for trade in order_trades:
                    print(json.dumps(trade, indent=2))
        
    except Exception as e:
        print(f"Error checking order: {e}")
    
    finally:
        await rise_client.close()


async def check_positions(account_address: str):
    """Check current positions for an account."""
    print(f"\n=== Checking Positions for {account_address} ===")
    
    rise_client = RiseClient()
    
    try:
        # Get positions
        positions_response = await rise_client._request(
            "GET",
            "/v1/positions",
            params={"account": account_address}
        )
        
        print(f"\nPositions Response:")
        print(json.dumps(positions_response, indent=2))
        
        # Also get account balance
        balance_response = await rise_client.get_balance(account_address)
        print(f"\nBalance Response:")
        print(json.dumps(balance_response, indent=2))
        
        # Get equity from RPC
        from app.services.equity_monitor import get_equity_monitor
        equity_monitor = get_equity_monitor()
        
        equity = await equity_monitor.fetch_equity(account_address)
        free_margin = await equity_monitor.fetch_free_margin(account_address)
        
        print(f"\nRPC Equity Data:")
        print(f"Total Equity: ${equity:.2f}")
        print(f"Free Margin: ${free_margin:.2f}")
        
    except Exception as e:
        print(f"Error checking positions: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await rise_client.close()


async def check_all_accounts():
    """Check positions for all accounts."""
    storage = JSONStorage()
    accounts = storage.get_all_accounts()
    
    for account_id, account_data in accounts.items():
        print(f"\n{'='*60}")
        print(f"Account: {account_data['persona']['name']} ({account_data['persona']['handle']})")
        print(f"Address: {account_data['address']}")
        
        await check_positions(account_data['address'])
        
        # Small delay between accounts
        await asyncio.sleep(0.5)


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Check orders and positions")
    parser.add_argument("--order", help="Order ID to check")
    parser.add_argument("--account", help="Account address")
    parser.add_argument("--all", action="store_true", help="Check all accounts")
    
    args = parser.parse_args()
    
    if args.order and args.account:
        await check_order(args.order, args.account)
    elif args.account:
        await check_positions(args.account)
    elif args.all:
        await check_all_accounts()
    else:
        # Default: check Midwit McGee and the recent order
        print("Checking Midwit McGee account and order 6037211...")
        midwit_address = "0x41972911b53D5B038c4c35F610e31963F60FaAd5"
        
        await check_order("6037211", midwit_address)
        await check_positions(midwit_address)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main())