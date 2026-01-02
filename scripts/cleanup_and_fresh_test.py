#!/usr/bin/env python3
"""Clean up accounts and create a completely fresh profile for testing."""

import asyncio
import json
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


async def analyze_current_accounts():
    """Analyze current accounts and categorize them."""
    storage = JSONStorage()
    accounts = storage.get_all_accounts()
    
    print("=" * 80)
    print("📊 CURRENT ACCOUNTS ANALYSIS")
    print("=" * 80)
    
    categories = {
        "production": [],      # Real profiles with equity > 0
        "test_accounts": [],   # Test accounts (test_ prefix)
        "zero_equity": [],     # Accounts with zero equity
        "incomplete": [],      # No persona or incomplete setup
        "duplicates": []       # Duplicate personas
    }
    
    persona_names = {}
    
    for account_id, account_data in accounts.items():
        equity = account_data.get("latest_equity", 0)
        persona = account_data.get("persona")
        
        # Categorize account
        if account_id.startswith("test"):
            categories["test_accounts"].append((account_id, account_data))
        elif not persona:
            categories["incomplete"].append((account_id, account_data))
        elif equity > 0:
            categories["production"].append((account_id, account_data))
        else:
            categories["zero_equity"].append((account_id, account_data))
        
        # Check for duplicate personas
        if persona:
            persona_name = persona.get("name", "Unknown")
            if persona_name in persona_names:
                categories["duplicates"].append((account_id, account_data))
            else:
                persona_names[persona_name] = account_id
    
    # Print analysis
    print(f"Total accounts: {len(accounts)}")
    print(f"Production (equity > 0): {len(categories['production'])}")
    print(f"Test accounts: {len(categories['test_accounts'])}")
    print(f"Zero equity: {len(categories['zero_equity'])}")
    print(f"Incomplete: {len(categories['incomplete'])}")
    print(f"Duplicates: {len(categories['duplicates'])}")
    
    print("\n" + "="*50)
    print("PRODUCTION ACCOUNTS (Have Equity)")
    print("="*50)
    for account_id, account_data in categories["production"]:
        persona = account_data.get("persona", {})
        equity = account_data.get("latest_equity", 0)
        print(f"  {persona.get('name', 'Unknown'):25} ${equity:>10,.2f}  ({account_id[:12]}...)")
    
    print("\n" + "="*50)
    print("TEST ACCOUNTS")
    print("="*50)
    for account_id, account_data in categories["test_accounts"]:
        persona = account_data.get("persona", {})
        equity = account_data.get("latest_equity", 0)
        registered = account_data.get("is_registered", False)
        deposited = account_data.get("has_deposited", False)
        print(f"  {account_id:30} ${equity:>8,.2f} R:{registered} D:{deposited}")
    
    print("\n" + "="*50)
    print("ZERO EQUITY ACCOUNTS")
    print("="*50)
    for account_id, account_data in categories["zero_equity"][:5]:  # Show first 5
        persona = account_data.get("persona", {})
        print(f"  {persona.get('name', 'Unknown'):25} {account_id[:12]}...")
    if len(categories["zero_equity"]) > 5:
        print(f"  ... and {len(categories['zero_equity']) - 5} more")
    
    return categories


async def cleanup_accounts(categories, keep_production=True):
    """Clean up accounts based on categories."""
    storage = JSONStorage()
    
    print("\n" + "=" * 80)
    print("🧹 CLEANUP PLAN")
    print("=" * 80)
    
    to_remove = []
    
    # Always remove test accounts
    to_remove.extend([account_id for account_id, _ in categories["test_accounts"]])
    print(f"Will remove {len(categories['test_accounts'])} test accounts")
    
    # Remove incomplete accounts
    to_remove.extend([account_id for account_id, _ in categories["incomplete"]])
    print(f"Will remove {len(categories['incomplete'])} incomplete accounts")
    
    # Option to remove duplicates (keep first occurrence)
    duplicate_ids = [account_id for account_id, _ in categories["duplicates"]]
    to_remove.extend(duplicate_ids)
    print(f"Will remove {len(duplicate_ids)} duplicate personas")
    
    # Option to remove zero equity accounts
    if not keep_production:
        zero_equity_ids = [account_id for account_id, _ in categories["zero_equity"]]
        to_remove.extend(zero_equity_ids)
        print(f"Will remove {len(zero_equity_ids)} zero equity accounts")
    else:
        print(f"Keeping {len(categories['zero_equity'])} zero equity accounts")
    
    print(f"\nTotal accounts to remove: {len(to_remove)}")
    print(f"Production accounts to keep: {len(categories['production'])}")
    
    # Confirm removal
    if to_remove:
        response = input("\nProceed with cleanup? (y/n): ")
        if response.lower() == 'y':
            # Load accounts
            accounts = storage.get_all_accounts()
            
            # Remove accounts
            for account_id in to_remove:
                if account_id in accounts:
                    del accounts[account_id]
                    print(f"  Removed: {account_id}")
            
            # Save updated accounts
            storage._save_json(storage.accounts_file, accounts)
            print(f"\n✅ Cleanup complete! Removed {len(to_remove)} accounts")
            
            # Also clean up related data
            await cleanup_related_data(to_remove, storage)
        else:
            print("Cleanup cancelled")


async def cleanup_related_data(removed_account_ids, storage):
    """Clean up related data files."""
    print("\n🧹 Cleaning up related data...")
    
    # Clean up equity snapshots
    equity_file = storage.data_dir / "equity_snapshots.json"
    if equity_file.exists():
        snapshots = storage._load_json(equity_file)
        original_count = len(snapshots)
        
        for account_id in removed_account_ids:
            if account_id in snapshots:
                del snapshots[account_id]
        
        storage._save_json(equity_file, snapshots)
        cleaned_count = original_count - len(snapshots)
        if cleaned_count > 0:
            print(f"  Cleaned {cleaned_count} equity snapshot entries")
    
    # Clean up chat sessions
    chat_file = storage.chat_sessions_file
    if chat_file.exists():
        sessions = storage._load_json(chat_file)
        original_count = len(sessions)
        
        for account_id in removed_account_ids:
            if account_id in sessions:
                del sessions[account_id]
        
        storage._save_json(chat_file, sessions)
        cleaned_count = original_count - len(sessions)
        if cleaned_count > 0:
            print(f"  Cleaned {cleaned_count} chat session entries")
    
    # Clean up trades
    trades_file = storage.trades_file
    if trades_file.exists():
        trades = storage._load_json(trades_file)
        original_count = len(trades)
        
        for account_id in removed_account_ids:
            if account_id in trades:
                del trades[account_id]
        
        storage._save_json(trades_file, trades)
        cleaned_count = original_count - len(trades)
        if cleaned_count > 0:
            print(f"  Cleaned {cleaned_count} trade entries")


async def create_fresh_profile():
    """Create a completely fresh profile with registration and deposit."""
    print("\n" + "=" * 80)
    print("🆕 CREATING FRESH PROFILE")
    print("=" * 80)
    
    storage = JSONStorage()
    rise_client = RiseClient()
    
    try:
        # Step 1: Generate fresh keys
        print("1️⃣  Generating fresh keys...")
        from web3 import Web3
        w3 = Web3()
        
        main_account = w3.eth.account.create()
        signer_account = w3.eth.account.create()
        
        print(f"   Main: {main_account.address}")
        print(f"   Signer: {signer_account.address}")
        
        # Step 2: Register signer
        print("2️⃣  Registering signer...")
        registration_result = await rise_client.register_signer(
            account_key=main_account.key.hex(),
            signer_key=signer_account.key.hex()
        )
        
        registration_success = registration_result.get("data", {}).get("success", False)
        if registration_success:
            print("   ✅ Signer registered successfully!")
            tx_hash = registration_result.get("data", {}).get("transaction_hash")
            print(f"   Transaction: {tx_hash}")
        else:
            print(f"   ⚠️  Registration result: {registration_result}")
        
        # Step 3: Deposit funds
        print("3️⃣  Depositing USDC...")
        deposit_result = await rise_client.deposit_usdc(
            account_key=main_account.key.hex(),
            amount=100.0
        )
        
        deposit_success = deposit_result.get("data", {}).get("success", False)
        if deposit_success:
            print("   ✅ Deposit successful!")
            tx_hash = deposit_result.get("data", {}).get("transaction_hash")
            print(f"   Transaction: {tx_hash}")
        else:
            print(f"   ⚠️  Deposit result: {deposit_result}")
        
        # Step 4: Create profile
        print("4️⃣  Creating AI profile...")
        profile_type = "cynical"  # Use cynical for testing
        trader_profile = create_trader_profile(profile_type)
        
        timestamp = int(datetime.now().timestamp())
        account_id = f"fresh_profile_{timestamp}"
        
        account = Account(
            id=account_id,
            address=main_account.address,
            private_key=main_account.key.hex(),
            signer_key=signer_account.key.hex(),
            persona=Persona(
                name=trader_profile.base_persona.name,
                handle=f"fresh_{timestamp}",
                bio=trader_profile.base_persona.core_personality[:100],
                trading_style="conservative",
                risk_tolerance=0.5,
                favorite_assets=["BTC", "ETH"],
                personality_traits=trader_profile.base_persona.base_traits[:3],
                sample_posts=["Fresh start, ready to trade!"]
            ),
            is_active=True,
            is_registered=registration_success,
            registered_at=datetime.now() if registration_success else None,
            has_deposited=deposit_success,
            deposited_at=datetime.now() if deposit_success else None,
            deposit_amount=100.0 if deposit_success else None,
            created_at=datetime.now()
        )
        
        storage.save_account(account)
        print(f"   ✅ Profile saved: {account_id}")
        print(f"   Persona: {account.persona.name}")
        
        # Step 5: Verify equity
        print("5️⃣  Checking equity...")
        await asyncio.sleep(2)  # Wait for blockchain confirmation
        
        equity_monitor = get_equity_monitor()
        equity = await equity_monitor.fetch_equity(main_account.address)
        
        if equity is not None and equity > 0:
            print(f"   ✅ On-chain equity: ${equity:,.2f}")
        else:
            print(f"   ⚠️  Equity: ${equity or 0:.2f} (may need time to sync)")
        
        return account_id, account
        
    except Exception as e:
        print(f"   ❌ Error creating profile: {e}")
        import traceback
        traceback.print_exc()
        return None, None
    
    finally:
        await rise_client.close()


async def test_fresh_profile(account_id):
    """Test the fresh profile with full AI flow."""
    if not account_id:
        print("No fresh profile to test")
        return
    
    print("\n" + "=" * 80)
    print("🧪 TESTING FRESH PROFILE")
    print("=" * 80)
    
    storage = JSONStorage()
    chat_service = ProfileChatService()
    
    # Test 1: Chat interaction
    print("1️⃣  Testing chat interaction...")
    try:
        chat_response = await chat_service.chat_with_profile(
            account_id=account_id,
            user_message="Hey! What's the current market looking like? Any trading opportunities?",
            user_session_id=f"fresh_test_{int(datetime.now().timestamp())}"
        )
        
        if chat_response.get("response"):
            print("   ✅ Chat response generated")
            print(f"   Preview: {chat_response['response'][:100]}...")
            if chat_response.get("tool_calls"):
                print(f"   Tool calls: {len(chat_response['tool_calls'])}")
        else:
            print(f"   ❌ Chat failed: {chat_response.get('error')}")
    
    except Exception as e:
        print(f"   ❌ Chat error: {e}")
    
    # Test 2: Trading system
    print("2️⃣  Testing trading system...")
    try:
        executor = ParallelProfileExecutor(dry_run=True)
        await executor.initialize()
        
        # Check if profile loaded
        fresh_profile = None
        for profile in executor.active_profiles:
            if profile.id == account_id:
                fresh_profile = profile
                break
        
        if fresh_profile:
            print("   ✅ Profile loaded in trading system")
            print(f"   Persona: {fresh_profile.persona.name}")
            
            # Run one cycle
            await executor.run_cycle()
            print("   ✅ Trading cycle completed")
        else:
            print("   ⚠️  Profile not found in trading system")
        
        await executor.shutdown()
    
    except Exception as e:
        print(f"   ❌ Trading test error: {e}")
    
    print("\n✅ Fresh profile testing complete!")


async def main():
    """Main cleanup and testing flow."""
    print("This will analyze and clean up accounts, then create a fresh profile")
    print("Make sure you understand what will be removed!")
    
    # Step 1: Analyze current accounts
    categories = await analyze_current_accounts()
    
    # Step 2: Cleanup (optional)
    cleanup_choice = input("\nPerform cleanup? (y/n): ")
    if cleanup_choice.lower() == 'y':
        await cleanup_accounts(categories, keep_production=True)
    
    # Step 3: Create fresh profile
    fresh_choice = input("\nCreate fresh profile? (y/n): ")
    if fresh_choice.lower() == 'y':
        account_id, account = await create_fresh_profile()
        
        if account_id:
            # Step 4: Test fresh profile
            test_choice = input("\nTest fresh profile with full AI flow? (y/n): ")
            if test_choice.lower() == 'y':
                await test_fresh_profile(account_id)
        
        print(f"\n🎉 Fresh profile ready: {account_id}")
    
    print("\n✅ All done!")


if __name__ == "__main__":
    asyncio.run(main())