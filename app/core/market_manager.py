"""Global market data manager - singleton pattern for efficient data sharing."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from threading import Lock

from ..services.rise_client import RiseClient


class GlobalMarketManager:
    """Singleton manager for market data shared across all trading profiles."""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.rise_client = RiseClient()
            self.market_cache = {}
            self.last_update = None
            self.update_interval = 30  # seconds
            self.logger = logging.getLogger(__name__)
            self._update_lock = asyncio.Lock()
            self.initialized = True
    
    async def get_latest_data(self, force_update: bool = False) -> Dict[str, any]:
        """Get latest market data, updating if stale or forced."""
        async with self._update_lock:
            now = datetime.now()
            
            # Check if update needed
            needs_update = (
                force_update or 
                not self.last_update or 
                (now - self.last_update) > timedelta(seconds=self.update_interval)
            )
            
            if needs_update:
                await self._update_market_data()
            
            return self.market_cache.copy()
    
    async def _update_market_data(self):
        """Fetch latest market data from RISE API."""
        try:
            self.logger.info("🔄 Updating global market data...")
            
            # Get enhanced market data with prices and changes
            enhanced_data = await self.rise_client.get_enhanced_market_data()
            
            # Get full markets list
            markets = await self.rise_client.get_markets()
            
            # Get additional market metrics
            btc_id = enhanced_data.get("btc_market_id", 1)
            eth_id = enhanced_data.get("eth_market_id", 2)
            
            # Try to get volume data
            btc_volume = 0
            eth_volume = 0
            for market in markets:
                if int(market.get("market_id", 0)) == btc_id:
                    btc_volume = float(market.get("volume_24h", 0))
                elif int(market.get("market_id", 0)) == eth_id:
                    eth_volume = float(market.get("volume_24h", 0))
            
            # Update cache with all data
            self.market_cache = {
                # Prices
                "btc_price": enhanced_data.get("btc_price", 0),
                "eth_price": enhanced_data.get("eth_price", 0),
                
                # Changes
                "btc_change": enhanced_data.get("btc_change", 0),
                "eth_change": enhanced_data.get("eth_change", 0),
                
                # Market IDs
                "btc_market_id": btc_id,
                "eth_market_id": eth_id,
                
                # Additional data
                "btc_high_24h": enhanced_data.get("btc_high_24h", 0),
                "btc_low_24h": enhanced_data.get("btc_low_24h", 0),
                "eth_high_24h": enhanced_data.get("eth_high_24h", 0),
                "eth_low_24h": enhanced_data.get("eth_low_24h", 0),
                
                # Volume
                "btc_volume_24h": btc_volume,
                "eth_volume_24h": eth_volume,
                
                # All markets reference
                "markets": markets,
                
                # Metadata
                "last_update": datetime.now(),
                "update_count": self.market_cache.get("update_count", 0) + 1
            }
            
            self.last_update = datetime.now()
            
            # Log summary
            self.logger.info(
                f"✅ Market data updated: "
                f"BTC ${self.market_cache['btc_price']:,.0f} ({self.market_cache['btc_change']:+.1%}), "
                f"ETH ${self.market_cache['eth_price']:,.0f} ({self.market_cache['eth_change']:+.1%})"
            )
            
        except Exception as e:
            self.logger.error(f"❌ Market data update failed: {e}")
            # Keep existing cache if update fails
    
    async def get_market_by_symbol(self, symbol: str) -> Optional[Dict]:
        """Get specific market data by symbol (e.g., 'BTC', 'ETH')."""
        data = await self.get_latest_data()
        
        # Direct price lookup
        price_key = f"{symbol.lower()}_price"
        if price_key in data:
            return {
                "symbol": symbol,
                "price": data[price_key],
                "change_24h": data.get(f"{symbol.lower()}_change", 0),
                "market_id": data.get(f"{symbol.lower()}_market_id"),
                "high_24h": data.get(f"{symbol.lower()}_high_24h"),
                "low_24h": data.get(f"{symbol.lower()}_low_24h"),
                "volume_24h": data.get(f"{symbol.lower()}_volume_24h", 0)
            }
        
        # Search in markets list
        for market in data.get("markets", []):
            if market.get("base_asset_symbol", "").startswith(symbol):
                return market
        
        return None
    
    def get_market_summary(self) -> Dict[str, str]:
        """Get human-readable market summary."""
        if not self.market_cache:
            return {"status": "No market data available"}
        
        btc_price = self.market_cache.get("btc_price", 0)
        eth_price = self.market_cache.get("eth_price", 0)
        btc_change = self.market_cache.get("btc_change", 0)
        eth_change = self.market_cache.get("eth_change", 0)
        
        return {
            "btc": f"${btc_price:,.0f} ({btc_change:+.1%})",
            "eth": f"${eth_price:,.0f} ({eth_change:+.1%})",
            "last_update": self.last_update.strftime("%H:%M:%S") if self.last_update else "Never"
        }
    
    async def start_background_updates(self):
        """Start background task to update market data periodically."""
        async def update_loop():
            while True:
                try:
                    await self.get_latest_data(force_update=True)
                except Exception as e:
                    self.logger.error(f"Background update error: {e}")
                
                await asyncio.sleep(self.update_interval)
        
        # Start background task
        asyncio.create_task(update_loop())
        self.logger.info(f"📡 Started market data updates every {self.update_interval}s")
    
    async def close(self):
        """Cleanup resources."""
        await self.rise_client.close()


# Convenience function to get singleton instance
def get_market_manager() -> GlobalMarketManager:
    """Get the global market manager instance."""
    return GlobalMarketManager()