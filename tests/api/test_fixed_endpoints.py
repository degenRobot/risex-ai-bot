#!/usr/bin/env python3
"""Test fixed API endpoints for P&L and balance calculations."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.equity_monitor import get_equity_monitor
from app.services.profile_chat import ProfileChatService
from app.services.storage import JSONStorage


async def test_api_fixes():
    """Test API fixes for P&L and balance calculations."""
    
    storage = JSONStorage()
    chat_service = ProfileChatService()
    equity_monitor = get_equity_monitor()
    
    print("🔍 Testing API Fixes")
    print("=" * 50)
    
    # Get all accounts
    accounts = storage.list_accounts()
    
    for account in accounts:
        print(f"\n👤 Testing {account.persona.name} ({account.persona.handle})")
        print(f"   Address: {account.address}")
        print(f"   Deposit Amount: ${account.deposit_amount}")
        
        # Test 0: Fetch equity directly
        print("\n🔍 Direct Equity Check:")
        direct_equity = await equity_monitor.fetch_equity(account.address)
        if direct_equity is not None:
            print(f"   Direct Equity (RPC): ${direct_equity:,.2f}")
        
        # Test 1: Get trading context
        print("\n📊 Trading Context:")
        context = await chat_service.get_profile_context(account)
        print(f"   Context Keys: {list(context.keys())}")
        
        # Display results
        current_equity = context.get("current_equity")
        print(f"   Raw equity value: {current_equity} (type: {type(current_equity)})")
        
        # Convert values for display
        current_equity_val = float(current_equity) if current_equity else 0.0
        current_pnl = context.get("current_pnl", 0) or 0
        available_balance = context.get("available_balance", 0) or 0
        open_positions = context.get("open_positions", 0) or 0
        
        print(f"   Current Equity: ${current_equity_val:,.2f}")
        print(f"   Current P&L: ${current_pnl:,.2f}")
        print(f"   Available Balance: ${available_balance:,.2f}")
        print(f"   Open Positions: {open_positions}")
        
        # Verify P&L calculation
        if context.get("current_equity"):
            expected_pnl = context["current_equity"] - account.deposit_amount
            actual_pnl = context.get("current_pnl", 0)
            print("\n   ✅ P&L Verification:")
            print(f"      Expected: ${expected_pnl:,.2f}")
            print(f"      Actual: ${actual_pnl:,.2f}")
            print(f"      Match: {'YES' if abs(expected_pnl - actual_pnl) < 0.01 else 'NO'}")
        
        # Test 2: Check free margin directly
        print("\n💰 Free Margin Check:")
        try:
            free_margin = await equity_monitor.fetch_free_margin(account.address)
            if free_margin is not None:
                print(f"   Free Margin (RPC): ${free_margin:,.2f}")
                print(f"   Available Balance (API): ${context.get('available_balance', 0):,.2f}")
                print(f"   Match: {'YES' if abs(free_margin - context.get('available_balance', 0)) < 0.01 else 'NO'}")
            else:
                print("   Free Margin: Unable to fetch")
        except Exception as e:
            print(f"   Error fetching free margin: {e}")
        
        # Test 3: Check positions
        if context.get("positions"):
            print(f"\n📈 Positions ({len(context['positions'])} total):")
            for pos in context["positions"]:
                print(f"   - {pos.get('market', 'Unknown')}: "
                      f"Size={pos.get('size', 0)}, "
                      f"Side={pos.get('side', 'Unknown')}")
    
    print("\n✅ API Fix Test Complete!")


if __name__ == "__main__":
    asyncio.run(test_api_fixes())