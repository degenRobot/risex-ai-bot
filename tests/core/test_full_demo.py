#!/usr/bin/env python3
"""Full system demo showing chat influence on trading."""

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


async def main():
    """Run full system demo."""
    print("🚀 RISE AI Trading Bot - Full System Demo")
    print("=" * 60)
    
    # Get test account
    storage = JSONStorage()
    accounts = storage.list_accounts()
    
    if not accounts:
        print("❌ No accounts found")
        return
    
    test_account = accounts[0]
    print(f"\n🧪 Using Account: {test_account.address}")
    print(f"   Persona: {test_account.persona.name}")
    
    # Initialize services
    chat_service = ProfileChatService()
    thought_manager = ThoughtProcessManager()
    ai_client = AIClient()
    
    # 1. Show current market state
    print("\n\n1️⃣ CURRENT MARKET STATE")
    print("=" * 60)
    
    async with RiseClient() as client:
        markets = await client.get_markets()
        
        # Show major markets
        major_markets = {
            1: "BTC/USDC",
            2: "ETH/USDC",
            4: "SOL/USDC",
            7: "SPY/USD",
            8: "TSLA/USD"
        }
        
        market_data = {}
        print("\n📊 Market Prices:")
        for market in markets:
            market_id = market.get('market_id')
            if market_id in major_markets:
                symbol = major_markets[market_id]
                price = float(market.get('last_price', 0))
                change = float(market.get('change_24h', 0))
                
                print(f"   {symbol}: ${price:,.2f} ({change:+.2f})")
                
                # Store for AI
                base = symbol.split('/')[0]
                market_data[f"{base}_price"] = price
                market_data[f"{base}_change"] = change / price if price > 0 else 0
        
        # Check current positions
        print("\n📍 Current Positions:")
        positions = {}
        
        for market_id, symbol in major_markets.items():
            try:
                response = await client._request(
                    "GET", "/v1/account/position",
                    params={"account": test_account.address, "market_id": market_id}
                )
                
                position = response.get("data", {}).get("position", {})
                size_raw = int(position.get("size", 0))
                
                if size_raw != 0:
                    size_human = abs(size_raw / 1e18)
                    side = "Long" if size_raw > 0 else "Short"
                    positions[symbol] = {"size": size_human, "side": side}
                    print(f"   {symbol}: {side} {size_human:.6f}")
            except:
                pass
        
        if not positions:
            print("   No open positions")
    
    # 2. Simulate chat influence
    print("\n\n2️⃣ CHAT INFLUENCE SIMULATION")
    print("=" * 60)
    
    chat_scenarios = [
        {
            "message": "BREAKING: Fed just announced emergency rate cut! 50 basis points! This is huge for risk assets!",
            "context": "bullish_macro"
        },
        {
            "message": "BTC just broke through $90k resistance! Next target $100k? What's your take?",
            "context": "btc_breakout"
        },
        {
            "message": "I'm worried about ETH, lots of selling pressure. Maybe it drops to $2800 before bouncing?",
            "context": "eth_concern"
        }
    ]
    
    for scenario in chat_scenarios:
        print(f"\n🗣️ User: {scenario['message']}")
        
        # Send chat message
        try:
            result = await chat_service.chat_with_profile(
                account_id=test_account.id,
                user_message=scenario['message'],
                chat_history=""
            )
            
            response = result.get('response', 'No response')
            print(f"\n🤖 {test_account.persona.name}: {response[:200]}...")
            
            # Show profile updates
            if 'profileUpdates' in result:
                print(f"\n📝 Profile Updates:")
                for update in result['profileUpdates']:
                    print(f"   - {update}")
            
        except Exception as e:
            print(f"❌ Chat error: {e}")
        
        await asyncio.sleep(2)
    
    # 3. Show thought process evolution
    print("\n\n3️⃣ THOUGHT PROCESS EVOLUTION")
    print("=" * 60)
    
    recent_thoughts = await thought_manager.get_recent_thoughts(
        test_account.id,
        minutes=5
    )
    
    if recent_thoughts:
        print(f"\n💭 Recent Thoughts ({len(recent_thoughts)}):")
        for thought in recent_thoughts[-5:]:  # Last 5
            print(f"\n   [{thought.timestamp}]")
            print(f"   Type: {thought.entry_type}")
            print(f"   Content: {thought.content[:100]}...")
            if thought.impact:
                print(f"   Impact: {thought.impact}")
            print(f"   Confidence: {thought.confidence:.2f}")
    else:
        print("\n   No recent thoughts recorded")
    
    # 4. Get trading decision
    print("\n\n4️⃣ AI TRADING DECISION")
    print("=" * 60)
    
    print("\n🤔 AI Analysis based on chat influence and market data...")
    
    try:
        decision = await ai_client.get_trade_decision(
            test_account.persona,
            market_data,
            positions,
            1000.0  # Test balance
        )
        
        if decision:
            print(f"\n   Decision: {'TRADE' if decision.should_trade else 'HOLD'}")
            if decision.should_trade:
                print(f"   Action: {decision.action.upper()}")
                print(f"   Market: {decision.market}")
                print(f"   Size: {decision.size_percent:.1%} of balance")
                print(f"   Confidence: {decision.confidence:.0%}")
                print(f"\n   Reasoning: {decision.reasoning}")
                
                # Log to thought process
                await thought_manager.add_entry(
                    account_id=test_account.id,
                    entry_type="trading_decision",
                    source="ai_analysis",
                    content=f"Decided to {decision.action} {decision.market}",
                    impact=decision.reasoning,
                    confidence=decision.confidence,
                    details={
                        "action": decision.action,
                        "market": decision.market,
                        "size_percent": decision.size_percent
                    }
                )
            else:
                print(f"   Reasoning: {decision.reasoning}")
                
    except Exception as e:
        print(f"   Error: {e}")
    
    # 5. Summary and improvements
    print("\n\n5️⃣ SYSTEM ANALYSIS")
    print("=" * 60)
    
    print("\n✅ Working Features:")
    print("- Market data for 12 markets (6 crypto, 6 stocks)")
    print("- Position tracking with size and side")
    print("- Chat system with personality-based responses")
    print("- Basic thought process logging")
    print("- AI trading decisions based on market data")
    
    print("\n🔧 Suggested Improvements:")
    
    print("\n1. Enhanced Thought Process with Price Targets:")
    print("   Current: 'Considering bullish BTC stance'")
    print("   Better: 'BTC target: $95k by 4pm based on Fed news (85% confidence)'")
    
    print("\n2. Multi-Market Consideration:")
    print("   - Add correlation analysis (BTC pump → ETH/SOL follow)")
    print("   - Consider stock markets for macro signals")
    print("   - Position sizing across all 12 markets")
    
    print("\n3. More Granular Chat Tools:")
    print("   - set_price_target(asset, price, timeframe)")
    print("   - update_stop_loss(asset, price)")
    print("   - set_market_bias(asset, bias, confidence)")
    
    print("\n4. Data Structure Improvements:")
    print("   - Centralized market data manager (30s updates)")
    print("   - Position limits per market")
    print("   - Correlation tracking between markets")
    
    # Show data persistence
    print("\n\n💾 Data Persistence Check:")
    data_files = ["accounts.json", "thought_processes.json", "chat_sessions.json", "trading_decisions.json"]
    for file in data_files:
        path = Path("data") / file
        if path.exists():
            size = path.stat().st_size
            print(f"   ✅ {file} ({size} bytes)")
        else:
            print(f"   ❌ {file} (missing)")


if __name__ == "__main__":
    asyncio.run(main())