#!/usr/bin/env python3
"""Test opening a DOGE position with Midwit McGee."""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.market_manager import get_market_manager
from app.services.equity_monitor import get_equity_monitor
from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage


async def test_doge_position():
    """Test opening a DOGE position."""
    print("=== Testing DOGE Position for Midwit McGee ===\n")
    
    # Get services
    rise_client = RiseClient()
    storage = JSONStorage()
    equity_monitor = get_equity_monitor()
    market_manager = get_market_manager()
    
    # Get Midwit McGee account
    accounts = storage.get_all_accounts()
    midwit = None
    for acc_id, acc in accounts.items():
        if acc["persona"]["name"] == "Midwit McGee":
            midwit = acc
            midwit_id = acc_id
            break
    
    if not midwit:
        print("❌ Midwit McGee account not found")
        return
    
    print(f"Account: {midwit['persona']['name']}")
    print(f"Address: {midwit['address']}")
    
    # Get current equity and free margin
    equity_data = await equity_monitor.fetch_equity_and_margin(midwit["address"])
    
    print("\nCurrent Status:")
    print(f"  Total Equity: ${equity_data['equity']:.2f}")
    print(f"  Free Margin: ${equity_data['free_margin']:.2f}")
    
    # Get DOGE market data
    doge_market = market_manager.get_market_by_symbol("DOGE")
    if not doge_market:
        print("❌ DOGE market not found")
        return
        
    doge_price = float(doge_market.get("index_price", doge_market.get("last_price", 0)))
    print("\nDOGE Market:")
    print(f"  Market ID: {doge_market['market_id']}")
    print(f"  Price: ${doge_price:.6f}")
    print(f"  Min Size: {doge_market['min_size']}")
    
    # Calculate position sizing
    free_margin = equity_data["free_margin"]
    
    # Test with different sizes
    test_percentages = [0.1, 0.25]  # 10% and 25% of free margin
    
    for pct in test_percentages:
        position_value = free_margin * pct
        doge_amount = position_value / doge_price
        
        print(f"\n--- Testing {pct*100}% of free margin ---")
        print(f"  Position Value: ${position_value:.2f}")
        print(f"  DOGE Amount: {doge_amount:.2f} DOGE")
        
        try:
            # Place market order
            result = await rise_client.place_market_order(
                account_key=midwit["private_key"],
                signer_key=midwit["signer_key"],
                market_id=5,  # DOGE market ID
                size=doge_amount,
                side="buy",
                reduce_only=False,
            )
            
            if result and "data" in result:
                order_id = result["data"].get("order_id")
                print(f"  ✅ Success! Order ID: {order_id}")
                
                # Wait a bit for order to process
                await asyncio.sleep(2)
                
                # Check if position was opened
                positions_resp = await rise_client._request(
                    "GET",
                    "/v1/positions",
                    params={"account": midwit["address"]},
                )
                
                if positions_resp.get("data", {}).get("positions"):
                    for pos in positions_resp["data"]["positions"]:
                        if pos["market_id"] == "5":
                            size = float(pos["size"]) / 1e18
                            print("\n  📊 DOGE Position Opened:")
                            print(f"     Size: {size:.2f} DOGE")
                            print(f"     Avg Price: ${float(pos['avg_entry_price']) / 1e18:.6f}")
                            print(f"     Side: {pos['side']}")
                            break
                
                # Only test one successful order
                break
            else:
                print(f"  ❌ Failed: {result}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Final status check
    print("\n=== Final Account Status ===")
    
    # Get updated equity
    updated_equity = await equity_monitor.fetch_equity_and_margin(midwit["address"])
    print(f"Total Equity: ${updated_equity['equity']:.2f}")
    print(f"Free Margin: ${updated_equity['free_margin']:.2f}")
    print(f"Margin Used: ${updated_equity['equity'] - updated_equity['free_margin']:.2f}")
    
    # Show all positions
    positions_resp = await rise_client._request(
        "GET",
        "/v1/positions",
        params={"account": midwit["address"]},
    )
    
    if positions_resp.get("data", {}).get("positions"):
        print("\nAll Open Positions:")
        for pos in positions_resp["data"]["positions"]:
            market_id = int(pos["market_id"])
            market_info = market_manager.get_market_by_id(market_id)
            symbol = market_info["base_asset_symbol"] if market_info else f"Market{market_id}"
            size = float(pos["size"]) / 1e18
            avg_price = float(pos["avg_entry_price"]) / 1e18
            print(f"  - {symbol}: {size:.6f} @ ${avg_price:.2f}")
    
    await rise_client.close()


async def main():
    """Run the test."""
    print("=" * 60)
    print("DOGE POSITION TEST")
    print("=" * 60)
    
    await test_doge_position()


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main())