#!/usr/bin/env python3
"""
Test profile creation and management via admin API.
"""

import asyncio
import os
from datetime import datetime

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "https://risex-trading-bot.fly.dev"
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
MASTER_KEY = "master-secret-key"


async def test_profile_creation():
    """Test creating a new profile through the API."""
    print("🧪 Profile Creation Test")
    print("="*60)
    
    if not ADMIN_API_KEY:
        print("❌ No ADMIN_API_KEY found in .env")
        print("First generate an API key:")
        print(f"curl -X POST {BASE_URL}/api/admin/api-keys/generate \\")
        print('  -H "X-Master-Key: master-secret-key"')
        return
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {"X-API-Key": ADMIN_API_KEY}
        
        # Create a unique handle
        timestamp = int(datetime.now().timestamp())
        handle = f"test_bot_{timestamp}"
        
        print(f"Creating profile with handle: {handle}")
        
        # Define different personality types to test
        profiles_to_create = [
            {
                "name": "Bearish Cynical Trader",
                "handle": f"bear_cynical_{timestamp}",
                "bio": "Always expecting the worst in crypto markets",
                "trading_style": "conservative",
                "risk_tolerance": 0.2,
                "personality_type": "cynical",
                "initial_deposit": 50.0,
                "favorite_assets": ["BTC"],
                "personality_traits": ["pessimistic", "cautious", "analytical"],
            },
            {
                "name": "Left Curve Degen",
                "handle": f"degen_left_{timestamp}",
                "bio": "YOLO into everything, no analysis needed",
                "trading_style": "degen",
                "risk_tolerance": 0.9,
                "personality_type": "leftCurve",
                "initial_deposit": 100.0,
                "favorite_assets": ["BTC", "ETH"],
                "personality_traits": ["impulsive", "excited", "simple"],
            },
            {
                "name": "Midwit Momentum Trader",
                "handle": f"midwit_momentum_{timestamp}",
                "bio": "Following trends with pseudo-intellectual analysis",
                "trading_style": "momentum",
                "risk_tolerance": 0.6,
                "personality_type": "midwit",
                "initial_deposit": 75.0,
                "favorite_assets": ["BTC", "ETH"],
                "personality_traits": ["verbose", "trend-following", "overconfident"],
            },
        ]
        
        created_profiles = []
        
        for profile_data in profiles_to_create:
            print(f"\n📝 Creating: {profile_data['name']}")
            print(f"   Handle: {profile_data['handle']}")
            print(f"   Style: {profile_data['trading_style']}")
            print(f"   Personality: {profile_data['personality_type']}")
            
            try:
                response = await client.post(
                    f"{BASE_URL}/api/admin/profiles",
                    headers=headers,
                    json=profile_data,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    created_profiles.append(data)
                    
                    print("✅ Profile created successfully!")
                    print(f"   ID: {data['profile_id']}")
                    print(f"   Address: {data['address']}")
                    print(f"   Signer: {data['signer_address']}")
                    print(f"   Message: {data['message']}")
                    
                    # Test chat with new profile
                    print("\n💬 Testing chat with new profile...")
                    chat_response = await client.post(
                        f"{BASE_URL}/api/profiles/{data['profile_id']}/chat",
                        json={
                            "message": "Hey! What do you think about Bitcoin right now?",
                            "chatHistory": "",
                        },
                    )
                    
                    if chat_response.status_code == 200:
                        chat_data = chat_response.json()
                        print(f"✅ Chat response: {chat_data['response'][:150]}...")
                    else:
                        print(f"❌ Chat failed: {chat_response.text}")
                        
                else:
                    print(f"❌ Failed to create profile: {response.text}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
        
        # Summary
        print("\n" + "="*60)
        print("📊 SUMMARY")
        print(f"Created {len(created_profiles)} profiles")
        
        if created_profiles:
            print("\n📋 Created Profile IDs:")
            for profile in created_profiles:
                print(f"   - {profile['profile_id']} ({profile['persona']['handle']})")
            
            # Test admin list
            print("\n📋 Verifying with admin list...")
            list_response = await client.get(
                f"{BASE_URL}/api/admin/profiles",
                headers=headers,
            )
            
            if list_response.status_code == 200:
                all_profiles = list_response.json()
                print(f"✅ Total profiles in system: {all_profiles['total']}")
                
                # Find our new profiles
                new_profile_ids = [p["profile_id"] for p in created_profiles]
                found = 0
                for profile in all_profiles["profiles"]:
                    if profile["id"] in new_profile_ids:
                        found += 1
                
                print(f"✅ Verified {found}/{len(created_profiles)} new profiles in list")
            else:
                print(f"❌ Failed to list profiles: {list_response.text}")


async def test_profile_operations():
    """Test various operations on profiles."""
    print("\n\n🧪 Profile Operations Test")
    print("="*60)
    
    if not ADMIN_API_KEY:
        print("❌ No ADMIN_API_KEY found")
        return
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {"X-API-Key": ADMIN_API_KEY}
        
        # Get list of profiles
        response = await client.get(
            f"{BASE_URL}/api/admin/profiles",
            headers=headers,
        )
        
        if response.status_code != 200:
            print("❌ Failed to get profile list")
            return
        
        profiles = response.json()["profiles"]
        if not profiles:
            print("❌ No profiles found")
            return
        
        # Test with first profile
        test_profile = profiles[0]
        profile_id = test_profile["id"]
        
        print(f"Testing with profile: {test_profile['persona']['name']}")
        print(f"ID: {profile_id}")
        
        # Test balance check
        print("\n💰 Checking balance...")
        balance_response = await client.get(
            f"{BASE_URL}/api/admin/profiles/{profile_id}/balance",
            headers=headers,
        )
        
        if balance_response.status_code == 200:
            balance_data = balance_response.json()
            print(f"✅ Balance: ${balance_data['balance']}")
            print(f"   Available: ${balance_data['available']}")
        else:
            print(f"⚠️  Balance check failed: {balance_response.text}")
        
        # Test position check
        print("\n📊 Checking positions...")
        positions_response = await client.get(
            f"{BASE_URL}/api/admin/profiles/{profile_id}/positions",
            headers=headers,
        )
        
        if positions_response.status_code == 200:
            positions_data = positions_response.json()
            print(f"✅ Total position value: ${positions_data['total_value']}")
            if positions_data["positions"]:
                for market, pos in positions_data["positions"].items():
                    print(f"   {market}: {pos}")
            else:
                print("   No open positions")
        else:
            print(f"⚠️  Position check failed: {positions_response.text}")


async def main():
    """Run all profile tests."""
    await test_profile_creation()
    await test_profile_operations()


if __name__ == "__main__":
    asyncio.run(main())