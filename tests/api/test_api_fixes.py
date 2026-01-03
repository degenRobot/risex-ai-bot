#!/usr/bin/env python3
"""Test API fixes for APIFIXES.md issues."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.api.server import get_profile_summary, list_profiles
from app.services.storage import JSONStorage


async def test_fixes():
    """Test all API fixes."""
    print("🧪 Testing API Fixes")
    print("=" * 50)
    
    storage = JSONStorage()
    
    # Test 1: Check duplicate handles are removed
    print("\n1. Testing duplicate handle removal...")
    try:
        response = await list_profiles(page=1, limit=100)
        handles_seen = set()
        duplicates = []
        
        for profile in response.profiles:
            if profile.handle in handles_seen:
                duplicates.append(profile.handle)
            handles_seen.add(profile.handle)
        
        if duplicates:
            print(f"❌ Found duplicate handles: {duplicates}")
        else:
            print(f"✅ No duplicate handles found ({len(handles_seen)} unique profiles)")
    except Exception as e:
        print(f"❌ Error testing profiles endpoint: {e}")
    
    # Test 2: Check net P&L calculation
    print("\n2. Testing net P&L calculation...")
    try:
        response = await list_profiles(page=1, limit=10)
        
        for profile in response.profiles[:3]:  # Check first 3
            print(f"\n   {profile.name}:")
            print(f"   - Current equity: ${profile.current_equity or 0:.2f}")
            print(f"   - Net P&L: ${profile.net_pnl:.2f}")
            print(f"   - Has equity data: {'Yes' if profile.current_equity is not None else 'No'}")
        
        print("✅ Net P&L fields present")
    except Exception as e:
        print(f"❌ Error checking net P&L: {e}")
    
    # Test 3: Check core_beliefs type consistency
    print("\n3. Testing core_beliefs type consistency...")
    try:
        accounts = storage.list_accounts()
        if accounts:
            account_id = accounts[0].id
            summary = await get_profile_summary(account_id)
            
            if "error" not in summary:
                core_beliefs = summary["profile"]["core_beliefs"]
                if isinstance(core_beliefs, list):
                    print(f"✅ core_beliefs is array type: {type(core_beliefs)}")
                    print(f"   Sample: {core_beliefs[:2] if core_beliefs else '[]'}")
                else:
                    print(f"❌ core_beliefs wrong type: {type(core_beliefs)}")
            else:
                print(f"❌ Could not fetch summary: {summary['error']}")
        else:
            print("⚠️  No accounts to test")
    except Exception as e:
        print(f"❌ Error testing core_beliefs: {e}")
    
    # Test 4: Check pending_actions type
    print("\n4. Testing pending_actions type...")
    try:
        response = await list_profiles(page=1, limit=10)
        
        for profile in response.profiles[:3]:
            if not isinstance(profile.pending_actions, int):
                print(f"❌ {profile.name} has wrong pending_actions type: {type(profile.pending_actions)}")
            else:
                print(f"✅ {profile.name} pending_actions is int: {profile.pending_actions}")
    except Exception as e:
        print(f"❌ Error testing pending_actions: {e}")
    
    print("\n" + "=" * 50)
    print("Testing complete!")


def main():
    """Run tests."""
    try:
        # Need to run in event loop for async functions
        import nest_asyncio
        nest_asyncio.apply()
        asyncio.run(test_fixes())
    except ImportError:
        # Fallback if nest_asyncio not available
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(test_fixes())


if __name__ == "__main__":
    main()