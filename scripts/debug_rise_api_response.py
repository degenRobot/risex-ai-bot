#!/usr/bin/env python3
"""Debug RISE API response structure."""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.storage import JSONStorage


async def debug_api():
    """Debug API response structure."""
    
    storage = JSONStorage()
    accounts = storage.list_accounts()
    
    if not accounts:
        print("No accounts found")
        return
    
    # Use the first account (Drunk Wassie)
    test_account = accounts[0]
    address = test_account.address
    
    print(f"🔍 Debugging API responses for {test_account.persona.name}")
    print(f"Address: {address}")
    print("=" * 50)
    
    base_url = "https://api.testnet.rise.trade"
    
    async with aiohttp.ClientSession() as session:
        # Test trade history
        print("\n1. Trade History Response:")
        url = f"{base_url}/v1/trade-history?account={address}"
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                print(json.dumps(data, indent=2))
            else:
                print(f"❌ Status {response.status}")
        
        # Test positions
        print("\n\n2. Positions Response:")
        url = f"{base_url}/v1/positions?account={address}"
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                print(json.dumps(data, indent=2))
            else:
                print(f"❌ Status {response.status}")
        
        # Test orders
        print("\n\n3. Orders Response:")
        url = f"{base_url}/v1/orders?account={address}"
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                print(json.dumps(data, indent=2))
            else:
                print(f"❌ Status {response.status}")


if __name__ == "__main__":
    asyncio.run(debug_api())