#!/usr/bin/env python3
"""
Test order placement with an existing account that might be whitelisted.
This avoids the new account registration/deposit issues.
"""

import asyncio
import json
from datetime import datetime

from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage
from app.models import Trade


async def test_with_existing_account():
    """Test order placement with an existing account."""
    print("🧪 Existing Account Order Test")
    print("="*60)
    
    storage = JSONStorage()
    
    # Get existing accounts
    accounts = storage.list_accounts()
    
    # Filter for accounts that have been deposited to
    deposited_accounts = [acc for acc in accounts if acc.has_deposited]
    
    if not deposited_accounts:
        print("❌ No accounts found with deposits")
        return
    
    # Use the first account with deposits
    account = deposited_accounts[0]
    
    print(f"Using account: {account.persona.name if account.persona else account.address}")
    print(f"Address: {account.address}")
    print(f"Has deposited: {account.has_deposited}")
    print(f"Deposit amount: ${account.deposit_amount if account.deposit_amount else 0}")
    
    async with RiseClient() as client:
        # 1. Check account balance
        print("\n💰 Checking Balance")
        print("-"*40)
        
        try:
            balance_info = await client.get_balance(account.address)
            margin_summary = balance_info.get("marginSummary", {})
            
            print(f"Account Value: ${margin_summary.get('accountValue', 0):,.2f}")
            print(f"Free Collateral: ${margin_summary.get('freeCollateral', 0):,.2f}")
        except Exception as e:
            print(f"⚠️  Balance check failed: {e}")
        
        # 2. Check current positions
        print("\n📊 Current Positions")
        print("-"*40)
        
        try:
            positions = await client.get_all_positions(account.address)
            if positions:
                for pos in positions:
                    print(f"- {pos.get('market', 'Unknown')}: {pos.get('size', 0)} @ ${pos.get('avgPrice', 0):,.2f}")
            else:
                print("No open positions")
        except Exception as e:
            print(f"⚠️  Position check failed: {e}")
        
        # 3. Check market status
        print("\n🏪 Market Status")
        print("-"*40)
        
        markets = await client.get_markets()
        btc_market = next((m for m in markets if int(m.get("market_id", 0)) == 1), None)
        
        if btc_market:
            print(f"BTC Market:")
            print(f"  Symbol: {btc_market.get('symbol', 'BTC-USD')}")
            print(f"  Last Price: ${float(btc_market.get('last_price', 0)):,.2f}")
            print(f"  Available: {btc_market.get('available', False)}")
            print(f"  Min Size: {btc_market.get('min_size', 'N/A')}")
            print(f"  Max Leverage: {btc_market.get('max_leverage', 'N/A')}")
        
        # 4. Attempt to place order
        print("\n📈 Attempting Order")
        print("-"*40)
        
        if btc_market and btc_market.get('available', False):
            try:
                # Place very small market order
                order_size = 0.0001  # Very small order
                
                print(f"Placing order: BUY {order_size} BTC (market order)")
                
                order = await client.place_order(
                    account_key=account.private_key,
                    signer_key=account.signer_key,
                    market_id=1,  # BTC
                    side="buy",
                    size=order_size,
                    price=0,  # Market order
                    order_type="market"
                )
                
                print(f"✅ Order placed successfully!")
                print(f"   Order ID: {order.get('orderId')}")
                print(f"   TX Hash: {order.get('txHash')}")
                
                # Save trade
                trade = Trade(
                    id=f"trade-{int(datetime.now().timestamp())}",
                    account_id=account.id,
                    market="BTC-USD",
                    market_id=1,
                    side="buy",
                    size=order_size,
                    price=order.get("price", 0),
                    reasoning="Test order with existing account",
                    timestamp=datetime.utcnow(),
                    order_id=order.get("orderId"),
                    status="submitted"
                )
                storage.save_trade(trade)
                
            except Exception as e:
                print(f"❌ Order failed: {e}")
        else:
            print("⚠️  Market unavailable - skipping order")
            print("\nThis is expected behavior on testnet when markets are disabled")
            print("Orders will work when:")
            print("1. Markets show 'available: true'")
            print("2. Account is whitelisted")
            print("3. Account has sufficient balance")


async def check_all_accounts_status():
    """Check status of all accounts to find whitelisted ones."""
    print("\n\n🔍 Checking All Accounts Status")
    print("="*60)
    
    storage = JSONStorage()
    accounts = storage.list_accounts()
    
    whitelisted = []
    
    async with RiseClient() as client:
        for account in accounts[:5]:  # Check first 5
            print(f"\nChecking: {account.persona.name if account.persona else account.address[:8]}")
            
            try:
                # Try to get balance (will fail if not whitelisted)
                balance_info = await client.get_balance(account.address)
                margin_summary = balance_info.get("marginSummary", {})
                balance = margin_summary.get("accountValue", 0)
                
                if balance > 0:
                    whitelisted.append({
                        "account": account,
                        "balance": balance
                    })
                    print(f"✅ Whitelisted - Balance: ${balance:,.2f}")
                else:
                    print(f"⚠️  No balance")
                    
            except Exception as e:
                print(f"❌ Not whitelisted or error: {str(e)[:50]}...")
    
    if whitelisted:
        print(f"\n✅ Found {len(whitelisted)} whitelisted accounts with balance")
        for item in whitelisted:
            acc = item["account"]
            print(f"   - {acc.persona.name}: ${item['balance']:,.2f}")
    else:
        print("\n❌ No whitelisted accounts found with balance")
        print("All new accounts need to be whitelisted by RISE team")


async def main():
    """Run tests."""
    await test_with_existing_account()
    await check_all_accounts_status()


if __name__ == "__main__":
    asyncio.run(main())