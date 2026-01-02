#!/usr/bin/env python3
"""Test the market manager with markets.json data."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.market_manager import GlobalMarketManager


async def test_market_manager():
    """Test market manager functionality."""
    print("🧪 Testing Market Manager with markets.json")
    print("=" * 60)
    
    # Get singleton instance
    manager = GlobalMarketManager()
    
    # Check loaded markets
    print(f"\n📊 Loaded Markets: {len(manager.markets_data.get('markets', {}))}")
    
    # List all tracked markets
    print("\n🏷️  Tracked Markets:")
    for market in manager.get_tracked_markets():
        status = "✅" if market.get("available") else "❌"
        print(f"   {status} {market['symbol']} (ID: {market['market_id']}) - ${float(market.get('last_price', 0)):,.2f}")
    
    # Test market lookup
    print("\n🔍 Market Lookup Tests:")
    
    # By ID
    btc_by_id = manager.get_market_by_id(1)
    if btc_by_id:
        print(f"   BTC by ID: {btc_by_id['symbol']} - ${float(btc_by_id.get('last_price', 0)):,.2f}")
    
    # By symbol
    eth_by_symbol = manager.get_market_by_symbol("ETH")
    if eth_by_symbol:
        print(f"   ETH by symbol: {eth_by_symbol['symbol']} - ${float(eth_by_symbol.get('last_price', 0)):,.2f}")
    
    # Test market data update
    print("\n🔄 Updating market data...")
    await manager.get_latest_data(force_update=True)
    
    # Show cache
    cache = await manager.get_latest_data()
    print(f"\n💾 Market Cache:")
    print(f"   BTC: ${cache.get('btc_price', 0):,.0f} ({cache.get('btc_change', 0):+.1%})")
    print(f"   ETH: ${cache.get('eth_price', 0):,.0f} ({cache.get('eth_change', 0):+.1%})")
    
    # Clean up
    await manager.close()
    print("\n✅ Market manager test complete!")


async def main():
    """Run the test."""
    await test_market_manager()


if __name__ == "__main__":
    asyncio.run(main())