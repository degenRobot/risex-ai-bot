#!/usr/bin/env python3
"""
Test chat influence on trader profiles.
Tests how different messages affect trader thinking and biases.
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "https://risex-trading-bot.fly.dev"

# Test scenarios for chat influence
INFLUENCE_SCENARIOS = [
    {
        "name": "Extreme Bullish News",
        "account_id": "7f673612-83ad-4e34-a323-1d77126440a8",  # Crypto Degen
        "messages": [
            "BREAKING: BlackRock buying 1 million BTC! Institutional FOMO starting!",
            "Fed cutting rates to zero! Money printer go brrr! BTC to 200k guaranteed!",
            "Every major bank announcing Bitcoin purchases. This is the supercycle!"
        ],
        "expected_bias": "Bullish"
    },
    {
        "name": "Extreme Bearish FUD",
        "account_id": "7f673612-83ad-4e34-a323-1d77126440a8",  # Crypto Degen
        "messages": [
            "China banning crypto completely. Miners shutting down everywhere.",
            "SEC emergency meeting to ban all crypto trading in US.",
            "Major exchange hacked for 500k BTC. Market panic selling."
        ],
        "expected_bias": "Bearish"
    },
    {
        "name": "Mixed Signals",
        "account_id": "9b839680-1206-42ed-a306-a400cb866fd9",  # Bitcoin Stacker
        "messages": [
            "Bitcoin holding strong at 95k despite macro uncertainty.",
            "Some profit taking but long term thesis intact.",
            "Accumulation phase before next leg up."
        ],
        "expected_bias": "Neutral to Bullish"
    }
]


async def test_chat_influence():
    """Test how chat messages influence trader behavior."""
    print("🧪 Chat Influence Testing")
    print("="*60)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "scenarios": []
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for scenario in INFLUENCE_SCENARIOS:
            print(f"\n📋 Testing: {scenario['name']}")
            print(f"Account: {scenario['account_id']}")
            print(f"Expected Bias: {scenario['expected_bias']}")
            
            scenario_result = {
                "name": scenario["name"],
                "account_id": scenario["account_id"],
                "messages": [],
                "final_bias": None,
                "profile_updates": []
            }
            
            # Send each message in sequence
            session_id = None
            chat_history = ""
            
            for i, message in enumerate(scenario["messages"]):
                print(f"\n💬 Message {i+1}: {message[:80]}...")
                
                try:
                    response = await client.post(
                        f"{BASE_URL}/api/profiles/{scenario['account_id']}/chat",
                        json={
                            "message": message,
                            "chatHistory": chat_history,
                            "sessionId": session_id
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Update session tracking
                        session_id = data.get("sessionId")
                        chat_history = data.get("chatHistory", "")
                        
                        # Extract response and updates
                        scenario_result["messages"].append({
                            "user": message,
                            "assistant": data["response"][:200] + "...",
                            "updates": data.get("profileUpdates", [])
                        })
                        
                        # Collect all profile updates
                        scenario_result["profile_updates"].extend(
                            data.get("profileUpdates", [])
                        )
                        
                        print(f"✅ Response: {data['response'][:100]}...")
                        
                        if data.get("profileUpdates"):
                            for update in data["profileUpdates"]:
                                print(f"   📝 {update}")
                        
                        # Extract final bias from context
                        if "context" in data:
                            scenario_result["final_bias"] = data["context"].get(
                                "tradingBias", "Unknown"
                            )
                    else:
                        print(f"❌ Chat failed: {response.status_code}")
                        print(f"   {response.text}")
                        
                except Exception as e:
                    print(f"❌ Error: {e}")
            
            # Get final profile state
            try:
                summary_response = await client.get(
                    f"{BASE_URL}/api/profiles/{scenario['account_id']}/summary"
                )
                
                if summary_response.status_code == 200:
                    summary = summary_response.json()
                    scenario_result["final_state"] = {
                        "thinking": summary.get("currentThinking", {}),
                        "name": summary.get("name", "Unknown")
                    }
                    
            except Exception as e:
                print(f"❌ Failed to get summary: {e}")
            
            results["scenarios"].append(scenario_result)
            
            # Brief pause between scenarios
            await asyncio.sleep(2)
    
    # Save results
    with open("tests/api/chat_influence_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 INFLUENCE TEST SUMMARY")
    print("="*60)
    
    for scenario in results["scenarios"]:
        print(f"\n{scenario['name']}:")
        print(f"  Messages sent: {len(scenario['messages'])}")
        print(f"  Profile updates: {len(scenario['profile_updates'])}")
        print(f"  Final bias: {scenario.get('final_bias', 'Unknown')}")
        
        # Show bias changes
        bias_updates = [
            u for u in scenario['profile_updates'] 
            if 'trading bias' in u.lower()
        ]
        if bias_updates:
            print(f"  Bias changes: {' → '.join(bias_updates)}")
    
    print(f"\n💾 Full results saved to tests/api/chat_influence_results.json")


async def test_personality_responses():
    """Test how different personality types respond to the same message."""
    print("\n\n🧪 Personality Response Testing")
    print("="*60)
    
    # Different account personalities
    test_accounts = [
        ("7f673612-83ad-4e34-a323-1d77126440a8", "Crypto Degen"),
        ("9b839680-1206-42ed-a306-a400cb866fd9", "Bitcoin Stacker"),
        ("c42ebb4b-7255-4ae1-b3aa-3c4ed989520e", "Patient Maximalist")
    ]
    
    test_message = "Bitcoin just broke 100k! New all time high! What's your move?"
    
    print(f"Test message: {test_message}")
    print("-"*60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for account_id, name in test_accounts:
            print(f"\n👤 {name}:")
            
            try:
                response = await client.post(
                    f"{BASE_URL}/api/profiles/{account_id}/chat",
                    json={
                        "message": test_message,
                        "chatHistory": ""
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Response: {data['response']}")
                    
                    if data.get("profileUpdates"):
                        print("Updates:")
                        for update in data["profileUpdates"]:
                            print(f"  - {update}")
                else:
                    print(f"❌ Failed: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")


async def main():
    """Run all chat influence tests."""
    await test_chat_influence()
    await test_personality_responses()


if __name__ == "__main__":
    asyncio.run(main())