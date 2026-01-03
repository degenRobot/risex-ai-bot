#!/usr/bin/env python3
"""Test opening positions with correct minimum sizes from markets.json."""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.market_manager import get_market_manager
from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage


async def test_positions_with_min_sizes():
    """Test opening positions using the exact minimum sizes."""
    print("=== Testing Positions with Minimum Sizes ===\n")
    
    # Get services
    rise_client = RiseClient()
    storage = JSONStorage()
    market_manager = get_market_manager()
    
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
    
    # Test different markets
    test_markets = [
        {"symbol": "DOGE", "id": 5},
        {"symbol": "SOL", "id": 4},
        {"symbol": "BNB", "id": 3},
    ]
    
    for market in test_markets:
        market_data = market_manager.get_market_by_symbol(market["symbol"])
        if not market_data:
            continue
            
        min_size = float(market_data["min_size"])
        price = float(market_data.get("index_price", market_data.get("last_price", 0)))
        
        print(f"\n{market['symbol']} Market:")
        print(f"  Price: ${price:.4f}")
        print(f"  Min Size: {min_size}")
        print(f"  Min Value: ${min_size * price:.2f}")
        
        # Test with minimum size and 10x minimum
        test_multipliers = [1, 10, 100]
        
        for mult in test_multipliers:
            size = min_size * mult
            value = size * price
            
            print(f"\n  Testing {size} {market['symbol']} (${value:.2f}):")
            
            try:
                result = await rise_client.place_market_order(
                    account_key=midwit["private_key"],
                    signer_key=midwit["signer_key"],
                    market_id=market["id"],
                    size=size,
                    side="buy",
                    reduce_only=False,
                )
                
                if result and "data" in result and result["data"].get("order_id"):
                    print(f"    ✅ Success! Order ID: {result['data']['order_id']}")
                    
                    # Wait for order to settle
                    await asyncio.sleep(2)
                    
                    # Check position
                    positions_resp = await rise_client._request(
                        "GET",
                        "/v1/positions",
                        params={"account": midwit["address"]},
                    )
                    
                    if positions_resp.get("data", {}).get("positions"):
                        for pos in positions_resp["data"]["positions"]:
                            if int(pos["market_id"]) == market["id"]:
                                actual_size = float(pos["size"]) / 1e18
                                avg_price = float(pos["avg_entry_price"]) / 1e18
                                print(f"    📊 Position: {actual_size:.6f} @ ${avg_price:.4f}")
                                break
                    
                    # Success - move to next market
                    break
                else:
                    print("    ❌ Failed")
                    
            except Exception as e:
                error_msg = str(e)
                if "reverted with status 0" in error_msg:
                    print("    ❌ Order reverted")
                elif "insufficient" in error_msg.lower():
                    print("    ❌ Insufficient balance")
                else:
                    print(f"    ❌ Error: {error_msg[:60]}...")
    
    # Final check
    print("\n=== Final Positions ===")
    
    positions_resp = await rise_client._request(
        "GET",
        "/v1/positions",
        params={"account": midwit["address"]},
    )
    
    if positions_resp.get("data", {}).get("positions"):
        for pos in positions_resp["data"]["positions"]:
            market_id = int(pos["market_id"])
            market_info = market_manager.get_market_by_id(market_id)
            symbol = market_info["base_asset_symbol"] if market_info else f"Market{market_id}"
            size = float(pos["size"]) / 1e18
            avg_price = float(pos["avg_entry_price"]) / 1e18
            side = pos["side"]
            print(f"  - {symbol}: {size:.6f} ({side}) @ ${avg_price:.2f}")
    
    await rise_client.close()


async def main():
    """Run the test."""
    print("=" * 60)
    print("MINIMUM SIZE POSITION TEST")
    print("=" * 60)
    
    await test_positions_with_min_sizes()


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main())