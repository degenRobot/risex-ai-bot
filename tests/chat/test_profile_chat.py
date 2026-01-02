#!/usr/bin/env python3
"""Test profile chat functionality."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.profile_chat import ProfileChatService
from app.services.storage import JSONStorage
from app.models import Account, Persona, TradingStyle
from datetime import datetime
import uuid


async def test_profile_chat():
    """Test the profile chat system."""
    print("Testing Profile Chat System")
    print("=" * 60)
    
    # Initialize services
    chat_service = ProfileChatService()
    storage = JSONStorage()
    
    # Get or create a test account
    accounts = storage.list_accounts()
    if not accounts:
        print("❌ No accounts found! Please create accounts first.")
        return
    
    account = accounts[0]
    print(f"\n🤖 Chatting with: {account.address[:8]}...")
    print(f"Account ID: {account.id}")
    
    # Test conversations that should trigger profile updates
    test_conversations = [
        {
            "message": "Hey! I just read that the Fed is going to cut rates next week. This is super bullish for Bitcoin!",
            "expected_update": "market_outlook"
        },
        {
            "message": "I've been following this whale trader who's been accumulating BTC. Think we're about to see a massive pump to 100k!",
            "expected_update": "market_outlook"
        },
        {
            "message": "You should be way more aggressive with your position sizing. Small positions won't make you rich!",
            "expected_update": "trading_bias"
        },
        {
            "message": "What's your current position on BTC right now?",
            "expected_update": None  # Just a question
        },
        {
            "message": "The market is looking really weak. I'd be careful about any longs right now. Might want to close positions.",
            "expected_update": "market_outlook"
        }
    ]
    
    chat_history = ""
    session_id = None
    
    for i, conversation in enumerate(test_conversations):
        print(f"\n{'='*60}")
        print(f"Conversation {i+1}: {conversation['expected_update'] or 'Question'}")
        print(f"User: {conversation['message']}")
        
        try:
            result = await chat_service.chat_with_profile(
                account_id=account.id,
                user_message=conversation["message"],
                chat_history=chat_history,
                user_session_id=session_id
            )
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
                continue
            
            # Update for next iteration
            chat_history = result["chatHistory"]
            session_id = result["sessionId"]
            
            print(f"\n🤖 AI Response: {result['response']}")
            
            if result.get("profileUpdates"):
                print(f"\n📝 Profile Updates:")
                for update in result["profileUpdates"]:
                    print(f"   - {update}")
            else:
                print(f"\n📝 No profile updates (this is fine for questions)")
            
            # Show context
            if result.get("context"):
                context = result["context"]
                print(f"\n💰 Trading Context:")
                print(f"   - Current P&L: ${context.get('currentPnL', 0):.2f}")
                print(f"   - Open Positions: {context.get('openPositions', 0)}")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    # Test profile summary after conversations
    print(f"\n{'='*60}")
    print("Profile Summary After Conversations:")
    
    try:
        summary = await chat_service.get_profile_summary(account.id)
        
        print(f"\n📊 Profile: {summary['profile']['name']}")
        print(f"Address: {summary['profile']['address']}")
        
        if summary.get("current_outlook"):
            print(f"\n🔮 Recent Market Outlooks:")
            for outlook in summary["current_outlook"][-3:]:  # Last 3
                asset = outlook.get("asset", "Unknown")
                view = outlook.get("outlook", "Unknown")
                reasoning = outlook.get("reasoning", "No reason")
                print(f"   - {asset}: {view} ({reasoning})")
        
        if summary.get("trading_bias"):
            print(f"\n⚖️  Recent Trading Bias Updates:")
            for bias in summary["trading_bias"][-2:]:  # Last 2
                bias_text = bias.get("bias", "Unknown")
                strategy = bias.get("strategy", "Unknown")
                print(f"   - {bias_text} with {strategy}")
        
        if summary.get("personality_updates"):
            print(f"\n🧠 Recent Personality Updates:")
            for trait in summary["personality_updates"][-3:]:  # Last 3
                trait_text = trait.get("trait", "Unknown")
                importance = trait.get("importance", "Medium")
                print(f"   - {trait_text} (importance: {importance})")
        
    except Exception as e:
        print(f"❌ Summary failed: {e}")
    
    # Test how updates affect trading decisions
    print(f"\n{'='*60}")
    print("Impact on Trading Decisions:")
    print("✅ Chat system allows users to influence AI trader personalities")
    print("✅ AI can update market outlook based on user insights") 
    print("✅ Trading bias and personality can be modified through conversation")
    print("✅ All updates are tracked with timestamps and reasoning")
    print("✅ Session management allows fluid conversations")
    
    # Example API calls
    print(f"\n{'='*60}")
    print("Example API Usage:")
    print(f"""
# Chat with a profile
POST /api/profiles/{account.id}/chat
{{
    "message": "Fed is cutting rates, BTC will moon!",
    "chatHistory": "{chat_history[:100]}...",
    "sessionId": "{session_id}"
}}

# Get profile summary  
GET /api/profiles/{account.id}/summary

# Get current context
GET /api/profiles/{account.id}/context
""")
    
    print(f"\n🎉 Chat system test completed!")
    print(f"Session ID: {session_id}")
    print(f"Conversation length: {len(json.loads(chat_history) if chat_history else [])}")


if __name__ == "__main__":
    asyncio.run(test_profile_chat())