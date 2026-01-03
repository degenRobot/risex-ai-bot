#!/usr/bin/env python3
"""Check actual deposit amounts by examining trade history."""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.storage import JSONStorage
from app.services.rise_client import RiseClient
from app.services.equity_monitor import get_equity_monitor


async def check_deposits():
    """Check actual starting deposits for accounts."""
    
    storage = JSONStorage()
    accounts = storage.list_accounts()
    
    print("🔍 Checking Actual Starting Deposits")
    print("=" * 50)
    
    rise_client = RiseClient()
    equity_monitor = get_equity_monitor()
    
    try:
        for account in accounts:
            print(f"\n👤 {account.persona.name} ({account.persona.handle})")
            print(f"   Address: {account.address}")
            print(f"   Stored deposit amount: ${account.deposit_amount}")
            
            # Get current equity
            equity = await equity_monitor.fetch_equity(account.address)
            print(f"   Current equity: ${equity:.2f}")
            
            # Get all trades
            trades = await rise_client.get_account_trade_history(account.address, limit=100)
            
            # Calculate total trading volume and P&L
            total_buy_volume = 0
            total_sell_volume = 0
            total_realized_pnl = 0
            
            for trade in trades:
                size = float(trade.get("size", 0))
                price = float(trade.get("price", 0))
                side = trade.get("side")
                realized_pnl = float(trade.get("realized_pnl", 0))
                
                volume = size * price
                if side == "BUY":
                    total_buy_volume += volume
                else:
                    total_sell_volume += volume
                
                total_realized_pnl += realized_pnl
            
            print(f"   Total buy volume: ${total_buy_volume:.2f}")
            print(f"   Total sell volume: ${total_sell_volume:.2f}")
            print(f"   Total realized P&L: ${total_realized_pnl:.2f}")
            print(f"   Trade count: {len(trades)}")
            
            # Estimate initial deposit
            # If no sells and minimal P&L, initial deposit ≈ current equity - unrealized P&L
            if total_sell_volume == 0 and abs(total_realized_pnl) < 10:
                estimated_initial = round(equity / 1000) * 1000  # Round to nearest 1000
                print(f"   📊 Estimated initial deposit: ${estimated_initial:.2f}")
                
                if estimated_initial != account.deposit_amount:
                    print(f"   ⚠️  MISMATCH: Stored ${account.deposit_amount} vs Estimated ${estimated_initial}")
                    
                    # Calculate correct P&L
                    net_pnl = equity - estimated_initial
                    net_pnl_pct = (net_pnl / estimated_initial) * 100
                    print(f"   ✅ Correct Net P&L: ${net_pnl:+.2f} ({net_pnl_pct:+.2f}%)")
    
    finally:
        await rise_client.close()


if __name__ == "__main__":
    asyncio.run(check_deposits())