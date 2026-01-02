#!/usr/bin/env python3
"""
Test re-registering a signer for an existing account.
This is useful when signer keys expire or need rotation.
"""

import asyncio
from datetime import datetime
from eth_account import Account as EthAccount

from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage
from app.models import Account


async def test_reregister_signer():
    """Test re-registering a signer with a new key."""
    print("🔄 Signer Re-registration Test")
    print("="*60)
    
    storage = JSONStorage()
    
    # Get an existing account (or use test account ID)
    accounts = storage.list_accounts()
    if not accounts:
        print("❌ No accounts found")
        return
    
    # Use first account for testing
    account = accounts[0]
    print(f"Testing with account: {account.persona.name if account.persona else account.address}")
    print(f"Current signer: {EthAccount.from_key(account.signer_key).address}")
    
    # Generate new signer key
    new_signer = EthAccount.create()
    print(f"\n🔑 Generated new signer: {new_signer.address}")
    
    try:
        # Register new signer
        async with RiseClient() as client:
            print("\n📝 Registering new signer...")
            
            await client.register_signer(
                account_key=account.private_key,
                signer_key=new_signer.key.hex()
            )
            
            print("✅ New signer registered successfully")
            
            # Update account with new signer
            old_signer = account.signer_key
            account.signer_key = new_signer.key.hex()
            account.registered_at = datetime.utcnow()
            storage.save_account(account)
            
            print("\n✅ Account updated with new signer")
            print(f"   Old signer: {EthAccount.from_key(old_signer).address}")
            print(f"   New signer: {new_signer.address}")
            
            # Test placing an order with new signer
            print("\n🧪 Testing order placement with new signer...")
            
            markets = await client.get_markets()
            btc_market = next((m for m in markets if m.get("base_asset_symbol") == "BTC"), None)
            
            if btc_market:
                try:
                    order = await client.place_order(
                        account_key=account.private_key,
                        signer_key=new_signer.key.hex(),
                        market_id=btc_market["market_id"],
                        side="buy",
                        size=0.0001,  # Very small test order
                        price=0,
                        order_type="market"
                    )
                    print(f"✅ Test order successful: {order.get('orderId')}")
                except Exception as e:
                    print(f"⚠️  Test order failed: {e}")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Re-registration failed: {e}")
        return False


async def test_bulk_reregister():
    """Test re-registering signers for multiple accounts."""
    print("\n\n🔄 Bulk Signer Re-registration Test")
    print("="*60)
    
    storage = JSONStorage()
    accounts = storage.list_accounts()
    
    # Filter accounts that need re-registration (e.g., older than 30 days)
    accounts_to_update = []
    for account in accounts:
        if account.is_registered and account.registered_at:
            days_old = (datetime.utcnow() - account.registered_at).days
            if days_old > 30:  # Example: re-register if older than 30 days
                accounts_to_update.append(account)
    
    if not accounts_to_update:
        print("✅ No accounts need re-registration")
        return
    
    print(f"Found {len(accounts_to_update)} accounts to re-register")
    
    success_count = 0
    failed_count = 0
    
    async with RiseClient() as client:
        for account in accounts_to_update:
            print(f"\n📝 Re-registering: {account.persona.name if account.persona else account.address}")
            
            try:
                # Generate new signer
                new_signer = EthAccount.create()
                
                # Register new signer
                await client.register_signer(
                    account_key=account.private_key,
                    signer_key=new_signer.key.hex()
                )
                
                # Update account
                account.signer_key = new_signer.key.hex()
                account.registered_at = datetime.utcnow()
                storage.save_account(account)
                
                success_count += 1
                print(f"✅ Success: {new_signer.address}")
                
            except Exception as e:
                failed_count += 1
                print(f"❌ Failed: {e}")
    
    print("\n" + "="*60)
    print(f"Re-registration Summary:")
    print(f"✅ Success: {success_count}")
    print(f"❌ Failed: {failed_count}")


if __name__ == "__main__":
    asyncio.run(test_reregister_signer())
    # Uncomment to test bulk re-registration
    # asyncio.run(test_bulk_reregister())