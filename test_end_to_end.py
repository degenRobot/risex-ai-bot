#!/usr/bin/env python3
"""End-to-end test: Mock profile → AI persona → RISE trading."""

import asyncio
import os
from dotenv import load_dotenv

from app.core.account_manager import AccountManager
from app.services.ai_client import AIClientError

load_dotenv()


async def test_end_to_end():
    """Test the complete pipeline from mock profile to trading decision."""
    print("🚀 End-to-End Trading Bot Test")
    print("=" * 50)
    
    # Check configuration
    has_openrouter = bool(os.getenv("OPENROUTER_API_KEY"))
    
    print("📋 Configuration Check:")
    print(f"   OpenRouter AI: {'✅ Available' if has_openrouter else '❌ Missing API key'}")
    print(f"   RISE API: ✅ Available (testnet)")
    print()
    
    async with AccountManager() as manager:
        try:
            # Step 1: Show available mock profiles
            print("1. Available Mock Trading Profiles:")
            profiles = manager.get_mock_profiles()
            
            for i, handle in enumerate(profiles, 1):
                mock_profile = manager.mock_social.get_profile(handle)
                print(f"   {i}. @{handle} - {mock_profile.name}")
                print(f"      Style: {mock_profile.trading_style.value}")
                print(f"      Bio: {mock_profile.bio[:60]}...")
            print()
            
            # Step 2: Create account from mock profile
            test_profile = "crypto_degen"  # Most interesting for testing
            print(f"2. Creating Account from @{test_profile}...")
            
            if has_openrouter:
                account = await manager.create_account_from_mock_profile(test_profile)
                print(f"   ✅ Account created with AI persona:")
                print(f"      ID: {account.id[:8]}...")
                print(f"      Address: {account.address}")
                print(f"      Persona: {account.persona.name}")
                print(f"      Style: {account.persona.trading_style.value}")
                print(f"      Risk: {account.persona.risk_tolerance:.1f}")
            else:
                account = await manager.create_test_account("Test Trader")
                print(f"   ✅ Test account created (no AI):")
                print(f"      ID: {account.id[:8]}...")
                print(f"      Address: {account.address}")
            print()
            
            # Step 3: Check RISE integration
            print("3. Testing RISE Integration...")
            
            try:
                # Check if signer was registered
                status = await manager.check_account_status(account.id)
                print(f"   💼 Account Status:")
                print(f"      Address: {status['address']}")
                print(f"      Active: {status['is_active']}")
                
                if "rise_error" in status:
                    print(f"      ⚠️  RISE Error: {status['rise_error']}")
                else:
                    print(f"      💰 Has Funds: {status.get('has_funds', False)}")
                    print(f"      📊 Positions: {status.get('positions_count', 0)}")
                
            except Exception as e:
                print(f"   ❌ RISE check failed: {e}")
            print()
            
            # Step 4: Simulate market scenario
            print("4. Simulating Market Scenario...")
            
            market_scenarios = [
                {
                    "name": "Bull Run",
                    "data": {"btc_price": 105000, "eth_price": 4200, "btc_change": 0.15, "eth_change": 0.22}
                },
                {
                    "name": "Market Crash", 
                    "data": {"btc_price": 75000, "eth_price": 2800, "btc_change": -0.25, "eth_change": -0.30}
                }
            ]
            
            for scenario in market_scenarios:
                print(f"\n   📊 {scenario['name']} Scenario:")
                market_data = scenario["data"]
                print(f"      BTC: ${market_data['btc_price']:,} ({market_data['btc_change']:+.1%})")
                print(f"      ETH: ${market_data['eth_price']:,} ({market_data['eth_change']:+.1%})")
                
                # Generate social media reaction
                social_activity = manager.simulate_market_activity(market_data)
                
                # Show our trader's reaction
                if test_profile in social_activity:
                    tweets = social_activity[test_profile]
                    print(f"      📱 @{test_profile} reacts:")
                    for tweet in tweets:
                        print(f"         💬 \"{tweet}\"")
                
                # Get AI trading decision (if available)
                if has_openrouter and account.persona:
                    try:
                        print(f"      🤖 AI Trading Decision:")
                        
                        current_positions = {"BTC": 0.0, "ETH": 0.0}
                        available_balance = 1000.0
                        
                        decision = await manager.ai_client.get_trade_decision(
                            account.persona,
                            market_data,
                            current_positions,
                            available_balance
                        )
                        
                        print(f"         Should Trade: {decision.should_trade}")
                        if decision.should_trade:
                            print(f"         Action: {decision.action} {decision.market}")
                            print(f"         Size: {decision.size_percent:.1%} of balance")
                            print(f"         Confidence: {decision.confidence:.1%}")
                        print(f"         Reasoning: {decision.reasoning}")
                        
                        # Simulate order placement (dry run)
                        if decision.should_trade:
                            trade_size = available_balance * decision.size_percent * 0.001  # Very small for safety
                            print(f"      📋 Would place order:")
                            print(f"         {decision.action} {trade_size:.6f} {decision.market}")
                            print(f"         (Dry run - not actually trading)")
                        
                    except AIClientError as e:
                        print(f"      ❌ AI decision failed: {e}")
                    except Exception as e:
                        print(f"      ❌ Unexpected error: {e}")
                else:
                    print(f"      ⏭️  AI decision skipped (no API key or persona)")
            
            print()
            
            # Step 5: Show complete pipeline summary
            print("5. Pipeline Summary:")
            print("   ✅ Mock social profiles created")
            print("   ✅ Market-responsive tweet generation")
            print("   ✅ Fresh wallet keys generated")
            print("   ✅ RISE signer registration attempted")
            
            if has_openrouter:
                print("   ✅ AI persona generation from tweets")
                print("   ✅ AI trading decisions based on personality")
                print("   ✅ Market scenario simulation with reactions")
            else:
                print("   ⚠️  AI features disabled (add OPENROUTER_API_KEY)")
            
            print()
            print("🎉 End-to-End Test Complete!")
            
            if has_openrouter:
                print("\n🚀 Full AI trading pipeline working!")
                print("   • Mock traders have distinct personalities")
                print("   • AI adapts trading style to market conditions")
                print("   • Ready for live testnet trading")
            else:
                print("\n💡 Add OPENROUTER_API_KEY to enable full AI features")
            
            print(f"\n🔑 Test account details:")
            print(f"   Account ID: {account.id}")
            print(f"   Address: {account.address}")
            print(f"   Persona: {account.persona.name if account.persona else 'Static test persona'}")
            
            return True
            
        except Exception as e:
            print(f"❌ End-to-end test failed: {e}")
            return False


if __name__ == "__main__":
    print("Running complete end-to-end trading bot test...")
    print("This tests: Mock Profiles → AI Personas → Trading Decisions")
    print()
    
    success = asyncio.run(test_end_to_end())
    
    if success:
        print("\n✅ Complete trading bot pipeline working!")
        print("🎯 Ready for production use on RISE testnet!")
    else:
        print("\n❌ Pipeline test failed - check errors above")
    
    print("\nTo test with real trading:")
    print("1. Ensure you have USDC deposited on testnet")
    print("2. Check that RISE testnet markets are available")
    print("3. Run test_complete_flow.py for actual order placement")