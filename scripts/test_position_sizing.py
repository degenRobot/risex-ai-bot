#!/usr/bin/env python3
"""Test position sizing calculations using free margin."""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.market_manager import get_market_manager
from app.services.equity_monitor import get_equity_monitor
from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage


async def test_free_margin_and_sizing():
    """Test free margin RPC call and position sizing calculations."""
    
    # Get services
    equity_monitor = get_equity_monitor()
    storage = JSONStorage()
    market_manager = get_market_manager()
    rise_client = RiseClient()
    
    # Load accounts
    accounts = storage.get_all_accounts()
    
    # Test each account
    for account_id, account_data in accounts.items():
        print(f"\n{'='*60}")
        print(f"Account: {account_data['persona']['name']}")
        print(f"Address: {account_data['address']}")
        
        try:
            # Get equity and free margin
            equity = await equity_monitor.fetch_equity(account_data["address"])
            free_margin = await equity_monitor.fetch_free_margin(account_data["address"])
            
            print("\nEquity Data:")
            print(f"  Total Equity: ${equity:.2f}")
            print(f"  Free Margin: ${free_margin:.2f}")
            print(f"  Margin Used: ${equity - free_margin:.2f}")
            
            # Get current positions
            positions_resp = await rise_client._request(
                "GET",
                "/v1/positions",
                params={"account": account_data["address"]},
            )
            
            positions = positions_resp.get("data", {}).get("positions", [])
            
            if positions:
                print("\nCurrent Positions:")
                for pos in positions:
                    size = float(pos["size"]) / 1e18
                    market_id = pos["market_id"]
                    side = pos["side"]
                    avg_price = float(pos["avg_entry_price"]) / 1e18
                    
                    # Get market info
                    market_info = market_manager.get_market_by_id(int(market_id))
                    symbol = market_info["base_asset_symbol"] if market_info else f"Market{market_id}"
                    
                    print(f"  - {symbol}: {size:.6f} ({side}) @ ${avg_price:.2f}")
            
            # Calculate max position sizes
            print("\nMax Position Sizes (using 50% of free margin):")
            
            # Get markets
            btc_market = market_manager.get_market_by_symbol("BTC")
            eth_market = market_manager.get_market_by_symbol("ETH")
            
            if btc_market and free_margin > 0:
                btc_price = float(btc_market.get("index_price", btc_market.get("last_price", 0)))
                if btc_price > 0:
                    max_btc_size = (free_margin * 0.5) / btc_price  # 50% of free margin
                    print(f"  BTC (${btc_price:.2f}): {max_btc_size:.6f} BTC (${max_btc_size * btc_price:.2f})")
            
            if eth_market and free_margin > 0:
                eth_price = float(eth_market.get("index_price", eth_market.get("last_price", 0)))
                if eth_price > 0:
                    max_eth_size = (free_margin * 0.5) / eth_price  # 50% of free margin
                    print(f"  ETH (${eth_price:.2f}): {max_eth_size:.6f} ETH (${max_eth_size * eth_price:.2f})")
            
            # Test order sizing
            print("\nTesting Order Placement:")
            
            # Only test on one account (Midwit McGee)
            if account_data["persona"]["name"] == "Midwit McGee" and free_margin > 100:
                # Test 1: Try order with size below max (should work)
                test_size_btc = min(0.0001, max_btc_size * 0.1) if "max_btc_size" in locals() else 0.0001
                
                print(f"\nTest 1: Small BTC order ({test_size_btc:.6f} BTC)")
                try:
                    result = await rise_client.place_market_order(
                        account_key=account_data["private_key"],
                        signer_key=account_data["signer_key"],
                        market_id=1,  # BTC
                        size=test_size_btc,
                        side="buy",
                        reduce_only=False,
                    )
                    
                    if result and "data" in result:
                        print(f"  ✅ Success! Order ID: {result['data'].get('order_id')}")
                    else:
                        print(f"  ❌ Failed: {result}")
                        
                except Exception as e:
                    print(f"  ❌ Error: {e}")
                
                # Test 2: Try order with size above max (should fail)
                test_size_large = max_btc_size * 2 if "max_btc_size" in locals() else 0.1
                
                print(f"\nTest 2: Large BTC order ({test_size_large:.6f} BTC)")
                try:
                    result = await rise_client.place_market_order(
                        account_key=account_data["private_key"],
                        signer_key=account_data["signer_key"],
                        market_id=1,  # BTC
                        size=test_size_large,
                        side="buy",
                        reduce_only=False,
                    )
                    
                    if result and "data" in result:
                        print(f"  ⚠️ Unexpected success! Order ID: {result['data'].get('order_id')}")
                    else:
                        print("  ✅ Expected failure: Insufficient margin")
                        
                except Exception as e:
                    error_msg = str(e)
                    if "reverted with status 0" in error_msg or "insufficient" in error_msg.lower():
                        print(f"  ✅ Expected failure: {error_msg[:100]}...")
                    else:
                        print(f"  ❌ Unexpected error: {e}")
                        
        except Exception as e:
            print(f"Error processing account: {e}")
            import traceback
            traceback.print_exc()
    
    # Cleanup
    await rise_client.close()


async def calculate_max_positions_for_all():
    """Calculate and display max position sizes for all accounts."""
    
    equity_monitor = get_equity_monitor()
    storage = JSONStorage()
    market_manager = get_market_manager()
    
    # Get market prices
    btc_market = market_manager.get_market_by_symbol("BTC")
    eth_market = market_manager.get_market_by_symbol("ETH")
    
    btc_price = float(btc_market.get("index_price", 90000)) if btc_market else 90000
    eth_price = float(eth_market.get("index_price", 3100)) if eth_market else 3100
    
    print("\n=== MAX POSITION SIZES (50% of Free Margin) ===")
    print(f"BTC Price: ${btc_price:,.2f}")
    print(f"ETH Price: ${eth_price:,.2f}")
    
    accounts = storage.get_all_accounts()
    
    max_positions = {}
    
    for account_id, account_data in accounts.items():
        name = account_data["persona"]["name"]
        address = account_data["address"]
        
        try:
            free_margin = await equity_monitor.fetch_free_margin(address)
            
            if free_margin and free_margin > 0:
                # Calculate max sizes (50% of free margin)
                max_btc = (free_margin * 0.5) / btc_price
                max_eth = (free_margin * 0.5) / eth_price
                
                max_positions[account_id] = {
                    "name": name,
                    "free_margin": free_margin,
                    "max_btc_size": max_btc,
                    "max_eth_size": max_eth,
                    "max_btc_value": max_btc * btc_price,
                    "max_eth_value": max_eth * eth_price,
                }
                
                print(f"\n{name}:")
                print(f"  Free Margin: ${free_margin:,.2f}")
                print(f"  Max BTC: {max_btc:.6f} BTC (${max_btc * btc_price:,.2f})")
                print(f"  Max ETH: {max_eth:.6f} ETH (${max_eth * eth_price:,.2f})")
            else:
                print(f"\n{name}: No free margin available")
                
        except Exception as e:
            print(f"\n{name}: Error - {e}")
    
    # Save max positions for use in trading
    with open("data/max_position_sizes.json", "w") as f:
        json.dump(max_positions, f, indent=2)
    
    return max_positions


async def main():
    """Run all tests."""
    print("=" * 80)
    print("POSITION SIZING TEST")
    print("=" * 80)
    
    # Test 1: Basic free margin and sizing
    await test_free_margin_and_sizing()
    
    # Test 2: Calculate max positions
    await asyncio.sleep(1)
    await calculate_max_positions_for_all()


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main())