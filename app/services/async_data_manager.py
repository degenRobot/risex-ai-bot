"""Async data manager for efficient parallel data fetching."""

import asyncio
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import logging

from .rise_client import RiseClient
from .equity_monitor import get_equity_monitor
from .storage import JSONStorage


logger = logging.getLogger(__name__)


class AsyncDataManager:
    """Manage async data fetching for trading bot."""
    
    def __init__(self):
        self.rise_client = RiseClient()
        self.equity_monitor = get_equity_monitor()
        self.storage = JSONStorage()
        self._market_cache = {}
        self._last_market_update = None
        self.market_cache_ttl = 60  # Cache market data for 60 seconds
    
    async def fetch_all_data_for_accounts(
        self, 
        accounts: List[Any]
    ) -> Dict[str, Dict]:
        """Fetch all data for multiple accounts in parallel.
        
        Returns:
            Dict mapping account_id to their complete data
        """
        # First, fetch market data (shared across all accounts)
        market_data = await self._get_market_data()
        
        # Create tasks for each account
        account_tasks = []
        for account in accounts:
            task = self._fetch_account_data(account, market_data)
            account_tasks.append(task)
        
        # Execute all account fetches in parallel
        results = await asyncio.gather(*account_tasks, return_exceptions=True)
        
        # Build result dict
        account_data = {}
        for account, result in zip(accounts, results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching data for {account.id}: {result}")
                account_data[account.id] = {
                    "error": str(result),
                    "account": account,
                    "market_data": market_data
                }
            else:
                account_data[account.id] = result
        
        return account_data
    
    async def _fetch_account_data(
        self, 
        account: Any, 
        market_data: Dict
    ) -> Dict:
        """Fetch all data for a single account in parallel."""
        # Create all tasks for this account
        tasks = {
            "equity": self.equity_monitor.fetch_equity(account.address),
            "positions": self.rise_client.get_all_positions(account.address),
            "trades": self.rise_client.get_account_trade_history(account.address, limit=20),
            "orders": self._get_recent_orders(account.address)
        }
        
        # Execute all tasks concurrently
        results = {}
        for key, task in tasks.items():
            try:
                results[key] = await task
            except Exception as e:
                logger.error(f"Error fetching {key} for {account.address}: {e}")
                results[key] = None
        
        # Calculate P&L
        pnl_data = self._calculate_pnl(
            account=account,
            equity=results["equity"],
            positions=results["positions"],
            trades=results["trades"],
            market_data=market_data
        )
        
        return {
            "account": account,
            "equity": results["equity"],
            "positions": results["positions"],
            "trades": results["trades"],
            "orders": results["orders"],
            "market_data": market_data,
            "pnl": pnl_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _get_market_data(self) -> Dict:
        """Get cached or fresh market data."""
        now = datetime.utcnow()
        
        # Check cache
        if (self._last_market_update and 
            self._market_cache and
            (now - self._last_market_update).total_seconds() < self.market_cache_ttl):
            return self._market_cache
        
        # Fetch fresh data in parallel
        enhanced_data_task = self.rise_client.get_enhanced_market_data()
        markets_task = self.rise_client.get_markets()
        
        try:
            enhanced_data, markets = await asyncio.gather(
                enhanced_data_task, 
                markets_task
            )
            
            # Build market lookup
            market_lookup = {}
            for market in markets:
                market_id = str(market.get("market_id"))
                symbol = market.get("base_asset_symbol", "").split("/")[0]
                market_lookup[market_id] = {
                    "symbol": symbol,
                    "last_price": float(market.get("last_price", 0)),
                    "change_24h": float(market.get("change_24h", 0))
                }
            
            self._market_cache = {
                **enhanced_data,
                "market_lookup": market_lookup,
                "markets": markets
            }
            self._last_market_update = now
            
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            # Return cached data if available
            if self._market_cache:
                return self._market_cache
            # Return minimal data
            return {"error": str(e)}
        
        return self._market_cache
    
    async def _get_recent_orders(self, account: str, limit: int = 10) -> List[Dict]:
        """Get recent orders for an account."""
        try:
            response = await self.rise_client._request(
                "GET", "/v1/orders",
                params={"account": account, "limit": limit}
            )
            return response.get("orders", [])
        except Exception as e:
            logger.error(f"Error fetching orders for {account}: {e}")
            return []
    
    def _calculate_pnl(
        self,
        account: Any,
        equity: Optional[float],
        positions: Optional[List[Dict]],
        trades: Optional[List[Dict]],
        market_data: Dict
    ) -> Dict:
        """Calculate comprehensive P&L data."""
        result = {
            "initial_deposit": account.deposit_amount or 1000.0,
            "current_equity": equity,
            "net_pnl": 0,
            "net_pnl_pct": 0,
            "unrealized_pnl": 0,
            "realized_pnl": 0,
            "total_trades": 0,
            "open_positions": 0
        }
        
        # Net P&L from equity
        if equity is not None:
            result["net_pnl"] = equity - result["initial_deposit"]
            result["net_pnl_pct"] = (result["net_pnl"] / result["initial_deposit"]) * 100
        
        # Unrealized P&L from positions
        if positions:
            result["open_positions"] = len(positions)
            market_lookup = market_data.get("market_lookup", {})
            
            for pos in positions:
                market_id = str(pos.get("market_id"))
                size_raw = float(pos.get("size", 0))
                size = size_raw / 1e18
                
                if size != 0:
                    entry_price = float(pos.get("avg_entry_price", 0)) / 1e18
                    market_info = market_lookup.get(market_id, {})
                    current_price = market_info.get("last_price", 0)
                    
                    if current_price > 0 and entry_price > 0:
                        if size > 0:  # Long
                            unrealized = (current_price - entry_price) * size
                        else:  # Short
                            unrealized = (entry_price - current_price) * abs(size)
                        
                        result["unrealized_pnl"] += unrealized
        
        # Realized P&L from trades
        if trades:
            result["total_trades"] = len(trades)
            for trade in trades:
                realized = float(trade.get("realized_pnl", 0))
                result["realized_pnl"] += realized
        
        return result
    
    async def close(self):
        """Cleanup resources."""
        await self.rise_client.close()