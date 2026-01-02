"""RISE API client with gasless trading support."""

import asyncio
import random
import time
from typing import Any, Dict, List, Optional

import httpx
from eth_abi.packed import encode_packed
from eth_account import Account as EthAccount
from eth_account.messages import encode_structured_data
from eth_utils import keccak
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings


class RiseAPIError(Exception):
    """RISE API error with details."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class RiseClient:
    """Simplified RISE API client for gasless trading."""
    
    def __init__(self):
        self.base_url = settings.rise_api_base
        self.chain_id = settings.rise_chain_id
        self.domain: Optional[Dict] = None
    
    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with error handling."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method, f"{self.base_url}{path}", **kwargs, timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                error_detail = f"HTTP {e.response.status_code}"
                try:
                    error_data = e.response.json()
                    error_detail = error_data.get("message", error_detail)
                    # Include more error details
                    if "error" in error_data:
                        error_detail = f"{error_detail}: {error_data['error']}"
                    if "details" in error_data:
                        error_detail = f"{error_detail} - {error_data['details']}"
                except Exception:
                    error_detail = f"{error_detail}: {e.response.text[:200]}"
                raise RiseAPIError(f"API request failed: {error_detail}", e.response.status_code)
            except Exception as e:
                raise RiseAPIError(f"Request failed: {str(e)}")
    
    async def get_eip712_domain(self) -> Dict[str, Any]:
        """Get EIP-712 domain for message signing."""
        if self.domain:
            return self.domain
        
        response = await self._request("GET", "/v1/auth/eip712-domain")
        raw_domain = response["data"]
        
        # Format for EIP-712 compatibility
        self.domain = {
            "name": raw_domain["name"],
            "version": raw_domain["version"],
            "chainId": int(raw_domain["chain_id"]),
            "verifyingContract": raw_domain["verifying_contract"],
        }
        return self.domain
    
    async def get_account_nonce(self, account: str) -> int:
        """Get nonce for account registration."""
        response = await self._request(
            "POST", "/v1/auth/nonce",
            json={"account": account}
        )
        nonce_data = response.get("data", response)
        return int(nonce_data["nonce"])
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def register_signer(
        self,
        account_key: str,
        signer_key: str
    ) -> Dict[str, Any]:
        """Register signer for gasless trading."""
        # Get addresses
        account = EthAccount.from_key(account_key)
        signer = EthAccount.from_key(signer_key)
        
        if account.address == signer.address:
            raise ValueError("Account and signer must be different addresses for security")
        
        # Get domain and nonce
        domain = await self.get_eip712_domain()
        nonce = await self.get_account_nonce(account.address)
        
        # Registration parameters
        message = "RISEx Signer Registration"
        expiration = int(time.time()) + (30 * 24 * 60 * 60)  # 30 days
        
        # Create RegisterSigner message (account signs)
        register_data = {
            "domain": domain,
            "message": {
                "signer": signer.address,
                "message": message,
                "expiration": expiration,
                "nonce": nonce,
            },
            "primaryType": "RegisterSigner",
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "RegisterSigner": [
                    {"name": "signer", "type": "address"},
                    {"name": "message", "type": "string"},
                    {"name": "expiration", "type": "uint40"},
                    {"name": "nonce", "type": "uint256"},
                ],
            },
        }
        account_signature = self._sign_typed_data(register_data, account_key)
        
        # Create VerifySigner message (signer signs)
        verify_data = {
            "domain": domain,
            "message": {
                "account": account.address,
                "nonce": nonce,
            },
            "primaryType": "VerifySigner",
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "VerifySigner": [
                    {"name": "account", "type": "address"},
                    {"name": "nonce", "type": "uint256"},
                ],
            },
        }
        signer_signature = self._sign_typed_data(verify_data, signer_key)
        
        # Register with API
        return await self._request(
            "POST", "/v1/auth/register-signer",
            json={
                "account": account.address,
                "signer": signer.address,
                "message": message,
                "expiration": expiration,
                "nonce": str(nonce),
                "account_signature": account_signature,
                "signer_signature": signer_signature,
            }
        )
    
    async def get_markets(self) -> List[Dict[str, Any]]:
        """Get available trading markets."""
        response = await self._request("GET", "/v1/markets")
        return response.get("data", {}).get("markets", [])
    
    async def get_position(self, account: str, market_id: int) -> Dict[str, Any]:
        """Get account position for specific market."""
        response = await self._request(
            "GET", "/v1/account/position",
            params={"account": account, "market_id": market_id}
        )
        return response.get("data", {}).get("position", {})
    
    async def get_all_positions(self, account: str) -> List[Dict[str, Any]]:
        """Get all positions for account."""
        response = await self._request(
            "GET", "/v1/positions",
            params={"account": account}
        )
        return response.get("positions", [])
    
    async def get_balance(self, account: str) -> Dict[str, Any]:
        """Get account balance."""
        # RISE uses cross-margin balance, not token balance
        response = await self._request(
            "GET", f"/v1/accounts/{account}"
        )
        return response.get("data", {})
    
    async def get_market_data(self, market_id: int, resolution: str = "1D", limit: int = 100) -> List[Dict[str, Any]]:
        """Get trading view data for a market using the correct endpoint."""
        response = await self._request(
            "GET", f"/v1/markets/id/{market_id}/trading-view-data",
            params={"resolution": resolution, "limit": limit}
        )
        data = response.get("data", [])
        
        # Ensure we return a list even if API returns something else
        if not isinstance(data, list):
            return []
        
        return data
    
    async def get_latest_price(self, market_id: int) -> Optional[float]:
        """Get latest price for a market."""
        try:
            data = await self.get_market_data(market_id, resolution="1H", limit=1)
            if data and len(data) > 0:
                return float(data[-1].get("close", 0))
        except Exception:
            pass
        return None
    
    async def get_trade_history(self, account: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get account trade history."""
        response = await self._request(
            "GET", "/v1/account/trade-history",
            params={"account": account, "limit": limit}
        )
        data = response.get("data", [])
        
        # Ensure we return a list
        if not isinstance(data, list):
            return []
        
        return data
    
    async def place_market_order(
        self,
        account_key: str,
        signer_key: str,
        market_id: int,
        size: float,
        side: str,
        reduce_only: bool = False,
        check_success: bool = True
    ) -> Dict[str, Any]:
        """Simplified market order placement with success detection.
        
        Note: RISE testnet requires limit orders with price=0 for market-like behavior.
        Using order_type="limit" with price=0 and TIF=3 (IOC) achieves market order execution.
        
        Args:
            account_key: Main account private key
            signer_key: Signer private key
            market_id: Market ID (1=BTC, 2=ETH, etc)
            size: Order size (e.g., 0.01 for 0.01 BTC)
            side: "buy" or "sell"
            reduce_only: Close position only
            check_success: Check if order was filled (default True)
            
        Returns:
            Order response with enhanced success detection
        """
        # Place the order
        result = await self.place_order(
            account_key=account_key,
            signer_key=signer_key,
            market_id=market_id,
            size=size,
            price=0,  # Price is 0 for market-like behavior
            side=side,
            order_type="limit",  # Use limit order with price=0 (works on testnet)
            tif=3,  # IOC for immediate execution
            reduce_only=reduce_only,
            max_retries=3  # Enable retries for RPC issues
        )
        
        # Extract order ID and check for success
        if check_success and result and "data" in result:
            order_id = result["data"].get("order_id")
            if order_id:
                # Import here to avoid circular dependency
                from .order_tracker import OrderTracker
                
                account = EthAccount.from_key(account_key)
                tracker = OrderTracker()
                
                try:
                    # Check if order was filled
                    success_check = await tracker.check_order_success(
                        account=account.address,
                        order_id=order_id,
                        expected_side=side,
                        expected_size=size,
                        timeout_seconds=10
                    )
                    
                    # Add success info to result
                    result["order_filled"] = success_check.get("success", False)
                    if success_check.get("success"):
                        result["fill_details"] = success_check
                finally:
                    await tracker.close()
        
        return result
    
    async def close_position(
        self,
        account_key: str,
        signer_key: str,
        market_id: int,
    ) -> Optional[Dict[str, Any]]:
        """Close an entire position using market order.
        
        Args:
            account_key: Main account private key
            signer_key: Signer private key
            market_id: Market ID to close
            
        Returns:
            Order response or None if no position
        """
        account = EthAccount.from_key(account_key)
        
        # Get current position
        positions = await self.get_all_positions(account.address)
        position = next((p for p in positions if p.get('market_id') == market_id), None)
        
        if not position:
            return None
            
        # Get position size and side
        size = abs(float(position.get('size', 0)))
        is_long = float(position.get('size', 0)) > 0
        
        # Place opposite market order to close
        close_side = "sell" if is_long else "buy"
        
        return await self.place_market_order(
            account_key=account_key,
            signer_key=signer_key,
            market_id=market_id,
            size=size,
            side=close_side,
            reduce_only=True
        )
    
    async def get_market_prices(self) -> Dict[str, float]:
        """Get current market prices for BTC and ETH.
        
        Returns:
            Dict with 'BTC' and 'ETH' prices
        """
        prices = {}
        
        try:
            # Get BTC price (market_id=1)
            btc_price = await self.get_latest_price(1)
            if btc_price:
                prices['BTC'] = btc_price
                
            # Get ETH price (market_id=2)
            eth_price = await self.get_latest_price(2)
            if eth_price:
                prices['ETH'] = eth_price
                
        except Exception:
            pass
            
        return prices
    
    async def calculate_pnl(self, account: str) -> Dict[str, float]:
        """Calculate P&L for all positions."""
        try:
            positions = await self.get_all_positions(account)
            markets = await self.get_markets()
            
            # Create market ID to symbol mapping
            market_map = {int(m.get("market_id", 0)): m.get("symbol", f"Market_{m.get('market_id')}") for m in markets}
            
            total_pnl = 0.0
            position_pnl = {}
            
            for position in positions:
                market_id = int(position.get("market_id", 0))
                size = float(position.get("size", 0))
                entry_price = float(position.get("entry_price", 0))
                
                if size == 0:  # No position
                    continue
                
                # Get current market price
                current_price = await self.get_latest_price(market_id)
                if not current_price:
                    continue
                
                # Calculate P&L
                pnl = (current_price - entry_price) * size
                if size < 0:  # Short position
                    pnl = -pnl
                
                symbol = market_map.get(market_id, f"Market_{market_id}")
                position_pnl[symbol] = pnl
                total_pnl += pnl
            
            return {
                "total_pnl": total_pnl,
                "positions": position_pnl
            }
            
        except Exception as e:
            print(f"P&L calculation error: {e}")
            return {"total_pnl": 0.0, "positions": {}}
    
    async def deposit_usdc(self, account_key: str, amount: float = 100.0) -> Dict[str, Any]:
        """Deposit USDC to account (triggers faucet on testnet)."""
        account = EthAccount.from_key(account_key)
        
        # Get domain for signing
        domain = await self.get_eip712_domain()
        
        # Convert amount to wei (18 decimals for testnet USDC)
        amount_wei = int(amount * 1e18)
        
        # Create EIP-712 signature for Deposit type
        # Deposit is signed by the MAIN account, not the signer
        typed_data = {
            "domain": domain,
            "message": {
                "account": account.address,
                "amount": amount_wei,
            },
            "primaryType": "Deposit",
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "Deposit": [
                    {"name": "account", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                ]
            }
        }
        
        # Sign with MAIN account private key (not signer!)
        signature = self._sign_typed_data(typed_data, account_key)
        
        # Create nonce using the RISE API algorithm
        nonce = self._create_client_nonce(account.address)
        deadline = int(time.time()) + 300  # 5 minutes
        
        # Prepare deposit request
        # API expects decimal format for amount
        deposit_request = {
            "account": account.address,
            "amount": str(amount),  # Decimal format, not wei
            "permit_params": {
                "account": account.address,
                "signer": account.address,  # For deposits, account signs for itself
                "deadline": str(deadline),  # API expects strings for numbers
                "signature": signature,
                "nonce": str(nonce)  # API expects string for nonce
            }
        }
        
        return await self._request(
            "POST", "/v1/account/deposit",
            json=deposit_request
        )
    
    async def place_order(
        self,
        account_key: str,
        signer_key: str,
        market_id: int,
        size: float,
        price: float,
        side: str,  # "buy" or "sell"
        order_type: str = "limit",  # "limit" or "market"
        tif: int = 3,  # Default to IOC (3) which works on testnet
        post_only: bool = False,
        reduce_only: bool = False,
        max_retries: int = 3,  # Retry for RPC errors
    ) -> Dict[str, Any]:
        """Place a gasless order.
        
        Args:
            account_key: Main account private key
            signer_key: Signer private key (must be different)
            market_id: Market ID (1=BTC, 2=ETH, 3=BNB)
            size: Order size (e.g., 0.01 for 0.01 BTC)
            price: Order price in USDC
            side: "buy" or "sell"
            order_type: "limit" or "market"
            tif: Time-in-force (0=GTC, 1=GTT, 2=FOK, 3=IOC). Default 3 (IOC) works on testnet
            post_only: Maker-only order
            reduce_only: Close position only
            
        Returns:
            Order response with order_id, transaction_hash, etc.
        """
        if EthAccount.from_key(account_key).address == EthAccount.from_key(signer_key).address:
            raise ValueError("Account and signer must be different addresses")
        
        account = EthAccount.from_key(account_key)
        signer = EthAccount.from_key(signer_key)
        
        # Get domain for signing
        domain = await self.get_eip712_domain()
        
        # Convert to raw amounts
        size_raw = int(size * 1e18)
        
        # For market orders, price should be 0
        # For limit orders, price needs proper precision
        if order_type.lower() == "market":
            price_raw = 0
        else:
            # Price might need different precision handling
            price_raw = int(price * 1e18) if price > 0 else 0
        
        # Convert parameters
        side_int = 0 if side.lower() == "buy" else 1
        order_type_int = 1 if order_type.lower() == "market" else 0
        # tif is now a parameter with default 3 (IOC)
        expiry = int(time.time()) + 86400 if tif == 1 else 0  # Only set expiry for GTT
        
        # Encode order for hashing (47-byte format)
        flags = (
            side_int |  # bit 0: side
            (1 if post_only else 0) << 1 |  # bit 1: post_only
            (1 if reduce_only else 0) << 2 |  # bit 2: reduce_only
            (0 << 3)  # bits 3-4: STP mode (cancel taker)
        )
        
        encoded_order = encode_packed(
            ["uint64", "uint128", "uint128", "uint8", "uint8", "uint8", "uint32"],
            [market_id, size_raw, price_raw, flags, order_type_int, tif, expiry],
        )
        
        if len(encoded_order) != 47:
            raise ValueError(f"Encoded order length is {len(encoded_order)}, expected 47 bytes")
        
        order_hash = keccak(encoded_order)
        
        # Create permit signature (signer signs)
        nonce = self._create_client_nonce(account.address)
        deadline = int(time.time()) + 300  # 5 minutes
        target = "0x68cAcD54a8c93A3186BF50bE6b78B761F728E1b4"  # PerpsManager
        
        verify_sig_data = {
            "domain": domain,
            "message": {
                "account": account.address,
                "target": target,
                "hash": order_hash,
                "nonce": nonce,
                "deadline": deadline,
            },
            "primaryType": "VerifySignature",
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "VerifySignature": [
                    {"name": "account", "type": "address"},
                    {"name": "target", "type": "address"},
                    {"name": "hash", "type": "bytes32"},
                    {"name": "nonce", "type": "uint256"},
                    {"name": "deadline", "type": "uint256"},
                ],
            },
        }
        
        signature = self._sign_typed_data(verify_sig_data, signer_key)
        
        # Submit order with retry logic for RPC errors
        order_request = {
            "order_params": {
                "market_id": str(market_id),
                "size": str(size_raw),
                "price": str(price_raw),
                "side": side_int,
                "order_type": order_type_int,
                "tif": tif,
                "post_only": post_only,
                "reduce_only": reduce_only,
                "stp_mode": 0,  # Cancel taker
                "expiry": expiry,
            },
            "permit_params": {
                "account": account.address,
                "signer": signer.address,
                "deadline": str(deadline),
                "signature": signature,
                "nonce": str(nonce),
            }
        }
        
        # Retry logic for RPC node issues
        for attempt in range(max_retries):
            try:
                return await self._request(
                    "POST", "/v1/orders/place",
                    json=order_request
                )
            except RiseAPIError as e:
                # Check if this is the specific RPC error that should be retried
                error_msg = str(e).lower()
                if "missing nonce" in error_msg and "insufficient funds" in error_msg:
                    # This is likely an RPC node issue, not an actual problem
                    if attempt < max_retries - 1:
                        print(f"RPC node error detected (attempt {attempt + 1}/{max_retries}). Retrying...")
                        await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                        
                        # Generate new nonce and deadline for retry
                        nonce = self._create_client_nonce(account.address)
                        deadline = int(time.time()) + 300
                        
                        # Re-sign with new nonce and deadline
                        verify_sig_data["message"]["nonce"] = nonce
                        verify_sig_data["message"]["deadline"] = deadline
                        signature = self._sign_typed_data(verify_sig_data, signer_key)
                        
                        # Update request
                        order_request["permit_params"]["deadline"] = str(deadline)
                        order_request["permit_params"]["signature"] = signature
                        order_request["permit_params"]["nonce"] = str(nonce)
                        
                        continue
                    else:
                        # Final attempt failed
                        raise RiseAPIError(
                            f"Order placement failed after {max_retries} attempts. "
                            "This appears to be an RPC node issue. The order parameters are correct. "
                            f"Original error: {e}",
                            e.status_code,
                            e.details
                        )
                # For other errors, don't retry
                raise
    
    def _sign_typed_data(self, typed_data: Dict, private_key: str) -> str:
        """Sign EIP-712 typed data."""
        message = encode_structured_data(typed_data)
        signed = EthAccount.from_key(private_key).sign_message(message)
        
        # Convert to proper format
        sig = bytearray(signed.signature)
        if len(sig) == 65 and sig[64] in (0, 1):
            sig[64] += 27
        
        return bytes(sig).hex()
    
    def _create_client_nonce(self, address: str) -> int:
        """Create a unique client nonce following RISE API specification."""
        # Milliseconds + 6 random digits to simulate nanoseconds
        rand_6_digits = str(random.randint(0, 999999)).zfill(6)
        base_nonce = f"{int(time.time() * 1000)}{rand_6_digits}"
        
        # Remove last 9 digits to get seconds
        second_of_nonce = base_nonce[:-9]
        
        # Hash the seconds + lowercase address
        hash_input = f"{second_of_nonce}{address.lower()}"
        
        # Java-style hash algorithm
        hash_val = 0
        for char in hash_input:
            hash_val = ((hash_val * 31 + ord(char)) & 0xFFFFFFFF)
            if hash_val >= 0x80000000:
                hash_val -= 0x100000000
        hash_val = hash_val & 0xFFFFFFFF
        
        # Take baseNonce without last 6 digits, then append last 6 digits of hash
        return int(base_nonce[:-6] + str(hash_val)[-6:])
    
    async def close(self):
        """Cleanup method for async context manager."""
        pass
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    # Enhanced API methods for real data
    async def get_transfer_history(self, account: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get account transfer history."""
        response = await self._request(
            "GET", "/v1/account/transfer-history",
            params={"account": account, "limit": limit}
        )
        return response.get("data", [])
    
    async def get_account_trade_history(self, account: str, market_id: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get account trade history with optional market filter."""
        params = {"account": account, "limit": limit}
        if market_id is not None:
            params["market_id"] = market_id
        
        response = await self._request(
            "GET", "/v1/trade-history", 
            params=params
        )
        # Response has trades in a nested data structure
        data = response.get("data", {})
        if isinstance(data, dict):
            return data.get("trades", [])
        return []
    
    async def get_realtime_market_prices(self) -> Dict[str, float]:
        """Get real-time prices for all markets."""
        markets = await self.get_markets()
        prices = {}
        
        for market in markets:
            base_asset = market.get("base_asset_symbol", "")
            last_price = market.get("last_price")
            
            if base_asset and last_price:
                # Extract the base currency (BTC from BTC/USDC)
                symbol = base_asset.split("/")[0] if "/" in base_asset else base_asset
                prices[symbol] = float(last_price)
        
        return prices
    
    async def calculate_24h_change(self, market_id: int) -> float:
        """Calculate 24h price change for a market."""
        try:
            # Get 24h data
            data = await self.get_market_data(market_id, resolution="1H", limit=24)
            if len(data) >= 2:
                current_price = float(data[-1].get("close", 0))
                old_price = float(data[0].get("open", 0))
                
                if old_price > 0:
                    return (current_price - old_price) / old_price
        except Exception:
            pass
        return 0.0
    
    async def get_enhanced_market_data(self) -> Dict[str, Any]:
        """Get comprehensive market data with prices and changes."""
        markets = await self.get_markets()
        market_data = {}
        
        for market in markets:
            market_id = int(market.get("market_id", 0))
            base_asset = market.get("base_asset_symbol", "")
            last_price = market.get("last_price")
            change_24h = market.get("change_24h")
            high_24h = market.get("high_24h")
            low_24h = market.get("low_24h")
            
            # Extract symbol (BTC from BTC/USDC)
            if "/" in base_asset:
                symbol = base_asset.split("/")[0]
                
                if symbol in ["BTC", "ETH"] and last_price:
                    # Convert price change to percentage
                    price_change_pct = 0.0
                    if change_24h and high_24h and low_24h:
                        # change_24h is the absolute price change
                        # Calculate percentage based on price 24h ago
                        price_24h_ago = float(last_price) - float(change_24h)
                        if price_24h_ago > 0:
                            price_change_pct = float(change_24h) / price_24h_ago
                    
                    market_data[f"{symbol.lower()}_price"] = float(last_price)
                    market_data[f"{symbol.lower()}_change"] = price_change_pct
                    market_data[f"{symbol.lower()}_market_id"] = market_id
                    market_data[f"{symbol.lower()}_high_24h"] = float(high_24h) if high_24h else 0
                    market_data[f"{symbol.lower()}_low_24h"] = float(low_24h) if low_24h else 0
        
        return market_data