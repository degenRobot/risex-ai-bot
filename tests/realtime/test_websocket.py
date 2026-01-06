"""Tests for WebSocket endpoint."""

import asyncio
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.realtime.bus import BUS
from app.realtime.events import EventType, create_chat_message, create_market_update
from app.realtime.ws import connection_manager, router


@pytest.fixture
def test_app():
    """Create test FastAPI app with WebSocket router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def test_client(test_app):
    """Create test client."""
    return TestClient(test_app)


def test_websocket_connection(test_client):
    """Test basic WebSocket connection."""
    with test_client.websocket_connect("/ws") as websocket:
        # Should receive connection confirmation
        data = websocket.receive_json()
        assert data["type"] == EventType.BOT_CONNECTED.value
        assert "connection_id" in data["payload"]
        assert data["payload"]["subscribed"] == False


def test_websocket_profile_subscription(test_client):
    """Test WebSocket with profile subscription."""
    profile_id = "test-profile"
    
    with test_client.websocket_connect(f"/ws?profile_id={profile_id}") as websocket:
        # Connection confirmation
        data = websocket.receive_json()
        assert data["type"] == EventType.BOT_CONNECTED.value
        assert data["payload"]["profile_id"] == profile_id
        assert data["payload"]["subscribed"] == True


def test_websocket_message_deduplication(test_client):
    """Test that user doesn't receive their own messages."""
    profile_id = "test-profile"
    user_id = "test-user-123"
    
    with test_client.websocket_connect(
        f"/ws?profile_id={profile_id}&user_id={user_id}",
    ) as websocket:
        # Skip connection message
        websocket.receive_json()
        
        # Send chat message via WebSocket
        websocket.send_json({
            "type": "chat.message",
            "content": "Hello from test",
            "profile_id": profile_id,
        })
        
        # Should get confirmation
        data = websocket.receive_json()
        assert data["type"] == "message_sent"
        
        # Should NOT receive the message back (deduplication)
        # Wait a bit to ensure no message comes
        websocket.send_json({"type": "ping"})
        pong = websocket.receive_json()
        assert pong["type"] == "pong"


@pytest.mark.asyncio
async def test_websocket_event_streaming():
    """Test receiving streamed events."""
    # This test needs to run in async context
    
    profile_id = "stream-test"
    
    # Manually create WebSocket test
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    
    with client.websocket_connect(f"/ws?profile_id={profile_id}") as websocket:
        # Skip connection message
        websocket.receive_json()
        
        # Publish events from another task
        async def publish_events():
            await asyncio.sleep(0.1)  # Let WebSocket settle
            
            # Market update (no profile, won't be received)
            await BUS.publish(create_market_update("BTC", 96000, 0.02, 1000000))
            
            # Chat message for our profile (will be received)
            await BUS.publish(create_chat_message(
                profile_id=profile_id,
                sender_id="other-user",
                message_id=str(uuid4()),
                content="Test message",
                role="user",
            ))
        
        # Run publisher in background
        task = asyncio.create_task(publish_events())
        
        # Should receive chat message
        data = websocket.receive_json()
        assert data["type"] == EventType.CHAT_USER_MESSAGE.value
        assert data["payload"]["content"] == "Test message"
        
        await task


def test_websocket_ping_pong(test_client):
    """Test ping/pong keepalive."""
    with test_client.websocket_connect("/ws") as websocket:
        # Skip connection message
        websocket.receive_json()
        
        # Send ping
        websocket.send_json({"type": "ping"})
        
        # Should receive pong
        data = websocket.receive_json()
        assert data["type"] == "pong"
        assert "timestamp" in data["payload"]


def test_websocket_dynamic_subscription(test_client):
    """Test subscribing to profiles after connection."""
    with test_client.websocket_connect("/ws") as websocket:
        # Skip connection message
        websocket.receive_json()
        
        # Subscribe to profile
        profile_id = "dynamic-profile"
        websocket.send_json({
            "type": "subscribe",
            "profile_id": profile_id,
        })
        
        # Should get confirmation
        data = websocket.receive_json()
        assert data["type"] == "subscribed"
        assert data["payload"]["profile_id"] == profile_id
        
        # Unsubscribe
        websocket.send_json({
            "type": "unsubscribe", 
            "profile_id": profile_id,
        })
        
        # Should get confirmation
        data = websocket.receive_json()
        assert data["type"] == "unsubscribed"
        assert data["payload"]["profile_id"] == profile_id


def test_websocket_status_endpoint(test_client):
    """Test WebSocket status endpoint."""
    response = test_client.get("/ws/status")
    assert response.status_code == 200
    
    data = response.json()
    assert "active_connections" in data
    assert "subscribers" in data
    assert data["event_bus"] == "active"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_connection_manager():
    """Test connection manager functionality."""
    # Create mock WebSocket
    class MockWebSocket:
        def __init__(self):
            self.accepted = False
            
        async def accept(self):
            self.accepted = True
    
    ws = MockWebSocket()
    conn_id = "test-conn-123"
    user_id = "test-user"
    
    # Connect
    await connection_manager.connect(ws, conn_id, user_id, "profile-1")
    assert connection_manager.get_connection_count() == 1
    assert conn_id in connection_manager.get_connections_for_user(user_id)
    
    # Disconnect
    connection_manager.disconnect(conn_id)
    assert connection_manager.get_connection_count() == 0
    assert conn_id not in connection_manager.get_connections_for_user(user_id)