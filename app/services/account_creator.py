#!/usr/bin/env python3
"""Account creation service with robust retry logic."""

import asyncio
from datetime import datetime
from typing import Optional

from web3 import Web3

from ..models import Account, Persona
from ..trader_profiles import create_trader_profile
from .equity_monitor import get_equity_monitor
from .rise_client import RiseClient
from .storage import JSONStorage


class AccountCreationError(Exception):
    """Raised when account creation fails."""
    pass


class AccountCreator:
    """Service for creating fresh trading accounts with full onboarding."""
    
    def __init__(self):
        self.rise_client = RiseClient()
        self.storage = JSONStorage()
        self.equity_monitor = get_equity_monitor()
        self.w3 = Web3()
    
    async def create_profile(
        self,
        personality_type: str = "cynical",
        deposit_amount: float = 1000.0,
        max_retries: int = 3,
    ) -> tuple[str, Account]:
        """
        Create a complete fresh trading profile.
        
        Args:
            personality_type: One of "cynical", "leftCurve", "midwit"
            deposit_amount: Amount of USDC to deposit
            max_retries: Maximum retry attempts for each step
            
        Returns:
            Tuple of (account_id, Account object)
            
        Raises:
            AccountCreationError: If creation fails after retries
        """
        print(f"🆕 Creating fresh profile: {personality_type} with ${deposit_amount}")
        
        # Step 1: Generate fresh keys
        main_account, signer_account = self._generate_keys()
        print(f"✅ Keys generated: {main_account.address[:10]}...{main_account.address[-6:]}")
        
        try:
            # Step 2: Register signer with retries
            registration_success = await self._register_signer_with_retry(
                main_account, signer_account, max_retries,
            )
            
            # Step 3: Wait briefly after registration
            if registration_success:
                print("⏳ Waiting 2 seconds after registration...")
                await asyncio.sleep(2)
            
            # Step 4: Deposit USDC with retries
            deposit_success = await self._deposit_usdc_with_retry(
                main_account, deposit_amount, max_retries,
            )
            
            # Step 5: Create profile object
            account_id, account = self._create_account_object(
                main_account, signer_account, personality_type, 
                deposit_amount, registration_success, deposit_success,
            )
            
            # Step 6: Save to storage
            self.storage.save_account(account)
            print(f"✅ Profile saved: {account_id}")
            
            # Step 7: Verify equity (best effort)
            await self._verify_equity(main_account.address)
            
            return account_id, account
            
        except Exception as e:
            print(f"❌ Account creation failed: {e}")
            raise AccountCreationError(f"Failed to create profile: {e}")
        
        finally:
            await self.rise_client.close()
    
    def _generate_keys(self) -> tuple[any, any]:
        """Generate cryptographic keys for main and signer accounts."""
        main_account = self.w3.eth.account.create()
        signer_account = self.w3.eth.account.create()
        
        # Ensure keys are different (should never fail but check anyway)
        if main_account.address == signer_account.address:
            raise AccountCreationError("Generated keys are identical (extremely rare)")
        
        return main_account, signer_account
    
    async def _register_signer_with_retry(
        self, 
        main_account: any, 
        signer_account: any,
        max_retries: int,
    ) -> bool:
        """Register signer with retry logic."""
        for attempt in range(max_retries):
            try:
                print(f"🔐 Registering signer (attempt {attempt + 1}/{max_retries})...")
                
                result = await self.rise_client.register_signer(
                    account_key=main_account.key.hex(),
                    signer_key=signer_account.key.hex(),
                )
                
                # Check nested success
                success = result.get("data", {}).get("success", False)
                if success:
                    tx_hash = result.get("data", {}).get("transaction_hash")
                    print(f"✅ Signer registered! TX: {tx_hash}")
                    return True
                else:
                    error_msg = result.get("error", "Unknown error")
                    print(f"⚠️  Registration failed: {error_msg}")
                    
            except Exception as e:
                print(f"⚠️  Registration attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"⏳ Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
        
        print(f"❌ Signer registration failed after {max_retries} attempts")
        return False
    
    async def _deposit_usdc_with_retry(
        self,
        main_account: any,
        amount: float,
        max_retries: int,
    ) -> bool:
        """Deposit USDC with retry logic for backend API issues."""
        for attempt in range(max_retries):
            try:
                print(f"💰 Depositing ${amount} (attempt {attempt + 1}/{max_retries})...")
                
                result = await self.rise_client.deposit_usdc(
                    account_key=main_account.key.hex(),
                    amount=amount,
                )
                
                # Check nested success
                success = result.get("data", {}).get("success", False)
                if success:
                    tx_hash = result.get("data", {}).get("transaction_hash")
                    print(f"✅ Deposit successful! Amount: ${amount}, TX: {tx_hash}")
                    return True
                else:
                    error_msg = result.get("error", "Unknown error")
                    print(f"⚠️  Deposit failed: {error_msg}")
                    
            except Exception as e:
                error_str = str(e)
                print(f"⚠️  Deposit attempt {attempt + 1} failed: {error_str}")
                
                if attempt < max_retries - 1:
                    wait_time = 3 + attempt * 2  # Linear backoff: 3s, 5s, 7s
                    print(f"⏳ Backend API issue, waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
        
        print(f"❌ Deposit failed after {max_retries} attempts (backend API issues)")
        return False
    
    def _create_account_object(
        self,
        main_account: any,
        signer_account: any,
        personality_type: str,
        deposit_amount: float,
        registration_success: bool,
        deposit_success: bool,
    ) -> tuple[str, Account]:
        """Create Account object from successful creation."""
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
                trading_style=self._map_trading_style(trader_profile.base_persona.risk_profile.value),
                risk_tolerance=self._map_risk_tolerance(personality_type),
                favorite_assets=["BTC", "ETH"],
                personality_traits=trader_profile.base_persona.base_traits[:3],
                sample_posts=[f"Fresh {personality_type} trader ready for action!"],
            ),
            is_active=True,
            is_registered=registration_success,
            registered_at=datetime.now() if registration_success else None,
            has_deposited=deposit_success,
            deposited_at=datetime.now() if deposit_success else None,
            deposit_amount=deposit_amount if deposit_success else None,
            created_at=datetime.now(),
        )
        
        return account_id, account
    
    async def _verify_equity(self, address: str) -> Optional[float]:
        """Verify on-chain equity (best effort, non-blocking)."""
        try:
            print("📊 Verifying on-chain equity...")
            # Wait a bit for blockchain confirmation
            await asyncio.sleep(3)
            
            equity = await self.equity_monitor.fetch_equity(address)
            if equity is not None and equity > 0:
                print(f"✅ Confirmed equity: ${equity:,.2f}")
                return equity
            else:
                print(f"⚠️  Equity: ${equity or 0:.2f} (may need time to sync)")
                return None
                
        except Exception as e:
            print(f"⚠️  Could not verify equity: {e}")
            return None
    
    def _map_trading_style(self, risk_profile: str) -> str:
        """Map risk profile to trading style."""
        mapping = {
            "ultra_conservative": "conservative",
            "conservative": "conservative", 
            "moderate": "momentum",
            "aggressive": "aggressive",
            "degen": "degen",
        }
        return mapping.get(risk_profile, "momentum")
    
    def _map_risk_tolerance(self, personality_type: str) -> float:
        """Map personality type to risk tolerance."""
        mapping = {
            "cynical": 0.3,
            "leftCurve": 0.9,
            "midwit": 0.6,
        }
        return mapping.get(personality_type, 0.5)


# Convenience function for external use
async def create_fresh_profile(
    personality_type: str = "cynical",
    deposit_amount: float = 1000.0,
) -> tuple[str, Account]:
    """
    Create a fresh trading profile with full onboarding.
    
    Args:
        personality_type: "cynical", "leftCurve", or "midwit"
        deposit_amount: Amount of USDC to deposit
        
    Returns:
        Tuple of (account_id, Account object)
        
    Raises:
        AccountCreationError: If creation fails
    """
    creator = AccountCreator()
    return await creator.create_profile(personality_type, deposit_amount)