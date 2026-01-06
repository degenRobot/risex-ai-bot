#!/usr/bin/env python3
"""Fetch and update markets data from RISE API."""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rise_client import RiseClient


async def fetch_and_save_markets():
    """Fetch markets from RISE API and save to data/markets.json."""
    async with RiseClient() as client:
        print("🔄 Fetching markets from RISE API...")
        
        try:
            # Get all markets
            markets = await client.get_markets()
            
            # Process and organize markets data
            markets_data = {
                "last_updated": datetime.utcnow().isoformat(),
                "source": "https://api.testnet.rise.trade/v1/markets",
                "markets": {},
                "market_id_map": {},  # Quick lookup by ID
                "symbol_map": {},      # Quick lookup by symbol
            }
            
            for market in markets:
                market_id = market.get("market_id")
                base_asset_full = market.get("base_asset_symbol", "")
                
                # Extract base asset (BTC from BTC/USDC)
                base_asset = base_asset_full.split("/")[0] if "/" in base_asset_full else base_asset_full
                
                # Create symbol (e.g., BTC-USD)
                symbol = f"{base_asset}-USD" if base_asset else ""
                
                if market_id:
                    # Store full market data
                    markets_data["markets"][str(market_id)] = {
                        "market_id": int(market_id),
                        "symbol": symbol,
                        "base_asset_symbol": base_asset,
                        "base_asset_full": base_asset_full,
                        "base_asset_address": market.get("base_asset_address"),
                        "quote_asset_symbol": market.get("quote_asset_symbol", "USD"),
                        "quote_asset_address": market.get("quote_asset_address"),
                        "available": market.get("available", False),
                        "post_only": market.get("post_only", False),
                        "step_size": market.get("step_size", "0.0001"),
                        "tick_size": market.get("tick_size", "0.01"),
                        "min_size": market.get("min_size", "0.0001"),
                        "max_size": market.get("max_size", "1000000"),
                        "max_leverage": market.get("max_leverage", "20"),
                        "max_open_interest": market.get("max_open_interest"),
                        "initial_margin_fraction": market.get("initial_margin_fraction", "0.05"),
                        "maintenance_margin_fraction": market.get("maintenance_margin_fraction", "0.025"),
                        "maker_fee": market.get("maker_fee", "0.0002"),
                        "taker_fee": market.get("taker_fee", "0.0005"),
                        "daily_volume": market.get("daily_volume", "0"),
                        "open_interest": market.get("open_interest", "0"),
                        "oracle_price": market.get("oracle_price"),
                        "last_price": market.get("last_price"),
                        "index_price": market.get("index_price"),
                        "funding_rate": market.get("funding_rate", "0"),
                        "next_funding_at": market.get("next_funding_at"),
                    }
                    
                    # Create quick lookup maps
                    markets_data["market_id_map"][str(market_id)] = symbol
                    if base_asset:
                        markets_data["symbol_map"][base_asset] = int(market_id)
            
            # Add summary
            markets_data["summary"] = {
                "total_markets": len(markets_data["markets"]),
                "available_markets": sum(1 for m in markets_data["markets"].values() if m["available"]),
                "post_only_markets": sum(1 for m in markets_data["markets"].values() if m["post_only"]),
            }
            
            # Save to file
            data_dir = Path(__file__).parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            
            markets_file = data_dir / "markets.json"
            with open(markets_file, "w") as f:
                json.dump(markets_data, f, indent=2)
            
            print(f"✅ Saved {len(markets_data['markets'])} markets to {markets_file}")
            
            # Print summary
            print("\n📊 Markets Summary:")
            print(f"   Total Markets: {markets_data['summary']['total_markets']}")
            print(f"   Available: {markets_data['summary']['available_markets']}")
            print(f"   Post-Only: {markets_data['summary']['post_only_markets']}")
            
            print("\n🏷️  Market IDs:")
            for market_id, symbol in sorted(markets_data["market_id_map"].items(), key=lambda x: int(x[0])):
                market = markets_data["markets"][market_id]
                status = "✅" if market["available"] else "❌"
                print(f"   {status} ID {market_id}: {symbol}")
            
            return markets_data
            
        except Exception as e:
            print(f"❌ Error fetching markets: {e}")
            raise


async def main():
    """Run the market update."""
    await fetch_and_save_markets()


if __name__ == "__main__":
    asyncio.run(main())