#!/usr/bin/env python3
"""Test what the positions API actually returns."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.rise_client import RiseClient


async def test_positions():
    """Test positions API response."""
    client = RiseClient()
    
    # Test addresses
    addresses = [
        "0x076652bc49B7818604F397f0320937248382301b",  # Drunk Wassie
        "0x41972911b53D5B038c4c35F610e31963F60FaAd5",  # Midwit McGee
        "0x5D8D12297Ca25AD78607d4ff37dd07889d5E57B5"   # Wise Chad
    ]
    
    for addr in addresses:
        print(f"\nTesting positions for {addr}:")
        try:
            positions = await client.get_all_positions(addr)
            print(f"  Type: {type(positions)}")
            print(f"  Length: {len(positions)}")
            if positions:
                print(f"  First item type: {type(positions[0])}")
                print(f"  First item: {positions[0]}")
        except Exception as e:
            print(f"  Error: {e}")
    
    await client.close()


if __name__ == "__main__":
    asyncio.run(test_positions())