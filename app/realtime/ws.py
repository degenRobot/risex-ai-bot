"""WebSocket endpoint for realtime event streaming."""

import asyncio
import json
import logging
from typing import Optional, Set
from uuid import UUID, uuid4

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from .bus import BUS
from .events import EventType, RealtimeEvent, create_chat_message
from datetime import datetime, timezone


logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections and their metadata."""
    
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}
        self._connection_metadata: dict[str, dict] = {}
    
    async def connect(
        self, 
        websocket: WebSocket,
        connection_id: str,
        user_id: Optional[str] = None,
        profile_id: Optional[str] = None
    ):
        """Register a new WebSocket connection."""
        await websocket.accept()
        self._connections[connection_id] = websocket
        self._connection_metadata[connection_id] = {
            "user_id": user_id,
            "profile_id": profile_id,
            "connected_at": datetime.now(timezone.utc)
        }
        logger.info(f"WebSocket connected: {connection_id} (user: {user_id})")
    
    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection."""
        self._connections.pop(connection_id, None)
        metadata = self._connection_metadata.pop(connection_id, {})
        logger.info(f"WebSocket disconnected: {connection_id} (user: {metadata.get('user_id')})")
    
    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self._connections)
    
    def get_connections_for_user(self, user_id: str) -> list[str]:
        """Get all connection IDs for a specific user."""
        return [
            conn_id for conn_id, metadata in self._connection_metadata.items()
            if metadata.get("user_id") == user_id
        ]


# Global connection manager
connection_manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    profile_id: Optional[str] = Query(None, description="Profile ID to subscribe to"),
    user_id: Optional[str] = Query(None, description="User ID for deduplication"),
    subscribe_global: bool = Query(False, description="Subscribe to all events"),
    last_event_id: Optional[str] = Query(None, description="Last received event ID for replay")
):
    """
    WebSocket endpoint for realtime event streaming.
    
    Query parameters:
    - profile_id: Subscribe to events for a specific profile
    - user_id: User identifier for message deduplication
    - subscribe_global: Subscribe to all events (requires auth)
    - last_event_id: Replay events after this ID
    """
    connection_id = str(uuid4())
    event_queue: Optional[asyncio.Queue] = None
    
    try:
        # Accept connection
        await connection_manager.connect(websocket, connection_id, user_id, profile_id)
        
        # Subscribe to event bus
        if subscribe_global:
            event_queue = await BUS.subscribe_global(connection_id, user_id)
            logger.info(f"Connection {connection_id} subscribed globally")
        elif profile_id:
            event_queue = await BUS.subscribe_profile(connection_id, profile_id, user_id)
            logger.info(f"Connection {connection_id} subscribed to profile {profile_id}")
        else:
            # No subscription requested, just keep connection alive
            logger.info(f"Connection {connection_id} has no subscriptions")
            event_queue = None
        
        # Send connection confirmation
        await websocket.send_json({
            "type": EventType.BOT_CONNECTED.value,
            "payload": {
                "connection_id": connection_id,
                "profile_id": profile_id,
                "user_id": user_id,
                "subscribed": subscribe_global or bool(profile_id)
            }
        })
        
        # Replay missed events if requested
        if last_event_id and event_queue:
            try:
                last_uuid = UUID(last_event_id)
                missed_events = await BUS.get_missed_events(connection_id, last_uuid)
                
                for event in missed_events:
                    await websocket.send_json(event.to_json())
                
                if missed_events:
                    logger.info(f"Replayed {len(missed_events)} missed events to {connection_id}")
            except Exception as e:
                logger.error(f"Failed to replay events: {e}")
        
        # Create tasks for handling incoming and outgoing messages
        receive_task = asyncio.create_task(handle_receive(websocket, connection_id, user_id, profile_id))
        
        # Only create send task if we have an event queue
        if event_queue:
            send_task = asyncio.create_task(handle_send(websocket, event_queue))
            tasks = [receive_task, send_task]
        else:
            tasks = [receive_task]
        
        # Wait for either task to complete
        done, pending = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel pending tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket {connection_id} disconnected by client")
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
    finally:
        # Clean up
        connection_manager.disconnect(connection_id)
        if event_queue:
            await BUS.unsubscribe(connection_id)
        
        # Send disconnect event if possible
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_json({
                    "type": EventType.BOT_DISCONNECTED.value,
                    "payload": {"connection_id": connection_id}
                })
            except:
                pass
        
        try:
            await websocket.close()
        except:
            pass


async def handle_receive(
    websocket: WebSocket,
    connection_id: str,
    user_id: Optional[str],
    profile_id: Optional[str]
):
    """Handle incoming messages from the WebSocket client."""
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle different message types
            message_type = data.get("type")
            
            if message_type == "ping":
                # Respond to ping
                await websocket.send_json({
                    "type": "pong",
                    "payload": {"timestamp": datetime.now(timezone.utc).isoformat()}
                })
            
            elif message_type == "subscribe":
                # Dynamic subscription
                new_profile_id = data.get("profile_id")
                if new_profile_id:
                    await BUS.subscribe_profile(connection_id, new_profile_id, user_id)
                    await websocket.send_json({
                        "type": "subscribed",
                        "payload": {"profile_id": new_profile_id}
                    })
            
            elif message_type == "unsubscribe":
                # Dynamic unsubscription
                remove_profile_id = data.get("profile_id")
                if remove_profile_id:
                    await BUS.unsubscribe(connection_id, remove_profile_id)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "payload": {"profile_id": remove_profile_id}
                    })
            
            elif message_type == "chat.message":
                # Handle chat messages sent via WebSocket
                content = data.get("content")
                target_profile_id = data.get("profile_id", profile_id)
                
                if content and target_profile_id:
                    # Create and publish chat event
                    message_id = str(uuid4())
                    event = create_chat_message(
                        profile_id=target_profile_id,
                        sender_id=user_id or connection_id,
                        message_id=message_id,
                        content=content,
                        role="user"
                    )
                    await BUS.publish(event)
                    
                    # Send confirmation back to sender
                    await websocket.send_json({
                        "type": "message_sent",
                        "payload": {
                            "message_id": message_id,
                            "profile_id": target_profile_id
                        }
                    })
            
            else:
                logger.warning(f"Unknown message type from {connection_id}: {message_type}")
    
    except WebSocketDisconnect:
        raise
    except Exception as e:
        logger.error(f"Error handling receive for {connection_id}: {e}")
        raise


async def handle_send(websocket: WebSocket, event_queue: asyncio.Queue):
    """Handle sending events from the queue to the WebSocket client."""
    try:
        while True:
            # Wait for event from queue
            event: RealtimeEvent = await event_queue.get()
            
            # Send event to client
            await websocket.send_json(event.to_json())
            
            # Log high-priority events
            if event.type in [EventType.TRADE_ORDER_FILLED, EventType.CHAT_ASSISTANT_START]:
                logger.debug(f"Sent {event.type} event to WebSocket")
    
    except WebSocketDisconnect:
        raise
    except Exception as e:
        logger.error(f"Error handling send: {e}")
        raise


@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status and statistics."""
    subscriber_stats = BUS.get_subscriber_count()
    
    return {
        "active_connections": connection_manager.get_connection_count(),
        "subscribers": subscriber_stats,
        "event_bus": "active",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }