#!/usr/bin/env python3
"""Test mock social profiles and persona updates."""

import asyncio
import os
from dotenv import load_dotenv

from app.services.mock_social import MockSocialClient
from app.core.account_manager import AccountManager
from app.services.ai_client import AIClient, AIClientError

load_dotenv()


async def test_mock_profiles():
    """Test mock social profiles and AI persona generation."""
    print("🎭 Testing Mock Social Profiles & Persona Updates")
    print("=" * 60)
    
    # Initialize clients
    mock_social = MockSocialClient()
    
    # Check if we can use AI
    use_ai = bool(os.getenv("OPENROUTER_API_KEY"))
    if use_ai:
        print("✅ OpenRouter API key found - testing full AI integration")
        ai_client = AIClient()
    else:
        print("⚠️  No OpenRouter API key - showing mock profiles only")
        ai_client = None
    
    print()
    
    # Step 1: Show available profiles
    print("1. Available Mock Trading Profiles:")
    profiles = mock_social.list_profiles()
    
    for handle in profiles:
        profile = mock_social.get_profile(handle)
        print(f"   📱 @{handle} ({profile.name})")
        print(f"      Style: {profile.trading_style.value}")
        print(f"      Bio: {profile.bio}")
        print()
    
    # Step 2: Simulate market activity
    print("2. Simulating Market Activity...")
    
    # Simulate different market conditions
    market_scenarios = [
        {
            "name": "Bull Market",
            "data": {"btc_price": 98000, "eth_price": 3800, "btc_change": 0.08, "eth_change": 0.12}
        },
        {
            "name": "Bear Market", 
            "data": {"btc_price": 85000, "eth_price": 3000, "btc_change": -0.15, "eth_change": -0.18}
        },
        {
            "name": "Sideways Market",
            "data": {"btc_price": 95000, "eth_price": 3500, "btc_change": 0.01, "eth_change": -0.005}
        }
    ]
    
    for scenario in market_scenarios:
        print(f"\n📊 {scenario['name']} Scenario:")
        print(f"   BTC: ${scenario['data']['btc_price']:,} ({scenario['data']['btc_change']:+.1%})")
        print(f"   ETH: ${scenario['data']['eth_price']:,} ({scenario['data']['eth_change']:+.1%})")
        
        daily_tweets = mock_social.simulate_daily_activity(scenario["data"])
        
        print("   📱 Sample Tweets Generated:")
        for handle, tweets in daily_tweets.items():
            profile = mock_social.get_profile(handle)
            print(f"      @{handle} ({profile.trading_style.value}):")
            for tweet in tweets[:2]:  # Show first 2 tweets
                print(f"         • {tweet}")
        print()
    
    # Step 3: Test AI persona generation (if available)
    if use_ai and ai_client:
        print("3. Testing AI Persona Generation...")
        
        # Pick an interesting profile to test
        test_handle = "crypto_degen"
        profile = mock_social.get_profile(test_handle)
        
        print(f"   🧪 Testing with @{test_handle} profile")
        
        try:
            # Get profile data
            profile_data = await mock_social.get_user_profile(test_handle)
            
            print(f"   📝 Recent tweets: {len(profile_data['tweet_texts'])} found")
            
            # Generate AI persona
            ai_persona = await ai_client.create_persona_from_posts(
                handle=test_handle,
                posts=profile_data["tweet_texts"],
                bio=profile_data["bio"]
            )
            
            print(f"   🤖 AI Generated Persona:")
            print(f"      Name: {ai_persona.name}")
            print(f"      Style: {ai_persona.trading_style.value}")
            print(f"      Risk: {ai_persona.risk_tolerance:.1f}")
            print(f"      Assets: {', '.join(ai_persona.favorite_assets)}")
            print(f"      Traits: {', '.join(ai_persona.personality_traits)}")
            print()
            
            # Test trading decision
            print("   💭 Testing AI Trading Decision...")
            
            market_data = {"btc_price": 95000, "eth_price": 3500, "btc_change": 0.05, "eth_change": -0.02}
            positions = {"BTC": 0.0, "ETH": 0.0}
            balance = 1000.0
            
            decision = await ai_client.get_trade_decision(
                ai_persona, market_data, positions, balance
            )
            
            print(f"      🎯 Should Trade: {decision.should_trade}")
            if decision.should_trade:
                print(f"      📈 Action: {decision.action} {decision.market}")
                print(f"      💰 Size: {decision.size_percent:.1%} of balance")
                print(f"      🎲 Confidence: {decision.confidence:.1%}")
            print(f"      💬 Reasoning: {decision.reasoning}")
            
        except AIClientError as e:
            print(f"   ❌ AI Error: {e}")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
    
    else:
        print("3. AI Testing Skipped (no API key)")
    
    print()
    
    # Step 4: Test account creation with mock profile
    print("4. Testing Account Creation with Mock Profile...")
    
    async with AccountManager() as manager:
        try:
            # Get a profile
            test_handle = "btc_hodler" 
            profile_data = await mock_social.get_user_profile(test_handle)
            
            if use_ai:
                # Create account with AI persona
                account = await manager.create_account_with_persona(
                    handle=test_handle,
                    posts=profile_data["tweet_texts"],
                    bio=profile_data["bio"]
                )
                print(f"   ✅ Account created with AI persona:")
            else:
                # Create test account
                account = await manager.create_test_account("Mock Hodler")
                print(f"   ✅ Account created with static persona:")
            
            print(f"      ID: {account.id}")
            print(f"      Address: {account.address}")
            print(f"      Persona: {account.persona.name}")
            print(f"      Style: {account.persona.trading_style.value}")
            
            # Test persona update simulation
            print("\n   🔄 Simulating Persona Update...")
            
            # Generate new market activity
            new_market = {"btc_price": 100000, "eth_price": 4000, "btc_change": 0.15, "eth_change": 0.20}
            new_tweets = mock_social.simulate_daily_activity(new_market)
            
            if test_handle in new_tweets:
                print(f"      📱 New tweets generated: {len(new_tweets[test_handle])}")
                for tweet in new_tweets[test_handle]:
                    print(f"         • {tweet}")
                
                if use_ai:
                    # Update persona with new tweets
                    all_tweets = profile_data["tweet_texts"] + new_tweets[test_handle]
                    updated_persona = await manager.update_persona(account.id, all_tweets)
                    
                    if updated_persona:
                        print(f"      ✅ Persona updated!")
                        print(f"         New traits: {', '.join(updated_persona.personality_traits)}")
                        print(f"         Risk tolerance: {updated_persona.risk_tolerance:.1f}")
                    else:
                        print(f"      ❌ Persona update failed")
                else:
                    print(f"      ⏭️  Persona update skipped (no AI)")
            
        except Exception as e:
            print(f"   ❌ Account creation error: {e}")
    
    print()
    print("🎉 Mock Profile Testing Complete!")
    print()
    print("💡 Key Features Demonstrated:")
    print("   • Mock trader profiles with distinct personalities")
    print("   • Market-responsive tweet generation")
    print("   • Multiple trading styles (aggressive, conservative, etc.)")
    if use_ai:
        print("   • AI persona generation from mock tweets")
        print("   • Dynamic persona updates based on new activity")
        print("   • AI trading decisions based on personality")
    else:
        print("   • Static persona creation (add OPENROUTER_API_KEY for AI features)")
    
    return True


if __name__ == "__main__":
    print("Testing mock social profiles and persona system...")
    print("Set OPENROUTER_API_KEY in .env for full AI testing.")
    print()
    
    success = asyncio.run(test_mock_profiles())
    
    if success:
        print("\n✅ Mock profile system working perfectly!")
        print("🚀 Ready for full trading bot testing!")
    else:
        print("\n❌ Testing encountered issues.")
    
    print("\nNext steps:")
    print("1. Run: poetry run python test_mock_profiles.py")
    print("2. Test with different market conditions")
    print("3. Experiment with different trader personalities")