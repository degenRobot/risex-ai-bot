"""RISE API client with gasless trading support."""

import asyncio
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
                except Exception:
                    pass
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
            "GET", "/v1/account/positions",
            params={"account": account}
        )
        return response.get("data", {}).get("positions", [])
    
    async def get_balance(self, account: str) -> Dict[str, Any]:
        """Get account balance."""
        response = await self._request(
            "GET", "/v1/account/balance",
            params={"account": account}
        )
        return response.get("data", {})
    
    async def get_market_data(self, market_id: int, resolution: str = "1D", limit: int = 100) -> List[Dict[str, Any]]:
        """Get trading view data for a market."""
        response = await self._request(
            "GET", f"/v1/markets/{market_id}/trading-view-data",
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
    
    async def deposit_usdc(self, account_key: str, amount: float) -> Dict[str, Any]:
        """Deposit USDC to PerpsManager contract."""
        account = EthAccount.from_key(account_key)
        
        # Get domain for signing
        domain = await self.get_eip712_domain()
        
        # Create Deposit message (signed by main account, not signer)
        amount_wei = int(amount * 10**18)  # Convert to wei
        
        deposit_data = {
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
                ],
            },
        }
        
        signature = self._sign_typed_data(deposit_data, account_key)
        
        # Create permit parameters  
        nonce = int(time.time() * 1_000_000_000)  # Nanosecond timestamp
        deadline = int(time.time()) + 300  # 5 minutes
        
        # Submit deposit
        return await self._request(
            "POST", "/v1/account/deposit",
            json={
                "account": account.address,
                "amount": str(amount),  # API expects decimal format
                "permit_params": {
                    "account": account.address,
                    "signer": account.address,  # For deposits, account signs for itself
                    "deadline": deadline,
                    "signature": signature,
                    "nonce": str(nonce),
                }
            }
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
        post_only: bool = False,
        reduce_only: bool = False,
    ) -> Dict[str, Any]:
        """Place a gasless order."""
        if EthAccount.from_key(account_key).address == EthAccount.from_key(signer_key).address:
            raise ValueError("Account and signer must be different addresses")
        
        account = EthAccount.from_key(account_key)
        signer = EthAccount.from_key(signer_key)
        
        # Get domain for signing
        domain = await self.get_eip712_domain()
        
        # Convert to raw amounts (wei)
        size_raw = int(size * 1e18)
        price_raw = int(price * 1e18)
        
        # Convert parameters
        side_int = 0 if side.lower() == "buy" else 1
        order_type_int = 1 if order_type.lower() == "market" else 0
        tif = 0  # GTC (Good Till Cancelled)
        expiry = int(time.time()) + 86400  # 24 hours
        
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
        nonce = int(time.time() * 1_000_000_000)  # Nanosecond timestamp
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
        
        # Submit order
        return await self._request(
            "POST", "/v1/orders/place",
            json={
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
        )
    
    def _sign_typed_data(self, typed_data: Dict, private_key: str) -> str:
        """Sign EIP-712 typed data."""
        message = encode_structured_data(typed_data)
        signed = EthAccount.from_key(private_key).sign_message(message)
        
        # Convert to proper format
        sig = bytearray(signed.signature)
        if len(sig) == 65 and sig[64] in (0, 1):
            sig[64] += 27
        
        return bytes(sig).hex()
    
    async def close(self):
        """Cleanup method for async context manager."""
        pass
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()