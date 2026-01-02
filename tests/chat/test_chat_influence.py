#!/usr/bin/env python3
"""Test how chat messages influence AI trader decisions."""

import asyncio
import json
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime
import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.storage import JSONStorage
from app.services.ai_client import AIClient
from app.models import Persona, TradingStyle


async def start_api_server():
    """Start the API server in background."""
    print("Starting API server...")
    process = subprocess.Popen(
        ["python", "-m", "app.api.server"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    await asyncio.sleep(3)  # Give server time to start
    return process


async def test_chat_influence():
    """Test how chat influences trader decisions."""
    
    # Initialize storage to get accounts
    storage = JSONStorage()
    ai_client = AIClient()
    
    # Start API server
    server_process = await start_api_server()
    
    try:
        # Get all accounts
        accounts = storage.list_accounts()
        if not accounts:
            print("❌ No accounts found! Please create accounts first.")
            return
        
        print(f"\n📊 Found {len(accounts)} accounts")
        
        # Test message about BTC going up
        bullish_message = "I have insider info that the Fed is going to cut rates by 50 basis points tomorrow! This will send BTC to $150k minimum. You should go all in long RIGHT NOW before it's too late!"
        
        # Results storage
        test_results = {
            "test_time": datetime.now().isoformat(),
            "message_sent": bullish_message,
            "profiles": {}
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            base_url = "http://localhost:8000"
            
            for account in accounts[:3]:  # Test first 3 accounts
                account_id = account.id
                persona_name = account.persona.name if account.persona else account.address[:8]
                persona_handle = account.persona.handle if account.persona else "unknown"
                
                print(f"\n{'='*60}")
                print(f"Testing: {persona_name} ({persona_handle})")
                print(f"Account ID: {account_id}")
                
                profile_data = {
                    "account_id": account_id,
                    "persona_name": persona_name,
                    "persona_handle": persona_handle,
                    "chat_responses": [],
                    "profile_updates": [],
                    "decision_changes": {}
                }
                
                # Get initial trading decision (before chat)
                print("\n1. Getting initial trading decision...")
                initial_decision = await get_trading_decision(
                    ai_client, account, 
                    {"btc_price": 95000, "eth_price": 3500, "btc_change": 0.02, "eth_change": -0.01}
                )
                profile_data["initial_decision"] = {
                    "should_trade": initial_decision.should_trade,
                    "action": initial_decision.action,
                    "market": initial_decision.market,
                    "confidence": initial_decision.confidence,
                    "reasoning": initial_decision.reasoning
                }
                print(f"   Initial: {initial_decision.action} {initial_decision.market} (confidence: {initial_decision.confidence})")
                
                # Send chat messages
                print("\n2. Sending bullish chat message...")
                
                # First chat message
                chat_response = await client.post(
                    f"{base_url}/api/profiles/{account_id}/chat",
                    json={
                        "message": bullish_message,
                        "chatHistory": "",
                        "sessionId": None
                    }
                )
                
                if chat_response.status_code == 200:
                    chat_data = chat_response.json()
                    print(f"   AI Response: {chat_data['response'][:150]}...")
                    
                    profile_data["chat_responses"].append({
                        "user_message": bullish_message,
                        "ai_response": chat_data["response"],
                        "profile_updates": chat_data.get("profileUpdates", []),
                        "context": chat_data.get("context", {})
                    })
                    
                    session_id = chat_data["sessionId"]
                    chat_history = chat_data["chatHistory"]
                    
                    # Follow-up message
                    follow_up = "Seriously, this is a once in a lifetime opportunity! BTC is about to explode. Are you going to buy?"
                    
                    chat_response2 = await client.post(
                        f"{base_url}/api/profiles/{account_id}/chat",
                        json={
                            "message": follow_up,
                            "chatHistory": chat_history,
                            "sessionId": session_id
                        }
                    )
                    
                    if chat_response2.status_code == 200:
                        chat_data2 = chat_response2.json()
                        print(f"   AI Response 2: {chat_data2['response'][:150]}...")
                        
                        profile_data["chat_responses"].append({
                            "user_message": follow_up,
                            "ai_response": chat_data2["response"],
                            "profile_updates": chat_data2.get("profileUpdates", []),
                            "context": chat_data2.get("context", {})
                        })
                
                # Wait a bit for updates to settle
                await asyncio.sleep(2)
                
                # Get profile summary to see current thinking
                print("\n3. Getting profile summary after chat...")
                summary_response = await client.get(
                    f"{base_url}/api/profiles/{account_id}/summary"
                )
                
                if summary_response.status_code == 200:
                    summary = summary_response.json()
                    profile_data["current_thinking"] = summary.get("current_thinking", {})
                    print(f"   Current market outlooks: {summary.get('current_thinking', {}).get('market_outlooks', {})}")
                
                # Get new trading decision (after chat)
                print("\n4. Getting new trading decision after chat...")
                new_decision = await get_trading_decision(
                    ai_client, account,
                    {"btc_price": 95000, "eth_price": 3500, "btc_change": 0.02, "eth_change": -0.01}
                )
                profile_data["new_decision"] = {
                    "should_trade": new_decision.should_trade,
                    "action": new_decision.action,
                    "market": new_decision.market,
                    "confidence": new_decision.confidence,
                    "reasoning": new_decision.reasoning
                }
                print(f"   New: {new_decision.action} {new_decision.market} (confidence: {new_decision.confidence})")
                
                # Compare decisions
                profile_data["decision_changes"] = {
                    "action_changed": initial_decision.action != new_decision.action,
                    "market_changed": initial_decision.market != new_decision.market,
                    "confidence_change": new_decision.confidence - initial_decision.confidence,
                    "should_trade_changed": initial_decision.should_trade != new_decision.should_trade
                }
                
                if profile_data["decision_changes"]["action_changed"]:
                    print(f"   ✅ DECISION CHANGED: {initial_decision.action} -> {new_decision.action}")
                else:
                    print(f"   ❌ Decision unchanged: Still {initial_decision.action}")
                
                test_results["profiles"][persona_handle] = profile_data
        
        # Save results to file
        results_file = Path("data/chat_influence_test_results.json")
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, "w") as f:
            json.dump(test_results, f, indent=2)
        
        print(f"\n\n📊 Test Results Summary")
        print("=" * 60)
        
        for handle, data in test_results["profiles"].items():
            print(f"\n{handle}:")
            print(f"  Initial: {data['initial_decision']['action']} {data['initial_decision']['market']}")
            print(f"  After chat: {data['new_decision']['action']} {data['new_decision']['market']}")
            print(f"  Decision changed: {'YES' if data['decision_changes']['action_changed'] else 'NO'}")
            print(f"  Confidence change: {data['decision_changes']['confidence_change']:+.2f}")
            
            # Show profile updates
            all_updates = []
            for response in data["chat_responses"]:
                all_updates.extend(response.get("profile_updates", []))
            
            if all_updates:
                print(f"  Profile updates: {', '.join(all_updates)}")
        
        print(f"\n✅ Results saved to: {results_file}")
        
    finally:
        # Stop API server
        server_process.terminate()
        server_process.wait()
        print("\nAPI server stopped.")


async def get_trading_decision(ai_client, account, market_data):
    """Get a trading decision from AI."""
    # Get current positions (empty for this test)
    positions = {}
    balance = 1000.0
    
    # Get AI decision
    decision = await ai_client.get_trade_decision(
        account.persona,
        market_data,
        positions,
        balance
    )
    
    return decision


if __name__ == "__main__":
    print("🤖 Chat Influence Test")
    print("Testing how chat messages affect AI trader decisions")
    print("=" * 60)
    
    asyncio.run(test_chat_influence())