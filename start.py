#!/usr/bin/env python3
"""Entry point for running the bot in production with FastAPI."""

import asyncio
import uvicorn
from threading import Thread
import signal
import sys
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import components
from app.api.server import app, set_active_traders
from app.core.parallel_executor import ParallelProfileExecutor

# Global variables
executor = None
fastapi_thread = None
should_exit = False


def run_fastapi():
    """Run FastAPI server in a separate thread."""
    logger.info("Starting FastAPI server on port 8080")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=int(os.environ.get("PORT", "8080")),
        log_level="info"
    )


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    global should_exit
    logger.info("Received shutdown signal, stopping services...")
    should_exit = True
    
    # Stop the executor if running
    if executor and hasattr(executor, 'is_running'):
        executor.is_running = False
    
    # Exit after cleanup
    sys.exit(0)


async def run_trading_bot():
    """Run the enhanced trading bot."""
    global executor
    
    # Get configuration from environment
    dry_run = os.environ.get("TRADING_MODE", "dry").lower() != "live"
    interval = int(os.environ.get("TRADING_INTERVAL", "60"))
    
    logger.info(f"Starting trading bot - Mode: {'DRY RUN' if dry_run else 'LIVE'}, Interval: {interval}s")
    
    # Initialize executor
    executor = ParallelProfileExecutor(dry_run=dry_run)
    
    try:
        # Initialize profiles and market manager
        await executor.initialize()
        
        if not executor.active_profiles:
            logger.warning("No active trading profiles found!")
            logger.info("Trading bot will wait for profiles to be activated via API")
        
        # Track active traders for API
        active_traders = {
            profile.id: True for profile in executor.active_profiles
        }
        set_active_traders(active_traders)
        
        logger.info(f"Trading bot initialized with {len(executor.active_profiles)} active profiles")
        
        # Main trading loop
        cycle_count = 0
        while not should_exit:
            cycle_count += 1
            
            # Run one trading cycle
            await executor.run_cycle()
            
            # Update active traders for API
            active_traders.update({
                profile.id: True for profile in executor.active_profiles
            })
            
            # Wait for next cycle
            await asyncio.sleep(interval)
            
    except Exception as e:
        logger.error(f"Trading bot error: {e}")
        raise
    finally:
        # Cleanup
        if executor:
            await executor.rise_client.close()
        logger.info("Trading bot stopped")


async def main():
    """Main runner for production."""
    logger.info("Starting RISE AI Trading Bot")
    logger.info("-" * 60)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start FastAPI in a separate thread
    global fastapi_thread
    fastapi_thread = Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()
    
    # Give FastAPI a moment to start
    await asyncio.sleep(2)
    
    logger.info(f"FastAPI server: http://0.0.0.0:{os.environ.get('PORT', '8080')}")
    logger.info("API docs: http://0.0.0.0:8080/docs")
    logger.info("-" * 60)
    
    # Run trading bot in main async loop
    await run_trading_bot()


if __name__ == "__main__":
    asyncio.run(main())