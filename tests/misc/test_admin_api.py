#!/usr/bin/env python3
"""Test admin API endpoints locally."""

import asyncio
import httpx
import json
from datetime import datetime

API_BASE = "http://localhost:8000"
MASTER_KEY = "master-secret-key"

async def test_admin_api():
    """Test admin API flow."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("1. Generate API Key")
        print("="*50)
        
        # Generate API key
        response = await client.post(
            f"{API_BASE}/api/admin/api-keys/generate",
            headers={"X-Master-Key": MASTER_KEY}
        )
        
        if response.status_code != 200:
            print(f"Error generating API key: {response.text}")
            return
            
        api_key_data = response.json()
        api_key = api_key_data["api_key"]
        print(f"Generated API key: {api_key}")
        
        # Set auth header for remaining requests
        auth_headers = {"X-API-Key": api_key}
        
        print("\n2. List Admin Profiles")
        print("="*50)
        
        response = await client.get(
            f"{API_BASE}/api/admin/profiles",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            profiles_data = response.json()
            print(f"Total profiles: {profiles_data['total']}")
            
            if profiles_data["profiles"]:
                test_profile = profiles_data["profiles"][0]
                profile_id = test_profile["id"]
                print(f"\nTesting with profile: {test_profile['persona']['name']}")
                print(f"Profile ID: {profile_id}")
                
                print("\n3. Get Profile Balance")
                print("="*50)
                
                response = await client.get(
                    f"{API_BASE}/api/admin/profiles/{profile_id}/balance",
                    headers=auth_headers
                )
                
                if response.status_code == 200:
                    balance_data = response.json()
                    print(f"Address: {balance_data['address']}")
                    print(f"Balance: ${balance_data['balance']}")
                    print(f"Available: ${balance_data['available']}")
                else:
                    print(f"Error getting balance: {response.text}")
                
                print("\n4. Get Profile Positions")
                print("="*50)
                
                response = await client.get(
                    f"{API_BASE}/api/admin/profiles/{profile_id}/positions",
                    headers=auth_headers
                )
                
                if response.status_code == 200:
                    positions_data = response.json()
                    print(f"Total position value: ${positions_data['total_value']}")
                    print(f"Positions: {json.dumps(positions_data['positions'], indent=2)}")
                else:
                    print(f"Error getting positions: {response.text}")
                
                print("\n5. Place Test Order")
                print("="*50)
                print("Placing small BTC buy order...")
                
                response = await client.post(
                    f"{API_BASE}/api/admin/profiles/{profile_id}/orders",
                    headers=auth_headers,
                    json={
                        "market": "BTC-USD",
                        "side": "buy",
                        "size": 0.001,
                        "reasoning": "Admin test order - small BTC buy"
                    }
                )
                
                if response.status_code == 200:
                    order_data = response.json()
                    print(f"Order placed successfully!")
                    print(f"Order ID: {order_data['order_id']}")
                    print(f"Market: {order_data['market']}")
                    print(f"Side: {order_data['side']}")
                    print(f"Size: {order_data['size']}")
                else:
                    print(f"Error placing order: {response.text}")
                
                print("\n6. Test Profile Creation")
                print("="*50)
                
                response = await client.post(
                    f"{API_BASE}/api/admin/profiles",
                    headers=auth_headers,
                    json={
                        "name": "Test Trader",
                        "handle": "test_trader_" + str(int(datetime.now().timestamp())),
                        "bio": "A test trading profile created via admin API",
                        "trading_style": "momentum",
                        "risk_tolerance": 0.5,
                        "personality_type": "midwit",
                        "initial_deposit": 50.0,
                        "favorite_assets": ["BTC", "ETH"],
                        "personality_traits": ["analytical", "balanced", "adaptive"]
                    }
                )
                
                if response.status_code == 200:
                    profile_data = response.json()
                    print(f"Profile created successfully!")
                    print(f"Profile ID: {profile_data['profile_id']}")
                    print(f"Address: {profile_data['address']}")
                    print(f"Signer Address: {profile_data['signer_address']}")
                    print(f"Message: {profile_data['message']}")
                else:
                    print(f"Error creating profile: {response.text}")
        else:
            print(f"Error listing profiles: {response.text}")

if __name__ == "__main__":
    print("🔧 Admin API Test")
    print("Make sure API server is running: poetry run python -m app.api.server")
    print("="*60)
    asyncio.run(test_admin_api())