"""Profile generation and setup utilities."""

import asyncio
import time
from datetime import datetime
from typing import Dict, Optional, Tuple
from eth_account import Account as EthAccount
from ..services.rise_client import RiseClient
from ..services.storage import JSONStorage
from ..models import Account
import logging

logger = logging.getLogger(__name__)


class ProfileGenerator:
    """Generate and setup new trading profiles."""
    
    def __init__(self):
        self.rise_client = RiseClient()
        self.storage = JSONStorage()
    
    async def create_new_profile(
        self,
        name: str,
        initial_deposit: float = 1000.0,
        profile_type: str = "aggressive"
    ) -> Dict[str, any]:
        """Create a new profile with keys, register signer, and deposit USDC.
        
        Args:
            name: Profile name
            initial_deposit: Amount of USDC to deposit
            profile_type: Trading profile type (conservative, moderate, aggressive)
            
        Returns:
            Dict with profile details and setup status
        """
        logger.info(f"Creating new profile: {name}")
        
        # Step 1: Generate keys
        account_key, signer_key = self._generate_keys()
        account = EthAccount.from_key(account_key)
        signer = EthAccount.from_key(signer_key)
        
        logger.info(f"Generated account: {account.address}")
        logger.info(f"Generated signer: {signer.address}")
        
        # Step 2: Save account to storage
        import uuid
        account_data = Account(
            id=str(uuid.uuid4()),
            address=account.address,
            private_key=account_key,
            signer_key=signer_key,
            created_at=datetime.now(),
            # Note: The Account model doesn't have name, profile_type, or risk_params fields
            # These would need to be stored separately or the model extended
        )
        
        self.storage.save_account(account_data)
        logger.info(f"Saved account to storage")
        
        # Step 3: Register signer for gasless trading
        try:
            logger.info("Registering signer for gasless trading...")
            signer_result = await self.rise_client.register_signer(
                account_key=account_key,
                signer_key=signer_key
            )
            logger.info("Signer registered successfully")
            signer_registered = True
        except Exception as e:
            logger.error(f"Failed to register signer: {e}")
            signer_registered = False
            signer_result = str(e)
        
        # Step 4: Deposit USDC
        deposit_success = False
        deposit_tx = None
        
        if signer_registered and initial_deposit > 0:
            try:
                logger.info(f"Depositing {initial_deposit} USDC...")
                deposit_result = await self._deposit_usdc(
                    account_key=account_key,
                    amount=initial_deposit
                )
                deposit_tx = deposit_result.get("data", {}).get("transaction_hash", "")
                deposit_success = bool(deposit_tx)
                logger.info(f"Deposit successful: {deposit_tx}")
                
                # Wait for deposit to process
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Failed to deposit: {e}")
                deposit_result = str(e)
        
        # Step 5: Return complete profile info
        return {
            "success": signer_registered and deposit_success,
            "profile": {
                "name": name,
                "address": account.address,
                "signer_address": signer.address,
                "profile_type": profile_type,
                "risk_params": {
                    "max_position_size": 0.1 if profile_type == "conservative" else 0.3,
                    "stop_loss_pct": 0.02 if profile_type == "conservative" else 0.05,
                    "take_profit_pct": 0.03 if profile_type == "conservative" else 0.10,
                }
            },
            "setup": {
                "keys_generated": True,
                "signer_registered": signer_registered,
                "signer_result": signer_result if not signer_registered else "Success",
                "deposit_success": deposit_success,
                "deposit_amount": initial_deposit,
                "deposit_tx": deposit_tx
            },
            "private_keys": {
                "account_key": account_key,
                "signer_key": signer_key
            }
        }
    
    def _generate_keys(self) -> Tuple[str, str]:
        """Generate account and signer private keys.
        
        Returns:
            Tuple of (account_key, signer_key)
        """
        # Generate two different accounts
        account = EthAccount.create()
        signer = EthAccount.create()
        
        return account.key.hex(), signer.key.hex()
    
    async def _deposit_usdc(self, account_key: str, amount: float) -> Dict:
        """Deposit USDC using 6 decimals."""
        account = EthAccount.from_key(account_key)
        domain = await self.rise_client.get_eip712_domain()
        
        # USDC uses 6 decimals
        amount_wei = int(amount * 1e6)
        
        # Create deposit signature
        typed_data = {
            "domain": domain,
            "message": {
                "account": account.address,
                "amount": amount_wei,
            },
            "primaryType": "Deposit",
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "Deposit": [
                    {"name": "account", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                ]
            }
        }
        
        signature = self.rise_client._sign_typed_data(typed_data, account_key)
        nonce = self.rise_client._create_client_nonce(account.address)
        deadline = int(time.time()) + 300
        
        # Submit deposit
        return await self.rise_client._request(
            "POST", "/v1/account/deposit",
            json={
                "account": account.address,
                "amount": str(amount_wei),
                "permit_params": {
                    "account": account.address,
                    "signer": account.address,
                    "deadline": str(deadline),
                    "signature": signature,
                    "nonce": str(nonce)
                }
            }
        )
    
    async def close(self):
        """Clean up resources."""
        await self.rise_client.close()


async def quick_setup_profile(
    name: str = "AI Trader",
    deposit: float = 1000.0,
    profile_type: str = "moderate"
) -> Dict:
    """Quick helper to setup a new profile."""
    generator = ProfileGenerator()
    try:
        result = await generator.create_new_profile(name, deposit, profile_type)
        return result
    finally:
        await generator.close()