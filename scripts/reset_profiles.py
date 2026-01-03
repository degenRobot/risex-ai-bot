#!/usr/bin/env python3
"""Reset all profiles and create 3 clean, funded profiles."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.account_creator import create_fresh_profile
from app.services.equity_monitor import get_equity_monitor
from app.services.storage import JSONStorage


async def main():
    """Clean up all profiles and create 3 fresh ones."""
    print("🧹 RESETTING ALL PROFILES")
    print("=" * 50)
    
    # Initialize storage
    storage = JSONStorage()
    
    # Step 1: Backup existing data
    print("\n1. Backing up existing data...")
    backup_result = storage.backup_data()
    print(f"✅ {backup_result}")
    
    # Step 2: Clear all accounts
    print("\n2. Clearing all existing accounts...")
    accounts_file = storage.accounts_file
    with open(accounts_file, "w") as f:
        json.dump({}, f, indent=2)
    print("✅ All accounts cleared")
    
    # Step 3: Create 3 fresh profiles with different personalities
    profiles = [
        ("cynical", "Bear Trader Bob", 1000.0),     # Conservative, skeptical
        ("leftCurve", "Degen Dave", 1000.0),        # Aggressive, easily influenced
        ("midwit", "Technical Terry", 1000.0),       # Overconfident analyst
    ]
    
    created_profiles = []
    
    print("\n3. Creating fresh profiles...")
    for personality, nickname, deposit in profiles:
        print(f"\n🤖 Creating {nickname} ({personality})...")
        try:
            account_id, account = await create_fresh_profile(
                personality_type=personality,
                deposit_amount=deposit,
            )
            
            # Update the name for clarity
            account.persona.name = nickname
            storage.save_account(account)
            
            created_profiles.append({
                "account_id": account_id,
                "name": nickname,
                "personality": personality,
                "address": account.address,
                "deposit": deposit,
            })
            
            print(f"✅ Created: {nickname}")
            print(f"   ID: {account_id}")
            print(f"   Address: {account.address}")
            print(f"   Deposit: ${deposit}")
            
        except Exception as e:
            print(f"❌ Failed to create {nickname}: {e}")
    
    # Step 4: Verify equity for all created profiles
    if created_profiles:
        print("\n4. Verifying equity for all profiles...")
        equity_monitor = get_equity_monitor()
        
        for profile in created_profiles:
            try:
                equity = await equity_monitor.fetch_equity(profile["address"])
                print(f"✅ {profile['name']}: ${equity or 0:,.2f}")
            except Exception as e:
                print(f"⚠️  {profile['name']}: Could not fetch equity - {e}")
    
    # Step 5: Summary
    print("\n" + "=" * 50)
    print("✅ PROFILE RESET COMPLETE!")
    print(f"\nCreated {len(created_profiles)} profiles:")
    for i, profile in enumerate(created_profiles, 1):
        print(f"\n{i}. {profile['name']} ({profile['personality']})")
        print(f"   ID: {profile['account_id']}")
        print(f"   Address: {profile['address']}")
        print(f"   Initial deposit: ${profile['deposit']}")
    
    print("\n💡 Next steps:")
    print("1. Update API to show net P&L")
    print("2. Fix duplicate handles issue")
    print("3. Deploy to Fly.io")
    
    # Close connections
    await equity_monitor.close()


if __name__ == "__main__":
    asyncio.run(main())