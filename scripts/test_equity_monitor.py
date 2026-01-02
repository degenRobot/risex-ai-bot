#!/usr/bin/env python3
"""Test the equity monitoring service."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.equity_monitor import get_equity_monitor
from app.services.storage import JSONStorage


async def test_equity_monitor():
    """Test equity monitor functionality."""
    print("=" * 60)
    print("🧪 Testing Equity Monitor Service")
    print("=" * 60)
    
    # Get services
    monitor = get_equity_monitor()
    storage = JSONStorage()
    
    # Test 1: Connection test
    print("\n1️⃣  Testing RPC connection...")
    is_connected = await monitor.w3.is_connected()
    print(f"   Connected: {is_connected}")
    
    if not is_connected:
        print("❌ RPC connection failed!")
        return
    
    # Test 2: Single account equity fetch
    print("\n2️⃣  Testing single account equity fetch...")
    
    # Get first account with address
    accounts = storage.get_all_accounts()
    test_account = None
    
    for account_id, account in accounts.items():
        if account.get("address"):
            test_account = account
            test_account["id"] = account_id
            break
    
    if not test_account:
        print("   ⚠️  No accounts with addresses found")
        return
    
    print(f"   Testing account: {test_account.get('handle', 'Unknown')} ({test_account['address'][:8]}...)")
    
    equity = await monitor.fetch_equity(test_account["address"])
    
    if equity is not None:
        print(f"   ✅ Equity: ${equity:,.2f} USDC")
    else:
        print(f"   ❌ Failed to fetch equity")
    
    # Test 3: Update account with equity
    print("\n3️⃣  Testing account equity update...")
    
    success = await monitor.update_account_equity(test_account["id"], test_account["address"])
    
    if success:
        # Check if account was updated
        updated_account = storage.get_account(test_account["id"])
        
        print(f"   ✅ Account updated successfully")
        
        if updated_account:
            print(f"   Latest equity: ${updated_account.latest_equity or 0:,.2f}")
            
            change_1h = updated_account.equity_change_1h
            change_24h = updated_account.equity_change_24h
            
            print(f"   1h change: {f'{change_1h:+.1%}' if change_1h is not None else 'N/A'}")
            print(f"   24h change: {f'{change_24h:+.1%}' if change_24h is not None else 'N/A'}")
            print(f"   Updated at: {updated_account.equity_updated_at or 'Never'}")
    else:
        print("   ❌ Failed to update account equity")
    
    # Test 4: Batch update all accounts
    print("\n4️⃣  Testing batch update for all accounts...")
    
    success, total = await monitor.update_all_accounts()
    print(f"   Updated {success}/{total} accounts successfully")
    
    # Test 5: Check equity snapshots
    print("\n5️⃣  Checking equity snapshots...")
    
    snapshots = storage.get_equity_snapshots(test_account["id"])
    print(f"   Found {len(snapshots)} snapshots for test account")
    
    if snapshots:
        latest = snapshots[-1]
        print(f"   Latest snapshot: ${latest['equity']:,.2f} at {latest['timestamp']}")
    
    # Test 6: Equity summary
    print("\n6️⃣  Getting equity summary...")
    
    summary = monitor.get_equity_summary()
    print(f"   Total equity: ${summary['total_equity_usdc']:,.2f}")
    print(f"   Accounts tracked: {summary['accounts_tracked']}")
    print(f"   Consecutive failures: {summary['consecutive_failures']}")
    
    # Test 7: Test polling (brief)
    print("\n7️⃣  Testing background polling (5 seconds)...")
    
    await monitor.start_polling(interval=2)  # Fast interval for testing
    await asyncio.sleep(5)
    await monitor.stop_polling()
    
    print("   ✅ Polling started and stopped successfully")
    
    # Final summary
    print("\n" + "=" * 60)
    print("✅ Equity monitor tests completed!")
    
    # Show all accounts with equity
    print("\n📊 Account Equity Summary:")
    all_accounts = storage.get_all_accounts()
    
    for account_id, account_data in all_accounts.items():
        if account_data.get("latest_equity") is not None:
            print(f"   {account_data.get('handle', 'Unknown'):20} ${account_data['latest_equity']:>12,.2f}")


async def main():
    """Run equity monitor tests."""
    await test_equity_monitor()


if __name__ == "__main__":
    asyncio.run(main())