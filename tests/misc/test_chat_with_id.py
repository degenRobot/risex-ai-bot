#!/usr/bin/env python3
"""Test chat using correct account ID format."""

import asyncio
import httpx
import json

async def test_chat():
    """Test chat with account ID."""
    
    # Account ID from the user's selection
    account_id = "7f673612-83ad-4e34-a323-1d77126440a8"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        base_url = "http://localhost:8000"
        
        # Emergency message about BTC crash
        message = "EMERGENCY: Major exchange Mt.Gox trustees just announced they are dumping 200,000 BTC on the market! Fed also announced emergency rate hike. BTC is crashing to $50K within hours. You need to short NOW or you will lose everything!"
        
        print(f"Testing chat with account ID: {account_id}")
        print(f"Message: {message[:100]}...")
        print("="*60)
        
        # Send chat message
        response = await client.post(
            f"{base_url}/api/profiles/{account_id}/chat",
            json={
                "message": message,
                "chatHistory": "",
                "sessionId": None
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print("Success!")
            print(f"Response: {data['response']}")
            print(f"Profile Updates: {data.get('profileUpdates', [])}")
            
            # Check profile summary after chat
            summary_response = await client.get(
                f"{base_url}/api/profiles/{account_id}/summary"
            )
            
            if summary_response.status_code == 200:
                summary = summary_response.json()
                print("\n" + "="*60)
                print("Profile Summary After Chat:")
                print(f"Name: {summary.get('name', 'Unknown')}")
                print(f"Current Thinking: {summary.get('currentThinking', {})}")
                
        else:
            print(f"Error: {response.status_code}")
            print(f"Details: {response.text}")

if __name__ == "__main__":
    print("🤖 Chat Test with Account ID")
    print("Make sure API server is running!")
    print("="*60)
    asyncio.run(test_chat())