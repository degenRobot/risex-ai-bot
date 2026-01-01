#!/usr/bin/env python3
"""Test RISE API flow: register signer -> deposit -> place order."""

import asyncio
import sys
from pathlib import Path
from eth_account import Account as EthAccount

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rise_client import RiseClient


async def test_rise_flow():
    """Test complete RISE API flow."""
    print("Testing RISE API Flow")
    print("=" * 50)
    
    rise_client = RiseClient()
    
    # Generate fresh keys
    account = EthAccount.create()
    signer = EthAccount.create()
    
    print(f"\n1. Generated Keys:")
    print(f"   Account: {account.address}")
    print(f"   Signer: {signer.address}")
    
    # Step 1: Register signer
    print(f"\n2. Registering signer...")
    try:
        result = await rise_client.register_signer(
            account.key.hex(),
            signer.key.hex()
        )
        print(f"   Success: {result.get('success', True)}")
        print(f"   Message: {result.get('data', {}).get('message', 'Signer registered')}")
    except Exception as e:
        print(f"   Error: {e}")
        # Continue anyway - signer might already be registered
    
    # Wait a moment
    await asyncio.sleep(2)
    
    # Step 2: Deposit USDC
    print(f"\n3. Depositing USDC (triggers faucet)...")
    try:
        deposit_result = await rise_client.deposit_usdc(
            account.key.hex(),
            amount=100.0
        )
        print(f"   Success: {deposit_result.get('success', True)}")
        print(f"   Data: {deposit_result.get('data', {})}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Wait for faucet
    print("\n   Waiting 5 seconds for faucet...")
    await asyncio.sleep(5)
    
    # Check balance
    print(f"\n4. Checking balance...")
    try:
        balance_data = await rise_client.get_balance(account.address)
        balance = float(balance_data.get('cross_margin_balance', 0))
        print(f"   Cross margin balance: ${balance:.2f}")
        print(f"   Available balance: ${balance_data.get('available_balance', 0)}")
    except Exception as e:
        print(f"   Error: {e}")
        balance = 0
    
    # Get market data
    print(f"\n5. Getting market data...")
    try:
        markets = await rise_client.get_markets()
        btc_market = next((m for m in markets if "BTC" in m.get("base_asset_symbol", "")), None)
        
        if btc_market:
            btc_id = int(btc_market.get("market_id"))
            btc_price = float(btc_market.get("last_price", 0))
            print(f"   BTC Market ID: {btc_id}")
            print(f"   BTC Price: ${btc_price:,.0f}")
        else:
            print("   BTC market not found")
            btc_id = 1
            btc_price = 90000
    except Exception as e:
        print(f"   Error: {e}")
        btc_id = 1
        btc_price = 90000
    
    # Step 3: Place order (if we have balance)
    if balance > 10:
        print(f"\n6. Placing test order...")
        try:
            # Small test order
            size = 0.0001  # Very small BTC amount
            price = btc_price * 0.99  # 1% below market for limit buy
            
            print(f"   Market: BTC (ID: {btc_id})")
            print(f"   Side: buy")
            print(f"   Size: {size} BTC")
            print(f"   Price: ${price:,.2f}")
            
            order_result = await rise_client.place_order(
                account_key=account.key.hex(),
                signer_key=signer.key.hex(),
                market_id=btc_id,
                size=size,
                price=price,
                side="buy",
                order_type="limit"
            )
            
            print(f"   Success: {order_result.get('success', False)}")
            if order_result.get('success'):
                order_data = order_result.get('data', {})
                print(f"   Order ID: {order_data.get('order_id', 'N/A')}")
                print(f"   Status: {order_data.get('status', 'N/A')}")
            else:
                print(f"   Error: {order_result.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"   Order error: {e}")
    else:
        print(f"\n6. Skipping order - insufficient balance (${balance:.2f})")
        print("   Note: Faucet may take up to 30 seconds to credit the account")
    
    await rise_client.close()
    
    print("\n" + "=" * 50)
    print("Test complete!")
    
    return {
        "account": account.address,
        "signer": signer.address,
        "balance": balance,
        "order_placed": balance > 10
    }


if __name__ == "__main__":
    result = asyncio.run(test_rise_flow())
    
    print("\nSummary:")
    print(f"Account: {result['account']}")
    print(f"Balance: ${result['balance']:.2f}")
    print(f"Order placed: {result['order_placed']}")
    
    if result['balance'] == 0:
        print("\nIf balance is 0, try running the test again in 30 seconds.")
        print("The testnet faucet sometimes takes time to credit the account.")