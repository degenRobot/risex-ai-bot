#!/usr/bin/env python3
"""Check trade history for accounts."""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage


async def check_trade_history(account_address: str):
    """Check trade history for an account."""
    print(f"\n=== Trade History for {account_address} ===")
    
    rise_client = RiseClient()
    
    try:
        # Get trade history
        trades_response = await rise_client._request(
            "GET",
            "/v1/trade-history",
            params={"account": account_address, "page_size": 20}
        )
        
        print(f"\nTotal trades: {trades_response.get('data', {}).get('total_count', 0)}")
        
        if trades_response.get("data", {}).get("trades"):
            print("\nRecent trades:")
            for trade in trades_response["data"]["trades"][:10]:  # Show last 10
                print(f"\nTrade ID: {trade.get('trade_id')}")
                print(f"Order ID: {trade.get('order_id')}")
                print(f"Market: {trade.get('market_id')}")
                print(f"Side: {trade.get('side')}")
                print(f"Size: {float(trade.get('size', '0')) / 1e18:.6f}")
                print(f"Price: ${float(trade.get('price', '0')) / 1e18:.2f}")
                print(f"Block: {trade.get('block_number')}")
                
                # Check if this is order 6037211
                if trade.get('order_id') == '6037211':
                    print("\n⚡ FOUND ORDER 6037211!")
                    print(json.dumps(trade, indent=2))
        
    except Exception as e:
        print(f"Error checking trade history: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await rise_client.close()


async def main():
    """Check trade history for all accounts."""
    storage = JSONStorage()
    accounts = storage.get_all_accounts()
    
    # Check each account
    for account_id, account_data in accounts.items():
        print(f"\n{'='*60}")
        print(f"Account: {account_data['persona']['name']}")
        
        await check_trade_history(account_data['address'])
        
        # Small delay
        await asyncio.sleep(0.5)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main())