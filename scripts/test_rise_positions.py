#!/usr/bin/env python3
"""Test RISE API positions endpoint directly."""

import asyncio
import json
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage

async def main():
    # Initialize
    client = RiseClient()
    storage = JSONStorage()
    
    print("Testing RISE API positions...\n")
    
    # Get all accounts
    accounts = storage.list_accounts()
    
    for account in accounts:
        if account.persona:
            print(f"\n{'='*60}")
            print(f"Profile: {account.persona.name} ({account.persona.handle})")
            print(f"Address: {account.address}")
            
            try:
                # Get positions from RISE API
                positions = await client.get_all_positions(account.address)
                
                print(f"Positions count: {len(positions)}")
                
                if positions:
                    print("\nPositions:")
                    for pos in positions:
                        market_id = pos.get("market_id")
                        size = float(pos.get("size", 0))
                        entry_price = float(pos.get("entry_price", 0))
                        unrealized_pnl = float(pos.get("unrealized_pnl", 0))
                        
                        print(f"  - Market ID: {market_id}")
                        print(f"    Size: {size}")
                        print(f"    Entry Price: ${entry_price:,.2f}")
                        print(f"    Unrealized PnL: ${unrealized_pnl:,.2f}")
                else:
                    print("  No positions found")
                    
                # Also check raw API response
                print("\nRaw API response:")
                response = await client._request(
                    "GET", "/v1/positions",
                    params={"account": account.address},
                )
                print(json.dumps(response, indent=2)[:500] + "..." if len(json.dumps(response)) > 500 else json.dumps(response, indent=2))
                
            except Exception as e:
                print(f"Error fetching positions: {e}")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())