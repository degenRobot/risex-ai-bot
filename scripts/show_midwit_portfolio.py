#!/usr/bin/env python3
"""Show Midwit McGee's complete portfolio and P&L."""

import asyncio
from pathlib import Path
import sys

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage
from app.services.equity_monitor import get_equity_monitor
from app.core.market_manager import get_market_manager


async def show_portfolio():
    """Display complete portfolio information."""
    print("=== Midwit McGee Portfolio Summary ===\n")
    
    # Get services
    rise_client = RiseClient()
    storage = JSONStorage()
    equity_monitor = get_equity_monitor()
    market_manager = get_market_manager()
    
    # Get Midwit McGee
    accounts = storage.get_all_accounts()
    midwit = None
    for acc_id, acc in accounts.items():
        if acc['persona']['name'] == "Midwit McGee":
            midwit = acc
            break
    
    if not midwit:
        print("❌ Midwit McGee account not found")
        return
    
    # Get current equity and margin
    equity_data = await equity_monitor.fetch_equity_and_margin(midwit['address'])
    
    print(f"Account: {midwit['address']}")
    print(f"\nEquity Overview:")
    print(f"  Total Equity: ${equity_data['equity']:,.2f}")
    print(f"  Free Margin: ${equity_data['free_margin']:,.2f}")
    print(f"  Margin Used: ${equity_data['equity'] - equity_data['free_margin']:,.2f}")
    print(f"  Starting Capital: ${midwit.get('deposit_amount', 2000):,.2f}")
    print(f"  Total P&L: ${equity_data['equity'] - midwit.get('deposit_amount', 2000):,.2f}")
    print(f"  Return: {((equity_data['equity'] / midwit.get('deposit_amount', 2000)) - 1) * 100:.2f}%")
    
    # Get all positions
    positions_resp = await rise_client._request(
        "GET",
        "/v1/positions",
        params={"account": midwit['address']}
    )
    
    if positions_resp.get("data", {}).get("positions"):
        print(f"\n📊 Open Positions ({len(positions_resp['data']['positions'])})")
        print("-" * 60)
        
        total_position_value = 0
        total_pnl = 0
        
        for pos in positions_resp["data"]["positions"]:
            market_id = int(pos['market_id'])
            market_info = market_manager.get_market_by_id(market_id)
            
            if market_info:
                symbol = market_info['base_asset_symbol']
                current_price = float(market_info.get('index_price', market_info.get('last_price', 0)))
            else:
                symbol = f"Market{market_id}"
                current_price = 0
            
            size = float(pos['size']) / 1e18
            avg_price = float(pos['avg_entry_price']) / 1e18
            side = pos['side']
            
            # Calculate P&L
            if side == "BUY":
                position_pnl = (current_price - avg_price) * size
            else:
                position_pnl = (avg_price - current_price) * size
            
            position_value = size * current_price
            total_position_value += position_value
            total_pnl += position_pnl
            
            print(f"\n{symbol} ({side}):")
            print(f"  Size: {size:.6f} {symbol}")
            print(f"  Entry Price: ${avg_price:,.2f}")
            print(f"  Current Price: ${current_price:,.2f}")
            print(f"  Position Value: ${position_value:,.2f}")
            print(f"  P&L: ${position_pnl:,.2f} ({(position_pnl/position_value)*100:.2f}%)")
        
        print("\n" + "-" * 60)
        print(f"Total Position Value: ${total_position_value:,.2f}")
        print(f"Total Unrealized P&L: ${total_pnl:,.2f}")
        
        # Position sizing info
        print(f"\n💡 Position Sizing Info:")
        print(f"  Max position per trade (50% of free margin): ${equity_data['free_margin'] * 0.5:,.2f}")
        print(f"  Conservative (10-20%): ${equity_data['free_margin'] * 0.1:,.2f} - ${equity_data['free_margin'] * 0.2:,.2f}")
        print(f"  Moderate (20-35%): ${equity_data['free_margin'] * 0.2:,.2f} - ${equity_data['free_margin'] * 0.35:,.2f}")
        print(f"  Aggressive (35-50%): ${equity_data['free_margin'] * 0.35:,.2f} - ${equity_data['free_margin'] * 0.5:,.2f}")
    
    await rise_client.close()


async def main():
    """Run portfolio display."""
    print("=" * 60)
    print("PORTFOLIO ANALYSIS")
    print("=" * 60)
    
    await show_portfolio()


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main())