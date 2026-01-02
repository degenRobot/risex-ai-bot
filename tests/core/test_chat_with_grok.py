#!/usr/bin/env python3
"""Test chat system with Grok-4.1-fast."""

import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.storage import JSONStorage
from app.services.profile_chat import ProfileChatService


async def main():
    """Test chat with Grok model."""
    print("🤖 Testing Chat with Grok-4.1-fast")
    print("=" * 60)
    
    # Get test account
    storage = JSONStorage()
    accounts = storage.list_accounts()
    
    if not accounts:
        print("❌ No accounts found")
        return
    
    # Find cynical account if available
    test_account = None
    for account in accounts:
        if hasattr(account.persona, 'handle') and account.persona.handle == "cynicalUser":
            test_account = account
            break
    
    if not test_account:
        test_account = accounts[0]
    
    print(f"\n🧪 Testing with: {test_account.persona.name}")
    print(f"   Handle: {getattr(test_account.persona, 'handle', 'N/A')}")
    
    # Initialize chat service
    chat_service = ProfileChatService()
    
    # Test messages that should trigger different responses
    test_messages = [
        "Fed just cut rates by 50 basis points! BTC to the moon! 🚀",
        "I think ETH is going to crash hard, maybe down to $2000. What's your take?",
        "SOL looks amazing, so much faster than ETH. I'm buying more!"
    ]
    
    for message in test_messages:
        print(f"\n🗣️ User: {message}")
        
        try:
            result = await chat_service.chat_with_profile(
                account_id=test_account.id,
                user_message=message,
                chat_history=""
            )
            
            response = result.get('response', 'No response')
            print(f"🤖 Response: {response}")
            
            # Check for profile updates
            updates = result.get('profileUpdates', [])
            if updates:
                print(f"📝 Profile Updates: {len(updates)} updates")
                for update in updates:
                    print(f"   - {update}")
            else:
                print("📝 No profile updates")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        await asyncio.sleep(2)
    
    print("\n✅ Chat test complete!")


if __name__ == "__main__":
    asyncio.run(main())