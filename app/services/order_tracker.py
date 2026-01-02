"""Order tracking service to detect successful trades."""

import asyncio
import json
from typing import Dict, Optional, List, Set
from datetime import datetime, timedelta

from .rise_client import RiseClient
from .storage import JSONStorage


class OrderTracker:
    """Track order success by monitoring trades and positions."""
    
    def __init__(self):
        self.rise_client = RiseClient()
        self.storage = JSONStorage()
        self.known_trades: Dict[str, Set[str]] = {}  # account -> set of trade IDs
        
    async def check_order_success(
        self,
        account: str,
        order_id: str,
        expected_side: str,
        expected_size: float,
        timeout_seconds: int = 10
    ) -> Dict:
        """Check if an order was successfully executed.
        
        Args:
            account: Account address
            order_id: Order ID to check
            expected_side: Expected side (buy/sell)
            expected_size: Expected size in BTC
            timeout_seconds: How long to wait for order to appear
            
        Returns:
            Dict with success status and trade details
        """
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout_seconds:
            try:
                # Check recent trades - need to await a bit for API to update
                if (datetime.now() - start_time).total_seconds() < 1:
                    await asyncio.sleep(1)  # Give API time to update
                
                trades = await self.rise_client.get_account_trade_history(account, limit=10)
                
                for trade in trades:
                    if str(trade.get("order_id")) == str(order_id):
                        # Found our order!
                        return {
                            "success": True,
                            "trade_id": trade.get("id"),
                            "price": float(trade.get("price", 0)),
                            "size": float(trade.get("size", 0)),
                            "side": trade.get("side"),
                            "fee": float(trade.get("fee", 0)),
                            "time": trade.get("time"),
                            "tx_hash": trade.get("blockchain_data", {}).get("tx_hash")
                        }
                
                # Also check orders endpoint
                response = await self.rise_client._request(
                    "GET", "/v1/orders",
                    params={"account": account, "limit": 20}
                )
                orders = response.get("orders", [])
                
                for order in orders:
                    if str(order.get("id")) == str(order_id):
                        # Check if order was filled
                        status = order.get("status", "").lower()
                        cancel_reason = order.get("cancel_reason", "").lower()
                        
                        if status == "filled" or cancel_reason == "filled":
                            return {
                                "success": True,
                                "order_status": "filled",
                                "filled_size": order.get("filled_size", order.get("size")),
                                "price": float(order.get("avg_fill_price", order.get("price", 0))),
                                "side": order.get("side"),
                                "type": order.get("type")
                            }
                        elif status in ["cancelled", "expired"]:
                            return {
                                "success": False,
                                "order_status": status,
                                "cancel_reason": cancel_reason,
                                "filled_size": order.get("filled_size", "0")
                            }
                
            except Exception as e:
                print(f"Error checking order {order_id}: {e}")
            
            # Wait before retrying
            await asyncio.sleep(1)
        
        # Timeout - order not found
        return {
            "success": False,
            "error": "Order not found within timeout",
            "order_id": order_id
        }
    
    async def get_account_positions_summary(self, account: str) -> Dict:
        """Get summary of account positions."""
        try:
            positions = await self.rise_client.get_all_positions(account)
            
            summary = {
                "total_positions": len(positions),
                "positions": []
            }
            
            for pos in positions:
                market_id = pos.get("market_id")
                size_raw = float(pos.get("size", 0))
                size_btc = size_raw / 1e18
                
                if size_btc != 0:
                    summary["positions"].append({
                        "market_id": market_id,
                        "side": "LONG" if size_btc > 0 else "SHORT",
                        "size": abs(size_btc),
                        "entry_price": float(pos.get("avg_entry_price", 0)) / 1e18,
                        "leverage": float(pos.get("leverage", 0)) / 1e18,
                        "margin_mode": pos.get("margin_mode", "CROSS")
                    })
            
            return summary
            
        except Exception as e:
            return {
                "error": str(e),
                "total_positions": 0,
                "positions": []
            }
    
    async def update_account_trading_data(self, account_id: str, account_address: str) -> Dict:
        """Update account with latest positions and trades."""
        
        # Get positions
        positions_summary = await self.get_account_positions_summary(account_address)
        
        # Get recent trades
        try:
            trades = await self.rise_client.get_account_trade_history(account_address, limit=20)
            recent_trades = []
            
            for trade in trades[:5]:  # Keep last 5 trades
                recent_trades.append({
                    "id": trade.get("id"),
                    "order_id": trade.get("order_id"),
                    "market_id": trade.get("market_id"),
                    "side": trade.get("side"),
                    "price": float(trade.get("price", 0)),
                    "size": float(trade.get("size", 0)),
                    "time": trade.get("time"),
                    "realized_pnl": float(trade.get("realized_pnl", 0))
                })
                
            # Store trades for the account
            # For now, store the trading summary in a separate file
            trading_data = {
                "account_id": account_id,
                "trades": recent_trades,
                "positions": positions_summary["positions"], 
                "last_updated": datetime.now().isoformat()
            }
            
            # Save to a trading data file
            trading_file = self.storage.data_dir / "trading_data.json"
            all_data = {}
            if trading_file.exists():
                with open(trading_file, 'r') as f:
                    all_data = json.loads(f.read())
            
            all_data[account_id] = trading_data
            
            with open(trading_file, 'w') as f:
                f.write(json.dumps(all_data, indent=2))
            
        except Exception as e:
            recent_trades = []
        
        return {
            "positions": positions_summary,
            "recent_trades": recent_trades
        }
    
    async def close(self):
        """Cleanup."""
        await self.rise_client.close()