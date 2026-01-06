#!/usr/bin/env python3
"""Start both API server and trading bot for production deployment."""

import asyncio
import logging
import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_api_server():
    """Run the FastAPI server."""
    import uvicorn

    from app.api.server import app
    
    port = int(os.environ.get("PORT", "8080"))
    host = "0.0.0.0"
    
    logger.info(f"🌐 Starting API server on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        access_log=True,
        log_level="info",
    )


async def run_trading_bot():
    """Run the trading bot."""
    from app.core.parallel_executor import ParallelProfileExecutor
    
    # Get settings from environment
    dry_run = os.environ.get("TRADING_MODE", "dry").lower() != "live"
    interval = int(os.environ.get("TRADING_INTERVAL", "300"))  # 5 minutes default
    
    logger.info("=" * 70)
    logger.info("🚀 RISE AI TRADING BOT")
    logger.info("=" * 70)
    logger.info(f"Mode: {'🧪 DRY RUN' if dry_run else '🚨 LIVE TRADING'}")
    logger.info(f"Cycle Interval: {interval} seconds")
    logger.info("=" * 70)
    
    # Initialize executor
    executor = ParallelProfileExecutor(dry_run=dry_run)
    
    try:
        # Initialize profiles and market manager
        await executor.initialize()
        
        if not executor.active_profiles:
            logger.error("❌ No active trading profiles found!")
            return
        
        logger.info(f"✅ Bot initialized with {len(executor.active_profiles)} active profiles")
        logger.info("📡 Market data updates every 30 seconds")
        logger.info(f"🔄 Trading cycles every {interval} seconds")
        
        # Main loop
        cycle_count = 0
        while True:
            cycle_count += 1
            
            logger.info(f"\n{'='*20} CYCLE #{cycle_count} {'='*20}")
            
            # Run one trading cycle
            await executor.run_cycle()
            
            # Wait for next cycle
            await asyncio.sleep(interval)
            
    except Exception as e:
        logger.error(f"❌ Trading bot error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        await executor.shutdown()
        await executor.rise_client.close()
        logger.info("✅ Trading bot stopped")


def main():
    """Run both API server and trading bot."""
    import threading
    
    # Start trading bot in thread
    bot_thread = threading.Thread(target=lambda: asyncio.run(run_trading_bot()))
    bot_thread.daemon = True
    bot_thread.start()
    
    # Give bot time to start
    import time
    time.sleep(5)
    
    # Run API server in main thread (blocking)
    run_api_server()


if __name__ == "__main__":
    main()