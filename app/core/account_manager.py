"""Account and persona management for RISE AI trading bot."""

import uuid
from typing import List, Optional

from eth_account import Account as EthAccount

from ..models import Account, Persona
from ..services.ai_client import AIClient
from ..services.rise_client import RiseClient
from ..services.storage import JSONStorage
from ..services.mock_social import MockSocialClient


class AccountManager:
    """Manages trading accounts and their AI personas."""
    
    def __init__(self):
        self.storage = JSONStorage()
        self.ai_client = AIClient()
        self.rise_client = RiseClient()
        self.mock_social = MockSocialClient()
    
    async def create_account_with_persona(
        self, 
        handle: str, 
        posts: List[str], 
        bio: str = ""
    ) -> Account:
        """Create a new trading account with AI-generated persona."""
        
        # Generate fresh wallet keys
        eth_account = EthAccount.create()
        signer_account = EthAccount.create()
        
        # Generate AI persona from posts
        persona = await self.ai_client.create_persona_from_posts(handle, posts, bio)
        
        # Create account
        account = Account(
            id=str(uuid.uuid4()),
            address=eth_account.address,
            private_key=eth_account.key.hex(),
            signer_key=signer_account.key.hex(),
            persona=persona,
            is_active=True
        )
        
        # Register signer with RISE
        try:
            await self.rise_client.register_signer(
                account.private_key, 
                account.signer_key
            )
        except Exception as e:
            print(f"Warning: Signer registration failed: {e}")
            # Continue anyway - we can retry later
        
        # Save to storage
        self.storage.save_account(account)
        
        return account
    
    async def create_test_account(self, persona_name: str = "Test Trader") -> Account:
        """Create a test account with a simple persona."""
        
        # Generate fresh wallet keys
        eth_account = EthAccount.create()
        signer_account = EthAccount.create()
        
        # Create a simple test persona
        from ..models import TradingStyle
        test_persona = Persona(
            name=persona_name,
            handle="test_trader",
            bio="A conservative test trader focused on learning the markets.",
            trading_style=TradingStyle.CONSERVATIVE,
            risk_tolerance=0.3,
            favorite_assets=["BTC", "ETH"],
            personality_traits=["cautious", "analytical", "patient"],
            sample_posts=["Testing the markets", "Learning about crypto trading"]
        )
        
        # Create account
        account = Account(
            id=str(uuid.uuid4()),
            address=eth_account.address,
            private_key=eth_account.key.hex(),
            signer_key=signer_account.key.hex(),
            persona=test_persona,
            is_active=True
        )
        
        # Register signer with RISE
        try:
            await self.rise_client.register_signer(
                account.private_key, 
                account.signer_key
            )
        except Exception as e:
            print(f"Warning: Signer registration failed: {e}")
        
        # Save to storage
        self.storage.save_account(account)
        
        return account
    
    async def get_account(self, account_id: str) -> Optional[Account]:
        """Get account by ID."""
        return self.storage.get_account(account_id)
    
    async def list_accounts(self) -> List[Account]:
        """List all accounts."""
        return self.storage.list_accounts()
    
    async def update_persona(self, account_id: str, posts: List[str]) -> Optional[Persona]:
        """Update account persona with fresh posts."""
        account = self.storage.get_account(account_id)
        if not account or not account.persona:
            return None
        
        # Generate updated persona
        new_persona = await self.ai_client.create_persona_from_posts(
            account.persona.handle, 
            posts,
            account.persona.bio
        )
        
        # Update account
        account.persona = new_persona
        self.storage.save_account(account)
        
        return new_persona
    
    async def check_account_status(self, account_id: str) -> dict:
        """Check account status including RISE balances and positions."""
        account = self.storage.get_account(account_id)
        if not account:
            return {"error": "Account not found"}
        
        status = {
            "account_id": account_id,
            "address": account.address,
            "persona": account.persona.name if account.persona else "No persona",
            "is_active": account.is_active,
        }
        
        try:
            # Check RISE balance and positions
            balance = await self.rise_client.get_balance(account.address)
            positions = await self.rise_client.get_all_positions(account.address)
            
            status.update({
                "balance": balance,
                "positions_count": len(positions),
                "has_funds": bool(balance.get("cross_margin_balance", 0)),
            })
            
        except Exception as e:
            status["rise_error"] = str(e)
        
        return status
    
    async def create_account_from_mock_profile(self, handle: str) -> Account:
        """Create account using one of the predefined mock profiles."""
        # Get mock profile
        mock_profile = self.mock_social.get_profile(handle)
        if not mock_profile:
            available = self.mock_social.list_profiles()
            raise ValueError(f"Mock profile '{handle}' not found. Available: {available}")
        
        # Generate some sample tweets first
        sample_market = {"btc_price": 95000, "eth_price": 3500, "btc_change": 0.02, "eth_change": -0.01}
        for _ in range(10):  # Generate 10 sample tweets
            mock_profile.generate_tweet_based_on_market(sample_market)
        
        # Get profile data
        profile_data = await self.mock_social.get_user_profile(handle)
        
        # Create account with persona
        return await self.create_account_with_persona(
            handle=handle,
            posts=profile_data["tweet_texts"],
            bio=profile_data["bio"]
        )
    
    def get_mock_profiles(self) -> List[str]:
        """Get list of available mock profiles."""
        return self.mock_social.list_profiles()
    
    def simulate_market_activity(self, market_data: dict) -> dict:
        """Simulate social media activity for all mock profiles."""
        return self.mock_social.simulate_daily_activity(market_data)
    
    async def close(self):
        """Cleanup resources."""
        await self.rise_client.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()