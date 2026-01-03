#!/usr/bin/env python3
"""Complete registration and funding for curve profiles."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage


async def complete_registration():
    """Complete registration and funding for any unregistered accounts."""
    
    storage = JSONStorage()
    accounts = storage.list_accounts()
    
    print("🔍 Checking account statuses...")
    print("=" * 50)
    
    unregistered = []
    unfunded = []
    
    for account in accounts:
        print(f"\n{account.persona.name} ({account.persona.handle}):")
        print(f"   Address: {account.address}")
        print(f"   Registered: {'✅' if account.is_registered else '❌'}")
        print(f"   Has deposited: {'✅' if account.has_deposited else '❌'}")
        
        if not account.is_registered:
            unregistered.append(account)
        elif not account.has_deposited:
            unfunded.append(account)
    
    # Try to register unregistered accounts
    if unregistered:
        print(f"\n📝 Found {len(unregistered)} unregistered accounts")
        rise_client = RiseClient()
        
        try:
            for account in unregistered:
                print(f"\nRegistering {account.persona.name}...")
                try:
                    success = await rise_client.register_signer(
                        account_key=account.private_key,
                        signer_key=account.signer_key,
                    )
                    if success:
                        account.is_registered = True
                        storage.save_account(account)
                        print(f"✅ Registered {account.persona.name}")
                        unfunded.append(account)  # Now needs funding
                    else:
                        print(f"❌ Failed to register {account.persona.name}")
                except Exception as e:
                    print(f"❌ Error registering {account.persona.name}: {e}")
                
                await asyncio.sleep(2)
        finally:
            await rise_client.close()
    
    # Try to fund accounts that need it
    if unfunded:
        print(f"\n💰 Found {len(unfunded)} accounts needing deposits")
        rise_client = RiseClient()
        
        try:
            for account in unfunded:
                if not account.is_registered:
                    continue  # Skip if not registered
                
                print(f"\nDepositing for {account.persona.name}...")
                max_retries = 3
                
                for attempt in range(max_retries):
                    try:
                        success = await rise_client.deposit_usdc(
                            account_key=account.private_key,
                            amount=account.deposit_amount or 1000.0,
                        )
                        if success:
                            account.has_deposited = True
                            storage.save_account(account)
                            print(f"✅ Deposited {account.deposit_amount} USDC for {account.persona.name}")
                            break
                        else:
                            print(f"⚠️ Deposit attempt {attempt + 1} failed")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(5)
                    except Exception as e:
                        print(f"⚠️ Deposit attempt {attempt + 1} error: {e}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(5)
                
                await asyncio.sleep(3)
        finally:
            await rise_client.close()
    
    # Final summary
    print("\n📊 Final Status:")
    print("=" * 50)
    
    accounts = storage.list_accounts()  # Refresh
    for account in accounts:
        print(f"\n{account.persona.name} ({account.persona.handle}):")
        print(f"   Address: {account.address}")
        print(f"   Registered: {'✅' if account.is_registered else '❌'}")
        print(f"   Has deposited: {'✅' if account.has_deposited else '❌'}")
        print(f"   Speech style: {account.persona.handle}")


if __name__ == "__main__":
    asyncio.run(complete_registration())