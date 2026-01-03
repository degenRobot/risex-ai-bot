"""Event bus for distributing realtime events to WebSocket subscribers."""

import asyncio
import logging
from collections import defaultdict
from typing import Optional
from uuid import UUID

from .events import RealtimeEvent

logger = logging.getLogger(__name__)


class EventSubscriber:
    """Represents a subscriber to the event bus."""
    
    def __init__(
        self, 
        subscriber_id: str,
        queue: asyncio.Queue,
        user_id: Optional[str] = None,
        profile_subscriptions: Optional[set[str]] = None,
    ):
        self.subscriber_id = subscriber_id
        self.queue = queue
        self.user_id = user_id
        self.profile_subscriptions = profile_subscriptions or set()
        self.is_global = False
        self.last_event_id: Optional[UUID] = None
    
    def should_receive_event(self, event: RealtimeEvent) -> bool:
        """Check if this subscriber should receive the event."""
        # Don't send events back to the sender
        if event.metadata.sender_id and event.metadata.sender_id == self.user_id:
            return False
        
        # Global subscribers get all events
        if self.is_global:
            return True
        
        # Profile subscribers get events for their subscribed profiles
        if event.profile_id and event.profile_id in self.profile_subscriptions:
            return True
        
        # Events without profile_id go to global subscribers only
        return False


class EventBus:
    """Central event bus for distributing realtime events."""
    
    def __init__(self, max_queue_size: int = 100):
        self.max_queue_size = max_queue_size
        self._subscribers: dict[str, EventSubscriber] = {}
        self._profile_subscribers: dict[str, set[str]] = defaultdict(set)
        self._global_subscribers: set[str] = set()
        self._lock = asyncio.Lock()
        self._event_history: dict[UUID, RealtimeEvent] = {}
        self._max_history_size = 1000
        
        logger.info("EventBus initialized")
    
    async def subscribe_global(
        self, 
        subscriber_id: str, 
        user_id: Optional[str] = None,
    ) -> asyncio.Queue:
        """Subscribe to all events."""
        async with self._lock:
            if subscriber_id in self._subscribers:
                logger.warning(f"Subscriber {subscriber_id} already exists")
                return self._subscribers[subscriber_id].queue
            
            queue = asyncio.Queue(maxsize=self.max_queue_size)
            subscriber = EventSubscriber(subscriber_id, queue, user_id)
            subscriber.is_global = True
            
            self._subscribers[subscriber_id] = subscriber
            self._global_subscribers.add(subscriber_id)
            
            logger.info(f"Global subscriber {subscriber_id} added (user_id: {user_id})")
            return queue
    
    async def subscribe_profile(
        self, 
        subscriber_id: str,
        profile_id: str,
        user_id: Optional[str] = None,
    ) -> asyncio.Queue:
        """Subscribe to events for a specific profile."""
        async with self._lock:
            if subscriber_id in self._subscribers:
                # Add profile to existing subscriber
                subscriber = self._subscribers[subscriber_id]
                subscriber.profile_subscriptions.add(profile_id)
                self._profile_subscribers[profile_id].add(subscriber_id)
                logger.info(f"Added profile {profile_id} to subscriber {subscriber_id}")
                return subscriber.queue
            
            # Create new subscriber
            queue = asyncio.Queue(maxsize=self.max_queue_size)
            subscriber = EventSubscriber(
                subscriber_id, 
                queue, 
                user_id,
                profile_subscriptions={profile_id},
            )
            
            self._subscribers[subscriber_id] = subscriber
            self._profile_subscribers[profile_id].add(subscriber_id)
            
            logger.info(f"Profile subscriber {subscriber_id} added for profile {profile_id}")
            return queue
    
    async def unsubscribe(
        self, 
        subscriber_id: str, 
        profile_id: Optional[str] = None,
    ) -> bool:
        """Unsubscribe from events."""
        async with self._lock:
            if subscriber_id not in self._subscribers:
                return False
            
            subscriber = self._subscribers[subscriber_id]
            
            if profile_id:
                # Remove specific profile subscription
                subscriber.profile_subscriptions.discard(profile_id)
                self._profile_subscribers[profile_id].discard(subscriber_id)
                
                # If no more subscriptions, remove subscriber entirely
                if not subscriber.profile_subscriptions and not subscriber.is_global:
                    del self._subscribers[subscriber_id]
                    logger.info(f"Removed subscriber {subscriber_id} (no remaining subscriptions)")
                else:
                    logger.info(f"Removed profile {profile_id} from subscriber {subscriber_id}")
            else:
                # Remove subscriber entirely
                for prof_id in subscriber.profile_subscriptions:
                    self._profile_subscribers[prof_id].discard(subscriber_id)
                
                self._global_subscribers.discard(subscriber_id)
                del self._subscribers[subscriber_id]
                logger.info(f"Removed subscriber {subscriber_id} entirely")
            
            return True
    
    async def publish(self, event: RealtimeEvent) -> int:
        """
        Publish an event to all relevant subscribers.
        Returns the number of subscribers that received the event.
        """
        # Store event in history
        async with self._lock:
            self._event_history[event.id] = event
            
            # Trim history if too large
            if len(self._event_history) > self._max_history_size:
                oldest_ids = sorted(self._event_history.keys())[:100]
                for event_id in oldest_ids:
                    del self._event_history[event_id]
        
        # Distribute to subscribers
        recipients = 0
        failed_subscribers = []
        
        async with self._lock:
            for subscriber_id, subscriber in self._subscribers.items():
                if subscriber.should_receive_event(event):
                    try:
                        # Try to put event in queue without blocking
                        subscriber.queue.put_nowait(event)
                        subscriber.last_event_id = event.id
                        recipients += 1
                    except asyncio.QueueFull:
                        # Queue is full, drop oldest event
                        try:
                            subscriber.queue.get_nowait()
                            subscriber.queue.put_nowait(event)
                            subscriber.last_event_id = event.id
                            recipients += 1
                            logger.warning(f"Dropped oldest event for subscriber {subscriber_id}")
                        except:
                            failed_subscribers.append(subscriber_id)
                            logger.error(f"Failed to send event to subscriber {subscriber_id}")
                    except Exception as e:
                        failed_subscribers.append(subscriber_id)
                        logger.error(f"Error sending event to {subscriber_id}: {e}")
        
        # Clean up failed subscribers
        if failed_subscribers:
            for sub_id in failed_subscribers:
                await self.unsubscribe(sub_id)
        
        logger.debug(f"Published {event.type} to {recipients} subscribers")
        return recipients
    
    async def get_missed_events(
        self, 
        subscriber_id: str, 
        after_event_id: Optional[UUID] = None,
    ) -> list[RealtimeEvent]:
        """Get events that a subscriber may have missed."""
        async with self._lock:
            if subscriber_id not in self._subscribers:
                return []
            
            subscriber = self._subscribers[subscriber_id]
            missed_events = []
            
            # Sort events by timestamp
            sorted_events = sorted(
                self._event_history.values(),
                key=lambda e: e.timestamp,
            )
            
            # Find events after the specified ID
            found_start = after_event_id is None
            for event in sorted_events:
                if not found_start:
                    if event.id == after_event_id:
                        found_start = True
                    continue
                
                if subscriber.should_receive_event(event):
                    missed_events.append(event)
            
            return missed_events
    
    def get_subscriber_count(self) -> dict[str, int]:
        """Get count of subscribers by type."""
        return {
            "total": len(self._subscribers),
            "global": len(self._global_subscribers),
            "profiles": len(self._profile_subscribers),
            "queued_events": sum(
                sub.queue.qsize() for sub in self._subscribers.values()
            ),
        }
    
    async def clear_subscriber(self, subscriber_id: str):
        """Clear all queued events for a subscriber."""
        async with self._lock:
            if subscriber_id in self._subscribers:
                subscriber = self._subscribers[subscriber_id]
                # Create new queue to clear old one
                subscriber.queue = asyncio.Queue(maxsize=self.max_queue_size)
                logger.info(f"Cleared queue for subscriber {subscriber_id}")


# Create singleton instance
BUS = EventBus()


# Convenience functions for common operations
async def publish_event(event: RealtimeEvent) -> int:
    """Publish an event to the global event bus."""
    return await BUS.publish(event)


async def subscribe_to_profile(
    subscriber_id: str, 
    profile_id: str,
    user_id: Optional[str] = None,
) -> asyncio.Queue:
    """Subscribe to events for a specific profile."""
    return await BUS.subscribe_profile(subscriber_id, profile_id, user_id)


async def subscribe_globally(
    subscriber_id: str,
    user_id: Optional[str] = None,
) -> asyncio.Queue:
    """Subscribe to all events."""
    return await BUS.subscribe_global(subscriber_id, user_id)