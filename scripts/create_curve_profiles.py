#!/usr/bin/env python3
"""Create left/mid/right curve profiles with completely new accounts."""

import asyncio
import json
import secrets
import sys
from datetime import datetime
from pathlib import Path

from eth_account import Account as EthAccount

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models import Account, Persona, TradingStyle
from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage
from app.trader_profiles import LEFT_CURVE, MID_CURVE, RIGHT_CURVE

# Profile definitions with curve meme personalities
CURVE_PROFILES = [
    {
        "profile_type": "leftCurve",
        "base_persona": LEFT_CURVE,
        "persona": Persona(
            handle="leftCurve",
            name="Drunk Wassie",
            bio="Simple trader with drunk wisdom. Makes decisions based on vibes. Often accidentally successful. *hic*",
            trading_style=TradingStyle.DEGEN,
            risk_tolerance=0.8,
            personality_traits=[
                "simple_minded",
                "drunk_intuition", 
                "vibes_based",
                "accidentally_wise",
                "easily_excited",
            ],
            favorite_assets=["BTC", "ETH", "DOGE", "SHIB"],
            sample_posts=[
                "*hic* vibes r gud rn fren, buying moar btc",
                "bartender said btc going up, im all in lmeow",
                "if it feels good buy it, thats my strategy *hic*",
                "markets go up when happy, down when sad, simple",
            ],
        ),
        "initial_deposit": 1000.0,
    },
    {
        "profile_type": "midCurve",
        "base_persona": MID_CURVE,
        "persona": Persona(
            handle="midCurve",
            name="Midwit McGee",
            bio="Chronic overthinker who gets lost in complexity. Uses 50 indicators. Follows all the influencers. Analysis paralysis.",
            trading_style=TradingStyle.MOMENTUM,
            risk_tolerance=0.5,
            personality_traits=[
                "overthinker",
                "easily_influenced",
                "information_overload",
                "complexity_addict",
                "follows_gurus",
            ],
            favorite_assets=["BTC", "ETH", "SOL", "LINK"],
            sample_posts=[
                "just analyzed 47 indicators n still not sure iwo",
                "guru said btc bullish but other guru said bearish hmm",
                "need moar data before can decide, checking 15 more charts",
                "wat if we combine elliot waves with fib retracements and moon phases",
            ],
        ),
        "initial_deposit": 1000.0,
    },
    {
        "profile_type": "rightCurve", 
        "base_persona": RIGHT_CURVE,
        "persona": Persona(
            handle="rightCurve",
            name="Wise Chad",
            bio="Experienced trader with profound understanding. Sees through complexity to simple truths. Makes decisive moves based on deep wisdom.",
            trading_style=TradingStyle.CONTRARIAN,
            risk_tolerance=0.6,
            personality_traits=[
                "profoundly_simple",
                "decisively_wise",
                "pattern_recognition",
                "zen_trader",
                "effortless_expertise",
            ],
            favorite_assets=["BTC", "ETH"],
            sample_posts=[
                "btc is simply digital gold lmeow, everything else is noise",
                "crowd panicking = time to buy. simple iwo",
                "all ponzis but some ponzis better than others",
                "survive first profit second, this is the way",
            ],
        ),
        "initial_deposit": 1000.0,
    },
]


async def create_fresh_account(profile_config: dict, storage: JSONStorage) -> Account:
    """Create a completely new account with fresh keys."""
    
    # Generate completely new private keys
    main_account = EthAccount.create(extra_entropy=secrets.token_bytes(32))
    signer_account = EthAccount.create(extra_entropy=secrets.token_bytes(32))
    
    print(f"\n🔑 Generated fresh keys for {profile_config['persona'].name}:")
    print(f"   Main address: {main_account.address}")
    print(f"   Signer address: {signer_account.address}")
    
    # Create account model
    account = Account(
        id=str(secrets.token_urlsafe(16)),
        address=main_account.address,
        private_key=main_account.key.hex(),
        signer_key=signer_account.key.hex(),
        is_registered=False,
        persona=profile_config["persona"],
        deposit_amount=profile_config["initial_deposit"],
        created_at=datetime.now(),
    )
    
    # Save account
    storage.save_account(account)
    print(f"✅ Created account for {profile_config['persona'].name}")
    
    return account


async def register_and_fund_account(account: Account, storage: JSONStorage):
    """Register signer and fund account on RISE."""
    rise_client = RiseClient()
    
    try:
        print(f"\n📝 Registering {account.persona.name}...")
        
        # Register signer
        success = await rise_client.register_signer(
            account_key=account.private_key,
            signer_key=account.signer_key,
        )
        
        if not success:
            print(f"❌ Failed to register signer for {account.persona.name}")
            return False
        
        account.is_registered = True
        storage.save_account(account)
        print(f"✅ Registered signer for {account.persona.name}")
        
        # Wait a moment for registration to process
        await asyncio.sleep(2)
        
        # Deposit with retry
        print(f"💰 Depositing {account.deposit_amount} USDC...")
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                success = await rise_client.deposit_usdc(
                    account_key=account.private_key,
                    amount=account.deposit_amount,
                )
                if success:
                    print(f"✅ Deposited {account.deposit_amount} USDC for {account.persona.name}")
                    return True
                else:
                    print(f"⚠️ Deposit attempt {attempt + 1} failed")
                    if attempt < max_retries - 1:
                        print("   Retrying in 5 seconds...")
                        await asyncio.sleep(5)
            except Exception as e:
                print(f"⚠️ Deposit attempt {attempt + 1} error: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(5)
        
        print(f"❌ Failed to deposit after {max_retries} attempts")
        return False
        
    except Exception as e:
        print(f"❌ Error registering {account.persona.name}: {e}")
        return False
    finally:
        await rise_client.close()


async def main():
    """Main function to create curve profiles."""
    print("🎯 Creating Left/Mid/Right Curve Profiles")
    print("=" * 50)
    
    storage = JSONStorage()
    
    # Clear existing accounts
    print("\n🗑️ Clearing existing accounts...")
    existing = storage.list_accounts()
    if existing:
        print(f"   Found {len(existing)} existing accounts")
        # Create backup
        backup_path = Path("data/accounts_backup.json")
        backup_path.write_text(json.dumps([acc.model_dump() for acc in existing], indent=2, default=str))
        print(f"   Backed up to {backup_path}")
    
    # Clear accounts by saving empty dict
    storage._save_json(storage.accounts_file, {})
    print("✅ Cleared all accounts")
    
    # Create new accounts
    created_accounts = []
    
    for profile_config in CURVE_PROFILES:
        account = await create_fresh_account(profile_config, storage)
        created_accounts.append(account)
    
    # Register and fund accounts
    print("\n🚀 Registering and funding accounts on RISE...")
    
    for account in created_accounts:
        await register_and_fund_account(account, storage)
        # Wait between accounts to avoid rate limits
        await asyncio.sleep(3)
    
    # Summary
    print("\n📊 Summary:")
    print("=" * 50)
    
    accounts = storage.list_accounts()
    for account in accounts:
        print(f"\n{account.persona.name} ({account.persona.handle}):")
        print(f"   Address: {account.address}")
        print(f"   Signer key: {account.signer_key[:10]}...")
        print(f"   Registered: {'✅' if account.is_registered else '❌'}")
        print(f"   Initial deposit: ${account.deposit_amount}")
        print(f"   Trading style: {account.persona.trading_style.value}")
        print(f"   Speech style: {CURVE_PROFILES[[p['persona'].handle for p in CURVE_PROFILES].index(account.persona.handle)]['base_persona'].speech_style}")
    
    print("\n✅ Curve profiles created successfully!")


if __name__ == "__main__":
    asyncio.run(main())