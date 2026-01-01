#!/usr/bin/env python3
"""Test AI persona generation and account management."""

import asyncio
import os
from dotenv import load_dotenv

from app.core.account_manager import AccountManager
from app.services.ai_client import AIClientError

load_dotenv()


async def test_ai_persona():
    """Test AI persona generation and account creation."""
    print("🤖 Testing AI Persona Generation")
    print("=" * 50)
    
    # Check OpenRouter API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("⚠️  OPENROUTER_API_KEY not found in .env")
        print("   Creating test account with static persona...")
        use_ai = False
    else:
        print(f"✅ OpenRouter API key found: {api_key[:10]}...")
        use_ai = True
    
    print()
    
    async with AccountManager() as manager:
        try:
            if use_ai:
                # Test 1: Create account with AI persona
                print("1. Creating account with AI-generated persona...")
                
                sample_posts = [
                    "Just bought more BTC on the dip! Diamond hands 💎🙌",
                    "Market looking volatile but I'm staying long-term focused",
                    "DCA is the way. Slow and steady wins the race",
                    "Not financial advice but ETH looks strong here",
                    "Been studying charts all morning, bullish pattern forming"
                ]
                
                account = await manager.create_account_with_persona(
                    handle="crypto_enthusiast",
                    posts=sample_posts,
                    bio="Crypto trader focused on long-term growth"
                )
                
                print(f"   ✅ Account created: {account.id}")
                print(f"   👤 Persona: {account.persona.name}")
                print(f"   📊 Style: {account.persona.trading_style.value}")
                print(f"   🎲 Risk: {account.persona.risk_tolerance:.1f}")
                print(f"   💰 Assets: {', '.join(account.persona.favorite_assets)}")
                print(f"   🧠 Traits: {', '.join(account.persona.personality_traits)}")
                print()
                
                # Test 2: Generate trade decision
                print("2. Testing AI trade decision...")
                
                market_data = {
                    "btc_price": 95000,
                    "eth_price": 3500,
                    "btc_change": 0.05,  # 5% up
                    "eth_change": -0.02  # 2% down
                }
                
                current_positions = {"BTC": 0.0, "ETH": 0.0}
                available_balance = 1000.0
                
                decision = await manager.ai_client.get_trade_decision(
                    account.persona,
                    market_data,
                    current_positions,
                    available_balance
                )
                
                print(f"   🤔 Should trade: {decision.should_trade}")
                if decision.should_trade:
                    print(f"   📈 Action: {decision.action} {decision.market}")
                    print(f"   💵 Size: {decision.size_percent:.1%} of balance")
                    print(f"   🎯 Confidence: {decision.confidence:.1%}")
                print(f"   💭 Reasoning: {decision.reasoning}")
                print()
            
            else:
                # Test without AI - create static persona
                print("1. Creating test account (no AI)...")
                
                account = await manager.create_test_account("Conservative Tester")
                
                print(f"   ✅ Account created: {account.id}")
                print(f"   👤 Persona: {account.persona.name}")
                print(f"   📊 Style: {account.persona.trading_style.value}")
                print()
            
            # Test 3: Check account status
            print("3. Checking account status...")
            
            status = await manager.check_account_status(account.id)
            print(f"   🏦 Address: {status['address']}")
            print(f"   👤 Persona: {status['persona']}")
            print(f"   🟢 Active: {status['is_active']}")
            
            if "rise_error" in status:
                print(f"   ⚠️  RISE status: {status['rise_error']}")
            else:
                print(f"   💰 Has funds: {status.get('has_funds', False)}")
                print(f"   📊 Positions: {status.get('positions_count', 0)}")
            print()
            
            # Test 4: List all accounts
            print("4. Listing all accounts...")
            accounts = await manager.list_accounts()
            print(f"   📋 Total accounts: {len(accounts)}")
            
            for acc in accounts[-3:]:  # Show last 3
                persona_name = acc.persona.name if acc.persona else "No persona"
                print(f"   • {acc.id[:8]}... - {persona_name}")
            print()
            
            print("🎉 AI persona test completed!")
            
            if use_ai:
                print("✅ AI persona generation working")
                print("✅ Trade decision AI working")
            else:
                print("✅ Static persona creation working")
                print("💡 Add OPENROUTER_API_KEY to test AI features")
            
            print("✅ Account management working")
            print("✅ Storage system working")
            
            return account
            
        except AIClientError as e:
            print(f"❌ AI Client Error: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None


if __name__ == "__main__":
    print("Testing AI persona generation and account management...")
    print("Set OPENROUTER_API_KEY in .env to test AI features.")
    print()
    
    account = asyncio.run(test_ai_persona())
    
    if account:
        print(f"\n🔑 Test account created successfully!")
        print(f"   Account ID: {account.id}")
        print(f"   Address: {account.address}")
        print(f"   Persona: {account.persona.name}")
        print("\n💡 You can now test trading with this account.")
    else:
        print("\n❌ Test failed. Check error messages above.")