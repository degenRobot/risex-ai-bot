#!/usr/bin/env python3
"""Test RISE API endpoints directly with different URL patterns."""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.storage import JSONStorage


async def test_direct_api():
    """Test RISE API endpoints directly."""
    
    storage = JSONStorage()
    accounts = storage.list_accounts()
    
    print("🔍 Testing Direct RISE API Endpoints")
    print("=" * 50)
    
    # Use the first account for testing
    test_account = accounts[0] if accounts else None
    if not test_account:
        print("❌ No accounts found")
        return
    
    address = test_account.address
    print(f"\n📊 Testing with account: {address}")
    
    base_url = "https://api.testnet.rise.trade"
    
    # Endpoints to test
    endpoints = [
        # Positions endpoints
        (f"/v1/positions?account={address}", "GET", None),
        (f"/v1/positions", "GET", {"account": address}),
        (f"/v1/accounts/{address}/positions", "GET", None),
        (f"/v1/account/{address}/positions", "GET", None),
        
        # Trade history endpoints
        (f"/v1/trade-history?account={address}", "GET", None),
        (f"/v1/trade-history", "GET", {"account": address}),
        (f"/v1/accounts/{address}/trade-history", "GET", None),
        (f"/v1/account/{address}/trade-history", "GET", None),
        (f"/v1/account/trade-history", "GET", {"account": address}),
        
        # Orders endpoints
        (f"/v1/orders?account={address}", "GET", None),
        (f"/v1/orders", "GET", {"account": address}),
        (f"/v1/accounts/{address}/orders", "GET", None),
        (f"/v1/account/{address}/orders", "GET", None),
        
        # Account info
        (f"/v1/accounts/{address}", "GET", None),
        (f"/v1/account/{address}", "GET", None),
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint, method, params in endpoints:
            print(f"\n🔗 Testing: {method} {endpoint}")
            if params:
                print(f"   Params: {params}")
            
            try:
                url = f"{base_url}{endpoint}"
                
                async with session.request(method, url, params=params) as response:
                    status = response.status
                    
                    if status == 200:
                        data = await response.json()
                        print(f"   ✅ Status {status} - Success!")
                        
                        # Show some data
                        if isinstance(data, dict):
                            if "data" in data:
                                if isinstance(data["data"], list):
                                    print(f"   Data: {len(data['data'])} items")
                                    if data["data"]:
                                        print(f"   First item: {json.dumps(data['data'][0], indent=2)[:200]}...")
                                else:
                                    print(f"   Data: {json.dumps(data['data'], indent=2)[:200]}...")
                            else:
                                print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
                    else:
                        text = await response.text()
                        print(f"   ❌ Status {status}")
                        if text:
                            try:
                                error_data = json.loads(text)
                                print(f"   Error: {error_data}")
                            except:
                                print(f"   Response: {text[:100]}...")
                        
            except Exception as e:
                print(f"   ❌ Exception: {e}")
    
    print("\n✅ Direct API testing complete!")


if __name__ == "__main__":
    asyncio.run(test_direct_api())