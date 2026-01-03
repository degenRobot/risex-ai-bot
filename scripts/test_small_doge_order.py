#!/usr/bin/env python3
"""Test opening a small DOGE position to find minimum working size."""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage


async def test_minimum_sizes():
    """Test different order sizes to find what works."""
    print("=== Testing Minimum Order Sizes ===\n")
    
    # Get services
    rise_client = RiseClient()
    storage = JSONStorage()
    
    # Get Midwit McGee
    accounts = storage.get_all_accounts()
    midwit = None
    for acc_id, acc in accounts.items():
        if acc["persona"]["name"] == "Midwit McGee":
            midwit = acc
            break
    
    if not midwit:
        print("❌ Midwit McGee account not found")
        return
    
    # Test sizes for DOGE
    test_sizes = [0.001, 0.01, 0.1, 1, 10, 100, 1000]
    
    print("Testing DOGE orders:")
    print("DOGE Price: ~$0.128\n")
    
    for size in test_sizes:
        value = size * 0.128
        print(f"\nSize: {size} DOGE (${value:.2f})")
        
        try:
            result = await rise_client.place_market_order(
                account_key=midwit["private_key"],
                signer_key=midwit["signer_key"],
                market_id=5,  # DOGE
                size=size,
                side="buy",
                reduce_only=False,
            )
            
            if result and "data" in result and result["data"].get("order_id"):
                print(f"  ✅ Success! Order ID: {result['data']['order_id']}")
                # Found working size, stop here
                break
            else:
                print("  ❌ Failed")
                
        except Exception as e:
            error_msg = str(e)
            if "reverted with status 0" in error_msg:
                print("  ❌ Reverted")
            else:
                print(f"  ❌ Error: {error_msg[:80]}...")
    
    # Try another market - SOL (market_id: 4)
    print("\n" + "="*40)
    print("\nTesting SOL orders:")
    print("SOL Price: ~$127\n")
    
    sol_sizes = [0.001, 0.01, 0.1, 1]
    
    for size in sol_sizes:
        value = size * 127
        print(f"\nSize: {size} SOL (${value:.2f})")
        
        try:
            result = await rise_client.place_market_order(
                account_key=midwit["private_key"],
                signer_key=midwit["signer_key"],
                market_id=4,  # SOL
                size=size,
                side="buy",
                reduce_only=False,
            )
            
            if result and "data" in result and result["data"].get("order_id"):
                print(f"  ✅ Success! Order ID: {result['data']['order_id']}")
                break
            else:
                print("  ❌ Failed")
                
        except Exception as e:
            error_msg = str(e)
            if "reverted with status 0" in error_msg:
                print("  ❌ Reverted")
            else:
                print(f"  ❌ Error: {error_msg[:80]}...")
    
    await rise_client.close()


async def check_market_details():
    """Check detailed market configuration."""
    print("\n=== Market Configuration Details ===\n")
    
    with open("data/markets.json") as f:
        markets = json.load(f)
    
    # Check a few markets
    for market_id in ["1", "2", "5", "4"]:  # BTC, ETH, DOGE, SOL
        market = markets["markets"][market_id]
        print(f"{market['base_asset_symbol']}:")
        print(f"  Min Size: {market['min_size']}")
        print(f"  Step Size: {market['step_size']}")
        print(f"  Available: {market['available']}")
        print(f"  Post Only: {market['post_only']}")
        print(f"  Max Leverage: {market['max_leverage']}")
        print()


async def main():
    """Run tests."""
    await check_market_details()
    await test_minimum_sizes()


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main())