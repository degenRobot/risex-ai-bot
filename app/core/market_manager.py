"""Global market data manager - singleton pattern for efficient data sharing."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
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
            self.markets_data = {}  # Loaded from markets.json
            self.last_update = None
            self.update_interval = 30  # seconds
            self.logger = logging.getLogger(__name__)
            self._update_lock = asyncio.Lock()
            self._update_task: Optional[asyncio.Task] = None
            self._shutdown = False
            self.initialized = True
            self._load_markets_data()
    
    def _load_markets_data(self):
        """Load markets data from markets.json file."""
        try:
            markets_file = Path(__file__).parent.parent.parent / "data" / "markets.json"
            if markets_file.exists():
                with open(markets_file, "r") as f:
                    self.markets_data = json.load(f)
                    self.logger.info(f"Loaded {len(self.markets_data.get('markets', {}))} markets from markets.json")
            else:
                self.logger.warning("markets.json not found - run scripts/update_markets.py to fetch market data")
                self.markets_data = {"markets": {}, "market_id_map": {}, "symbol_map": {}}
        except Exception as e:
            self.logger.error(f"Failed to load markets.json: {e}")
            self.markets_data = {"markets": {}, "market_id_map": {}, "symbol_map": {}}
    
    async def update_markets_file(self):
        """Update the markets.json file with fresh data from API."""
        try:
            markets = await self.rise_client.get_markets()
            
            markets_data = {
                "last_updated": datetime.utcnow().isoformat(),
                "source": "https://api.testnet.rise.trade/v1/markets",
                "markets": {},
                "market_id_map": {},
                "symbol_map": {}
            }
            
            for market in markets:
                market_id = market.get("market_id")
                base_asset_full = market.get("base_asset_symbol", "")
                base_asset = base_asset_full.split("/")[0] if "/" in base_asset_full else base_asset_full
                symbol = f"{base_asset}-USD" if base_asset else ""
                
                if market_id:
                    markets_data["markets"][str(market_id)] = {
                        "market_id": int(market_id),
                        "symbol": symbol,
                        "base_asset_symbol": base_asset,
                        "base_asset_full": base_asset_full,
                        "available": market.get("available", False),
                        "last_price": market.get("last_price"),
                        "index_price": market.get("index_price"),
                        "min_size": market.get("min_size", "0.0001"),
                        "max_leverage": market.get("max_leverage", "20"),
                        "maker_fee": market.get("maker_fee", "0.0002"),
                        "taker_fee": market.get("taker_fee", "0.0005"),
                    }
                    
                    markets_data["market_id_map"][str(market_id)] = symbol
                    if base_asset:
                        markets_data["symbol_map"][base_asset] = int(market_id)
            
            # Save to file
            markets_file = Path(__file__).parent.parent.parent / "data" / "markets.json"
            markets_file.parent.mkdir(exist_ok=True)
            
            with open(markets_file, "w") as f:
                json.dump(markets_data, f, indent=2)
            
            self.markets_data = markets_data
            self.logger.info(f"Updated markets.json with {len(markets_data['markets'])} markets")
            
        except Exception as e:
            self.logger.error(f"Failed to update markets file: {e}")
    
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
            
            # Update our stored market data with latest prices
            for market in markets:
                market_id_str = str(market.get("market_id"))
                if market_id_str in self.markets_data.get("markets", {}):
                    stored_market = self.markets_data["markets"][market_id_str]
                    stored_market["last_price"] = market.get("last_price")
                    stored_market["index_price"] = market.get("index_price")
                    stored_market["available"] = market.get("available", False)
                    stored_market["daily_volume"] = market.get("daily_volume", "0")
                    stored_market["open_interest"] = market.get("open_interest", "0")
                    stored_market["funding_rate"] = market.get("funding_rate", "0")
            
            # Get market IDs from our data
            btc_id = self.markets_data.get("symbol_map", {}).get("BTC", 1)
            eth_id = self.markets_data.get("symbol_map", {}).get("ETH", 2)
            
            # Get volume data from our stored markets
            btc_market = self.markets_data["markets"].get(str(btc_id), {})
            eth_market = self.markets_data["markets"].get(str(eth_id), {})
            
            btc_volume = float(btc_market.get("daily_volume", 0))
            eth_volume = float(eth_market.get("daily_volume", 0))
            
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
        if self._update_task and not self._update_task.done():
            self.logger.warning("Background updates already running")
            return
        
        async def update_loop():
            update_count = 0
            while not self._shutdown:
                try:
                    await self.get_latest_data(force_update=True)
                    update_count += 1
                    
                    # Update markets file every 30 updates (15 minutes if interval is 30s)
                    if update_count % 30 == 0:
                        self.logger.info("📝 Updating markets.json file...")
                        await self.update_markets_file()
                        
                except Exception as e:
                    self.logger.error(f"Background update error: {e}")
                
                # Use cancellable sleep
                try:
                    await asyncio.sleep(self.update_interval)
                except asyncio.CancelledError:
                    break
        
        # Start background task
        self._update_task = asyncio.create_task(update_loop())
        self.logger.info(f"📡 Started market data updates every {self.update_interval}s")
    
    async def stop_background_updates(self):
        """Stop background market data updates gracefully."""
        self._shutdown = True
        if self._update_task and not self._update_task.done():
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        self.logger.info("🛑 Stopped market data background updates")
    
    def get_tracked_markets(self) -> List[Dict]:
        """Get all markets we're tracking from markets.json."""
        return list(self.markets_data.get("markets", {}).values())
    
    def get_market_by_id(self, market_id: int) -> Optional[Dict]:
        """Get market info by market ID."""
        return self.markets_data.get("markets", {}).get(str(market_id))
    
    def get_market_by_symbol(self, symbol: str) -> Optional[Dict]:
        """Get market info by symbol (e.g., 'BTC', 'ETH')."""
        market_id = self.markets_data.get("symbol_map", {}).get(symbol)
        if market_id:
            return self.get_market_by_id(market_id)
        return None
    
    async def close(self):
        """Cleanup resources."""
        await self.rise_client.close()


# Convenience function to get singleton instance
def get_market_manager() -> GlobalMarketManager:
    """Get the global market manager instance."""
    return GlobalMarketManager()