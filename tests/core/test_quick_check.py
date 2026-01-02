#!/usr/bin/env python3
"""Quick test to check current system state."""

import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage


async def main():
    """Quick check of system state."""
    print("🔍 Quick System Check")
    print("=" * 60)
    
    # 1. Check accounts
    storage = JSONStorage()
    accounts = storage.list_accounts()
    print(f"\n✅ Found {len(accounts)} accounts")
    
    if accounts:
        account = accounts[0]
        print(f"   Test account: {account.address}")
        print(f"   Persona: {account.persona.name}")
    
    # 2. Check markets structure
    async with RiseClient() as client:
        print("\n📊 Checking markets structure...")
        markets = await client.get_markets()
        print(f"   Markets type: {type(markets)}")
        print(f"   Number of markets: {len(markets)}")
        
        if markets and len(markets) > 0:
            first = markets[0]
            print(f"   First market type: {type(first)}")
            if isinstance(first, dict):
                print(f"   First market keys: {list(first.keys())[:10]}")
                print(f"   Market ID: {first.get('market_id', first.get('id'))}")
                print(f"   Symbol: {first.get('symbol', first.get('base_asset_symbol'))}")
        
        # 3. Check positions
        if accounts:
            print("\n📍 Checking position...")
            try:
                response = await client._request(
                    "GET", "/v1/account/position",
                    params={"account": account.address, "market_id": 1}
                )
                
                position = response.get("data", {}).get("position", {})
                size_raw = int(position.get("size", 0))
                
                if size_raw != 0:
                    size_human = abs(size_raw / 1e18)
                    print(f"   BTC Position: {'Long' if size_raw > 0 else 'Short'} {size_human:.6f}")
                else:
                    print("   No BTC position")
                    
            except Exception as e:
                print(f"   Error: {e}")
    
    # 4. Check data files
    print("\n💾 Data files:")
    data_dir = Path("data")
    for file in ["accounts.json", "thought_processes.json", "chat_sessions.json"]:
        path = data_dir / file
        exists = "✅" if path.exists() else "❌"
        print(f"   {exists} {file}")
    
    print("\n✅ Quick check complete!")


if __name__ == "__main__":
    asyncio.run(main())