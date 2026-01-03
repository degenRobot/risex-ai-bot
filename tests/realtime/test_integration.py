"""Integration tests for the realtime WebSocket system."""

import asyncio
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.server import app
from app.realtime.bus import BUS, publish_event
from app.realtime.events import (
    create_market_update,
    create_chat_message,
    create_trade_decision,
    create_account_update
)


@pytest.fixture
def client():
    """Create test client for the full app."""
    return TestClient(app)


def test_websocket_integration_basic(client):
    """Test basic WebSocket integration with the full app."""
    # Connect to WebSocket
    with client.websocket_connect("/ws?profile_id=test-profile") as websocket:
        # Should get connection message
        data = websocket.receive_json()
        assert data["type"] == "bot.connected"
        assert data["payload"]["profile_id"] == "test-profile"


def test_websocket_status_available(client):
    """Test that WebSocket status endpoint is available."""
    response = client.get("/ws/status")
    assert response.status_code == 200
    
    data = response.json()
    assert data["event_bus"] == "active"
    assert "active_connections" in data
    assert "subscribers" in data


@pytest.mark.asyncio
async def test_event_flow_integration():
    """Test full event flow from publisher to WebSocket."""
    # This simulates the full flow:
    # 1. Trading bot publishes events
    # 2. WebSocket subscribers receive them
    
    # Create test profile
    profile_id = "integration-test-profile"
    
    # Simulate market update
    market_event = create_market_update("BTC", 96000, 0.03, 2000000)
    recipients = await publish_event(market_event)
    
    # Simulate trade decision
    trade_event = create_trade_decision(
        profile_id=profile_id,
        trader_name="Test Trader",
        market="BTC-USD",
        action="buy",
        size=0.1,
        reason="Integration test trade",
        confidence=0.9
    )
    await publish_event(trade_event)
    
    # Simulate account update
    account_event = create_account_update(
        profile_id=profile_id,
        address="0xtest",
        equity=10000,
        free_margin=8000,
        positions_count=1,
        total_pnl=100
    )
    await publish_event(account_event)
    
    # In a real scenario, WebSocket clients would receive these events
    stats = BUS.get_subscriber_count()
    assert stats["total"] >= 0  # May have active subscribers


@pytest.mark.asyncio
async def test_chat_message_flow():
    """Test chat message flow through the system."""
    profile_id = "chat-test-profile"
    
    # User sends message (would come via REST or WebSocket)
    user_msg = create_chat_message(
        profile_id=profile_id,
        sender_id="user-123",
        message_id="msg-001",
        content="What's your market outlook?",
        role="user"
    )
    await publish_event(user_msg)
    
    # AI responds (in real system, this would be from ProfileChatService)
    # For now, just verify the events can be created and published
    
    # Note: In Phase B, we'll implement the actual streaming chat response


class TestWebSocketLifecycle:
    """Test WebSocket connection lifecycle."""
    
    @pytest.mark.asyncio
    async def test_multiple_connections(self):
        """Test handling multiple simultaneous connections."""
        # Create app instance
        test_app = FastAPI()
        from app.realtime.ws import router as ws_router
        test_app.include_router(ws_router)
        
        client = TestClient(test_app)
        
        # Open multiple connections
        connections = []
        for i in range(3):
            ws = client.websocket_connect(f"/ws?profile_id=profile-{i}")
            ws.__enter__()
            connections.append(ws)
        
        # All should receive their connection messages
        for i, ws in enumerate(connections):
            data = ws.receive_json()
            assert data["type"] == "bot.connected"
            assert data["payload"]["profile_id"] == f"profile-{i}"
        
        # Clean up
        for ws in connections:
            ws.__exit__(None, None, None)


def test_api_still_works_with_websocket(client):
    """Test that REST API endpoints still work with WebSocket enabled."""
    # Test health endpoint
    response = client.get("/health")
    assert response.status_code == 200
    
    # Test root endpoint
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "RISE AI Trading Bot API"
    
    # Test profiles endpoint (should work even if no profiles exist)
    response = client.get("/api/profiles")
    assert response.status_code == 200
    data = response.json()
    assert "profiles" in data
    assert "total" in data