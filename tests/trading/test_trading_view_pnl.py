#!/usr/bin/env python3
"""
Test using TradingView API data to update P&L for accounts.
This provides real-time position and P&L data.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List

from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage
from app.models import Account, Position


class TradingViewPnLUpdater:
    """Update P&L using TradingView data from RISE API."""
    
    def __init__(self):
        self.storage = JSONStorage()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "accounts_updated": 0,
            "total_unrealized_pnl": 0.0,
            "total_realized_pnl": 0.0,
            "account_details": []
        }
    
    async def update_all_accounts_pnl(self):
        """Update P&L for all accounts using TradingView data."""
        print("📊 TradingView P&L Update")
        print("="*60)
        
        accounts = self.storage.list_accounts()
        active_accounts = [acc for acc in accounts if acc.is_active and acc.has_deposited]
        
        print(f"Found {len(active_accounts)} active accounts with deposits")
        
        async with RiseClient() as client:
            for account in active_accounts:
                await self.update_account_pnl(client, account)
        
        self.save_results()
        self.print_summary()
    
    async def update_account_pnl(self, client: RiseClient, account: Account):
        """Update P&L for a single account."""
        print(f"\n📈 Updating: {account.persona.name if account.persona else account.address}")
        
        account_data = {
            "account_id": account.id,
            "address": account.address,
            "name": account.persona.name if account.persona else "Unknown",
            "positions": [],
            "unrealized_pnl": 0.0,
            "realized_pnl": 0.0,
            "account_value": 0.0
        }
        
        try:
            # Get TradingView data (combines positions, P&L, and account info)
            # This endpoint provides comprehensive trading data
            trading_data = await self.get_trading_view_data(client, account.address)
            
            if not trading_data:
                print("   ⚠️  No trading data found")
                account_data["status"] = "no_data"
                self.results["account_details"].append(account_data)
                return
            
            # Parse positions from trading data
            positions_data = trading_data.get("positions", [])
            account_info = trading_data.get("accountInfo", {})
            
            # Update account value
            margin_summary = account_info.get("marginSummary", {})
            account_data["account_value"] = margin_summary.get("accountValue", 0)
            
            # Process each position
            for pos_data in positions_data:
                position = Position(
                    account_id=account.id,
                    market=pos_data.get("market", "Unknown"),
                    side=pos_data.get("side", "long"),
                    size=abs(pos_data.get("size", 0)),
                    entry_price=pos_data.get("avgPrice", 0),
                    mark_price=pos_data.get("markPrice", 0),
                    notional_value=abs(pos_data.get("notionalValue", 0)),
                    unrealized_pnl=pos_data.get("unrealizedPnl", 0),
                    realized_pnl=pos_data.get("realizedPnl", 0)
                )
                
                # Save position snapshot
                self.storage.save_position_snapshot(position)
                
                account_data["positions"].append({
                    "market": position.market,
                    "side": position.side,
                    "size": position.size,
                    "unrealized_pnl": position.unrealized_pnl,
                    "realized_pnl": position.realized_pnl
                })
                
                account_data["unrealized_pnl"] += position.unrealized_pnl
                account_data["realized_pnl"] += position.realized_pnl
                
                print(f"   📊 {position.market}: {position.side} {position.size}")
                print(f"      Unrealized P&L: ${position.unrealized_pnl:,.2f}")
            
            # Update account totals
            account_data["total_pnl"] = account_data["unrealized_pnl"] + account_data["realized_pnl"]
            account_data["status"] = "updated"
            
            # Update global totals
            self.results["accounts_updated"] += 1
            self.results["total_unrealized_pnl"] += account_data["unrealized_pnl"]
            self.results["total_realized_pnl"] += account_data["realized_pnl"]
            
            print(f"   💰 Account Value: ${account_data['account_value']:,.2f}")
            print(f"   📊 Total Unrealized P&L: ${account_data['unrealized_pnl']:,.2f}")
            print(f"   📊 Total Realized P&L: ${account_data['realized_pnl']:,.2f}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            account_data["status"] = "error"
            account_data["error"] = str(e)
        
        self.results["account_details"].append(account_data)
    
    async def get_trading_view_data(self, client: RiseClient, address: str) -> Dict:
        """
        Get TradingView-style data for an account.
        This simulates the TradingView API endpoint that provides comprehensive data.
        """
        try:
            # In production, this would call the actual TradingView endpoint:
            # GET /v1/markets/trading-view/{address}
            # For now, we'll combine data from multiple endpoints
            
            # Get positions
            positions = await client.get_all_positions(address)
            
            # Get account balance info
            balance_info = await client.get_balance(address)
            
            # Combine into TradingView format
            trading_data = {
                "positions": positions,
                "accountInfo": balance_info,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return trading_data
            
        except Exception as e:
            print(f"Failed to get trading view data: {e}")
            return {}
    
    def save_results(self):
        """Save P&L update results."""
        with open("tests/trading/trading_view_pnl_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print("\n💾 Results saved to tests/trading/trading_view_pnl_results.json")
    
    def print_summary(self):
        """Print P&L update summary."""
        print("\n" + "="*60)
        print("📊 P&L UPDATE SUMMARY")
        print("="*60)
        
        print(f"Accounts Updated: {self.results['accounts_updated']}")
        print(f"Total Unrealized P&L: ${self.results['total_unrealized_pnl']:,.2f}")
        print(f"Total Realized P&L: ${self.results['total_realized_pnl']:,.2f}")
        print(f"Total P&L: ${self.results['total_unrealized_pnl'] + self.results['total_realized_pnl']:,.2f}")
        
        if self.results["account_details"]:
            print("\n📋 Top Performers:")
            # Sort by total P&L
            sorted_accounts = sorted(
                [a for a in self.results["account_details"] if a.get("status") == "updated"],
                key=lambda x: x.get("total_pnl", 0),
                reverse=True
            )
            
            for i, account in enumerate(sorted_accounts[:5]):
                print(f"\n{i+1}. {account['name']}")
                print(f"   Total P&L: ${account.get('total_pnl', 0):,.2f}")
                print(f"   Positions: {len(account.get('positions', []))}")


async def continuous_pnl_update(interval_seconds: int = 60):
    """Continuously update P&L at specified interval."""
    print(f"🔄 Starting continuous P&L updates (every {interval_seconds}s)")
    print("Press Ctrl+C to stop")
    
    updater = TradingViewPnLUpdater()
    
    while True:
        try:
            await updater.update_all_accounts_pnl()
            print(f"\n⏰ Next update in {interval_seconds} seconds...")
            await asyncio.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n✋ Stopping continuous updates")
            break
        except Exception as e:
            print(f"\n❌ Error in update cycle: {e}")
            print(f"Retrying in {interval_seconds} seconds...")
            await asyncio.sleep(interval_seconds)


async def main():
    """Run P&L update test."""
    # Single update
    updater = TradingViewPnLUpdater()
    await updater.update_all_accounts_pnl()
    
    # Uncomment for continuous updates
    # await continuous_pnl_update(interval_seconds=30)


if __name__ == "__main__":
    asyncio.run(main())