"""AI tools for structured trading actions via OpenRouter."""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from ..pending_actions import (
    PendingAction, ActionType, ActionStatus, 
    TriggerCondition, OperatorType, ActionParams
)


class TradingTools:
    """Collection of trading tools available to AI agents."""
    
    def __init__(self, rise_client, storage):
        self.rise_client = rise_client
        self.storage = storage
        self.logger = logging.getLogger(__name__)
    
    @property
    def tools_schema(self) -> List[Dict[str, Any]]:
        """Get OpenRouter-compatible tool schemas."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "place_market_order",
                    "description": "Place an immediate market order",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "market": {
                                "type": "string",
                                "description": "Market symbol (e.g., 'BTC', 'ETH')",
                                "enum": ["BTC", "ETH"]
                            },
                            "side": {
                                "type": "string",
                                "description": "Order side",
                                "enum": ["buy", "sell"]
                            },
                            "size_percent": {
                                "type": "number",
                                "description": "Size as percentage of available balance (0.01 to 1.0)",
                                "minimum": 0.01,
                                "maximum": 1.0
                            }
                        },
                        "required": ["market", "side", "size_percent"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "place_limit_order",
                    "description": "Place a limit order at specific price",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "market": {
                                "type": "string",
                                "description": "Market symbol",
                                "enum": ["BTC", "ETH"]
                            },
                            "side": {
                                "type": "string",
                                "description": "Order side",
                                "enum": ["buy", "sell"]
                            },
                            "size_percent": {
                                "type": "number",
                                "description": "Size as percentage of available balance",
                                "minimum": 0.01,
                                "maximum": 1.0
                            },
                            "price": {
                                "type": "number",
                                "description": "Limit order price",
                                "minimum": 0
                            }
                        },
                        "required": ["market", "side", "size_percent", "price"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "close_position",
                    "description": "Close an existing position",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "market": {
                                "type": "string",
                                "description": "Market symbol",
                                "enum": ["BTC", "ETH"]
                            },
                            "percent": {
                                "type": "number",
                                "description": "Percentage of position to close (default 100)",
                                "minimum": 0,
                                "maximum": 100,
                                "default": 100
                            }
                        },
                        "required": ["market"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "set_stop_loss",
                    "description": "Set stop loss for a position",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "market": {
                                "type": "string",
                                "description": "Market symbol",
                                "enum": ["BTC", "ETH"]
                            },
                            "trigger_price": {
                                "type": "number",
                                "description": "Price at which to trigger stop loss",
                                "minimum": 0
                            }
                        },
                        "required": ["market", "trigger_price"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "set_take_profit",
                    "description": "Set take profit target for a position",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "market": {
                                "type": "string",
                                "description": "Market symbol",
                                "enum": ["BTC", "ETH"]
                            },
                            "trigger_price": {
                                "type": "number",
                                "description": "Price at which to take profit",
                                "minimum": 0
                            }
                        },
                        "required": ["market", "trigger_price"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "schedule_limit_order",
                    "description": "Schedule a limit order when price condition is met",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "market": {
                                "type": "string",
                                "description": "Market symbol",
                                "enum": ["BTC", "ETH"]
                            },
                            "side": {
                                "type": "string",
                                "description": "Order side",
                                "enum": ["buy", "sell"]
                            },
                            "size_percent": {
                                "type": "number",
                                "description": "Size as percentage of balance",
                                "minimum": 0.01,
                                "maximum": 1.0
                            },
                            "trigger_price": {
                                "type": "number",
                                "description": "Price condition to trigger order",
                                "minimum": 0
                            },
                            "trigger_condition": {
                                "type": "string",
                                "description": "When to trigger relative to price",
                                "enum": ["above", "below"]
                            },
                            "limit_price": {
                                "type": "number",
                                "description": "Limit order price",
                                "minimum": 0
                            },
                            "expires_hours": {
                                "type": "number",
                                "description": "Hours until order expires (default 24)",
                                "default": 24
                            }
                        },
                        "required": ["market", "side", "size_percent", "trigger_price", "trigger_condition", "limit_price"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "cancel_pending_action",
                    "description": "Cancel a pending action by ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action_id": {
                                "type": "string",
                                "description": "ID of the pending action to cancel"
                            }
                        },
                        "required": ["action_id"]
                    }
                }
            }
        ]
    
    async def execute_tool_call(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any], 
        account_id: str,
        persona_name: str,
        account_key: str,
        signer_key: str
    ) -> Dict[str, Any]:
        """Execute a tool call and return result."""
        
        self.logger.info(f"🔧 Executing tool: {tool_name} with args: {arguments}")
        
        try:
            if tool_name == "place_market_order":
                return await self._place_market_order(
                    account_id, persona_name, account_key, signer_key, **arguments
                )
            
            elif tool_name == "place_limit_order":
                return await self._place_limit_order(
                    account_id, persona_name, account_key, signer_key, **arguments
                )
            
            elif tool_name == "close_position":
                return await self._close_position(
                    account_id, persona_name, account_key, signer_key, **arguments
                )
            
            elif tool_name == "set_stop_loss":
                return await self._set_stop_loss(
                    account_id, persona_name, **arguments
                )
            
            elif tool_name == "set_take_profit":
                return await self._set_take_profit(
                    account_id, persona_name, **arguments
                )
            
            elif tool_name == "schedule_limit_order":
                return await self._schedule_limit_order(
                    account_id, persona_name, **arguments
                )
            
            elif tool_name == "cancel_pending_action":
                return await self._cancel_pending_action(
                    account_id, **arguments
                )
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}"
                }
                
        except Exception as e:
            self.logger.error(f"Tool execution error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _place_market_order(
        self, account_id: str, persona_name: str, account_key: str, 
        signer_key: str, market: str, side: str, size_percent: float
    ) -> Dict[str, Any]:
        """Place immediate market order."""
        # Get market ID
        from ..core.market_manager import get_market_manager
        market_mgr = get_market_manager()
        market_data = await market_mgr.get_market_by_symbol(market)
        
        if not market_data:
            return {"success": False, "error": f"Market {market} not found"}
        
        market_id = int(market_data.get("market_id", 0))
        current_price = float(market_data.get("price", 0))
        
        # Get available balance
        from eth_account import Account as EthAccount
        account_address = EthAccount.from_key(account_key).address
        balance_data = await self.rise_client.get_balance(account_address)
        available = float(balance_data.get("cross_margin_balance", 0))
        
        # Calculate size
        size = (available * size_percent) / current_price
        
        # Place order with slippage
        slippage_price = current_price * 1.01 if side == "buy" else current_price * 0.99
        
        result = await self.rise_client.place_order(
            account_key=account_key,
            signer_key=signer_key,
            market_id=market_id,
            size=size,
            price=slippage_price,
            side=side,
            order_type="limit"  # Use limit with slippage for market
        )
        
        return {
            "success": result.get("success", False),
            "order_id": result.get("data", {}).get("order_id"),
            "executed_size": size,
            "executed_price": slippage_price
        }
    
    async def _place_limit_order(
        self, account_id: str, persona_name: str, account_key: str,
        signer_key: str, market: str, side: str, 
        size_percent: float, price: float
    ) -> Dict[str, Any]:
        """Place limit order at specific price."""
        # Similar to market order but with exact price
        from ..core.market_manager import get_market_manager
        market_mgr = get_market_manager()
        market_data = await market_mgr.get_market_by_symbol(market)
        
        if not market_data:
            return {"success": False, "error": f"Market {market} not found"}
        
        market_id = int(market_data.get("market_id", 0))
        
        # Get available balance
        from eth_account import Account as EthAccount
        account_address = EthAccount.from_key(account_key).address
        balance_data = await self.rise_client.get_balance(account_address)
        available = float(balance_data.get("cross_margin_balance", 0))
        
        # Calculate size
        size = (available * size_percent) / price
        
        result = await self.rise_client.place_order(
            account_key=account_key,
            signer_key=signer_key,
            market_id=market_id,
            size=size,
            price=price,
            side=side,
            order_type="limit"
        )
        
        return {
            "success": result.get("success", False),
            "order_id": result.get("data", {}).get("order_id"),
            "limit_price": price,
            "size": size
        }
    
    async def _close_position(
        self, account_id: str, persona_name: str, account_key: str,
        signer_key: str, market: str, percent: float = 100
    ) -> Dict[str, Any]:
        """Close existing position."""
        # Get position
        from ..core.market_manager import get_market_manager
        market_mgr = get_market_manager()
        market_data = await market_mgr.get_market_by_symbol(market)
        
        if not market_data:
            return {"success": False, "error": f"Market {market} not found"}
        
        market_id = int(market_data.get("market_id", 0))
        current_price = float(market_data.get("price", 0))
        
        from eth_account import Account as EthAccount
        account_address = EthAccount.from_key(account_key).address
        position = await self.rise_client.get_position(account_address, market_id)
        
        position_size = float(position.get("size", 0))
        if position_size == 0:
            return {"success": False, "error": f"No position in {market}"}
        
        # Calculate close size
        close_size = abs(position_size * (percent / 100))
        side = "sell" if position_size > 0 else "buy"
        
        # Place close order
        slippage_price = current_price * 0.99 if side == "sell" else current_price * 1.01
        
        result = await self.rise_client.place_order(
            account_key=account_key,
            signer_key=signer_key,
            market_id=market_id,
            size=close_size,
            price=slippage_price,
            side=side,
            order_type="limit",
            reduce_only=True
        )
        
        return {
            "success": result.get("success", False),
            "order_id": result.get("data", {}).get("order_id"),
            "closed_size": close_size,
            "closed_percent": percent
        }
    
    async def _set_stop_loss(
        self, account_id: str, persona_name: str, 
        market: str, trigger_price: float
    ) -> Dict[str, Any]:
        """Create pending stop loss action."""
        import uuid
        
        action = PendingAction(
            id=str(uuid.uuid4()),
            account_id=account_id,
            persona_name=persona_name,
            action_type=ActionType.STOP_LOSS,
            condition=TriggerCondition(
                field="price",
                operator=OperatorType.LESS_EQUAL,
                value=trigger_price,
                market=market
            ),
            action_params=ActionParams(
                market=market,
                reduce_percent=100  # Close full position
            ),
            reasoning=f"Stop loss at ${trigger_price:,.0f} for {market} position"
        )
        
        self.storage.save_pending_action(action)
        
        return {
            "success": True,
            "action_id": action.id,
            "trigger_price": trigger_price,
            "market": market
        }
    
    async def _set_take_profit(
        self, account_id: str, persona_name: str,
        market: str, trigger_price: float
    ) -> Dict[str, Any]:
        """Create pending take profit action."""
        import uuid
        
        action = PendingAction(
            id=str(uuid.uuid4()),
            account_id=account_id,
            persona_name=persona_name,
            action_type=ActionType.TAKE_PROFIT,
            condition=TriggerCondition(
                field="price",
                operator=OperatorType.GREATER_EQUAL,
                value=trigger_price,
                market=market
            ),
            action_params=ActionParams(
                market=market,
                reduce_percent=100  # Close full position
            ),
            reasoning=f"Take profit at ${trigger_price:,.0f} for {market} position"
        )
        
        self.storage.save_pending_action(action)
        
        return {
            "success": True,
            "action_id": action.id,
            "trigger_price": trigger_price,
            "market": market
        }
    
    async def _schedule_limit_order(
        self, account_id: str, persona_name: str, market: str,
        side: str, size_percent: float, trigger_price: float,
        trigger_condition: str, limit_price: float, expires_hours: float = 24
    ) -> Dict[str, Any]:
        """Schedule conditional limit order."""
        import uuid
        
        operator = (
            OperatorType.GREATER_EQUAL if trigger_condition == "above" 
            else OperatorType.LESS_EQUAL
        )
        
        action = PendingAction(
            id=str(uuid.uuid4()),
            account_id=account_id,
            persona_name=persona_name,
            action_type=ActionType.LIMIT_ORDER,
            condition=TriggerCondition(
                field="price",
                operator=operator,
                value=trigger_price,
                market=market
            ),
            action_params=ActionParams(
                market=market,
                side=side,
                size_percent=size_percent,
                price=limit_price
            ),
            expires_at=datetime.now() + timedelta(hours=expires_hours),
            reasoning=f"Scheduled {side} order for {market} when price {trigger_condition} ${trigger_price:,.0f}"
        )
        
        self.storage.save_pending_action(action)
        
        return {
            "success": True,
            "action_id": action.id,
            "scheduled_order": {
                "market": market,
                "side": side,
                "trigger": f"{trigger_condition} ${trigger_price:,.0f}",
                "limit_price": limit_price,
                "expires": action.expires_at.isoformat()
            }
        }
    
    async def _cancel_pending_action(
        self, account_id: str, action_id: str
    ) -> Dict[str, Any]:
        """Cancel a pending action."""
        action = self.storage.get_pending_action(action_id)
        
        if not action:
            return {"success": False, "error": "Action not found"}
        
        if action.account_id != account_id:
            return {"success": False, "error": "Action belongs to different account"}
        
        if action.status != ActionStatus.PENDING:
            return {"success": False, "error": f"Action is {action.status.value}, not pending"}
        
        action.status = ActionStatus.CANCELLED
        self.storage.save_pending_action(action)
        
        return {
            "success": True,
            "cancelled_action": {
                "id": action.id,
                "type": action.action_type.value,
                "market": action.action_params.market
            }
        }