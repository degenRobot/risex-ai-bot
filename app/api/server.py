"""FastAPI server for RISE AI Trading Bot."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from fastapi import Query
import logging

from ..services.storage import JSONStorage
from ..services.profile_chat import ProfileChatService
from ..services.equity_monitor import get_equity_monitor
from ..services.async_data_manager import AsyncDataManager
from ..models import Account
from ..pending_actions import ActionStatus
from .profile_manager import router as admin_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="RISE AI Trading Bot API",
    description="API for managing AI trading profiles on RISE testnet",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage instance
storage = JSONStorage()

# Chat service instance
chat_service = ProfileChatService()

# Active trading status (managed by main bot)
active_traders = {}

# Include admin router
app.include_router(admin_router)


# Application startup
@app.on_event("startup")
async def startup():
    """Initialize services on startup."""
    logger.info("Starting RISE AI Trading Bot API...")
    
    # Check and repair data files if needed
    try:
        logger.info("Validating data files...")
        repair_results = storage.repair_all_data_files()
        repaired = [f for f, status in repair_results.items() if status == "repaired"]
        if repaired:
            logger.warning(f"Repaired corrupted files: {', '.join(repaired)}")
        else:
            logger.info("All data files are valid")
    except Exception as e:
        logger.error(f"Failed to validate data files: {e}")
    
    logger.info("API startup complete")


class ProfileSummary(BaseModel):
    """Profile summary response."""
    account_id: str  # Added for frontend
    handle: str
    name: str
    trading_style: str
    is_trading: bool
    total_pnl: float
    net_pnl: float  # Current equity - initial deposit
    current_equity: Optional[float]  # Current account value
    position_count: int
    pending_actions: int


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    chatHistory: Optional[str] = ""
    sessionId: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    chatHistory: str
    profileUpdates: List[str] = []
    sessionId: str
    context: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ProfileDetail(BaseModel):
    """Detailed profile response."""
    account_id: str  # Added for frontend
    handle: str
    name: str
    bio: str
    trading_style: str
    risk_tolerance: float
    personality_traits: List[str]
    is_trading: bool
    account_address: str
    positions: Dict[str, Any]
    pending_actions: List[Dict[str, Any]]
    recent_trades: List[Dict[str, Any]]
    total_pnl: float
    win_rate: Optional[float]


class ActionResponse(BaseModel):
    """Response for action operations."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class ProfilesResponse(BaseModel):
    """Paginated profiles response."""
    profiles: List[ProfileSummary]
    total: int
    page: int
    limit: int
    has_more: bool


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "RISE AI Trading Bot API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check if storage is accessible
        accounts = storage.list_accounts()
        return {
            "status": "healthy",
            "accounts": len(accounts),
            "storage": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.get("/api/profiles", response_model=ProfilesResponse)
async def list_profiles(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    """List all trading profiles with pagination."""
    try:
        accounts = storage.list_accounts()
        equity_monitor = get_equity_monitor()
        profiles = []
        seen_handles = set()  # Track seen handles for deduplication
        
        # Default initial deposit amount (all profiles start with this)
        DEFAULT_INITIAL_DEPOSIT = 1000.0
        
        for account in accounts:
            if account.persona:
                # Skip if we've already seen this handle (deduplication)
                if account.persona.handle in seen_handles:
                    continue
                seen_handles.add(account.persona.handle)
                
                # Get trading status from external tracking
                is_trading = account.id in active_traders
                
                # Get basic stats
                positions = []  # Would be fetched from RISE API
                pending_actions = storage.get_pending_actions(
                    account.id, 
                    status=ActionStatus.PENDING
                )
                
                # Get current equity from on-chain
                current_equity = None
                net_pnl = 0.0
                try:
                    current_equity = await equity_monitor.fetch_equity(account.address)
                    if current_equity is not None:
                        # Use the actual deposit amount if available, otherwise use default
                        initial_deposit = getattr(account, 'deposit_amount', DEFAULT_INITIAL_DEPOSIT) or DEFAULT_INITIAL_DEPOSIT
                        net_pnl = current_equity - initial_deposit
                except Exception as e:
                    logger.warning(f"Could not fetch equity for {account.address}: {e}")
                
                # Calculate P&L from analytics (for backward compatibility)
                analytics = storage.get_trading_analytics(account.id)
                total_pnl = analytics.get("total_pnl", 0.0)
                
                profiles.append(ProfileSummary(
                    account_id=account.id,
                    handle=account.persona.handle,
                    name=account.persona.name,
                    trading_style=account.persona.trading_style.value,
                    is_trading=is_trading,
                    total_pnl=total_pnl,
                    net_pnl=net_pnl,
                    current_equity=current_equity,
                    position_count=len(positions),
                    pending_actions=len(pending_actions)
                ))
        
        # Apply pagination
        total = len(profiles)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_profiles = profiles[start_idx:end_idx]
        
        return ProfilesResponse(
            profiles=paginated_profiles,
            total=total,
            page=page,
            limit=limit,
            has_more=end_idx < total
        )
        
    except Exception as e:
        logger.error(f"Error listing profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profiles/all", response_model=List[ProfileSummary])
async def list_all_profiles():
    """List all trading profiles without pagination (backward compatibility)."""
    try:
        # Call paginated endpoint with high limit
        response = await list_profiles(page=1, limit=1000)
        return response.profiles
    except Exception as e:
        logger.error(f"Error listing all profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profiles/{handle}", response_model=ProfileDetail)
async def get_profile(handle: str):
    """Get detailed profile information."""
    try:
        # Find account by persona handle
        accounts = storage.list_accounts()
        account = None
        
        for acc in accounts:
            if acc.persona and acc.persona.handle == handle:
                account = acc
                break
        
        if not account:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Get detailed information
        is_trading = account.id in active_traders
        
        # Get pending actions
        pending_actions = storage.get_pending_actions(
            account.id,
            status=ActionStatus.PENDING
        )
        pending_summary = []
        for action in pending_actions:
            pending_summary.append({
                "id": action.id,
                "type": action.action_type.value,
                "condition": f"{action.condition.field} {action.condition.operator.value} {action.condition.value}",
                "market": action.action_params.market,
                "created_at": action.created_at.isoformat()
            })
        
        # Get recent trades
        trades = storage.get_trades(account.id, limit=10)
        recent_trades = []
        for trade in trades:
            recent_trades.append({
                "id": trade.id,
                "market": getattr(trade, 'market', 'Unknown'),
                "side": trade.side,
                "size": trade.size,
                "price": trade.price,
                "reasoning": trade.reasoning,
                "timestamp": trade.timestamp.isoformat(),
                "status": trade.status
            })
        
        # Calculate analytics
        analytics = storage.get_trading_analytics(account.id)
        
        # Mock positions (would be fetched from RISE API)
        positions = {}
        
        return ProfileDetail(
            account_id=account.id,  # Include account_id
            handle=account.persona.handle,
            name=account.persona.name,
            bio=account.persona.bio,
            trading_style=account.persona.trading_style.value,
            risk_tolerance=account.persona.risk_tolerance,
            personality_traits=account.persona.personality_traits,
            is_trading=is_trading,
            account_address=account.address,
            positions=positions,
            pending_actions=pending_summary,
            recent_trades=recent_trades,
            total_pnl=analytics.get("avg_session_pnl", 0) * analytics.get("total_sessions", 0),
            win_rate=analytics.get("win_rate")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile {handle}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/profiles/{handle}/start", response_model=ActionResponse)
async def start_trading(handle: str):
    """Start trading for a profile."""
    try:
        # Find account
        accounts = storage.list_accounts()
        account = None
        
        for acc in accounts:
            if acc.persona and acc.persona.handle == handle:
                account = acc
                break
        
        if not account:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        if account.id in active_traders:
            return ActionResponse(
                success=False,
                message="Profile is already trading"
            )
        
        # Mark as active (actual bot process handles trading)
        active_traders[account.id] = True
        
        return ActionResponse(
            success=True,
            message=f"Trading started for {handle}",
            data={"account_id": account.id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting trading for {handle}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/profiles/{handle}/stop", response_model=ActionResponse)
async def stop_trading(handle: str):
    """Stop trading for a profile."""
    try:
        # Find account
        accounts = storage.list_accounts()
        account = None
        
        for acc in accounts:
            if acc.persona and acc.persona.handle == handle:
                account = acc
                break
        
        if not account:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        if account.id not in active_traders:
            return ActionResponse(
                success=False,
                message="Profile is not currently trading"
            )
        
        # Mark as inactive
        del active_traders[account.id]
        
        return ActionResponse(
            success=True,
            message=f"Trading stopped for {handle}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping trading for {handle}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profiles/{handle}/actions")
async def get_pending_actions(handle: str):
    """Get pending actions for a profile."""
    try:
        # Find account
        accounts = storage.list_accounts()
        account = None
        
        for acc in accounts:
            if acc.persona and acc.persona.handle == handle:
                account = acc
                break
        
        if not account:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Get all pending actions
        actions = storage.get_pending_actions(account.id)
        
        result = []
        for action in actions:
            result.append({
                "id": action.id,
                "type": action.action_type.value,
                "status": action.status.value,
                "condition": {
                    "field": action.condition.field,
                    "operator": action.condition.operator.value,
                    "value": action.condition.value,
                    "market": action.condition.market
                },
                "params": action.action_params.model_dump(),
                "created_at": action.created_at.isoformat(),
                "expires_at": action.expires_at.isoformat() if action.expires_at else None,
                "reasoning": action.reasoning
            })
        
        return {"actions": result}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting actions for {handle}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/profiles/{handle}/actions/{action_id}", response_model=ActionResponse)
async def cancel_action(handle: str, action_id: str):
    """Cancel a pending action."""
    try:
        # Find account
        accounts = storage.list_accounts()
        account = None
        
        for acc in accounts:
            if acc.persona and acc.persona.handle == handle:
                account = acc
                break
        
        if not account:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Get action
        action = storage.get_pending_action(action_id)
        if not action:
            raise HTTPException(status_code=404, detail="Action not found")
        
        if action.account_id != account.id:
            raise HTTPException(status_code=403, detail="Action belongs to different profile")
        
        # Cancel action
        success = storage.update_pending_action_status(
            action_id, 
            ActionStatus.CANCELLED
        )
        
        if success:
            return ActionResponse(
                success=True,
                message=f"Action {action_id} cancelled"
            )
        else:
            return ActionResponse(
                success=False,
                message="Failed to cancel action"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling action {action_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/profiles/{account_id}/chat", response_model=ChatResponse)
async def chat_with_profile(account_id: str, chat_request: ChatRequest):
    """Chat with a specific AI trading profile.
    
    This endpoint allows users to have conversations with AI traders.
    The AI can update its market outlook, trading bias, and personality
    based on information shared in the conversation.
    
    Example conversation:
    - User: "Fed is going to drop rates, BTC will pump!"
    - AI: "That's bullish! I should reconsider my short position..."
    """
    try:
        result = await chat_service.chat_with_profile(
            account_id=account_id,
            user_message=chat_request.message,
            chat_history=chat_request.chatHistory,
            user_session_id=chat_request.sessionId
        )
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return ChatResponse(
            response=result["response"],
            chatHistory=result["chatHistory"],
            profileUpdates=result.get("profileUpdates", []),
            sessionId=result["sessionId"],
            context=result.get("context")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat with profile {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@app.get("/api/profiles/{account_id}/summary")
async def get_profile_summary(account_id: str):
    """Get detailed profile summary including recent chat updates.
    
    Returns current market outlook, trading bias, and personality updates
    that have been influenced by recent conversations.
    """
    try:
        summary = await chat_service.get_profile_summary(account_id)
        
        if "error" in summary:
            raise HTTPException(status_code=404, detail=summary["error"])
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile summary {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profiles/{account_id}/context")
async def get_profile_context(account_id: str):
    """Get current trading context for a profile.
    
    Returns current positions, P&L, recent trades, and market data
    that the AI is using for decision making.
    """
    try:
        # Get the account
        account = storage.get_account(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Get trading context
        context = await chat_service.get_profile_context(account)
        
        return {
            "profile_id": account_id,
            "profile_name": account.persona.name if account.persona else account.address[:8],
            "trading_context": context,
            "timestamp": context.get("timestamp")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile context {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Set active traders reference for bot integration
def set_active_traders(traders_dict):
    """Set reference to active traders from main bot."""
    global active_traders
    active_traders = traders_dict


# V2 Chat endpoints with enhanced personalities
@app.post("/api/v2/profiles/{account_id}/chat", response_model=ChatResponse)
async def chat_with_profile_v2(account_id: str, chat_request: ChatRequest):
    """Chat with AI trader using enhanced personality system with immutable personas."""
    try:
        # Check if account exists
        account = storage.get_account(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Use chat service with enhanced profiles
        result = await chat_service.chat_with_profile(
            account_id=account_id,
            user_message=chat_request.message,
            chat_history=chat_request.chatHistory,
            user_session_id=chat_request.sessionId
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return ChatResponse(
            response=result["response"],
            chatHistory=result["chatHistory"],
            profileUpdates=result.get("profileUpdates", []),
            sessionId=result["sessionId"],
            context=result.get("context", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in v2 chat with profile {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v2/profiles/{account_id}/summary")
async def get_profile_summary_v2(account_id: str):
    """Get enhanced profile summary with immutable base and mutable thinking."""
    try:
        # Check if account exists
        account = storage.get_account(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Get summary from chat service
        summary = await chat_service.get_profile_summary(account_id)
        
        if "error" in summary:
            raise HTTPException(status_code=404, detail=summary["error"])
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting v2 profile summary {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))