#!/usr/bin/env python3
"""Test AI-driven trading with existing funded account."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage
from app.core.market_manager import get_market_manager
from eth_account import Account as EthAccount
from eth_abi.packed import encode_packed
from eth_utils import keccak
import time


async def ai_trading_decision(market_data):
    """Simulate AI trading decision based on market data."""
    btc_price = market_data.get("btc_price", 90000)
    eth_price = market_data.get("eth_price", 3000)
    btc_change = market_data.get("btc_change", 0)
    
    print("\n🤖 AI Trading Analysis")
    print("=" * 60)
    print(f"BTC: ${btc_price:,.0f} ({btc_change:+.2%})")
    print(f"ETH: ${eth_price:,.0f}")
    
    # Simple AI logic
    if btc_change > 0.02:
        print("\n📈 Analysis: Strong bullish momentum detected")
        print("Decision: LONG BTC")
        return "long", "BTC", "Riding the momentum wave 🚀"
    elif btc_change < -0.02:
        print("\n📉 Analysis: Bearish pressure building")
        print("Decision: SHORT BTC (if we had short capability)")
        return "short", "BTC", "Time to hedge 🛡️"
    else:
        print("\n😴 Analysis: Market consolidating")
        print("Decision: LONG BTC with smaller size")
        return "long", "BTC", "Accumulating during consolidation 📊"


async def test_ai_trading():
    """Test AI-driven trading flow."""
    print("RISE AI Trading Test")
    print("=" * 80)
    
    # Initialize services
    rise_client = RiseClient()
    storage = JSONStorage()
    market_manager = get_market_manager()
    
    # Get first account (should be funded from previous tests)
    accounts = storage.list_accounts()
    if not accounts:
        print("❌ No accounts found!")
        return
    
    account = accounts[0]  # Use first account that we funded earlier
    print(f"\n👤 Using account: {account.address}")
    print(f"   Signer: {EthAccount.from_key(account.signer_key).address}")
    
    # Get market data
    print("\n📊 Fetching market data...")
    await market_manager.get_latest_data(force_update=True)
    
    market_data = {
        "btc_price": market_manager.market_cache.get("btc_price", 90000),
        "eth_price": market_manager.market_cache.get("eth_price", 3000),
        "btc_change": market_manager.market_cache.get("btc_change", 0),
    }
    
    # AI makes trading decision
    decision, asset, reasoning = await ai_trading_decision(market_data)
    
    print(f"\n💭 AI Reasoning: {reasoning}")
    
    # Execute the trade
    if decision == "long" and asset == "BTC":
        # Calculate position size (use small amount for test)
        position_size = 0.01  # 0.01 BTC
        order_price = market_data["btc_price"] * 0.99  # 1% below market
        
        print(f"\n📝 Placing order:")
        print(f"   Asset: {asset}")
        print(f"   Side: BUY (Long)")
        print(f"   Size: {position_size} BTC")
        print(f"   Price: ${order_price:,.2f}")
        print(f"   Value: ${position_size * order_price:,.2f}")
        
        # Place order with IOC (which we know works)
        account_obj = EthAccount.from_key(account.private_key)
        signer_obj = EthAccount.from_key(account.signer_key)
        
        domain = await rise_client.get_eip712_domain()
        
        # Order parameters
        market_id = 1  # BTC
        size_raw = int(position_size * 1e18)
        price_raw = int(order_price * 1e18)
        
        side_int = 0  # buy
        order_type_int = 0  # limit
        tif = 3  # IOC (we know this works)
        expiry = 0
        
        # Encode order
        flags = (
            side_int |
            (0 << 1) |  # post_only = false
            (0 << 2) |  # reduce_only = false
            (0 << 3)    # stp_mode = 0
        )
        
        encoded_order = encode_packed(
            ["uint64", "uint128", "uint128", "uint8", "uint8", "uint8", "uint32"],
            [market_id, size_raw, price_raw, flags, order_type_int, tif, expiry]
        )
        
        order_hash = keccak(encoded_order)
        
        # Create signature
        nonce = rise_client._create_client_nonce(account_obj.address)
        deadline = int(time.time()) + 300
        target = "0x68cAcD54a8c93A3186BF50bE6b78B761F728E1b4"
        
        verify_sig_data = {
            "domain": domain,
            "message": {
                "account": account_obj.address,
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
        
        signature = rise_client._sign_typed_data(verify_sig_data, account.signer_key)
        
        # Place order
        try:
            print("\n⏳ Submitting order...")
            result = await rise_client._request(
                "POST", "/v1/orders/place",
                json={
                    "order_params": {
                        "market_id": str(market_id),
                        "size": str(size_raw),
                        "price": str(price_raw),
                        "side": side_int,
                        "order_type": order_type_int,
                        "tif": tif,
                        "post_only": False,
                        "reduce_only": False,
                        "stp_mode": 0,
                        "expiry": expiry,
                    },
                    "permit_params": {
                        "account": account_obj.address,
                        "signer": signer_obj.address,
                        "deadline": str(deadline),
                        "signature": signature,
                        "nonce": str(nonce),
                    }
                }
            )
            
            print("\n✅ Order placed successfully!")
            print(f"   Order ID: {result['data']['order_id']}")
            print(f"   Transaction: {result['data']['transaction_hash']}")
            print(f"   Status: {result['data']['order']['status']}")
            
            print(f"\n🎉 AI successfully executed a {asset} long position!")
            print(f"   The AI is now managing ${position_size * order_price:,.2f} in {asset}")
            
        except Exception as e:
            print(f"\n❌ Order failed: {e}")
    
    print("\n" + "=" * 80)
    print("AI Trading Summary:")
    print(f"- Market Analysis: {reasoning}")
    print(f"- Decision: {decision.upper()} {asset}")
    print(f"- Execution: {'Success' if 'result' in locals() else 'Failed'}")
    
    # Clean up
    await rise_client.close()
    await market_manager.close()


if __name__ == "__main__":
    print(f"Starting AI trading test at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    asyncio.run(test_ai_trading())