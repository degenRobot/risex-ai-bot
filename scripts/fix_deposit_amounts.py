#!/usr/bin/env python3
"""Fix deposit amounts to reflect actual starting balances."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.storage import JSONStorage


def fix_deposits():
    """Update accounts with correct deposit amounts."""
    
    storage = JSONStorage()
    accounts = storage.list_accounts()
    
    print("🔧 Fixing Deposit Amounts")
    print("=" * 50)
    
    # Correct deposit amounts based on analysis
    correct_deposits = {
        "0x076652bc49B7818604F397f0320937248382301b": 3000.0,  # Drunk Wassie
        "0x41972911b53D5B038c4c35F610e31963F60FaAd5": 2000.0,  # Midwit McGee  
        "0x5D8D12297Ca25AD78607d4ff37dd07889d5E57B5": 2000.0,  # Wise Chad
    }
    
    updated = 0
    for account in accounts:
        if account.address in correct_deposits:
            old_amount = account.deposit_amount
            new_amount = correct_deposits[account.address]
            
            if old_amount != new_amount:
                account.deposit_amount = new_amount
                storage.save_account(account)
                print(f"\n✅ Updated {account.persona.name}:")
                print(f"   Address: {account.address}")
                print(f"   Old deposit: ${old_amount}")
                print(f"   New deposit: ${new_amount}")
                updated += 1
    
    print(f"\n📊 Summary: Updated {updated} accounts")
    
    # Verify the updates
    print("\n🔍 Verifying updates:")
    accounts = storage.list_accounts()  # Reload
    for account in accounts:
        print(f"   {account.persona.name}: ${account.deposit_amount}")


if __name__ == "__main__":
    fix_deposits()