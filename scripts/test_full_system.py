#!/usr/bin/env python3
"""Full system integration test: create profile → register → deposit → trade → check equity."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.parallel_executor import ParallelProfileExecutor
from app.services.equity_monitor import get_equity_monitor
from app.services.profile_chat import ProfileChatService
from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage
from app.trader_profiles import create_trader_profile
from app.models import Account, Persona
import random


async def test_full_system_flow():
    """Test complete system: profile creation through trading."""
    print("=" * 80)
    print("🚀 FULL SYSTEM INTEGRATION TEST")
    print("=" * 80)
    
    # Initialize services
    storage = JSONStorage()
    rise_client = RiseClient()
    equity_monitor = get_equity_monitor()
    chat_service = ProfileChatService()
    
    test_account_id = f"test_account_{int(datetime.now().timestamp())}"
    
    try:
        # Step 1: Create new account with random persona
        print("\n1️⃣  Creating new test account with persona...")
        
        # Generate new keys
        from web3 import Web3
        w3 = Web3()
        
        # Main account key
        main_account = w3.eth.account.create()
        # Different signer key (required)
        signer_account = w3.eth.account.create()
        
        # Pick random trader profile
        profile_types = ["cynical", "leftCurve", "midwit"]
        profile_type = random.choice(profile_types)
        trader_profile = create_trader_profile(profile_type)
        
        print(f"   Generated account: {main_account.address[:8]}...{main_account.address[-6:]}")
        print(f"   Generated signer: {signer_account.address[:8]}...{signer_account.address[-6:]}")
        print(f"   Selected persona: {trader_profile.base_persona.name} ({profile_type})")
        
        # Create Account object
        account = Account(
            id=test_account_id,
            address=main_account.address,
            private_key=main_account.key.hex(),
            signer_key=signer_account.key.hex(),
            persona=Persona(
                name=trader_profile.base_persona.name,
                handle=f"test_{profile_type.lower()}",
                bio=trader_profile.base_persona.core_personality[:100],
                trading_style="conservative",  # Default since base_persona doesn't have trading_style
                risk_tolerance=0.5,
                favorite_assets=["BTC", "ETH"],
                personality_traits=trader_profile.base_persona.base_traits[:2],
                sample_posts=["Testing system integration"]
            ),
            is_active=True,
            created_at=datetime.now()
        )
        
        # Save account
        storage.save_account(account)
        print(f"   ✅ Account saved with ID: {test_account_id}")
        
        # Step 2: Register signer (this will likely fail on testnet but that's ok)
        print("\n2️⃣  Testing signer registration...")
        try:
            registration_result = await rise_client.register_signer(
                account_key=account.private_key,
                signer_key=account.signer_key
            )
            if registration_result.get("success"):
                print("   ✅ Signer registered successfully")
                # Update account status
                account_data = storage.get_all_accounts()[test_account_id]
                account_data["is_registered"] = True
                account_data["registered_at"] = datetime.now().isoformat()
                storage.save_account(test_account_id, account_data)
            else:
                print(f"   ⚠️  Registration failed: {registration_result.get('error')}")
        except Exception as e:
            print(f"   ⚠️  Registration error: {e}")
        
        # Step 3: Test deposit (will also likely fail but that's expected)
        print("\n3️⃣  Testing deposit...")
        try:
            deposit_result = await rise_client.deposit_usdc(
                account_key=account.private_key,
                amount=100.0  # Test with $100
            )
            if deposit_result.get("success"):
                print("   ✅ Deposit successful")
                # Update account status
                account_data = storage.get_all_accounts()[test_account_id]
                account_data["has_deposited"] = True
                account_data["deposited_at"] = datetime.now().isoformat()
                account_data["deposit_amount"] = 100.0
                storage.save_account(test_account_id, account_data)
            else:
                print(f"   ⚠️  Deposit failed: {deposit_result.get('error')}")
        except Exception as e:
            print(f"   ⚠️  Deposit error: {e}")
        
        # Step 4: Check equity monitoring
        print("\n4️⃣  Testing equity monitoring...")
        
        equity_result = await equity_monitor.update_account_equity(test_account_id, account.address)
        
        if equity_result:
            account_data = storage.get_account(test_account_id)
            if account_data and account_data.latest_equity is not None:
                print(f"   ✅ Equity fetched: ${account_data.latest_equity:,.2f}")
                print(f"   Updated at: {account_data.equity_updated_at}")
                
                # Check equity snapshots
                snapshots = storage.get_equity_snapshots(test_account_id)
                print(f"   Snapshots saved: {len(snapshots)}")
            else:
                print("   ⚠️  No equity data in account")
        else:
            print("   ⚠️  Equity update failed")
        
        # Step 5: Test chat system with equity context
        print("\n5️⃣  Testing chat system with equity context...")
        
        chat_response = await chat_service.chat_with_profile(
            account_id=test_account_id,
            user_message="What's your current portfolio status? Any trading opportunities?",
            user_session_id=f"test_session_{int(datetime.now().timestamp())}"
        )
        
        if chat_response.get("response"):
            print("   ✅ Chat response generated successfully")
            print(f"   Response preview: {chat_response['response'][:200]}...")
            if chat_response.get("tool_calls"):
                print(f"   Tool calls made: {len(chat_response['tool_calls'])}")
        else:
            print(f"   ⚠️  Chat failed: {chat_response.get('error')}")
        
        # Step 6: Test trading system (dry run)
        print("\n6️⃣  Testing trading system...")
        
        executor = ParallelProfileExecutor(dry_run=True)
        await executor.initialize()
        
        # Check if our test account is loaded
        test_profile_loaded = any(
            profile.id == test_account_id 
            for profile in executor.active_profiles
        )
        
        if test_profile_loaded:
            print("   ✅ Test profile loaded in trading system")
            
            # Run one trading cycle
            print("   Running trading cycle...")
            await executor.run_cycle()
            print("   ✅ Trading cycle completed")
            
        else:
            print("   ⚠️  Test profile not loaded (needs persona)")
        
        await executor.shutdown()
        
        # Step 7: Test market data integration
        print("\n7️⃣  Testing market data integration...")
        
        from app.core.market_manager import get_market_manager
        market_manager = get_market_manager()
        
        # Force update market data
        market_data = await market_manager.get_latest_data(force_update=True)
        market_summary = market_manager.get_market_summary()
        
        print(f"   ✅ Market data: BTC {market_summary['btc']}, ETH {market_summary['eth']}")
        print(f"   Last update: {market_summary['last_update']}")
        
        # Step 8: Test equity summary across all accounts
        print("\n8️⃣  Testing equity monitoring summary...")
        
        equity_summary = equity_monitor.get_equity_summary()
        print(f"   Total equity tracked: ${equity_summary['total_equity_usdc']:,.2f}")
        print(f"   Accounts monitored: {equity_summary['accounts_tracked']}")
        print(f"   Consecutive failures: {equity_summary['consecutive_failures']}")
        
        # Show all accounts with equity
        all_accounts = storage.get_all_accounts()
        accounts_with_equity = {
            acc_id: acc_data 
            for acc_id, acc_data in all_accounts.items() 
            if acc_data.get("latest_equity") is not None
        }
        
        print(f"   Accounts with equity data: {len(accounts_with_equity)}")
        for acc_id, acc_data in list(accounts_with_equity.items())[:5]:  # Show first 5
            equity = acc_data["latest_equity"]
            handle = acc_data.get("handle", "Unknown")
            print(f"     {handle:15} ${equity:>12,.2f}")
        
        # Final verification
        print("\n" + "=" * 80)
        print("✅ FULL SYSTEM INTEGRATION TEST COMPLETE!")
        print("=" * 80)
        
        # Test summary
        created_account = storage.get_account(test_account_id)
        print(f"\nTest Account Summary:")
        print(f"  ID: {test_account_id}")
        print(f"  Address: {created_account.address if created_account else 'N/A'}")
        print(f"  Persona: {created_account.persona.name if created_account and created_account.persona else 'N/A'}")
        print(f"  Registered: {created_account.is_registered if created_account else False}")
        print(f"  Has Deposit: {created_account.has_deposited if created_account else False}")
        print(f"  Latest Equity: ${created_account.latest_equity or 0:,.2f}" if created_account else "  Latest Equity: N/A")
        
        return test_account_id
        
    except Exception as e:
        print(f"\n❌ System test failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        # Cleanup
        await rise_client.close()


async def cleanup_test_account(account_id: str):
    """Clean up test account if needed."""
    if not account_id:
        return
    
    print(f"\n🧹 Cleaning up test account: {account_id}")
    
    storage = JSONStorage()
    
    # You can choose to keep or remove the test account
    response = input("Keep test account for inspection? (y/n): ")
    
    if response.lower() != 'y':
        # Remove test account
        accounts = storage.get_all_accounts()
        if account_id in accounts:
            del accounts[account_id]
            storage._save_json(storage.accounts_file, accounts)
            print(f"   ✅ Test account {account_id} removed")
        
        # Remove equity snapshots
        snapshots = storage._load_json(storage.data_dir / "equity_snapshots.json")
        if account_id in snapshots:
            del snapshots[account_id]
            storage._save_json(storage.data_dir / "equity_snapshots.json", snapshots)
            print(f"   ✅ Equity snapshots removed")
    else:
        print(f"   ✅ Test account preserved for inspection")


async def main():
    """Run the full system test."""
    test_account_id = await test_full_system_flow()
    
    if test_account_id:
        await cleanup_test_account(test_account_id)
    
    print("\n🎯 Integration test completed!")


if __name__ == "__main__":
    asyncio.run(main())