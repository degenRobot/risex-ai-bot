#!/usr/bin/env python3
"""Production script to run the automated trading bot."""

import argparse
import asyncio
import os
import signal
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.account_manager import AccountManager
from app.core.trading_loop import TradingBot

load_dotenv()


async def create_demo_accounts():
    """Create demo accounts for testing."""
    print("🏗️  Creating demo trading accounts...")
    
    async with AccountManager() as manager:
        profiles = ["crypto_degen", "btc_hodler", "trend_master"]
        created = 0
        
        for profile in profiles:
            try:
                if os.getenv("OPENROUTER_API_KEY"):
                    account = await manager.create_account_from_mock_profile(profile)
                    print(f"   ✅ Created {account.persona.name} with AI persona")
                else:
                    account = await manager.create_test_account(f"Demo {profile}")
                    print(f"   ✅ Created {account.persona.name} (static persona)")
                created += 1
            except Exception as e:
                print(f"   ❌ Failed to create {profile}: {e}")
        
        print(f"🎉 Created {created} demo accounts")
        return created


async def run_bot(interval: int, max_position: float, dry_run: bool):
    """Run the trading bot."""
    print("🤖 RISE AI Trading Bot")
    print("=" * 50)
    
    # Check configuration
    if not os.getenv("OPENROUTER_API_KEY"):
        print("⚠️  Warning: OPENROUTER_API_KEY not set - AI features limited")
    
    print("📋 Configuration:")
    print(f"   Interval: {interval} seconds")
    print(f"   Max Position: ${max_position}")
    print(f"   Mode: {'DRY RUN' if dry_run else '🚨 LIVE TRADING'}")
    print()
    
    # Initialize bot
    bot = TradingBot(
        interval_seconds=interval,
        max_position_usd=max_position,
        dry_run=dry_run,
    )
    
    # Check for accounts
    storage = bot.storage
    accounts = storage.list_accounts()
    active_accounts = [acc for acc in accounts if acc.is_active and acc.persona]
    
    if not active_accounts:
        print("❌ No active accounts found!")
        response = input("Create demo accounts? (y/N): ").lower()
        if response == "y":
            await create_demo_accounts()
        else:
            print("Exiting - no accounts to trade with.")
            return
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print(f"\n⚠️  Received signal {signum}, shutting down gracefully...")
        asyncio.create_task(bot.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Run the bot
        await bot.run()
    except Exception as e:
        print(f"❌ Bot error: {e}")
    finally:
        await bot.cleanup()


def main():
    parser = argparse.ArgumentParser(description="RISE AI Trading Bot")
    parser.add_argument(
        "--interval", 
        type=int, 
        default=300, 
        help="Trading interval in seconds (default: 300)",
    )
    parser.add_argument(
        "--max-position", 
        type=float, 
        default=100.0, 
        help="Maximum position size in USD (default: 100.0)",
    )
    parser.add_argument(
        "--live", 
        action="store_true", 
        help="Enable live trading (default: dry run)",
    )
    parser.add_argument(
        "--create-accounts", 
        action="store_true", 
        help="Create demo accounts and exit",
    )
    
    args = parser.parse_args()
    
    if args.create_accounts:
        print("Creating demo accounts...")
        asyncio.run(create_demo_accounts())
        return
    
    # Safety check for live trading
    if args.live:
        print("🚨 WARNING: Live trading mode enabled!")
        print("This will place real orders on RISE testnet.")
        confirmation = input("Are you sure? Type 'YES' to confirm: ")
        if confirmation != "YES":
            print("Cancelled.")
            return
    
    # Run the bot
    try:
        asyncio.run(run_bot(
            interval=args.interval,
            max_position=args.max_position,
            dry_run=not args.live,
        ))
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Bot crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()