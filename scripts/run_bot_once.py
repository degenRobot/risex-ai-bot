#!/usr/bin/env python3
"""Run the trading bot for one cycle to test trading decisions."""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.parallel_executor import ParallelProfileExecutor


async def main():
    """Run one trading cycle."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    print("\n" + "="*70)
    print("🚀 RISE AI TRADING BOT - SINGLE CYCLE TEST")
    print("="*70)
    print("Mode: 🧪 DRY RUN")
    print("Running one trading cycle to test decision making...")
    print("="*70 + "\n")
    
    # Initialize executor
    executor = ParallelProfileExecutor(dry_run=True)
    
    try:
        # Initialize profiles and market manager
        await executor.initialize()
        
        if not executor.active_profiles:
            print("\n❌ No active trading profiles found!")
            return
        
        print(f"\n✅ Bot initialized with {len(executor.active_profiles)} active profiles")
        
        # Run one trading cycle
        print(f"\n{'='*20} TRADING CYCLE {'='*20}")
        await executor.run_cycle()
        
        print("\n✅ Trading cycle complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        await executor.shutdown()
        await executor.rise_client.close()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())