"""Tests for the event bus system."""

import asyncio

import pytest

from app.realtime.bus import EventBus
from app.realtime.events import (
    EventMetadata,
    EventType,
    RealtimeEvent,
    create_chat_message,
    create_market_update,
)


@pytest.fixture
def event_bus():
    """Create a fresh event bus for testing."""
    return EventBus(max_queue_size=10)


@pytest.mark.asyncio
async def test_global_subscription(event_bus):
    """Test global subscription and event delivery."""
    # Subscribe globally
    subscriber_id = "test-global-sub"
    queue = await event_bus.subscribe_global(subscriber_id, user_id="test-user")
    
    # Publish event
    event = create_market_update("BTC", 95000, 0.05, 1000000)
    recipients = await event_bus.publish(event)
    
    # Check event received
    assert recipients == 1
    received_event = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert received_event.id == event.id
    assert received_event.payload["symbol"] == "BTC"


@pytest.mark.asyncio
async def test_profile_subscription(event_bus):
    """Test profile-specific subscription."""
    # Subscribe to specific profile
    subscriber_id = "test-profile-sub"
    profile_id = "profile-123"
    queue = await event_bus.subscribe_profile(subscriber_id, profile_id, user_id="test-user")
    
    # Publish event for subscribed profile
    event1 = create_chat_message(profile_id, "user1", "msg1", "Hello", "user")
    recipients1 = await event_bus.publish(event1)
    assert recipients1 == 1
    
    # Publish event for different profile
    event2 = create_chat_message("other-profile", "user2", "msg2", "Hi", "user")
    recipients2 = await event_bus.publish(event2)
    assert recipients2 == 0
    
    # Check only first event received
    received_event = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert received_event.id == event1.id
    
    # Queue should be empty
    assert queue.empty()


@pytest.mark.asyncio
async def test_message_deduplication(event_bus):
    """Test that messages aren't sent back to sender."""
    # Subscribe with user_id
    subscriber_id = "test-dedup"
    user_id = "sender-123"
    queue = await event_bus.subscribe_global(subscriber_id, user_id=user_id)
    
    # Publish event from same user
    event = RealtimeEvent(
        type=EventType.CHAT_USER_MESSAGE,
        payload={"content": "Test message"},
        metadata=EventMetadata(sender_id=user_id),
    )
    recipients = await event_bus.publish(event)
    
    # Should not receive own message
    assert recipients == 0
    assert queue.empty()
    
    # Publish event from different user
    event2 = RealtimeEvent(
        type=EventType.CHAT_USER_MESSAGE,
        payload={"content": "Other message"},
        metadata=EventMetadata(sender_id="other-user"),
    )
    recipients2 = await event_bus.publish(event2)
    
    # Should receive this one
    assert recipients2 == 1
    received = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert received.id == event2.id


@pytest.mark.asyncio
async def test_multiple_subscribers(event_bus):
    """Test multiple subscribers receive events."""
    # Create multiple subscribers
    queues = []
    for i in range(3):
        sub_id = f"sub-{i}"
        queue = await event_bus.subscribe_global(sub_id)
        queues.append(queue)
    
    # Publish event
    event = create_market_update("ETH", 3100, -0.02, 500000)
    recipients = await event_bus.publish(event)
    
    assert recipients == 3
    
    # All should receive the event
    for queue in queues:
        received = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert received.id == event.id


@pytest.mark.asyncio
async def test_queue_overflow_handling(event_bus):
    """Test behavior when queue is full."""
    # Subscribe
    subscriber_id = "test-overflow"
    queue = await event_bus.subscribe_global(subscriber_id)
    
    # Fill queue beyond capacity
    events = []
    for i in range(15):  # More than max_queue_size=10
        event = create_market_update("BTC", 95000 + i, 0.01, 1000000)
        events.append(event)
        await event_bus.publish(event)
    
    # Should have dropped oldest events
    received_events = []
    while not queue.empty():
        received_events.append(await queue.get())
    
    # Should have last 10 events
    assert len(received_events) == 10
    assert received_events[-1].id == events[-1].id


@pytest.mark.asyncio
async def test_unsubscribe(event_bus):
    """Test unsubscription."""
    # Subscribe
    subscriber_id = "test-unsub"
    profile_id = "profile-456"
    await event_bus.subscribe_profile(subscriber_id, profile_id)
    
    # Unsubscribe
    success = await event_bus.unsubscribe(subscriber_id)
    assert success
    
    # Publish event
    event = create_chat_message(profile_id, "user", "msg", "Test", "user")
    recipients = await event_bus.publish(event)
    
    # Should have no recipients
    assert recipients == 0


@pytest.mark.asyncio
async def test_missed_events_replay(event_bus):
    """Test retrieving missed events."""
    # Subscribe and receive some events
    subscriber_id = "test-replay"
    queue = await event_bus.subscribe_global(subscriber_id)
    
    # Publish events
    events = []
    for i in range(5):
        event = create_market_update("BTC", 95000 + i, 0.01, 1000000)
        events.append(event)
        await event_bus.publish(event)
    
    # Consume first 2 events
    await queue.get()
    second_event = await queue.get()
    
    # Get missed events after second event
    missed = await event_bus.get_missed_events(subscriber_id, second_event.id)
    
    # Should get events 3, 4, 5
    assert len(missed) == 3
    assert missed[0].id == events[2].id
    assert missed[-1].id == events[-1].id


@pytest.mark.asyncio
async def test_subscriber_stats(event_bus):
    """Test subscriber statistics."""
    # Add various subscribers
    await event_bus.subscribe_global("global-1")
    await event_bus.subscribe_global("global-2")
    await event_bus.subscribe_profile("profile-1", "profile-123")
    await event_bus.subscribe_profile("profile-2", "profile-456")
    
    stats = event_bus.get_subscriber_count()
    
    assert stats["total"] == 4
    assert stats["global"] == 2
    assert stats["profiles"] == 2
    assert stats["queued_events"] == 0