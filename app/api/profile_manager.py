"""Profile Manager API with authentication for creating new trading profiles."""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
import secrets
import uuid
from datetime import datetime
from eth_account import Account as EthAccount

from ..services.storage import JSONStorage
from ..services.rise_client import RiseClient
from ..models import Account, Persona, TradingStyle, Trade
from ..config import settings


router = APIRouter(prefix="/api/admin", tags=["admin"])
storage = JSONStorage()


class CreateProfileRequest(BaseModel):
    """Request to create a new trading profile."""
    name: str
    handle: str
    bio: str
    trading_style: TradingStyle
    risk_tolerance: float  # 0.0 to 1.0
    personality_type: str  # "cynical", "leftCurve", "midwit"
    initial_deposit: float = 100.0  # USDC amount
    favorite_assets: list[str] = ["BTC", "ETH"]
    personality_traits: list[str] = []


class CreateProfileResponse(BaseModel):
    """Response with created profile details."""
    profile_id: str
    address: str
    signer_address: str
    persona: Dict
    initial_deposit: float
    message: str


class APIKeyConfig:
    """Manage API keys for admin endpoints."""
    
    # In production, store these in database or environment
    # For now, use a simple in-memory store
    _keys: Dict[str, str] = {}
    
    @classmethod
    def generate_key(cls) -> str:
        """Generate a new API key."""
        key = f"ska_{secrets.token_urlsafe(32)}"
        # In production, hash and store this
        cls._keys[key] = "admin"
        return key
    
    @classmethod
    def validate_key(cls, key: str) -> bool:
        """Validate an API key."""
        # Check environment for master key
        master_key = settings.admin_api_key if hasattr(settings, 'admin_api_key') else None
        if master_key and key == master_key:
            return True
        # Check generated keys
        return key in cls._keys


async def verify_api_key(x_api_key: str = Header(...)) -> str:
    """Verify the API key from header."""
    if not APIKeyConfig.validate_key(x_api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return x_api_key


@router.post("/profiles", response_model=CreateProfileResponse)
async def create_profile(
    request: CreateProfileRequest,
    api_key: str = Depends(verify_api_key)
) -> CreateProfileResponse:
    """
    Create a new trading profile with automated setup.
    
    This endpoint:
    1. Generates new account and signer keys
    2. Creates the persona based on personality type
    3. Registers signer on RISE
    4. Deposits initial USDC
    5. Activates the profile for trading
    
    Requires API key authentication in X-API-Key header.
    """
    try:
        # Generate new keys
        account = EthAccount.create()
        signer = EthAccount.create()
        
        # Map personality type to speech style
        speech_styles = {
            "cynical": "financialAdvisor",
            "leftCurve": "smol",
            "midwit": "ct"
        }
        
        # Create persona
        persona = Persona(
            name=request.name,
            handle=request.handle,
            bio=request.bio,
            trading_style=request.trading_style,
            risk_tolerance=request.risk_tolerance,
            favorite_assets=request.favorite_assets,
            personality_traits=request.personality_traits or [
                "unique", "programmatic", "adaptive"
            ],
            sample_posts=[]  # Will be generated from personality
        )
        
        # Create account object
        account_obj = Account(
            id=str(uuid.uuid4()),
            address=account.address,
            private_key=account.key.hex(),
            signer_key=signer.key.hex(),
            persona=persona,
            is_active=True
        )
        
        # Save to storage
        storage.save_account(account_obj)
        
        # Setup on RISE (register signer and deposit)
        async with RiseClient() as client:
            try:
                # Register signer
                await client.register_signer(
                    account_key=account.key.hex(),
                    signer_key=signer.key.hex()
                )
                
                # Update registration status
                account_obj.is_registered = True
                account_obj.registered_at = datetime.utcnow()
                storage.save_account(account_obj)
                
                # Deposit initial USDC
                if request.initial_deposit > 0:
                    tx_hash = await client.deposit_usdc(
                        account_key=account.key.hex(),
                        amount=request.initial_deposit
                    )
                    # Update deposit status
                    account_obj.has_deposited = True
                    account_obj.deposited_at = datetime.utcnow()
                    account_obj.deposit_amount = request.initial_deposit
                    storage.save_account(account_obj)
                    
                    message = f"Profile created and funded with {request.initial_deposit} USDC (tx: {tx_hash})"
                else:
                    message = "Profile created (no initial deposit)"
                    
            except Exception as e:
                # If RISE setup fails, still return the created profile
                message = f"Profile created but RISE setup failed: {str(e)}"
        
        return CreateProfileResponse(
            profile_id=account_obj.id,
            address=account.address,
            signer_address=signer.address,
            persona=persona.model_dump(),
            initial_deposit=request.initial_deposit,
            message=message
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create profile: {str(e)}"
        )


@router.get("/profiles")
async def list_admin_profiles(
    api_key: str = Depends(verify_api_key)
) -> Dict:
    """List all profiles with full details (admin view)."""
    accounts = storage.list_accounts()
    
    return {
        "total": len(accounts),
        "profiles": [
            {
                "id": acc.id,
                "address": acc.address,
                "signer_address": EthAccount.from_key(acc.signer_key).address,
                "persona": acc.persona.model_dump() if acc.persona else None,
                "is_active": acc.is_active,
                "created_at": acc.created_at
            }
            for acc in accounts
        ]
    }


@router.delete("/profiles/{profile_id}")
async def delete_profile(
    profile_id: str,
    api_key: str = Depends(verify_api_key)
) -> Dict:
    """Delete a profile (deactivate it)."""
    account = storage.get_account(profile_id)
    if not account:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Deactivate instead of delete
    account.is_active = False
    storage.save_account(account)
    
    return {"message": f"Profile {profile_id} deactivated"}


@router.post("/api-keys/generate")
async def generate_api_key(
    master_key: str = Header(None, alias="X-Master-Key")
) -> Dict:
    """
    Generate a new API key (requires master key).
    
    In production, this would:
    1. Verify master key from environment
    2. Generate and hash the new key
    3. Store in database with metadata
    4. Return the key only once
    """
    # Simple check for demo - in production use proper auth
    if master_key != "master-secret-key":
        raise HTTPException(status_code=401, detail="Invalid master key")
    
    new_key = APIKeyConfig.generate_key()
    
    return {
        "api_key": new_key,
        "message": "Save this key - it won't be shown again",
        "usage": "Include in X-API-Key header for admin endpoints"
    }


class OrderRequest(BaseModel):
    """Request to place an order for a profile."""
    market: str  # e.g. "BTC-USD"
    side: str  # "buy" or "sell"
    size: float  # Amount in base currency
    reasoning: str = "Admin manual order"


class PositionsResponse(BaseModel):
    """Response with profile positions."""
    positions: Dict[str, Any]
    total_value: float
    timestamp: str


@router.post("/profiles/{profile_id}/orders")
async def place_order(
    profile_id: str,
    order_request: OrderRequest,
    api_key: str = Depends(verify_api_key)
) -> Dict:
    """
    Place a market order for a specific profile.
    
    This admin endpoint allows forcing a profile to place an order.
    Useful for testing or manual intervention.
    """
    try:
        # Get account
        account = storage.get_account(profile_id)
        if not account:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Place market order
        async with RiseClient() as client:
            # Get market ID from market name
            markets = await client.get_markets()
            market_id = None
            for market in markets:
                # Check base_asset_symbol field as mentioned in improvements.md
                if market.get("base_asset_symbol") == order_request.market.split("-")[0]:
                    market_id = market.get("market_id")
                    break
            
            if market_id is None:
                raise ValueError(f"Market {order_request.market} not found")
            
            # Place the order
            order = await client.place_order(
                account_key=account.private_key,
                signer_key=account.signer_key,
                market_id=market_id,
                side=order_request.side,
                size=order_request.size,
                price=0,  # Market order
                order_type="market"
            )
            
            # Save trade record
            trade = Trade(
                id=str(uuid.uuid4()),
                account_id=account.id,
                side=order_request.side,
                size=order_request.size,
                market=order_request.market,
                price=order.get("price", 0),
                reasoning=order_request.reasoning,
                timestamp=datetime.utcnow(),
                status="executed",
                order_id=order["orderId"]
            )
            storage.save_trade(trade)
            
            return {
                "success": True,
                "order_id": order["orderId"],
                "market": order_request.market,
                "side": order_request.side,
                "size": order_request.size,
                "message": f"Order placed successfully"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to place order: {str(e)}"
        )


@router.get("/profiles/{profile_id}/positions", response_model=PositionsResponse)
async def get_positions(
    profile_id: str,
    api_key: str = Depends(verify_api_key)
) -> PositionsResponse:
    """
    Get current positions for a profile.
    
    Returns all open positions and their current values.
    """
    try:
        # Get account
        account = storage.get_account(profile_id)
        if not account:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Get positions from RISE
        async with RiseClient() as client:
            positions_list = await client.get_all_positions(account.address)
            
            # Convert list to dict by market
            positions = {}
            total_value = 0
            for pos in positions_list:
                if isinstance(pos, dict):
                    market = pos.get("market", "Unknown")
                    positions[market] = pos
                    if "notionalValue" in pos:
                        total_value += abs(pos["notionalValue"])
            
            return PositionsResponse(
                positions=positions,
                total_value=total_value,
                timestamp=datetime.utcnow().isoformat()
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get positions: {str(e)}"
        )


@router.get("/profiles/{profile_id}/balance")
async def get_balance(
    profile_id: str,
    api_key: str = Depends(verify_api_key)
) -> Dict:
    """
    Get USDC balance for a profile.
    
    Returns available balance and other account info.
    """
    try:
        # Get account
        account = storage.get_account(profile_id)
        if not account:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Get balance from RISE
        async with RiseClient() as client:
            balance_info = await client.get_balance(account.address)
            
            return {
                "address": account.address,
                "balance": balance_info.get("marginSummary", {}).get("accountValue", 0),
                "available": balance_info.get("marginSummary", {}).get("freeCollateral", 0),
                "account_info": balance_info
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get balance: {str(e)}"
        )