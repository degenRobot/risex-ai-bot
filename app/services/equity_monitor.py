"""RPC-based account equity monitoring service."""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.exceptions import ContractLogicError

from ..config import settings
from .storage import JSONStorage

# Contract configuration
PERPS_MANAGER_ADDRESS = "0x68cAcD54a8c93A3186BF50bE6b78B761F728E1b4"

# Minimal ABI for getAccountEquity
PERPS_MANAGER_ABI = [
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "getAccountEquity",
        "outputs": [{"name": "", "type": "int256"}],
        "stateMutability": "view",
        "type": "function"
    }
]


class EquityMonitor:
    """Monitor on-chain account equity via RPC calls."""
    
    def __init__(self):
        """Initialize equity monitor with RPC connection."""
        # Use indexing RPC for better reliability
        self.rpc_url = os.getenv("BACKEND_RPC_URL", "https://indexing.testnet.riselabs.xyz")
        self.w3 = AsyncWeb3(AsyncHTTPProvider(self.rpc_url))
        
        # Contract setup
        self.perps_manager = self.w3.eth.contract(
            address=PERPS_MANAGER_ADDRESS,
            abi=PERPS_MANAGER_ABI
        )
        
        # Storage and cache
        self.storage = JSONStorage()
        self.cache: Dict[str, Dict] = {}  # address -> {equity, timestamp, block}
        
        # Configuration
        self.batch_size = int(os.getenv("EQUITY_BATCH_SIZE", "10"))
        self.history_limit = int(os.getenv("EQUITY_HISTORY_LIMIT", "200"))
        
        # State
        self._shutdown = False
        self._update_task: Optional[asyncio.Task] = None
        self.consecutive_failures = 0
        self.max_failures = 5
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Equity monitor initialized with RPC: {self.rpc_url}")
    
    async def fetch_equity(self, address: str) -> Optional[float]:
        """Fetch equity for a single account."""
        try:
            # Ensure address has correct checksum
            address = self.w3.to_checksum_address(address)
            
            # Call contract
            equity_raw = await self.perps_manager.functions.getAccountEquity(address).call()
            
            # PerpsManager returns equity in 18 decimals, convert to USDC
            # Note: While USDC has 6 decimals, RISE internal uses 18 decimals
            equity_usdc = float(equity_raw) / 10**18
            
            # Get current block
            block = await self.w3.eth.get_block("latest")
            
            # Update cache
            self.cache[address] = {
                "equity": equity_usdc,
                "timestamp": datetime.utcnow(),
                "block_number": block["number"],
                "raw_value": str(equity_raw)
            }
            
            return equity_usdc
            
        except ContractLogicError as e:
            self.logger.warning(f"Contract error for {address}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to fetch equity for {address}: {e}")
            return None
    
    async def fetch_equity_batch(self, addresses: List[str]) -> Dict[str, Optional[float]]:
        """Batch fetch equity for multiple accounts."""
        results = {}
        
        # Process in chunks to avoid overwhelming RPC
        for i in range(0, len(addresses), self.batch_size):
            chunk = addresses[i:i + self.batch_size]
            
            # Create tasks for concurrent fetching
            tasks = [self.fetch_equity(addr) for addr in chunk]
            
            # Execute chunk
            chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for addr, result in zip(chunk, chunk_results):
                if isinstance(result, Exception):
                    self.logger.error(f"Batch fetch error for {addr}: {result}")
                    results[addr] = None
                else:
                    results[addr] = result
            
            # Small delay between chunks to avoid rate limiting
            if i + self.batch_size < len(addresses):
                await asyncio.sleep(0.1)
        
        return results
    
    def calculate_equity_changes(self, account_id: str, current_equity: float) -> Dict[str, Optional[float]]:
        """Calculate equity changes over different time periods."""
        snapshots = self.storage.get_equity_snapshots(account_id)
        
        if not snapshots:
            return {"change_1h": None, "change_24h": None}
        
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)
        
        # Find closest snapshots to target times
        equity_1h = None
        equity_24h = None
        
        for snapshot in reversed(snapshots):  # Most recent first
            snap_time = datetime.fromisoformat(snapshot["timestamp"])
            
            if not equity_1h and snap_time <= one_hour_ago:
                equity_1h = snapshot["equity"]
            
            if not equity_24h and snap_time <= one_day_ago:
                equity_24h = snapshot["equity"]
                break
        
        # Calculate percentage changes
        changes = {}
        
        if equity_1h is not None and equity_1h > 0:
            changes["change_1h"] = ((current_equity - equity_1h) / equity_1h) * 100
        else:
            changes["change_1h"] = None
            
        if equity_24h is not None and equity_24h > 0:
            changes["change_24h"] = ((current_equity - equity_24h) / equity_24h) * 100
        else:
            changes["change_24h"] = None
        
        return changes
    
    async def update_account_equity(self, account_id: str, address: str) -> bool:
        """Update equity for a single account."""
        equity = await self.fetch_equity(address)
        
        if equity is None:
            return False
        
        # Save snapshot
        snapshot = {
            "timestamp": datetime.utcnow().isoformat(),
            "equity": equity,
            "block_number": self.cache[address].get("block_number")
        }
        
        self.storage.save_equity_snapshot(account_id, snapshot, limit=self.history_limit)
        
        # Calculate changes
        changes = self.calculate_equity_changes(account_id, equity)
        
        # Update account with latest equity data
        accounts = self.storage.get_all_accounts()
        account_data = accounts.get(account_id)
        
        if account_data:
            account_data["latest_equity"] = equity
            account_data["equity_updated_at"] = datetime.utcnow().isoformat()
            account_data["equity_change_1h"] = changes.get("change_1h")
            account_data["equity_change_24h"] = changes.get("change_24h")
            
            self.storage.save_account(account_id, account_data)
            
            change_1h = changes.get('change_1h')
            change_24h = changes.get('change_24h')
            
            self.logger.info(
                f"Updated equity for {account_data.get('handle', account_id)}: "
                f"${equity:,.2f} (1h: {f'{change_1h:+.1f}%' if change_1h is not None else 'N/A'}, "
                f"24h: {f'{change_24h:+.1f}%' if change_24h is not None else 'N/A'})"
            )
        
        return True
    
    async def update_all_accounts(self) -> Tuple[int, int]:
        """Update equity for all active accounts."""
        self.logger.info("Updating equity for all accounts...")
        
        # Get all accounts
        accounts = self.storage.get_all_accounts()
        
        if not accounts:
            self.logger.warning("No accounts found to update")
            return 0, 0
        
        # Filter to accounts with addresses
        account_map = {
            acc["address"]: account_id 
            for account_id, acc in accounts.items() 
            if acc.get("address")
        }
        
        if not account_map:
            self.logger.warning("No accounts with addresses found")
            return 0, 0
        
        # Batch fetch equity
        addresses = list(account_map.keys())
        equity_results = await self.fetch_equity_batch(addresses)
        
        # Update each account
        success_count = 0
        total_count = len(addresses)
        
        for address, equity in equity_results.items():
            account_id = account_map[address]
            
            if equity is not None:
                # Save snapshot and update account
                await self.update_account_equity(account_id, address)
                success_count += 1
        
        # Reset failure counter on success
        if success_count > 0:
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1
            
            if self.consecutive_failures >= self.max_failures:
                self.logger.error(f"Max consecutive failures ({self.max_failures}) reached!")
        
        self.logger.info(f"Equity update complete: {success_count}/{total_count} successful")
        return success_count, total_count
    
    async def start_polling(self, interval: int = None):
        """Start background polling task."""
        if self._update_task and not self._update_task.done():
            self.logger.warning("Polling already running")
            return
        
        poll_interval = interval or int(os.getenv("EQUITY_POLL_INTERVAL", "60"))
        
        async def poll_loop():
            """Background polling loop."""
            while not self._shutdown:
                try:
                    # Update all accounts
                    await self.update_all_accounts()
                    
                except Exception as e:
                    self.logger.error(f"Polling error: {e}")
                    self.consecutive_failures += 1
                
                # Wait for next cycle (with cancellable sleep)
                try:
                    await asyncio.sleep(poll_interval)
                except asyncio.CancelledError:
                    break
        
        # Start background task
        self._update_task = asyncio.create_task(poll_loop())
        self.logger.info(f"Started equity polling every {poll_interval}s")
    
    async def stop_polling(self):
        """Stop background polling gracefully."""
        self._shutdown = True
        
        if self._update_task and not self._update_task.done():
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Stopped equity polling")
    
    def get_account_equity(self, address: str) -> Optional[Dict]:
        """Get cached equity data for an account."""
        return self.cache.get(address)
    
    def get_equity_summary(self) -> Dict:
        """Get summary of all tracked equity."""
        total_equity = sum(
            data["equity"] 
            for data in self.cache.values() 
            if data.get("equity")
        )
        
        return {
            "total_equity_usdc": total_equity,
            "accounts_tracked": len(self.cache),
            "last_update": max(
                (d["timestamp"] for d in self.cache.values()),
                default=None
            ),
            "consecutive_failures": self.consecutive_failures
        }


# Singleton instance
_equity_monitor: Optional[EquityMonitor] = None


def get_equity_monitor() -> EquityMonitor:
    """Get or create the singleton equity monitor instance."""
    global _equity_monitor
    if _equity_monitor is None:
        _equity_monitor = EquityMonitor()
    return _equity_monitor