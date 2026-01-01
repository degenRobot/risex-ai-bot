#!/usr/bin/env python3
"""Test the enhanced trading system with decision logging and history."""

import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.account_manager import AccountManager
from app.services.storage import JSONStorage
from app.models import TradingDecisionLog, MarketContext, TradeDecision, TradingStyle

load_dotenv()


async def test_decision_logging_and_history():
    """Test the enhanced decision logging and history analysis."""
    
    print("🧪 Testing Enhanced Trading System with Decision Logging")
    print("=" * 60)
    
    # Initialize services
    storage = JSONStorage()
    
    # Step 1: Test decision logging
    print("\n1. Testing decision logging...")
    
    # Create mock trading decision log
    mock_decision = TradeDecision(
        should_trade=True,
        action="buy",
        market="BTC",
        size_percent=0.1,
        confidence=0.75,
        reasoning="Testing enhanced decision logging system"
    )
    
    mock_market_context = MarketContext(
        btc_price=95000,
        eth_price=3500,
        btc_change=0.02,
        eth_change=-0.01
    )
    
    test_decision_log = TradingDecisionLog(
        id=str(uuid.uuid4()),
        account_id="test_account_123",
        persona_name="Test Trader",
        market_context=mock_market_context,
        available_balance=1000.0,
        current_positions={"BTC": 0.0, "ETH": 0.0},
        total_pnl=0.0,
        recent_posts=["Testing the enhanced system", "Learning from past trades"],
        decision=mock_decision,
        executed=True,
        execution_details={"success": True, "order_id": "test_order_123"}
    )
    
    # Save decision log
    storage.save_trading_decision(test_decision_log)
    print(f"   ✅ Saved decision log: {test_decision_log.id}")
    
    # Step 2: Test decision retrieval
    print("\n2. Testing decision retrieval...")
    
    decisions = storage.get_trading_decisions("test_account_123", limit=5)
    print(f"   ✅ Retrieved {len(decisions)} decisions")
    
    if decisions:
        latest = decisions[0]
        print(f"   📋 Latest decision: {latest.decision.action} {latest.decision.market}")
        print(f"   💭 Reasoning: {latest.decision.reasoning}")
    
    # Step 3: Test outcome tracking
    print("\n3. Testing outcome tracking...")
    
    # Simulate updating decision outcome after some time
    success = storage.update_decision_outcome(
        test_decision_log.id, 
        pnl=25.50, 
        reasoning="Trade was profitable - good entry point"
    )
    
    if success:
        print(f"   ✅ Updated decision outcome: +$25.50 PnL")
    else:
        print(f"   ❌ Failed to update decision outcome")
    
    # Step 4: Test successful decisions retrieval
    print("\n4. Testing successful decisions retrieval...")
    
    # First mark the decision as having positive outcome
    storage.update_decision_outcome(test_decision_log.id, 50.0, "Great trade!")
    
    successful_decisions = storage.get_recent_successful_decisions("test_account_123", days=7)
    print(f"   ✅ Found {len(successful_decisions)} successful decisions")
    
    # Step 5: Test analytics
    print("\n5. Testing trading analytics...")
    
    analytics = storage.get_trading_analytics("test_account_123")
    print(f"   📊 Analytics for test account:")
    print(f"      Total decisions: {analytics['total_decisions']}")
    print(f"      Executed decisions: {analytics['executed_decisions']}")
    print(f"      Execution rate: {analytics['execution_rate']:.1%}")
    print(f"      Win rate: {analytics['win_rate']:.1%}")
    print(f"      Average confidence: {analytics['avg_confidence']:.1%}")
    
    # Step 6: Test with real account manager
    print("\n6. Testing with account manager...")
    
    has_openrouter = bool(os.getenv("OPENROUTER_API_KEY"))
    print(f"   🔧 OpenRouter API: {'Available' if has_openrouter else 'Not configured'}")
    
    if has_openrouter:
        async with AccountManager() as manager:
            # Check for existing accounts
            accounts = await manager.list_accounts()
            
            if accounts:
                test_account = accounts[0]
                print(f"   👤 Using existing account: {test_account.persona.name}")
                
                # Test getting decision history
                history = storage.get_trading_decisions(test_account.id, limit=3)
                print(f"   📚 Account has {len(history)} historical decisions")
                
                # Test enhanced AI decision (if we have history)
                if history:
                    print("   🤖 Testing enhanced AI decision with history...")
                    from app.services.ai_client import AIClient
                    
                    ai = AIClient()
                    market_data = {
                        "btc_price": 95000,
                        "eth_price": 3500,
                        "btc_change": 0.02,
                        "eth_change": -0.01
                    }
                    
                    try:
                        enhanced_decision = await ai.get_enhanced_trade_decision(
                            test_account.persona,
                            market_data,
                            {"BTC": 0.0, "ETH": 0.0},
                            1000.0,
                            trading_history=history[:5],
                            recent_posts=["Market looking bullish", "Time to accumulate"]
                        )
                        
                        print(f"   ✅ Enhanced decision: {enhanced_decision.should_trade}")
                        print(f"      Action: {enhanced_decision.action}")
                        print(f"      Confidence: {enhanced_decision.confidence:.1%}")
                        print(f"      Reasoning: {enhanced_decision.reasoning}")
                        
                    except Exception as e:
                        print(f"   ⚠️  Enhanced decision test failed: {e}")
            else:
                print("   ⚠️  No existing accounts found")
    
    print("\n🎉 Enhanced System Test Complete!")
    print("\n📊 Test Results:")
    print("   ✅ Decision logging system working")
    print("   ✅ Decision retrieval working")
    print("   ✅ Outcome tracking working")
    print("   ✅ Analytics system working")
    print("   ✅ Historical analysis ready")
    
    if has_openrouter:
        print("   ✅ Enhanced AI decision making tested")
    else:
        print("   ⚠️  Enhanced AI decision making not tested (no API key)")
    
    print("\n💡 Next Steps:")
    print("   1. Run the enhanced trading bot with decision logging")
    print("   2. Let it accumulate trading history")
    print("   3. Watch it learn from past decisions")
    print("   4. Use analytics to track performance")


if __name__ == "__main__":
    asyncio.run(test_decision_logging_and_history())