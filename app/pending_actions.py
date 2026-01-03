"""Models for pending and conditional actions."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Types of pending actions."""
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    LIMIT_ORDER = "limit_order"
    MARKET_ORDER = "market_order"
    CLOSE_POSITION = "close_position"
    CUSTOM = "custom"


class ActionStatus(str, Enum):
    """Status of a pending action."""
    PENDING = "pending"
    TRIGGERED = "triggered"
    EXECUTED = "executed"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class OperatorType(str, Enum):
    """Comparison operators for conditions."""
    GREATER_THAN = ">"
    GREATER_EQUAL = ">="
    LESS_THAN = "<"
    LESS_EQUAL = "<="
    EQUAL = "=="
    NOT_EQUAL = "!="
    BETWEEN = "between"


class TriggerCondition(BaseModel):
    """Condition that triggers an action."""
    field: str  # "price", "pnl", "time", "volume"
    operator: OperatorType
    value: float
    value2: Optional[float] = None  # For BETWEEN operator
    market: Optional[str] = None  # For price conditions (e.g., "BTC", "ETH")
    
    def evaluate(self, context: dict[str, Any]) -> bool:
        """Evaluate if condition is met given context."""
        # Get the value to check
        if self.field == "price" and self.market:
            actual_value = context.get(f"{self.market.lower()}_price", 0)
        elif self.field == "pnl":
            actual_value = context.get("total_pnl", 0)
        elif self.field == "time":
            actual_value = datetime.now().timestamp()
        else:
            actual_value = context.get(self.field, 0)
        
        # Evaluate based on operator
        if self.operator == OperatorType.GREATER_THAN:
            return actual_value > self.value
        elif self.operator == OperatorType.GREATER_EQUAL:
            return actual_value >= self.value
        elif self.operator == OperatorType.LESS_THAN:
            return actual_value < self.value
        elif self.operator == OperatorType.LESS_EQUAL:
            return actual_value <= self.value
        elif self.operator == OperatorType.EQUAL:
            return actual_value == self.value
        elif self.operator == OperatorType.NOT_EQUAL:
            return actual_value != self.value
        elif self.operator == OperatorType.BETWEEN and self.value2 is not None:
            return self.value <= actual_value <= self.value2
        
        return False


class ActionParams(BaseModel):
    """Parameters for action execution."""
    market: Optional[str] = None
    side: Optional[str] = None  # "buy" or "sell"
    size_percent: Optional[float] = None  # Percentage of balance
    size: Optional[float] = None  # Absolute size
    price: Optional[float] = None  # For limit orders
    reduce_percent: Optional[float] = None  # For partial close
    custom_data: Optional[dict[str, Any]] = None


class PendingAction(BaseModel):
    """A conditional action to execute when criteria are met."""
    id: str
    account_id: str
    persona_name: str
    action_type: ActionType
    condition: TriggerCondition
    action_params: ActionParams
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    status: ActionStatus = ActionStatus.PENDING
    triggered_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[dict[str, Any]] = None
    reasoning: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Check if action has expired."""
        if self.expires_at and datetime.now() > self.expires_at:
            return True
        return False
    
    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Check if action should be triggered given current context."""
        if self.status != ActionStatus.PENDING:
            return False
        
        if self.is_expired():
            return False
        
        return self.condition.evaluate(context)
    
    def mark_triggered(self):
        """Mark action as triggered."""
        self.status = ActionStatus.TRIGGERED
        self.triggered_at = datetime.now()
    
    def mark_executed(self, result: dict[str, Any]):
        """Mark action as successfully executed."""
        self.status = ActionStatus.EXECUTED
        self.executed_at = datetime.now()
        self.result = result
    
    def mark_failed(self, error: str):
        """Mark action as failed."""
        self.status = ActionStatus.FAILED
        self.error_message = error


class PendingActionSummary(BaseModel):
    """Summary of pending actions for a profile."""
    account_id: str
    persona_name: str
    total_actions: int
    pending: int
    stop_losses: list[dict[str, Any]]
    take_profits: list[dict[str, Any]]
    limit_orders: list[dict[str, Any]]
    other_actions: list[dict[str, Any]]
    
    @classmethod
    def from_actions(cls, account_id: str, persona_name: str, actions: list[PendingAction]):
        """Create summary from list of actions."""
        pending_actions = [a for a in actions if a.status == ActionStatus.PENDING]
        
        stop_losses = []
        take_profits = []
        limit_orders = []
        others = []
        
        for action in pending_actions:
            summary = {
                "id": action.id,
                "condition": f"{action.condition.field} {action.condition.operator.value} {action.condition.value}",
                "market": action.action_params.market,
                "created": action.created_at.isoformat(),
            }
            
            if action.action_type == ActionType.STOP_LOSS:
                stop_losses.append(summary)
            elif action.action_type == ActionType.TAKE_PROFIT:
                take_profits.append(summary)
            elif action.action_type == ActionType.LIMIT_ORDER:
                limit_orders.append(summary)
            else:
                others.append(summary)
        
        return cls(
            account_id=account_id,
            persona_name=persona_name,
            total_actions=len(actions),
            pending=len(pending_actions),
            stop_losses=stop_losses,
            take_profits=take_profits,
            limit_orders=limit_orders,
            other_actions=others,
        )