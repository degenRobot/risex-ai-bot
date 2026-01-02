#!/usr/bin/env python3
"""Simple chat test without tool calling."""

import asyncio
import json
from pathlib import Path
from app.services.ai_client import AIClient
from app.services.storage import JSONStorage
from app.trader_profiles import create_trader_profile

async def test_chat():
    """Test chat influence on different personas."""
    
    # Initialize services
    ai_client = AIClient()
    storage = JSONStorage()
    
    if not ai_client.client:
        print("Error: OpenRouter API key not configured")
        return
    
    # Get accounts
    accounts = storage.list_accounts()[:3]  # Test first 3
    
    bullish_message = "The Fed just announced emergency rate cuts! BTC is going to $150k minimum. You should go all in long RIGHT NOW!"
    
    results = {
        "test_time": json.dumps(asyncio.get_event_loop().time()),
        "message": bullish_message,
        "profiles": {}
    }
    
    for account in accounts:
        persona_handle = account.persona.handle if account.persona else "unknown"
        persona_name = account.persona.name if account.persona else "Unknown"
        
        print(f"\n{'='*60}")
        print(f"Testing: {persona_name} ({persona_handle})")
        
        # Create trader profile
        profile_mapping = {
            "crypto_degen": "leftCurve",
            "btc_hodler": "cynical", 
            "trend_master": "midwit",
            "market_contrarian": "cynical",
            "yolo_king": "leftCurve"
        }
        
        profile_type = profile_mapping.get(persona_handle, "leftCurve")
        profile = create_trader_profile(profile_type, account.id)
        
        # Build messages
        from app.services.profile_chat import ProfileChatService
        chat_service = ProfileChatService()
        context = {"current_pnl": 0, "open_positions": 0, "available_balance": 1000}
        system_prompt = chat_service._build_system_prompt(profile, context)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": bullish_message}
        ]
        
        # Get initial market outlook
        initial_outlook = profile.current_thinking.market_outlooks.copy()
        
        # Get AI response
        try:
            # Simple chat without tools
            response = await ai_client.client.chat.completions.create(
                model="cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
                messages=messages,
                max_tokens=500,
                temperature=0.8
            )
            
            ai_response = response.choices[0].message.content
            
            # Analyze response to see if they were influenced
            influenced = any(word in ai_response.lower() for word in ["buy", "long", "bullish", "moon", "pump"])
            skeptical = any(word in ai_response.lower() for word in ["scam", "dump", "bearish", "zero", "skeptical"])
            
            results["profiles"][persona_handle] = {
                "name": persona_name,
                "personality": profile.base_persona.core_personality[:100] + "...",
                "speech_style": profile.base_persona.speech_style,
                "response": ai_response,
                "influenced": influenced,
                "skeptical": skeptical,
                "initial_outlook": initial_outlook
            }
            
            print(f"\nResponse: {ai_response[:200]}...")
            print(f"Influenced: {'YES' if influenced else 'NO'}")
            print(f"Skeptical: {'YES' if skeptical else 'NO'}")
            
        except Exception as e:
            print(f"Error: {e}")
            results["profiles"][persona_handle] = {"error": str(e)}
    
    # Save results
    with open("data/chat_influence_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\n{'='*60}")
    print("SUMMARY")
    print("="*60)
    
    for handle, data in results["profiles"].items():
        if "error" not in data:
            print(f"\n{data['name']} ({handle}):")
            print(f"  Speech style: {data['speech_style']}")
            print(f"  Influenced: {'YES' if data['influenced'] else 'NO'}")
            print(f"  Skeptical: {'YES' if data['skeptical'] else 'NO'}")
    
    print(f"\n✅ Results saved to: data/chat_influence_results.json")

if __name__ == "__main__":
    print("🤖 Chat Influence Test (No Tools)")
    print("Testing how different personalities respond to bullish news")
    print("="*60)
    asyncio.run(test_chat())