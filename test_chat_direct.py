#!/usr/bin/env python3
"""Direct test of chat service without API server."""

import asyncio
import json
from pathlib import Path
from app.services.profile_chat import ProfileChatService
from app.services.storage import JSONStorage

async def test_direct():
    """Test chat service directly."""
    
    # Initialize services
    chat_service = ProfileChatService()
    storage = JSONStorage()
    
    # Get first account
    accounts = storage.list_accounts()
    if not accounts:
        print("No accounts found!")
        return
    
    account = accounts[0]
    print(f"Testing with: {account.persona.name} ({account.persona.handle})")
    print(f"Account ID: {account.id}")
    
    # Test message
    message = "The Fed just announced emergency rate cuts! BTC is going to $150k minimum. You should go all in long RIGHT NOW!"
    
    print(f"\nUser message: {message}")
    print("-" * 60)
    
    try:
        # Send chat message
        result = await chat_service.chat_with_profile(
            account_id=account.id,
            user_message=message,
            chat_history="",
            user_session_id=None
        )
        
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"\nAI Response: {result['response']}")
            print(f"\nProfile Updates: {result.get('profileUpdates', [])}")
            print(f"\nContext:")
            print(f"  Personality: {result['context'].get('personality')}")
            print(f"  Speech Style: {result['context'].get('speechStyle')}")
            print(f"  Risk Profile: {result['context'].get('riskProfile')}")
            
            # Get summary
            summary = await chat_service.get_profile_summary(account.id)
            if "current_thinking" in summary:
                print(f"\nCurrent Thinking:")
                print(f"  Market Outlooks: {summary['current_thinking'].get('market_outlooks', {})}")
                print(f"  Recent Influences: {len(summary['current_thinking'].get('recent_influences', []))} influences")
    
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🤖 Direct Chat Test")
    print("=" * 60)
    asyncio.run(test_direct())