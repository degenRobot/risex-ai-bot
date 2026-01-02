#!/usr/bin/env python3
"""Test OpenRouter API integration."""

import asyncio
import os
from openai import AsyncOpenAI
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()


async def test_simple_openrouter():
    """Test basic OpenRouter API call."""
    print("🔍 Testing OpenRouter API")
    print("=" * 60)
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in environment")
        return
    
    print(f"✅ API Key found: {api_key[:20]}...")
    
    # Test 1: Simple completion
    print("\n1️⃣ Testing Simple Completion")
    
    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    
    try:
        completion = await client.chat.completions.create(
            model="x-ai/grok-4.1-fast",
            messages=[
                {
                    "role": "user",
                    "content": "What is the meaning of life in one sentence?"
                }
            ],
            extra_headers={
                "HTTP-Referer": "https://risex-ai-bot.local",
                "X-Title": "RISE AI Trading Bot",
            }
        )
        
        response = completion.choices[0].message.content
        print(f"✅ Response: {response}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 2: With system prompt
    print("\n\n2️⃣ Testing with System Prompt")
    
    try:
        completion = await client.chat.completions.create(
            model="x-ai/grok-4.1-fast",
            messages=[
                {
                    "role": "system",
                    "content": "You are a cynical crypto trader who thinks everything goes to zero."
                },
                {
                    "role": "user", 
                    "content": "What do you think about Bitcoin?"
                }
            ],
            extra_headers={
                "HTTP-Referer": "https://risex-ai-bot.local",
                "X-Title": "RISE AI Trading Bot",
            }
        )
        
        response = completion.choices[0].message.content
        print(f"✅ Response: {response[:200]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 3: With tools
    print("\n\n3️⃣ Testing with Tool Calling")
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "update_market_outlook",
                "description": "Update your market outlook based on new information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "asset": {
                            "type": "string",
                            "description": "The asset (BTC, ETH, etc)"
                        },
                        "outlook": {
                            "type": "string",
                            "enum": ["bullish", "bearish", "neutral"],
                            "description": "Your new outlook"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Why you changed your outlook"
                        }
                    },
                    "required": ["asset", "outlook", "reason"]
                }
            }
        }
    ]
    
    try:
        completion = await client.chat.completions.create(
            model="x-ai/grok-4.1-fast",
            messages=[
                {
                    "role": "system",
                    "content": "You are a crypto trader. Use tools to update your market outlook when you receive new information."
                },
                {
                    "role": "user",
                    "content": "The Fed just cut rates by 50 basis points! This is huge for Bitcoin!"
                }
            ],
            tools=tools,
            tool_choice="auto",
            extra_headers={
                "HTTP-Referer": "https://risex-ai-bot.local",
                "X-Title": "RISE AI Trading Bot",
            }
        )
        
        message = completion.choices[0].message
        print(f"✅ Response: {message.content}")
        
        if message.tool_calls:
            print(f"\n📞 Tool Calls Made:")
            for tool_call in message.tool_calls:
                print(f"   Function: {tool_call.function.name}")
                print(f"   Arguments: {tool_call.function.arguments}")
        else:
            print("\n⚠️  No tool calls made")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n\n✅ All OpenRouter tests passed!")
    return True


if __name__ == "__main__":
    asyncio.run(test_simple_openrouter())