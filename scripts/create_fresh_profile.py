#!/usr/bin/env python3
"""Create a completely fresh profile from scratch with full onboarding flow."""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage
from app.services.equity_monitor import get_equity_monitor
from app.trader_profiles import create_trader_profile
from app.models import Account, Persona

# Available personality types
PERSONALITY_TYPES = {
    "1": ("cynical", "Cynical Chad - Extremely pessimistic, hard to convince"),
    "2": ("leftCurve", "Degen Trader - Believes anything, gets excited easily"),
    "3": ("midwit", "Technical Terry - Overanalyzes everything with 47 indicators")
}

async def create_fresh_profile(personality_type="cynical", deposit_amount=100.0):
    """Create a fresh profile with complete onboarding."""
    print("=" * 80)
    print("🆕 CREATING FRESH AI TRADING PROFILE")
    print("=" * 80)
    
    storage = JSONStorage()
    rise_client = RiseClient()
    
    try:
        # Step 1: Generate fresh keys
        print("1️⃣  Generating fresh cryptographic keys...")
        from web3 import Web3
        w3 = Web3()
        
        main_account = w3.eth.account.create()
        signer_account = w3.eth.account.create()
        
        print(f"   Main Account: {main_account.address}")
        print(f"   Signer Account: {signer_account.address}")
        assert main_account.address != signer_account.address, "❌ Keys must be different!"
        
        # Step 2: Register signer
        print("2️⃣  Registering signer for gasless trading...")
        registration_result = await rise_client.register_signer(
            account_key=main_account.key.hex(),
            signer_key=signer_account.key.hex()
        )
        
        registration_success = registration_result.get("data", {}).get("success", False)
        if registration_success:
            print("   ✅ Signer registration successful!")
            tx_hash = registration_result.get("data", {}).get("transaction_hash")
            print(f"   Transaction: {tx_hash}")
        else:
            print(f"   ⚠️  Registration response: {registration_result}")
            # Continue anyway for testing
        
        # Step 3: Deposit funds (mints testnet USDC)
        print(f"3️⃣  Depositing ${deposit_amount} USDC...")
        deposit_result = await rise_client.deposit_usdc(
            account_key=main_account.key.hex(),
            amount=deposit_amount
        )
        
        deposit_success = deposit_result.get("data", {}).get("success", False)
        if deposit_success:
            print("   ✅ Deposit successful!")
            tx_hash = deposit_result.get("data", {}).get("transaction_hash")
            print(f"   Transaction: {tx_hash}")
        else:
            print(f"   ⚠️  Deposit response: {deposit_result}")
            # Continue anyway for testing
        
        # Step 4: Create AI personality
        print("4️⃣  Creating AI trading personality...")
        trader_profile = create_trader_profile(personality_type)
        
        timestamp = int(datetime.now().timestamp())
        account_id = f"profile_{timestamp}"
        
        account = Account(
            id=account_id,
            address=main_account.address,
            private_key=main_account.key.hex(),
            signer_key=signer_account.key.hex(),
            persona=Persona(
                name=trader_profile.base_persona.name,
                handle=f"{trader_profile.base_persona.handle}_{timestamp}",
                bio=trader_profile.base_persona.core_personality,
                trading_style="conservative" if personality_type == "cynical" else "aggressive",
                risk_tolerance=0.3 if personality_type == "cynical" else 0.8,
                favorite_assets=["BTC", "ETH"],
                personality_traits=trader_profile.base_persona.base_traits[:3],
                sample_posts=["Ready to trade! Let's see what the market brings."]
            ),
            is_active=True,
            is_registered=registration_success,
            registered_at=datetime.now() if registration_success else None,
            has_deposited=deposit_success,
            deposited_at=datetime.now() if deposit_success else None,
            deposit_amount=deposit_amount if deposit_success else None,
            created_at=datetime.now()
        )
        
        storage.save_account(account)
        print(f"   ✅ Profile saved: {account_id}")
        print(f"   Persona: {account.persona.name}")
        print(f"   Handle: {account.persona.handle}")
        
        # Step 5: Verify equity
        print("5️⃣  Verifying on-chain equity...")
        await asyncio.sleep(2)  # Wait for blockchain confirmation
        
        equity_monitor = get_equity_monitor()
        equity = await equity_monitor.fetch_equity(main_account.address)
        
        if equity is not None and equity > 0:
            print(f"   ✅ On-chain equity: ${equity:,.2f}")
        else:
            print(f"   ⚠️  Equity: ${equity or 0:.2f} (may need time to sync)")
        
        # Step 6: Test basic functionality
        print("6️⃣  Testing basic functionality...")
        
        # Test balance check
        try:
            balance_info = await rise_client.get_balance(main_account.address)
            if balance_info:
                available_balance = balance_info.get("cross_margin_balance", 0)
                print(f"   💰 Available balance: ${float(available_balance):.2f}")
            else:
                print("   ⚠️  Could not fetch balance")
        except Exception as e:
            print(f"   ⚠️  Balance check failed: {e}")
        
        print("\n" + "=" * 80)
        print("✅ FRESH PROFILE CREATION COMPLETE!")
        print("=" * 80)
        print(f"Profile ID: {account_id}")
        print(f"Address: {main_account.address}")
        print(f"Personality: {trader_profile.base_persona.name}")
        print(f"Equity: ${equity or 0:.2f}")
        print()
        print("🎯 READY FOR:")
        print("- 💬 Chat interactions")
        print("- 🤖 AI trading decisions") 
        print("- 📊 Real-time equity monitoring")
        print("- 🔄 Automated trading cycles")
        
        return account_id, account
        
    except Exception as e:
        print(f"\n❌ Profile creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None
    
    finally:
        await rise_client.close()


async def interactive_creation():
    """Interactive profile creation with user input."""
    print("🎭 AI TRADER PERSONALITY SELECTOR")
    print("=" * 50)
    
    for key, (type_name, description) in PERSONALITY_TYPES.items():
        print(f"{key}. {description}")
    
    choice = input("\nSelect personality type (1-3, default=1): ").strip()
    if not choice:
        choice = "1"
    
    if choice not in PERSONALITY_TYPES:
        print("Invalid choice, using default (cynical)")
        choice = "1"
    
    personality_type = PERSONALITY_TYPES[choice][0]
    
    # Get deposit amount
    deposit_input = input("Enter deposit amount (default=100): ").strip()
    try:
        deposit_amount = float(deposit_input) if deposit_input else 100.0
    except ValueError:
        deposit_amount = 100.0
    
    print(f"\nCreating {PERSONALITY_TYPES[choice][1]} with ${deposit_amount} deposit...")
    
    return await create_fresh_profile(personality_type, deposit_amount)


async def main():
    """Main entry point."""
    print("This will create a completely fresh AI trading profile")
    print("The process includes: key generation → signer registration → deposit → AI profile")
    print()
    
    if len(sys.argv) > 1:
        # Command line mode
        personality = sys.argv[1] if sys.argv[1] in ["cynical", "leftCurve", "midwit"] else "cynical"
        deposit = float(sys.argv[2]) if len(sys.argv) > 2 else 100.0
        account_id, account = await create_fresh_profile(personality, deposit)
    else:
        # Interactive mode
        account_id, account = await interactive_creation()
    
    if account_id:
        print(f"\n🎉 Success! New profile created: {account_id}")
        
        # Ask if user wants to test it immediately
        test_choice = input("\nTest the profile with chat interaction? (y/n): ")
        if test_choice.lower() == 'y':
            print("\nYou can now test with:")
            print(f"poetry run python tests/chat/test_profile_chat.py --account-id {account_id}")
            print("or")
            print(f"poetry run python scripts/run_enhanced_bot.py --profiles {account_id}")
    else:
        print("\n💥 Profile creation failed - check logs above")


if __name__ == "__main__":
    asyncio.run(main())