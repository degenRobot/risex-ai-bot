#!/usr/bin/env python3
"""Test P&L calculations with async data gathering."""

import asyncio
import json
from datetime import datetime
from decimal import Decimal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.storage import JSONStorage
from app.services.rise_client import RiseClient
from app.services.equity_monitor import get_equity_monitor
from app.services.order_tracker import OrderTracker


async def test_pnl_calculations():
    """Test P&L calculations with proper starting values."""
    
    storage = JSONStorage()
    accounts = storage.list_accounts()
    
    print("📊 Testing P&L Calculations with Async Data Flow")
    print("=" * 50)
    
    # Initial deposit amount for all accounts
    INITIAL_DEPOSIT = 1000.0
    
    rise_client = RiseClient()
    equity_monitor = get_equity_monitor()
    order_tracker = OrderTracker()
    
    try:
        # First, get market data asynchronously
        print("\n🌐 Fetching market data...")
        market_data_task = rise_client.get_enhanced_market_data()
        markets_task = rise_client.get_markets()
        
        # Wait for market data
        market_data, markets = await asyncio.gather(market_data_task, markets_task)
        
        print(f"   BTC Price: ${market_data.get('btc_price', 0):,.2f}")
        print(f"   BTC 24h Change: {market_data.get('btc_change', 0):.2%}")
        print(f"   ETH Price: ${market_data.get('eth_price', 0):,.2f}")
        print(f"   ETH 24h Change: {market_data.get('eth_change', 0):.2%}")
        
        # Create market lookup
        market_lookup = {}
        for market in markets:
            market_id = market.get("market_id")
            symbol = market.get("base_asset_symbol", "").split("/")[0]
            market_lookup[market_id] = symbol
        
        print(f"\n📈 Processing {len(accounts)} accounts...")
        
        # Process each account with async data gathering
        for account in accounts:
            print(f"\n{'='*60}")
            print(f"👤 {account.persona.name} ({account.persona.handle})")
            print(f"   Address: {account.address}")
            print(f"   Initial deposit: ${account.deposit_amount or INITIAL_DEPOSIT:.2f}")
            
            # Gather all data asynchronously
            equity_task = equity_monitor.fetch_equity(account.address)
            positions_task = rise_client.get_all_positions(account.address)
            trades_task = rise_client.get_account_trade_history(account.address, limit=50)
            
            # Execute all tasks concurrently
            equity, positions, trades = await asyncio.gather(
                equity_task, positions_task, trades_task
            )
            
            # Process equity
            print(f"\n💰 Equity Analysis:")
            if equity is not None:
                print(f"   Current on-chain equity: ${equity:,.2f}")
                net_pnl = equity - (account.deposit_amount or INITIAL_DEPOSIT)
                net_pnl_pct = (net_pnl / (account.deposit_amount or INITIAL_DEPOSIT)) * 100
                print(f"   Net P&L: ${net_pnl:+,.2f} ({net_pnl_pct:+.2f}%)")
            else:
                print(f"   ❌ Could not fetch equity")
            
            # Process positions
            print(f"\n📍 Open Positions:")
            if positions:
                total_unrealized_pnl = 0
                
                for pos in positions:
                    market_id = pos.get("market_id")
                    symbol = market_lookup.get(market_id, f"Market_{market_id}")
                    size_raw = float(pos.get("size", 0))
                    size = size_raw / 1e18
                    
                    if size != 0:
                        side = "LONG" if size > 0 else "SHORT"
                        entry_price = float(pos.get("avg_entry_price", 0)) / 1e18
                        
                        # Get current price
                        current_price = 0
                        if symbol == "BTC":
                            current_price = market_data.get('btc_price', 0)
                        elif symbol == "ETH":
                            current_price = market_data.get('eth_price', 0)
                        
                        # Calculate unrealized P&L
                        if current_price > 0 and entry_price > 0:
                            if side == "LONG":
                                unrealized_pnl = (current_price - entry_price) * abs(size)
                            else:
                                unrealized_pnl = (entry_price - current_price) * abs(size)
                            
                            total_unrealized_pnl += unrealized_pnl
                            
                            print(f"   - {symbol}: {side} {abs(size):.6f} @ ${entry_price:,.2f}")
                            print(f"     Current: ${current_price:,.2f}, Unrealized P&L: ${unrealized_pnl:+,.2f}")
                        else:
                            print(f"   - {symbol}: {side} {abs(size):.6f} @ ${entry_price:,.2f}")
                
                print(f"   Total Unrealized P&L: ${total_unrealized_pnl:+,.2f}")
            else:
                print("   No open positions")
            
            # Process trades
            print(f"\n📜 Recent Trades:")
            if trades:
                total_realized_pnl = 0
                trade_count = len(trades)
                
                # Show first few trades
                for trade in trades[:5]:
                    order_id = trade.get("order_id")
                    side = trade.get("side")
                    size = float(trade.get("size", 0))
                    price = float(trade.get("price", 0))
                    realized_pnl = float(trade.get("realized_pnl", 0))
                    total_realized_pnl += realized_pnl
                    
                    print(f"   - Order {order_id}: {side} {size} @ ${price:,.2f} (P&L: ${realized_pnl:+.2f})")
                
                # Sum all realized P&L
                for trade in trades[5:]:
                    realized_pnl = float(trade.get("realized_pnl", 0))
                    total_realized_pnl += realized_pnl
                
                print(f"   Total trades: {trade_count}")
                print(f"   Total Realized P&L: ${total_realized_pnl:+,.2f}")
            else:
                print("   No trades found")
            
            # Update account trading data
            await order_tracker.update_account_trading_data(account.id, account.address)
        
        print(f"\n{'='*60}")
        print("✅ P&L calculation test complete!")
        
        # Show async performance benefit
        print(f"\n⚡ Async Performance:")
        print(f"   - Fetched market data + {len(accounts)} account data concurrently")
        print(f"   - Each account: equity + positions + trades fetched in parallel")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await rise_client.close()
        await order_tracker.close()


if __name__ == "__main__":
    asyncio.run(test_pnl_calculations())