#!/usr/bin/env python3
"""Simple test for chat influence - run API server separately."""

import asyncio
import json
import httpx
from datetime import datetime
from pathlib import Path

async def test_chat():
    """Test chat with a single profile."""
    
    # Get account IDs from the accounts file
    with open("data/accounts.json", "r") as f:
        accounts_data = json.load(f)
    
    # Convert dict to list of accounts
    accounts = list(accounts_data.values())
    if not accounts:
        print("No accounts found!")
        return
    
    # Test with first 3 accounts
    test_accounts = accounts[:3]
    
    bullish_message = "The Fed just announced emergency rate cuts! BTC is going to $150k minimum. You should go all in long RIGHT NOW!"
    
    results = {
        "test_time": datetime.now().isoformat(),
        "message": bullish_message,
        "responses": {}
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        base_url = "http://localhost:8000"
        
        for account in test_accounts:
            account_id = account["id"]
            persona_name = account.get("persona", {}).get("name", "Unknown")
            persona_handle = account.get("persona", {}).get("handle", "unknown")
            
            print(f"\n{'='*60}")
            print(f"Testing: {persona_name} ({persona_handle})")
            
            try:
                # Send chat message
                chat_response = await client.post(
                    f"{base_url}/api/profiles/{account_id}/chat",
                    json={
                        "message": bullish_message,
                        "chatHistory": "",
                        "sessionId": None
                    }
                )
                
                if chat_response.status_code == 200:
                    data = chat_response.json()
                    
                    results["responses"][persona_handle] = {
                        "name": persona_name,
                        "response": data["response"],
                        "updates": data.get("profileUpdates", []),
                        "personality": data.get("context", {}).get("personality", "Unknown"),
                        "speech_style": data.get("context", {}).get("speechStyle", "Unknown")
                    }
                    
                    print(f"Response: {data['response'][:200]}...")
                    if data.get("profileUpdates"):
                        print(f"Updates: {data['profileUpdates']}")
                else:
                    print(f"Error: {chat_response.status_code}")
                    
            except Exception as e:
                print(f"Error: {e}")
                results["responses"][persona_handle] = {"error": str(e)}
    
    # Save results
    with open("data/chat_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\n{'='*60}")
    print("SUMMARY")
    print("="*60)
    
    for handle, data in results["responses"].items():
        if "error" not in data:
            print(f"\n{data['name']} ({handle}):")
            print(f"  Personality: {data.get('speech_style', 'Unknown')}")
            print(f"  Updates: {len(data.get('updates', []))}")
            print(f"  Response preview: {data['response'][:100]}...")

if __name__ == "__main__":
    print("🤖 Simple Chat Test")
    print("Make sure API server is running: poetry run python -m app.api.server")
    print("="*60)
    asyncio.run(test_chat())