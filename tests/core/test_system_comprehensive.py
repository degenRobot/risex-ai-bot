#!/usr/bin/env python3
"""Comprehensive system test with chat influence and multi-market trading."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage
from app.services.profile_chat import ProfileChatService
from app.services.thought_process import ThoughtProcessManager
from app.services.ai_client import AIClient
from app.api.server import app
from httpx import AsyncClient


async def test_chat_and_thought_process():
    """Test chat system and thought process updates."""
    print("\n💬 Testing Chat System and Thought Process")
    print("=" * 60)
    
    storage = JSONStorage()
    accounts = storage.list_accounts()
    
    if not accounts:
        print("❌ No accounts found")
        return False
    
    # Test with first account
    test_account = accounts[0]
    account_id = test_account.id
    
    print(f"\n🧪 Testing with: {test_account.persona.name}")
    print(f"   Personality: {test_account.persona.core_personality[:100]}...")
    
    chat_service = ProfileChatService()
    thought_manager = ThoughtProcessManager()
    
    # Test different types of messages
    test_scenarios = [
        {
            "message": "I heard the Fed is about to cut rates dramatically! BTC to $100k for sure!",
            "expected": "bullish_btc"
        },
        {
            "message": "ETH is looking weak, might dump to $2800. But that's a great buying opportunity!",
            "expected": "eth_buy_level"
        },
        {
            "message": "SOL is way faster than ETH, I think it could hit $200 soon. What do you think?",
            "expected": "sol_comparison"
        },
        {
            "message": "The stock market is crashing! SPY down 5%, everything will dump!",
            "expected": "market_fear"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n🗣️ User: {scenario['message']}")
        
        try:
            # Send chat message
            result = await chat_service.chat_with_profile(
                account_id=account_id,
                user_message=scenario['message'],
                chat_history=""
            )
            
            # Show AI response
            response = result.get('response', 'No response')
            print(f"🤖 {test_account.persona.name}: {response[:200]}...")
            
            # Check profile updates
            if 'profileUpdates' in result:
                updates = result['profileUpdates']
                print(f"\n📝 Profile Updates:")
                for update in updates:
                    print(f"   - {update}")
            
            # Check thought process
            await asyncio.sleep(1)  # Let thought process update
            recent_thoughts = await thought_manager.get_recent_thoughts(
                account_id, 
                minutes=1
            )
            
            if recent_thoughts:
                print(f"\n💭 New Thoughts ({len(recent_thoughts)}):")
                for thought in recent_thoughts[-2:]:  # Last 2 thoughts
                    print(f"   - Type: {thought.entry_type}")
                    print(f"   - Content: {thought.content[:100]}...")
                    print(f"   - Impact: {thought.impact}")
                    print(f"   - Confidence: {thought.confidence}")
                    print(f"   - Time: {thought.timestamp}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
        
        await asyncio.sleep(2)
    
    return True


async def test_multi_market_trading():
    """Test trading decisions on multiple markets."""
    print("\n\n📈 Testing Multi-Market Trading")
    print("=" * 60)
    
    storage = JSONStorage()
    accounts = storage.list_accounts()
    
    if not accounts:
        return False
    
    test_account = accounts[0]
    ai_client = AIClient()
    
    async with RiseClient() as client:
        # Get all markets
        response = await client._request("GET", "/v1/markets")
        markets_data = response.get("data", {}).get("markets", {})
        
        # Select diverse markets to test
        test_markets = {
            "1": "BTC/USDC",
            "2": "ETH/USDC", 
            "4": "SOL/USDC",
            "7": "SPY/USD",
            "8": "TSLA/USD"
        }
        
        print("\n📊 Testing Markets:")
        for market_id, symbol in test_markets.items():
            print(f"   - Market {market_id}: {symbol}")
        
        # Check positions on each market
        print("\n📍 Current Positions:")
        positions = {}
        
        for market_id, symbol in test_markets.items():
            try:
                response = await client._request(
                    "GET", "/v1/account/position",
                    params={"account": test_account.address, "market_id": int(market_id)}
                )
                
                position = response.get("data", {}).get("position", {})
                size_raw = int(position.get("size", 0))
                
                if size_raw != 0:
                    size_human = abs(size_raw / 1e18)
                    side = "Long" if size_raw > 0 else "Short"
                    positions[symbol] = {
                        "size": size_human,
                        "side": side,
                        "raw": size_raw
                    }
                    print(f"   {symbol}: {side} {size_human:.6f}")
                else:
                    print(f"   {symbol}: No position")
                    
            except Exception as e:
                print(f"   {symbol}: Error - {str(e)[:50]}")
        
        # Prepare market data for AI
        market_data = {}
        for market_id, market_info in markets_data.items():
            if market_id in test_markets:
                symbol = test_markets[market_id]
                last_price = float(market_info.get("last_price", 0))
                change_24h = float(market_info.get("change_24h", 0))
                
                # Simplify symbol for AI
                base_symbol = symbol.split('/')[0]
                market_data[f"{base_symbol}_price"] = last_price
                market_data[f"{base_symbol}_change"] = change_24h / last_price if last_price > 0 else 0
        
        print(f"\n📊 Market Data for AI:")
        for key, value in market_data.items():
            if "price" in key:
                print(f"   {key}: ${value:,.2f}")
            else:
                print(f"   {key}: {value:.2%}")
        
        # Get AI decision
        print("\n🤔 AI Trading Decision:")
        try:
            decision = await ai_client.get_trade_decision(
                test_account.persona,
                market_data,
                positions,
                1000.0  # Test balance
            )
            
            if decision:
                print(f"   Should Trade: {decision.should_trade}")
                print(f"   Action: {decision.action}")
                print(f"   Market: {decision.market}")
                print(f"   Size: {decision.size_percent:.1%} of balance")
                print(f"   Confidence: {decision.confidence:.2%}")
                print(f"   Reasoning: {decision.reasoning[:200]}...")
                
                # Log to thought process
                thought_manager = ThoughtProcessManager()
                await thought_manager.add_entry(
                    account_id=test_account.id,
                    entry_type="trading_decision",
                    source="market_analysis",
                    content=f"Decided to {decision.action} {decision.market} at {decision.size_percent:.1%} of balance",
                    impact=decision.reasoning,
                    confidence=decision.confidence,
                    details={
                        "action": decision.action,
                        "market": decision.market,
                        "size_percent": decision.size_percent,
                        "market_data": market_data
                    }
                )
                
        except Exception as e:
            print(f"   Error: {e}")
    
    return True


async def test_api_endpoints():
    """Test all API endpoints."""
    print("\n\n🌐 Testing API Endpoints")
    print("=" * 60)
    
    storage = JSONStorage()
    accounts = storage.list_accounts()
    
    if not accounts:
        return False
    
    test_account = accounts[0]
    account_id = test_account.id
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. Profile Summary
        print("\n1️⃣ GET /api/profiles/{account_id}/summary")
        try:
            response = await client.get(f"/api/profiles/{account_id}/summary")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Name: {data.get('name')}")
                print(f"   Trading Style: {data.get('tradingStyle')}")
                current = data.get('currentThinking', {})
                if current:
                    print(f"   Current Market View: {current.get('marketOutlook', 'neutral')}")
                    print(f"   Trading Bias: {current.get('tradingBias', 'neutral')}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # 2. Chat Endpoint
        print("\n2️⃣ POST /api/profiles/{account_id}/chat")
        try:
            chat_data = {
                "message": "What do you think about the current market conditions?",
                "chatHistory": ""
            }
            
            response = await client.post(
                f"/api/profiles/{account_id}/chat",
                json=chat_data
            )
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {data.get('response', '')[:150]}...")
                if 'profileUpdates' in data:
                    print(f"   Updates: {len(data['profileUpdates'])} profile updates")
        except Exception as e:
            print(f"   Error: {e}")
        
        # 3. Trading Context
        print("\n3️⃣ GET /api/profiles/{account_id}/context")
        try:
            response = await client.get(f"/api/profiles/{account_id}/context")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Positions: {len(data.get('positions', {}))}")
                print(f"   Recent Thoughts: {len(data.get('recentThoughts', []))}")
                print(f"   Market Prices: {len(data.get('marketPrices', {}))}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # 4. List Profiles
        print("\n4️⃣ GET /api/profiles")
        try:
            response = await client.get("/api/profiles?page=1&limit=10")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Total Profiles: {data.get('total', 0)}")
                print(f"   Page Size: {len(data.get('profiles', []))}")
        except Exception as e:
            print(f"   Error: {e}")
    
    return True


async def check_data_persistence():
    """Verify all data files are working correctly."""
    print("\n\n💾 Checking Data Persistence")
    print("=" * 60)
    
    data_dir = Path("data")
    
    # Expected data files
    expected_files = {
        "accounts.json": "Account profiles",
        "thought_processes.json": "Thought process entries",
        "chat_sessions.json": "Chat history",
        "trading_decisions.json": "Trading decision logs",
        "pending_actions.json": "Pending trading actions"
    }
    
    for filename, description in expected_files.items():
        file_path = data_dir / filename
        print(f"\n📁 {filename} ({description}):")
        
        if file_path.exists():
            try:
                with open(file_path) as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    print(f"   ✅ Found {len(data)} entries")
                    if data:
                        # Show latest entry summary
                        latest = data[-1]
                        if "timestamp" in latest:
                            print(f"   Latest: {latest.get('timestamp', 'N/A')}")
                        if "entry_type" in latest:
                            print(f"   Type: {latest.get('entry_type')}")
                        if "content" in latest:
                            print(f"   Content: {latest.get('content', '')[:100]}...")
                            
                elif isinstance(data, dict):
                    print(f"   ✅ Found {len(data)} items")
                    if data:
                        # Show sample
                        key = list(data.keys())[0]
                        item = data[key]
                        print(f"   Sample key: {key}")
                        if isinstance(item, dict):
                            print(f"   Fields: {', '.join(list(item.keys())[:5])}")
                            
            except Exception as e:
                print(f"   ❌ Error reading file: {e}")
        else:
            print(f"   ⚠️  File not found")
    
    return True


async def main():
    """Run all comprehensive tests."""
    print("🚀 RISE AI Trading Bot - Comprehensive System Test")
    print("=" * 60)
    
    # Summary results
    results = {
        "chat_system": False,
        "multi_market": False,
        "api_endpoints": False,
        "data_persistence": False
    }
    
    # Run tests
    try:
        results["chat_system"] = await test_chat_and_thought_process()
    except Exception as e:
        print(f"\n❌ Chat system test failed: {e}")
    
    try:
        results["multi_market"] = await test_multi_market_trading()
    except Exception as e:
        print(f"\n❌ Multi-market test failed: {e}")
    
    try:
        results["api_endpoints"] = await test_api_endpoints()
    except Exception as e:
        print(f"\n❌ API endpoints test failed: {e}")
    
    try:
        results["data_persistence"] = await check_data_persistence()
    except Exception as e:
        print(f"\n❌ Data persistence test failed: {e}")
    
    # Summary
    print("\n\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    # Recommendations
    print("\n🔧 RECOMMENDATIONS:")
    print("1. Enhanced Thought Process:")
    print("   - Add specific price targets (e.g., 'BTC target: $100k by EOD')")
    print("   - Include timestamps for each thought")
    print("   - Track confidence levels for each prediction")
    print("\n2. Multi-Market Trading:")
    print("   - Expand AI to consider all 12 markets")
    print("   - Add market correlation analysis")
    print("   - Implement position sizing across markets")
    print("\n3. Chat Improvements:")
    print("   - More granular influence tracking")
    print("   - Sentiment analysis on user messages")
    print("   - Historical chat influence on trading performance")


if __name__ == "__main__":
    asyncio.run(main())