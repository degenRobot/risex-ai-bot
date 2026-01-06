"""Tests for event models."""

import json
from datetime import datetime
from uuid import UUID

from app.realtime.events import (
    EventMetadata,
    EventType,
    RealtimeEvent,
    create_account_update,
    create_chat_message,
    create_chat_stream_chunk,
    create_chat_stream_final,
    create_chat_stream_start,
    create_market_update,
    create_trade_decision,
)


def test_event_type_enum():
    """Test EventType enum values."""
    assert EventType.MARKET_UPDATE.value == "market.update"
    assert EventType.CHAT_USER_MESSAGE.value == "chat.user_message"
    assert EventType.CHAT_ASSISTANT_CHUNK.value == "chat.assistant_chunk"
    assert EventType.TRADE_DECISION.value == "trade.decision"


def test_realtime_event_creation():
    """Test creating a basic RealtimeEvent."""
    event = RealtimeEvent(
        type=EventType.MARKET_UPDATE,
        profile_id="test-profile",
        payload={"symbol": "BTC", "price": 95000},
        metadata=EventMetadata(sender_id="test-sender"),
    )
    
    assert isinstance(event.id, UUID)
    assert isinstance(event.timestamp, datetime)
    assert event.type == EventType.MARKET_UPDATE
    assert event.profile_id == "test-profile"
    assert event.payload["symbol"] == "BTC"
    assert event.metadata.sender_id == "test-sender"


def test_event_serialization():
    """Test event to/from JSON."""
    original = RealtimeEvent(
        type=EventType.CHAT_USER_MESSAGE,
        profile_id="prof-123",
        payload={"content": "Hello world"},
        metadata=EventMetadata(
            sender_id="user-456",
            message_id="msg-789",
        ),
    )
    
    # Serialize to JSON
    json_data = original.to_json()
    assert isinstance(json_data, dict)
    assert json_data["type"] == "chat.user_message"
    assert json_data["profile_id"] == "prof-123"
    assert json_data["payload"]["content"] == "Hello world"
    
    # Can be JSON stringified
    json_str = json.dumps(json_data)
    assert isinstance(json_str, str)
    
    # Deserialize back
    reconstructed = RealtimeEvent.from_json(json_data)
    assert reconstructed.id == original.id
    assert reconstructed.type == original.type
    assert reconstructed.profile_id == original.profile_id
    assert reconstructed.payload == original.payload
    assert reconstructed.metadata.sender_id == original.metadata.sender_id


def test_create_market_update():
    """Test market update event factory."""
    event = create_market_update(
        symbol="ETH",
        price=3100.50,
        change_24h=-0.025,
        volume_24h=1500000.0,
        funding_rate=0.001,
    )
    
    assert event.type == EventType.MARKET_UPDATE
    assert event.payload["symbol"] == "ETH"
    assert event.payload["price"] == 3100.50
    assert event.payload["change_24h"] == -0.025
    assert event.payload["volume_24h"] == 1500000.0
    assert event.payload["funding_rate"] == 0.001


def test_create_chat_message():
    """Test chat message event factory."""
    event = create_chat_message(
        profile_id="prof-abc",
        sender_id="user-123",
        message_id="msg-456",
        content="What's the market outlook?",
        role="user",
    )
    
    assert event.type == EventType.CHAT_USER_MESSAGE
    assert event.profile_id == "prof-abc"
    assert event.payload["content"] == "What's the market outlook?"
    assert event.payload["role"] == "user"
    assert event.metadata.sender_id == "user-123"
    assert event.metadata.message_id == "msg-456"


def test_chat_streaming_events():
    """Test chat streaming event factories."""
    profile_id = "prof-123"
    message_id = "msg-789"
    correlation_id = "corr-abc"
    
    # Start event
    start = create_chat_stream_start(profile_id, message_id, correlation_id)
    assert start.type == EventType.CHAT_ASSISTANT_START
    assert start.profile_id == profile_id
    assert start.payload["message_id"] == message_id
    assert start.metadata.correlation_id == correlation_id
    
    # Chunk events
    chunk1 = create_chat_stream_chunk(
        profile_id, message_id, "The market", 0, correlation_id,
    )
    assert chunk1.type == EventType.CHAT_ASSISTANT_CHUNK
    assert chunk1.payload["content"] == "The market"
    assert chunk1.payload["chunk_index"] == 0
    assert chunk1.metadata.chunk_index == 0
    
    chunk2 = create_chat_stream_chunk(
        profile_id, message_id, " looks bullish", 1, correlation_id,
    )
    assert chunk2.payload["content"] == " looks bullish"
    assert chunk2.payload["chunk_index"] == 1
    
    # Final event
    final = create_chat_stream_final(
        profile_id, message_id,
        "The market looks bullish",
        correlation_id, 2,
    )
    assert final.type == EventType.CHAT_ASSISTANT_FINAL
    assert final.payload["content"] == "The market looks bullish"
    assert final.metadata.total_chunks == 2


def test_create_trade_decision():
    """Test trade decision event factory."""
    event = create_trade_decision(
        profile_id="prof-123",
        trader_name="Bullish Bob",
        market="BTC-USD",
        action="buy",
        size=0.1,
        reason="Strong support at 95k",
        confidence=0.85,
    )
    
    assert event.type == EventType.TRADE_DECISION
    assert event.profile_id == "prof-123"
    assert event.payload["trader_name"] == "Bullish Bob"
    assert event.payload["market"] == "BTC-USD"
    assert event.payload["action"] == "buy"
    assert event.payload["size"] == 0.1
    assert event.payload["reason"] == "Strong support at 95k"
    assert event.payload["confidence"] == 0.85


def test_create_account_update():
    """Test account update event factory."""
    event = create_account_update(
        profile_id="prof-123",
        address="0x1234...5678",
        equity=10500.50,
        free_margin=8000.0,
        positions_count=3,
        total_pnl=500.50,
    )
    
    assert event.type == EventType.ACCOUNT_UPDATE
    assert event.profile_id == "prof-123"
    assert event.payload["address"] == "0x1234...5678"
    assert event.payload["equity"] == 10500.50
    assert event.payload["free_margin"] == 8000.0
    assert event.payload["positions_count"] == 3
    assert event.payload["total_pnl"] == 500.50


def test_metadata_optional_fields():
    """Test that metadata handles optional fields correctly."""
    # Empty metadata
    meta1 = EventMetadata()
    assert meta1.sender_id is None
    assert meta1.message_id is None
    assert meta1.chunk_index is None
    
    # Partial metadata
    meta2 = EventMetadata(sender_id="user-123")
    assert meta2.sender_id == "user-123"
    assert meta2.message_id is None
    
    # Full metadata
    meta3 = EventMetadata(
        sender_id="user-456",
        message_id="msg-789",
        chunk_index=5,
        total_chunks=10,
        correlation_id="corr-xyz",
    )
    assert meta3.sender_id == "user-456"
    assert meta3.chunk_index == 5
    assert meta3.total_chunks == 10