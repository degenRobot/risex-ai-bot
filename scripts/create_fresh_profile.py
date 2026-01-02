#!/usr/bin/env python3
"""Create a completely fresh profile from scratch with full onboarding flow."""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.account_creator import create_fresh_profile as create_profile_service, AccountCreationError

# Available personality types
PERSONALITY_TYPES = {
    "1": ("cynical", "Cynical Chad - Extremely pessimistic, hard to convince"),
    "2": ("leftCurve", "Degen Trader - Believes anything, gets excited easily"),
    "3": ("midwit", "Technical Terry - Overanalyzes everything with 47 indicators")
}

async def create_fresh_profile(personality_type="cynical", deposit_amount=1000.0):
    """Create a fresh profile using the robust account creator service."""
    print("=" * 80)
    print("🆕 CREATING FRESH AI TRADING PROFILE")
    print("=" * 80)
    
    try:
        account_id, account = await create_profile_service(personality_type, deposit_amount)
        
        print("\n" + "=" * 80)
        print("✅ FRESH PROFILE CREATION COMPLETE!")
        print("=" * 80)
        print(f"Profile ID: {account_id}")
        print(f"Address: {account.address}")
        print(f"Personality: {account.persona.name}")
        print(f"Registered: {account.is_registered}")
        print(f"Deposited: ${account.deposit_amount or 0:.2f}")
        print()
        print("🎯 READY FOR:")
        print("- 💬 Chat interactions")
        print("- 🤖 AI trading decisions") 
        print("- 📊 Real-time equity monitoring")
        print("- 🔄 Automated trading cycles")
        
        return account_id, account
        
    except AccountCreationError as e:
        print(f"\n❌ Profile creation failed: {e}")
        return None, None


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
    deposit_input = input("Enter deposit amount (default=1000): ").strip()
    try:
        deposit_amount = float(deposit_input) if deposit_input else 1000.0
    except ValueError:
        deposit_amount = 1000.0
    
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