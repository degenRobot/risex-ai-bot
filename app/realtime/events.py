"""Realtime event models and types for WebSocket streaming."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Types of realtime events."""
    
    # Market events
    MARKET_UPDATE = "market.update"
    MARKET_SUMMARY = "market.summary"
    
    # Trading events
    TRADE_DECISION = "trade.decision"
    TRADE_ORDER_SUBMITTED = "trade.order_submitted"
    TRADE_ORDER_FILLED = "trade.order_filled"
    TRADE_ORDER_REJECTED = "trade.order_rejected"
    TRADE_POSITION_OPENED = "trade.position_opened"
    TRADE_POSITION_CLOSED = "trade.position_closed"
    
    # Account events
    ACCOUNT_UPDATE = "account.update"
    ACCOUNT_EQUITY_UPDATE = "account.equity_update"
    ACCOUNT_POSITION_UPDATE = "account.position_update"
    
    # Chat events
    CHAT_USER_MESSAGE = "chat.user_message"
    CHAT_ASSISTANT_START = "chat.assistant_start"
    CHAT_ASSISTANT_CHUNK = "chat.assistant_chunk"
    CHAT_ASSISTANT_FINAL = "chat.assistant_final"
    CHAT_HISTORY_LOADED = "chat.history_loaded"
    CHAT_ERROR = "chat.error"
    
    # Profile events
    PROFILE_UPDATED = "profile.updated"
    PROFILE_CREATED = "profile.created"
    PROFILE_THINKING_UPDATE = "profile.thinking_update"
    
    # Bot status events
    BOT_STATUS = "bot.status"
    BOT_ERROR = "bot.error"
    BOT_CONNECTED = "bot.connected"
    BOT_DISCONNECTED = "bot.disconnected"


class EventMetadata(BaseModel):
    """Metadata for event tracking and deduplication."""
    
    sender_id: Optional[str] = Field(None, description="ID of the user/client that triggered the event")
    message_id: Optional[str] = Field(None, description="ID of the message (for chat events)")
    chunk_index: Optional[int] = Field(None, description="Index of chunk (for streaming events)")
    total_chunks: Optional[int] = Field(None, description="Total expected chunks (if known)")
    correlation_id: Optional[str] = Field(None, description="ID to correlate related events")


class RealtimeEvent(BaseModel):
    """Base model for all realtime events."""
    
    id: UUID = Field(default_factory=uuid4, description="Unique event ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp")
    type: EventType = Field(..., description="Event type")
    profile_id: Optional[str] = Field(None, description="Profile ID this event relates to")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event-specific data")
    metadata: EventMetadata = Field(default_factory=EventMetadata, description="Event metadata")
    
    def to_json(self) -> Dict[str, Any]:
        """Convert event to JSON-serializable dict."""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "type": self.type.value,
            "profile_id": self.profile_id,
            "payload": self.payload,
            "metadata": self.metadata.model_dump(exclude_none=True)
        }
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "RealtimeEvent":
        """Create event from JSON dict."""
        return cls(
            id=UUID(data["id"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            type=EventType(data["type"]),
            profile_id=data.get("profile_id"),
            payload=data.get("payload", {}),
            metadata=EventMetadata(**data.get("metadata", {}))
        )


# Event factory functions for common event types

def create_market_update(
    symbol: str,
    price: float,
    change_24h: float,
    volume_24h: float,
    funding_rate: Optional[float] = None,
    **kwargs
) -> RealtimeEvent:
    """Create a market update event."""
    return RealtimeEvent(
        type=EventType.MARKET_UPDATE,
        payload={
            "symbol": symbol,
            "price": price,
            "change_24h": change_24h,
            "volume_24h": volume_24h,
            "funding_rate": funding_rate,
            **kwargs
        }
    )


def create_chat_message(
    profile_id: str,
    sender_id: str,
    message_id: str,
    content: str,
    role: str = "user"
) -> RealtimeEvent:
    """Create a chat message event."""
    return RealtimeEvent(
        type=EventType.CHAT_USER_MESSAGE,
        profile_id=profile_id,
        payload={
            "content": content,
            "role": role,
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        metadata=EventMetadata(
            sender_id=sender_id,
            message_id=message_id
        )
    )


def create_chat_stream_start(
    profile_id: str,
    message_id: str,
    correlation_id: str
) -> RealtimeEvent:
    """Create a chat streaming start event."""
    return RealtimeEvent(
        type=EventType.CHAT_ASSISTANT_START,
        profile_id=profile_id,
        payload={
            "message_id": message_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        metadata=EventMetadata(
            message_id=message_id,
            correlation_id=correlation_id
        )
    )


def create_chat_stream_chunk(
    profile_id: str,
    message_id: str,
    chunk_content: str,
    chunk_index: int,
    correlation_id: str
) -> RealtimeEvent:
    """Create a chat streaming chunk event."""
    return RealtimeEvent(
        type=EventType.CHAT_ASSISTANT_CHUNK,
        profile_id=profile_id,
        payload={
            "content": chunk_content,
            "chunk_index": chunk_index
        },
        metadata=EventMetadata(
            message_id=message_id,
            chunk_index=chunk_index,
            correlation_id=correlation_id
        )
    )


def create_chat_stream_final(
    profile_id: str,
    message_id: str,
    full_content: str,
    correlation_id: str,
    total_chunks: int
) -> RealtimeEvent:
    """Create a chat streaming completion event."""
    return RealtimeEvent(
        type=EventType.CHAT_ASSISTANT_FINAL,
        profile_id=profile_id,
        payload={
            "content": full_content,
            "message_id": message_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        metadata=EventMetadata(
            message_id=message_id,
            correlation_id=correlation_id,
            total_chunks=total_chunks
        )
    )


def create_trade_decision(
    profile_id: str,
    trader_name: str,
    market: str,
    action: str,
    size: float,
    reason: str,
    confidence: float
) -> RealtimeEvent:
    """Create a trading decision event."""
    return RealtimeEvent(
        type=EventType.TRADE_DECISION,
        profile_id=profile_id,
        payload={
            "trader_name": trader_name,
            "market": market,
            "action": action,
            "size": size,
            "reason": reason,
            "confidence": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


def create_account_update(
    profile_id: str,
    address: str,
    equity: float,
    free_margin: float,
    positions_count: int,
    total_pnl: float
) -> RealtimeEvent:
    """Create an account update event."""
    return RealtimeEvent(
        type=EventType.ACCOUNT_UPDATE,
        profile_id=profile_id,
        payload={
            "address": address,
            "equity": equity,
            "free_margin": free_margin,
            "positions_count": positions_count,
            "total_pnl": total_pnl,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )