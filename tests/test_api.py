#!/usr/bin/env python3
"""Test the FastAPI endpoints."""

import asyncio
import httpx
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_URL = "http://localhost:8080"


async def test_api():
    """Test basic API functionality."""
    print("Testing RISE AI Trading Bot API")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        # Test root endpoint
        print("\nTesting GET /")
        response = await client.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        print(f"Status: {data['status']}")
        
        # Test health endpoint
        print("\nTesting GET /health")
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        print(f"Health: {data['status']}")
        print(f"Accounts: {data.get('accounts', 0)}")
        
        # Test list profiles
        print("\nTesting GET /api/profiles")
        response = await client.get(f"{BASE_URL}/api/profiles")
        assert response.status_code == 200
        profiles = response.json()
        print(f"Found {len(profiles)} profiles")
        
        if profiles:
            # Test get profile detail
            handle = profiles[0]['handle']
            print(f"\nTesting GET /api/profiles/{handle}")
            response = await client.get(f"{BASE_URL}/api/profiles/{handle}")
            assert response.status_code == 200
            profile = response.json()
            print(f"Profile: {profile['name']} ({profile['trading_style']})")
            print(f"Trading: {profile['is_trading']}")
            print(f"Pending actions: {len(profile['pending_actions'])}")
            
            # Test get actions
            print(f"\nTesting GET /api/profiles/{handle}/actions")
            response = await client.get(f"{BASE_URL}/api/profiles/{handle}/actions")
            assert response.status_code == 200
            data = response.json()
            print(f"Actions: {len(data['actions'])}")
    
    print("\n" + "=" * 50)
    print("All API tests passed!")


if __name__ == "__main__":
    asyncio.run(test_api())