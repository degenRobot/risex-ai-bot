"""Profile Manager API with authentication for creating new trading profiles."""

# from ..profiles.factory import ProfileFactory, ProfileCreationError  # Removed module
import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from eth_account import Account as EthAccount
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field, validator

from ..config import settings
from ..models import Trade, TradingStyle
from ..services.rise_client import RiseClient
from ..services.storage import JSONStorage

logger = logging.getLogger(__name__)


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
    persona: dict
    initial_deposit: float
    message: str


class PersonaUpdate(BaseModel):
    """Updatable persona fields."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    bio: Optional[str] = Field(None, min_length=1, max_length=500)
    trading_style: Optional[TradingStyle] = None
    risk_tolerance: Optional[float] = Field(None, ge=0.0, le=1.0)
    favorite_assets: Optional[list[str]] = Field(None, max_items=10)
    personality_traits: Optional[list[str]] = Field(None, max_items=20)
    
    @validator("favorite_assets")
    def validate_assets(cls, v):
        if v is not None:
            # Validate asset symbols
            valid_assets = ["BTC", "ETH", "SOL", "LINK", "UNI", "AAVE", "SNX", "CRV"]
            for asset in v:
                if asset not in valid_assets:
                    raise ValueError(f"Invalid asset: {asset}. Must be one of {valid_assets}")
        return v


class UpdateProfileRequest(BaseModel):
    """Request to update profile attributes."""
    persona_update: Optional[PersonaUpdate] = None
    is_active: Optional[bool] = None
    deposit_amount: Optional[float] = None  # For tracking only


class APIKeyConfig:
    """Manage API keys for admin endpoints."""
    
    @classmethod
    def validate_key(cls, key: str) -> bool:
        """Validate an API key."""
        # Only use the master ADMIN_API_KEY from environment for production deployment
        # This ensures consistency across multiple instances on Fly.io
        if not settings.admin_api_key:
            return False
        return key == settings.admin_api_key


async def verify_api_key(x_api_key: str = Header(...)) -> str:
    """Verify the API key from header."""
    if not APIKeyConfig.validate_key(x_api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )
    return x_api_key


@router.post("/profiles", response_model=CreateProfileResponse)
async def create_profile(
    request: CreateProfileRequest,
    api_key: str = Depends(verify_api_key),
) -> CreateProfileResponse:
    """
    Create a new trading profile with automated setup.
    
    This endpoint:
    1. Generates new account and signer keys
    2. Creates the persona based on personality type
    3. Registers signer on RISE
    4. Deposits initial USDC
    5. Fetches initial equity for P&L tracking
    6. Activates the profile for trading
    
    Requires API key authentication in X-API-Key header.
    """
    try:
        # ProfileFactory removed - would need reimplementation
        raise HTTPException(
            status_code=501, 
            detail="Profile creation temporarily disabled during refactoring",
        )
        
        # Success message with equity info
        equity_info = ""
        if profile_data.get("initial_equity"):
            equity_info = f", initial equity: ${profile_data['initial_equity']:.2f}"
        
        message = f"Profile created and funded with {request.initial_deposit} USDC{equity_info}"
        
        return CreateProfileResponse(
            profile_id=profile_data["profile_id"],
            address=profile_data["address"],
            signer_address=profile_data["signer_address"],
            persona=profile_data["persona"],
            initial_deposit=request.initial_deposit,
            message=message,
        )
        
    except ValueError as e:  # ProfileCreationError was removed
        # Profile creation specific error
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except Exception as e:
        # Generic error
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create profile: {e!s}",
        )


@router.get("/profiles/{profile_id}")
async def get_admin_profile(
    profile_id: str,
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Get detailed profile information (admin view with sensitive data)."""
    account = storage.get_account(profile_id)
    if not account:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Get current equity if available
    current_equity = None
    try:
        from ..services.equity_monitor import EquityMonitor
        equity_monitor = EquityMonitor()
        equity_data = await equity_monitor.fetch_equity(account.address)
        if equity_data and "equity" in equity_data:
            current_equity = equity_data["equity"]
    except Exception as e:
        logger.warning(f"Could not fetch equity: {e}")
    
    return {
        "profile_id": account.id,
        "address": account.address,
        "signer_address": EthAccount.from_key(account.signer_key).address,
        "persona": account.persona.model_dump() if account.persona else None,
        "is_active": account.is_active,
        "is_registered": account.is_registered,
        "has_deposited": account.has_deposited,
        "deposit_amount": account.deposit_amount,
        "initial_equity": account.initial_equity,
        "current_equity": current_equity,
        "created_at": account.created_at.isoformat() if account.created_at else None,
        "registered_at": account.registered_at.isoformat() if account.registered_at else None,
        "deposited_at": account.deposited_at.isoformat() if account.deposited_at else None,
    }


@router.get("/profiles")
async def list_admin_profiles(
    api_key: str = Depends(verify_api_key),
) -> dict:
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
                "created_at": acc.created_at,
            }
            for acc in accounts
        ],
    }


@router.put("/profiles/{profile_id}")
async def update_profile(
    profile_id: str,
    request: UpdateProfileRequest,
    api_key: str = Depends(verify_api_key),
) -> dict:
    """
    Update an existing profile's editable attributes.
    
    Editable fields:
    - Persona attributes (bio, trading_style, risk_tolerance, etc.)
    - Active status
    - Deposit amount (for tracking purposes only)
    
    Non-editable fields (for security):
    - Address, private keys, signer key
    - Profile ID
    - Registration status
    """
    try:
        account = storage.get_account(profile_id)
        if not account:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Update persona if provided
        if request.persona_update:
            if account.persona:
                # Update existing persona fields
                update_data = request.persona_update.model_dump(exclude_unset=True)
                for field, value in update_data.items():
                    if hasattr(account.persona, field):
                        setattr(account.persona, field, value)
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot update persona - profile has no persona",
                )
        
        # Update account fields
        if request.is_active is not None:
            account.is_active = request.is_active
            
        if request.deposit_amount is not None:
            # Only update tracking amount, doesn't affect on-chain balance
            account.deposit_amount = request.deposit_amount
        
        # Save updated account
        storage.save_account(account)
        
        # Publish update event
        from ..realtime.bus import BUS
        from ..realtime.events import EventType, RealtimeEvent
        
        update_event = RealtimeEvent(
            type=EventType.PROFILE_UPDATED,
            profile_id=profile_id,
            payload={
                "profile_id": profile_id,
                "updated_fields": list(request.model_dump(exclude_unset=True).keys()),
                "is_active": account.is_active,
            },
        )
        await BUS.publish(update_event)
        
        return {
            "message": f"Profile {profile_id} updated successfully",
            "profile_id": profile_id,
            "updated_fields": list(request.model_dump(exclude_unset=True).keys()),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update profile: {e!s}",
        )


@router.delete("/profiles/{profile_id}")
async def delete_profile(
    profile_id: str,
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Delete a profile (deactivate it)."""
    account = storage.get_account(profile_id)
    if not account:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Deactivate instead of delete
    account.is_active = False
    storage.save_account(account)
    
    # Publish deactivation event
    from ..realtime.bus import BUS
    from ..realtime.events import EventType, RealtimeEvent
    
    delete_event = RealtimeEvent(
        type=EventType.PROFILE_UPDATED,
        profile_id=profile_id,
        payload={
            "profile_id": profile_id,
            "is_active": False,
            "action": "deactivated",
        },
    )
    await BUS.publish(delete_event)
    
    return {"message": f"Profile {profile_id} deactivated"}


# Note: API key generation removed for production deployment
# Use the ADMIN_API_KEY environment variable directly for all admin authentication


class OrderRequest(BaseModel):
    """Request to place an order for a profile."""
    market: str  # e.g. "BTC-USD"
    side: str  # "buy" or "sell"
    size: float  # Amount in base currency
    reasoning: str = "Admin manual order"


class PositionsResponse(BaseModel):
    """Response with profile positions."""
    positions: dict[str, Any]
    total_value: float
    timestamp: str


@router.post("/profiles/{profile_id}/orders")
async def place_order(
    profile_id: str,
    order_request: OrderRequest,
    api_key: str = Depends(verify_api_key),
) -> dict:
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
            # RISE testnet requires order_type="limit" with price=0 for market orders
            order = await client.place_order(
                account_key=account.private_key,
                signer_key=account.signer_key,
                market_id=market_id,
                side=order_request.side,
                size=order_request.size,
                price=0,  # Market order
                order_type="limit",  # Must use "limit" for market orders on RISE testnet
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
                order_id=order["orderId"],
            )
            storage.save_trade(trade)
            
            return {
                "success": True,
                "order_id": order["orderId"],
                "market": order_request.market,
                "side": order_request.side,
                "size": order_request.size,
                "message": "Order placed successfully",
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to place order: {e!s}",
        )


@router.get("/profiles/{profile_id}/positions", response_model=PositionsResponse)
async def get_positions(
    profile_id: str,
    api_key: str = Depends(verify_api_key),
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
                timestamp=datetime.utcnow().isoformat(),
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get positions: {e!s}",
        )


@router.get("/profiles/{profile_id}/balance")
async def get_balance(
    profile_id: str,
    api_key: str = Depends(verify_api_key),
) -> dict:
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
                "account_info": balance_info,
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get balance: {e!s}",
        )