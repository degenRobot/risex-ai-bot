#!/usr/bin/env python3
"""Test available markets on RISE."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.rise_client import RiseClient


async def test_markets():
    """Check all available markets."""
    print("📊 RISE Markets Test")
    print("=" * 60)
    
    async with RiseClient() as client:
        # Get raw markets data
        response = await client._request("GET", "/v1/markets")
        print(f"\nRaw response keys: {list(response.keys())}")
        
        data = response.get("data", {})
        print(f"Data type: {type(data)}")
        
        if isinstance(data, dict):
            print(f"Data keys: {list(data.keys())}")
            markets = data.get("markets", [])
        else:
            markets = data
        
        print(f"\nFound {len(markets)} markets:")
        
        print("\n" + "-" * 60)
        print("\nParsed Markets:")
        
        if isinstance(markets, dict):
            # If markets is a dict, iterate over items
            for market_id, market_data in markets.items():
                print(f"\nMarket {market_id}:")
                if isinstance(market_data, dict):
                    for key, value in market_data.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"  Data: {market_data}")
        elif isinstance(markets, list):
            # If markets is a list
            for i, market in enumerate(markets):
                print(f"\nMarket {i+1}:")
                if isinstance(market, dict):
                    for key, value in market.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"  Data: {market}")
        
        # Test getting prices
        print("\n" + "-" * 60)
        print("\nMarket Prices:")
        
        prices = await client.get_market_prices()
        for symbol, price in prices.items():
            print(f"  {symbol}: ${price:,.2f}")
        
        # Test individual market data
        print("\n" + "-" * 60)
        print("\nTesting Individual Market Data:")
        
        for market_id in [1, 2, 3]:
            try:
                price = await client.get_latest_price(market_id)
                print(f"  Market {market_id}: ${price:,.2f}" if price else f"  Market {market_id}: No price")
            except Exception as e:
                print(f"  Market {market_id}: Error - {e}")


if __name__ == "__main__":
    asyncio.run(test_markets())