#!/usr/bin/env python3
"""Enhanced trading bot with parallel execution and tool calling."""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.parallel_executor import ParallelProfileExecutor


async def main():
    """Run the enhanced trading bot with parallel profile execution."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    
    # Command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Run enhanced RISE AI trading bot")
    parser.add_argument(
        "--interval", 
        type=int, 
        default=60,
        help="Trading cycle interval in seconds (default: 60)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Run in dry-run mode (no real trades)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run in LIVE mode (real trades)",
    )
    
    args = parser.parse_args()
    
    # Override dry-run if --live is specified
    dry_run = not args.live
    
    print("\n" + "="*70)
    print("🚀 RISE AI TRADING BOT - ENHANCED VERSION")
    print("="*70)
    print(f"Mode: {'🧪 DRY RUN' if dry_run else '🚨 LIVE TRADING'}")
    print(f"Cycle Interval: {args.interval} seconds")
    print("Architecture: Parallel execution with tool calling")
    print("="*70 + "\n")
    
    if not dry_run:
        response = input("⚠️  WARNING: Live trading mode. Continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            return
    
    # Initialize executor
    executor = ParallelProfileExecutor(dry_run=dry_run)
    
    try:
        # Initialize profiles and market manager
        await executor.initialize()
        
        if not executor.active_profiles:
            print("\n❌ No active trading profiles found!")
            print("Please create profiles first using setup_profiles.py")
            return
        
        print(f"\n✅ Bot initialized with {len(executor.active_profiles)} active profiles")
        print("📡 Market data will update every 30 seconds")
        print(f"🔄 Trading cycles will run every {args.interval} seconds")
        print("\nPress Ctrl+C to stop the bot\n")
        
        # Main loop
        cycle_count = 0
        while True:
            cycle_count += 1
            
            print(f"\n{'='*20} CYCLE #{cycle_count} {'='*20}")
            
            # Run one trading cycle
            await executor.run_cycle()
            
            # Wait for next cycle
            print(f"\n😴 Waiting {args.interval} seconds until next cycle...")
            await asyncio.sleep(args.interval)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Shutting down trading bot...")
        await executor.shutdown()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        await executor.shutdown()
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        await executor.rise_client.close()
        print("✅ Bot stopped cleanly")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())