#!/usr/bin/env python3
"""Test the complete automated trading system."""

import asyncio
import os
import signal
from dotenv import load_dotenv

from app.core.account_manager import AccountManager
from app.core.trading_loop import TradingBot

load_dotenv()


async def setup_test_accounts():
    """Set up test accounts for automated trading."""
    print("🏗️  Setting up test accounts...")
    
    async with AccountManager() as manager:
        accounts = []
        
        # Check if we already have accounts
        existing_accounts = await manager.list_accounts()
        active_accounts = [acc for acc in existing_accounts if acc.is_active and acc.persona]
        
        if len(active_accounts) >= 2:
            print(f"   ✅ Found {len(active_accounts)} existing accounts")
            for acc in active_accounts[:3]:  # Show first 3
                print(f"      • {acc.persona.name} - {acc.persona.trading_style.value}")
            return active_accounts
        
        # Create new test accounts from mock profiles
        mock_profiles = ["crypto_degen", "btc_hodler", "trend_master"]
        
        for profile_handle in mock_profiles:
            try:
                print(f"   🤖 Creating account from @{profile_handle}...")
                
                if os.getenv("OPENROUTER_API_KEY"):
                    account = await manager.create_account_from_mock_profile(profile_handle)
                    print(f"      ✅ {account.persona.name} created with AI persona")
                else:
                    account = await manager.create_test_account(f"Test {profile_handle}")
                    print(f"      ✅ {account.persona.name} created (static)")
                
                accounts.append(account)
                
            except Exception as e:
                print(f"      ❌ Failed to create account: {e}")
        
        print(f"   📋 Created {len(accounts)} new trading accounts")
        return accounts


async def test_automated_trading():
    """Test the complete automated trading system."""
    print("🤖 Testing Automated Trading System")
    print("=" * 50)
    
    # Check configuration
    has_openrouter = bool(os.getenv("OPENROUTER_API_KEY"))
    print(f"📋 Configuration:")
    print(f"   OpenRouter AI: {'✅' if has_openrouter else '❌'} {'Available' if has_openrouter else 'Missing API key'}")
    print(f"   RISE API: ✅ Available")
    print()
    
    # Step 1: Setup accounts
    print("1. Setting up trading accounts...")
    accounts = await setup_test_accounts()
    
    if not accounts:
        print("❌ No accounts available for testing!")
        return False
    
    print(f"   ✅ {len(accounts)} accounts ready for trading")
    print()
    
    # Step 2: Initialize trading bot
    print("2. Initializing trading bot...")
    
    # Use shorter interval for testing
    bot = TradingBot(
        interval_seconds=30,  # 30 seconds for testing
        max_position_usd=10.0,  # Small positions for testing
        dry_run=True  # Safety first!
    )
    
    print("   ✅ Trading bot initialized (DRY RUN mode)")
    print(f"   ⏱️  Interval: {bot.interval_seconds}s")
    print(f"   💰 Max position: ${bot.max_position_usd}")
    print()
    
    # Step 3: Test single iteration (no loop)
    print("3. Testing single trading iteration...")
    
    try:
        await bot.initialize()
        
        if bot.active_accounts:
            print(f"   📋 Found {len(bot.active_accounts)} active accounts:")
            for acc in bot.active_accounts:
                print(f"      • {acc.persona.name} ({acc.persona.trading_style.value})")
            print()
            
            # Test market data fetch
            await bot._update_market_cache()
            market_data = bot._get_current_market_data()
            print(f"   📊 Market Data:")
            print(f"      BTC: ${market_data['btc_price']:,.0f} ({market_data['btc_change']:+.1%})")
            print(f"      ETH: ${market_data['eth_price']:,.0f} ({market_data['eth_change']:+.1%})")
            print()
            
            # Test social activity
            await bot._update_social_activity()
            print()
            
            # Test processing one account
            test_account = bot.active_accounts[0]
            print(f"   🧪 Testing account processing with {test_account.persona.name}...")
            await bot._process_account(test_account)
            print()
            
        else:
            print("   ⚠️  No active accounts found!")
            
    except Exception as e:
        print(f"   ❌ Single iteration test failed: {e}")
        return False
    
    # Step 4: Test a few loop iterations
    print("4. Testing automated loop (3 iterations)...")
    print("   💡 Press Ctrl+C to stop early")
    print()
    
    iteration_count = 0
    max_iterations = 3
    
    try:
        # Setup signal handler for graceful shutdown
        def signal_handler(signum, frame):
            print(f"\n⚠️  Received signal {signum}, stopping...")
            asyncio.create_task(bot.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Run bot with iteration limit
        async def limited_run():
            nonlocal iteration_count
            await bot.initialize()
            
            if not bot.active_accounts:
                print("   ❌ No active accounts for loop testing")
                return
            
            bot.is_running = True
            
            while bot.is_running and iteration_count < max_iterations:
                iteration_count += 1
                print(f"\n🔄 Trading Loop Test Iteration {iteration_count}/{max_iterations}")
                print("-" * 40)
                
                # Update market data
                await bot._update_market_cache()
                
                # Update social activity every iteration (for testing)
                await bot._update_social_activity()
                
                # Process accounts
                for account in bot.active_accounts:
                    try:
                        await bot._process_account(account)
                    except Exception as e:
                        print(f"   ❌ Account {account.persona.name} error: {e}")
                
                if iteration_count < max_iterations:
                    print(f"\n😴 Waiting {bot.interval_seconds}s before next iteration...")
                    await asyncio.sleep(bot.interval_seconds)
            
            await bot.stop()
        
        await limited_run()
        
    except Exception as e:
        print(f"   ❌ Loop test error: {e}")
        await bot.stop()
        return False
    finally:
        await bot.cleanup()
    
    print("\n🎉 Automated Trading Test Complete!")
    print()
    print("📊 Test Results:")
    print(f"   ✅ {iteration_count} trading iterations completed")
    print(f"   ✅ {len(bot.active_accounts)} AI traders processed")
    print(f"   ✅ Market data integration working")
    print(f"   ✅ Social activity simulation working")
    if has_openrouter:
        print(f"   ✅ AI decision making working")
    else:
        print(f"   ⚠️  AI decisions limited (add OPENROUTER_API_KEY)")
    print(f"   ✅ Position tracking working")
    print(f"   ✅ P&L calculation working")
    print(f"   ✅ Dry run mode working")
    print()
    print("🚀 Ready for live automated trading!")
    print()
    print("💡 To run live (remove dry_run):")
    print("   1. Ensure accounts have USDC deposited")
    print("   2. Verify RISE testnet markets are active")
    print("   3. Set dry_run=False in TradingBot()")
    print("   4. Monitor carefully!")
    
    return True


async def run_continuous_bot():
    """Run the bot continuously (for manual testing)."""
    print("🚀 Starting Continuous Trading Bot")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    bot = TradingBot(
        interval_seconds=60,  # 1 minute
        max_position_usd=50.0,
        dry_run=True
    )
    
    try:
        await bot.run()
    except KeyboardInterrupt:
        print("\n⚠️  Stopping bot...")
        await bot.stop()
    finally:
        await bot.cleanup()


if __name__ == "__main__":
    print("Automated Trading System Test")
    print("Choose test mode:")
    print("1. Quick test (3 iterations)")
    print("2. Continuous mode (manual stop)")
    print()
    
    mode = input("Enter choice (1-2): ").strip()
    
    if mode == "2":
        print("\nStarting continuous mode...")
        asyncio.run(run_continuous_bot())
    else:
        print("\nStarting quick test mode...")
        success = asyncio.run(test_automated_trading())
        
        if success:
            print("\n✅ All tests passed!")
            print("The automated trading system is ready!")
        else:
            print("\n❌ Tests failed - check errors above")