#!/usr/bin/env python3
"""Setup test accounts with different trading personalities."""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import uuid
from eth_account import Account as EthAccount

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models import Account, Persona, TradingStyle
from app.services.storage import JSONStorage
from app.services.rise_client import RiseClient


async def create_test_accounts():
    """Create test accounts with different personalities."""
    storage = JSONStorage()
    rise_client = RiseClient()
    
    print("Setting up test trading accounts")
    print("=" * 50)
    
    # Define test personas
    test_personas = [
        {
            "name": "Always Long",
            "handle": "always_long",
            "bio": "I buy when I have collateral and no positions",
            "style": TradingStyle.MOMENTUM,
            "risk": 0.8,
            "traits": ["bullish", "optimistic", "patient"]
        },
        {
            "name": "Conservative Trader",
            "handle": "conservative",
            "bio": "Careful entries, small positions, risk management first",
            "style": TradingStyle.CONSERVATIVE,
            "risk": 0.3,
            "traits": ["cautious", "analytical", "disciplined"]
        },
        {
            "name": "Dip Buyer",
            "handle": "dip_buyer",
            "bio": "I buy the fear when prices drop",
            "style": TradingStyle.CONTRARIAN,
            "risk": 0.6,
            "traits": ["contrarian", "patient", "value-focused"]
        }
    ]
    
    created_accounts = []
    
    for persona_data in test_personas:
        print(f"\nCreating account for {persona_data['name']}...")
        
        # Generate fresh keys
        main_account = EthAccount.create()
        signer_account = EthAccount.create()
        
        # Create persona
        persona = Persona(
            name=persona_data["name"],
            handle=persona_data["handle"],
            bio=persona_data["bio"],
            trading_style=persona_data["style"],
            risk_tolerance=persona_data["risk"],
            favorite_assets=["BTC", "ETH"],
            personality_traits=persona_data["traits"],
            sample_posts=["Trading is life", "Always learning"]
        )
        
        # Create account
        account = Account(
            id=str(uuid.uuid4()),
            address=main_account.address,
            private_key=main_account.key.hex(),
            signer_key=signer_account.key.hex(),
            persona=persona,
            is_active=True,
            created_at=datetime.now()
        )
        
        # Save account
        storage.save_account(account)
        created_accounts.append(account)
        
        print(f"   Account: {account.address}")
        print(f"   Signer: {signer_account.address}")
        
        # Register signer
        try:
            print("   Registering signer...")
            await rise_client.register_signer(
                account.private_key,
                account.signer_key
            )
            print("   Signer registered successfully")
        except Exception as e:
            print(f"   Registration error: {e}")
        
        # Small delay between accounts
        await asyncio.sleep(1)
    
    print(f"\n{len(created_accounts)} test accounts created!")
    print("\nAccount Summary:")
    print("-" * 50)
    
    for acc in created_accounts:
        print(f"{acc.persona.handle}: {acc.persona.name}")
        print(f"   Style: {acc.persona.trading_style.value}")
        print(f"   Risk: {acc.persona.risk_tolerance:.0%}")
        print(f"   Address: {acc.address}")
        print()
    
    await rise_client.close()
    return created_accounts


if __name__ == "__main__":
    asyncio.run(create_test_accounts())