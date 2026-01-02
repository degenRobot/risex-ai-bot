#!/usr/bin/env python3
"""Test trading functionality for curve profiles."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.storage import JSONStorage
from app.services.rise_client import RiseClient
from app.services.equity_monitor import get_equity_monitor
from web3 import AsyncWeb3, AsyncHTTPProvider
from decimal import Decimal


async def test_trading():
    """Test that curve profiles can place trades."""
    
    storage = JSONStorage()
    accounts = storage.list_accounts()
    
    print("🎯 Testing Trading Functionality")
    print("=" * 50)
    
    # Test one small trade per account
    for account in accounts:
        print(f"\n📊 Testing {account.persona.name} ({account.persona.handle})")
        print(f"   Address: {account.address}")
        
        rise_client = RiseClient()
        
        try:
            # Get equity directly from blockchain via RPC
            equity_monitor = get_equity_monitor()
            equity = await equity_monitor.fetch_equity(account.address)
            
            if equity is not None:
                print(f"   ✅ On-chain equity: ${equity:.2f}")
                balance = equity  # Use equity as balance for trading decisions
            else:
                print("   ❌ Could not fetch on-chain equity")
                balance = 0
                
            # Optional: Try RISE API as fallback (but likely unreliable)
            try:
                balance_data = await rise_client.get_balance(account.address)
                if balance_data and "error" not in balance_data:
                    api_balance = float(balance_data.get("balance", 0))
                    print(f"   📡 RISE API balance: ${api_balance:.2f}")
                    if equity is not None and equity != api_balance:
                        print(f"   ⚠️  Mismatch: RPC=${equity:.2f} vs API=${api_balance:.2f}")
            except Exception as e:
                print(f"   ℹ️  RISE API unavailable: {e}")
            
            # Place a small test trade (0.001 BTC)
            if balance > 10:  # Need at least $10
                print(f"   🎲 Placing test trade...")
                
                # Decide side based on personality
                side = "buy" if account.persona.handle in ["leftCurve", "rightCurve"] else "sell"
                
                try:
                    result = await rise_client.place_market_order(
                        account_key=account.private_key,
                        signer_key=account.signer_key,
                        market_id=1,  # BTC
                        side=side,
                        size=0.001  # Small test trade
                    )
                    
                    # Check for successful order placement
                    if result and "data" in result:
                        data = result["data"]
                        if data.get("order_id") and data.get("transaction_hash"):
                            print(f"   ✅ Successfully placed {side} order!")
                            print(f"   Order ID: {data.get('order_id')}")
                            print(f"   TX Hash: {data.get('transaction_hash')[:20]}...")
                            if data.get("receipt", {}).get("status") == 1:
                                print(f"   Confirmed on-chain ✓")
                        else:
                            print(f"   ❌ Order placement issue: {result}")
                    else:
                        print(f"   ❌ Unexpected response: {result}")
                except Exception as e:
                    print(f"   ❌ Error placing order: {e}")
            else:
                print(f"   ⚠️ Insufficient balance for test trade")
                
        except Exception as e:
            print(f"   ❌ Error testing {account.persona.name}: {e}")
        finally:
            await rise_client.close()
        
        # Wait between accounts
        await asyncio.sleep(3)
    
    print("\n✅ Trading test complete!")


if __name__ == "__main__":
    asyncio.run(test_trading())