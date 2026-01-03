"""Trading action queue system for managing and prioritizing trades."""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of trading actions."""
    MARKET_ORDER = "market_order"
    LIMIT_ORDER = "limit_order"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    CLOSE_POSITION = "close_position"
    REBALANCE = "rebalance"
    
    
class ActionPriority(Enum):
    """Priority levels for actions."""
    CRITICAL = 1  # Stop losses, risk management
    HIGH = 2      # Take profits, time-sensitive
    NORMAL = 3    # Regular trading
    LOW = 4       # Rebalancing, non-urgent


@dataclass
class PendingAction:
    """Represents a pending trading action."""
    id: str
    profile_id: str
    action_type: ActionType
    priority: ActionPriority
    symbol: str
    side: str  # "buy" or "sell"
    size: Optional[float] = None
    price: Optional[float] = None
    reasoning: str = ""
    not_before: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    attempts: int = 0
    last_error: Optional[str] = None
    
    def is_ready(self) -> bool:
        """Check if action is ready to execute."""
        now = datetime.now()
        
        # Check if we've waited long enough
        if self.not_before and now < self.not_before:
            return False
            
        # Check if action has expired
        if self.expires_at and now > self.expires_at:
            return False
            
        return True
        
    def is_expired(self) -> bool:
        """Check if action has expired."""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False
        
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "action_type": self.action_type.value,
            "priority": self.priority.value,
            "symbol": self.symbol,
            "side": self.side,
            "size": self.size,
            "price": self.price,
            "reasoning": self.reasoning,
            "not_before": self.not_before.isoformat() if self.not_before else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
            "attempts": self.attempts,
            "last_error": self.last_error,
        }
        
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PendingAction":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            profile_id=data["profile_id"],
            action_type=ActionType(data["action_type"]),
            priority=ActionPriority(data["priority"]),
            symbol=data["symbol"],
            side=data["side"],
            size=data.get("size"),
            price=data.get("price"),
            reasoning=data.get("reasoning", ""),
            not_before=datetime.fromisoformat(data["not_before"]) if data.get("not_before") else None,
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            metadata=data.get("metadata", {}),
            attempts=data.get("attempts", 0),
            last_error=data.get("last_error"),
        )


class TradingActionQueue:
    """Manages pending trading actions with prioritization and throttling."""
    
    def __init__(self, storage_path: str = "data/pending_actions.json"):
        self.storage_path = storage_path
        self._actions: dict[str, PendingAction] = {}
        self._lock = asyncio.Lock()
        self._load_actions()
        
        # Throttling settings
        self.min_interval_seconds = 5  # Minimum seconds between actions
        self.max_actions_per_minute = 10
        self.last_execution_times: dict[str, datetime] = {}
        self.execution_history: list[datetime] = []
        
    def _load_actions(self):
        """Load pending actions from storage."""
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
                for action_data in data.get("actions", []):
                    action = PendingAction.from_dict(action_data)
                    self._actions[action.id] = action
            logger.info(f"Loaded {len(self._actions)} pending actions")
        except FileNotFoundError:
            logger.info("No pending actions file found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading pending actions: {e}")
            
    def _save_actions(self):
        """Save pending actions to storage."""
        try:
            data = {
                "actions": [action.to_dict() for action in self._actions.values()],
                "last_updated": datetime.now().isoformat(),
            }
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving pending actions: {e}")
            
    async def add_action(self, action: PendingAction) -> bool:
        """Add a new action to the queue."""
        async with self._lock:
            # Check for duplicate actions
            for existing in self._actions.values():
                if (existing.profile_id == action.profile_id and 
                    existing.symbol == action.symbol and
                    existing.side == action.side and
                    existing.action_type == action.action_type and
                    not existing.is_expired()):
                    logger.warning(f"Duplicate action rejected: {action.symbol} {action.side}")
                    return False
                    
            self._actions[action.id] = action
            self._save_actions()
            logger.info(f"Added action: {action.id} - {action.symbol} {action.side} for {action.profile_id}")
            return True
            
    async def get_ready_actions(self, profile_id: Optional[str] = None) -> list[PendingAction]:
        """Get actions ready for execution, optionally filtered by profile."""
        async with self._lock:
            ready_actions = []
            expired_ids = []
            
            for action_id, action in self._actions.items():
                # Filter by profile if specified
                if profile_id and action.profile_id != profile_id:
                    continue
                    
                # Remove expired actions
                if action.is_expired():
                    expired_ids.append(action_id)
                    continue
                    
                # Check if ready
                if action.is_ready():
                    ready_actions.append(action)
                    
            # Clean up expired actions
            for action_id in expired_ids:
                del self._actions[action_id]
                
            if expired_ids:
                self._save_actions()
                
            # Sort by priority (lower number = higher priority)
            ready_actions.sort(key=lambda x: (x.priority.value, x.created_at))
            
            return ready_actions
            
    async def can_execute_action(self, profile_id: str, symbol: str) -> bool:
        """Check if we can execute an action based on throttling rules."""
        now = datetime.now()
        
        # Check profile-specific throttling
        profile_key = f"{profile_id}:{symbol}"
        if profile_key in self.last_execution_times:
            time_since_last = (now - self.last_execution_times[profile_key]).total_seconds()
            if time_since_last < self.min_interval_seconds:
                return False
                
        # Check global rate limit
        self.execution_history = [t for t in self.execution_history 
                                 if (now - t).total_seconds() < 60]
        if len(self.execution_history) >= self.max_actions_per_minute:
            return False
            
        return True
        
    async def mark_executed(self, action_id: str, success: bool = True, error: Optional[str] = None):
        """Mark an action as executed."""
        async with self._lock:
            if action_id in self._actions:
                action = self._actions[action_id]
                
                if success:
                    # Remove successful action
                    del self._actions[action_id]
                    
                    # Update execution tracking
                    now = datetime.now()
                    profile_key = f"{action.profile_id}:{action.symbol}"
                    self.last_execution_times[profile_key] = now
                    self.execution_history.append(now)
                    
                    logger.info(f"Action executed successfully: {action_id}")
                else:
                    # Update failed action
                    action.attempts += 1
                    action.last_error = error
                    
                    # Remove if too many attempts
                    if action.attempts >= 3:
                        del self._actions[action_id]
                        logger.warning(f"Action removed after 3 failed attempts: {action_id}")
                    else:
                        # Delay retry
                        action.not_before = datetime.now() + timedelta(seconds=30 * action.attempts)
                        
                self._save_actions()
                
    async def get_next_action(self, profile_id: str) -> Optional[PendingAction]:
        """Get the next action to execute for a profile."""
        ready_actions = await self.get_ready_actions(profile_id)
        
        for action in ready_actions:
            if await self.can_execute_action(profile_id, action.symbol):
                return action
                
        return None
        
    async def clear_profile_actions(self, profile_id: str):
        """Clear all actions for a specific profile."""
        async with self._lock:
            to_remove = [aid for aid, action in self._actions.items() 
                        if action.profile_id == profile_id]
            for action_id in to_remove:
                del self._actions[action_id]
                
            if to_remove:
                self._save_actions()
                logger.info(f"Cleared {len(to_remove)} actions for profile {profile_id}")
                
    def get_queue_stats(self) -> dict[str, Any]:
        """Get statistics about the queue."""
        stats = {
            "total_actions": len(self._actions),
            "by_priority": {},
            "by_type": {},
            "by_profile": {},
            "ready_count": 0,
        }
        
        for action in self._actions.values():
            # Count by priority
            priority = action.priority.name
            stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1
            
            # Count by type
            action_type = action.action_type.name
            stats["by_type"][action_type] = stats["by_type"].get(action_type, 0) + 1
            
            # Count by profile
            stats["by_profile"][action.profile_id] = stats["by_profile"].get(action.profile_id, 0) + 1
            
            # Count ready
            if action.is_ready():
                stats["ready_count"] += 1
                
        return stats
        

# Global instance
_action_queue = None


def get_action_queue() -> TradingActionQueue:
    """Get the singleton action queue instance."""
    global _action_queue
    if _action_queue is None:
        _action_queue = TradingActionQueue()
    return _action_queue