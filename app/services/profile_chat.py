"""Profile chat service - allows users to chat with AI trading personalities."""

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .ai_client import AIClient
from .equity_monitor import get_equity_monitor
from .storage import JSONStorage
from .rise_client import RiseClient
from .speech_styles import speechDict
from .thought_process import ThoughtProcessManager
from ..models import Account, Persona
from ..trader_profiles import TraderProfile, create_trader_profile, CurrentThinking
from ..ai.prompt_loader import get_prompt_loader
from ..ai.prompt_loader_improved import get_improved_prompt_loader
from ..chat.store import ChatStore


class ProfileChatService:
    """Service for chatting with AI trading personalities with immutable personas and mutable thinking."""
    
    def __init__(self):
        self.ai_client = AIClient()
        self.storage = JSONStorage()
        self.rise_client = RiseClient()
        self.trader_profiles: Dict[str, TraderProfile] = {}
        
        # New improved system components
        self.improved_loader = get_improved_prompt_loader()
        self.chat_store = ChatStore()
        self.thought_process = ThoughtProcessManager()
        self.use_improved_prompts = True  # Feature flag
        
        # Available tools for AI to use
        self.available_tools = [
            {
                "type": "function",
                "function": {
                    "name": "update_market_outlook",
                    "description": "Update my market outlook and trading bias for specific assets",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "asset": {
                                "type": "string",
                                "description": "Asset symbol (BTC, ETH, etc)"
                            },
                            "outlook": {
                                "type": "string",
                                "enum": ["Bullish", "Bearish", "Neutral"],
                                "description": "Market outlook"
                            },
                            "reasoning": {
                                "type": "string", 
                                "description": "Reasoning for this outlook"
                            },
                            "timeframe": {
                                "type": "string",
                                "enum": ["Short-term", "Medium-term", "Long-term"],
                                "description": "Timeframe for outlook"
                            },
                            "confidence": {
                                "type": "number",
                                "description": "Confidence level 0-1"
                            }
                        },
                        "required": ["asset", "outlook", "reasoning"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_trading_bias",
                    "description": "Update my overall trading bias and risk approach",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "bias": {
                                "type": "string",
                                "description": "New trading bias"
                            },
                            "strategy": {
                                "type": "string",
                                "description": "Trading strategy to follow"
                            },
                            "risk_level": {
                                "type": "string",
                                "enum": ["Conservative", "Moderate", "Aggressive", "Degen"],
                                "description": "Risk approach"
                            }
                        },
                        "required": ["bias"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "add_influence",
                    "description": "Record an influence that affected my thinking",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "source": {
                                "type": "string",
                                "description": "Source of influence (user, market, news)"
                            },
                            "message": {
                                "type": "string",
                                "description": "What influenced me"
                            },
                            "impact": {
                                "type": "string",
                                "description": "How it impacted my thinking"
                            }
                        },
                        "required": ["source", "message", "impact"]
                    }
                }
            }
        ]
    
    def _get_or_create_profile(self, account_id: str, account: Account) -> TraderProfile:
        """Get existing trader profile or create from account persona."""
        if account_id in self.trader_profiles:
            return self.trader_profiles[account_id]
        
        # Map account personas to our profile types
        profile_mapping = {
            "crypto_degen": "leftCurve",
            "btc_hodler": "cynical", 
            "trend_master": "midCurve",
            "market_contrarian": "rightCurve",
            "yolo_king": "leftCurve",
            # Direct curve mappings
            "leftCurve": "leftCurve",
            "midCurve": "midCurve",
            "rightCurve": "rightCurve"
        }
        
        # Default to midCurve if not mapped
        profile_type = profile_mapping.get(account.persona.handle, "midCurve")
        
        profile = create_trader_profile(profile_type, account_id)
        self.trader_profiles[account_id] = profile
        return profile
    
    def _get_speech_style(self, profile: TraderProfile) -> str:
        """Get the speech style instructions for the profile."""
        style_name = profile.base_persona.speech_style
        return speechDict.get(style_name, speechDict["smol"])
    
    def _map_risk_to_trading_style(self, risk_profile: str) -> str:
        """Map risk profile to trading style."""
        mapping = {
            "Conservative": "conservative",
            "Moderate": "momentum", 
            "Aggressive": "aggressive",
            "Very Aggressive": "degen"
        }
        return mapping.get(risk_profile, "momentum")
    
    def _map_risk_profile_to_tolerance(self, risk_profile: str) -> float:
        """Map risk profile string to numeric tolerance."""
        mapping = {
            "Conservative": 0.2,
            "Moderate": 0.5,
            "Aggressive": 0.7,
            "Very Aggressive": 0.9
        }
        return mapping.get(risk_profile, 0.5)
    
    def _map_to_personality_type(self, speech_style: str) -> str:
        """Map speech style to personality type."""
        mapping = {
            "uwu": "leftCurve",
            "smol": "leftCurve",
            "tiktok": "midwit",
            "zoomer": "midwit",
            "pepe": "cynical",
            "mumu": "cynical",
            "boomer": "cynical",
            "quant": "midwit",
            "degen": "leftCurve",
            "based": "cynical",
            "schizo": "leftCurve",
            "wagie": "cynical",
            "npc": "midwit",
            "doomer": "cynical",
            "chad": "leftCurve",
            "virgin": "cynical",
            "coomer": "leftCurve",
            "grug": "leftCurve",
            "midwit": "midwit",
            "topwit": "cynical",
            "bottomwit": "leftCurve",
            "cope": "cynical",
            "seethe": "cynical",
            "dilate": "leftCurve",
            "mald": "cynical",
            "reddit": "midwit",
            "twitter": "midwit"
        }
        return mapping.get(speech_style, "midwit")
    
    def _format_chat_history(self, messages: List) -> str:
        """Format recent chat messages for context."""
        if not messages:
            return "No recent chat history"
        
        formatted = []
        for msg in messages[-10:]:  # Last 10 messages
            role = "User" if msg.role == "user" else "Assistant"
            formatted.append(f"{role}: {msg.content[:100]}...")
        
        return "\n".join(formatted)
    
    def _load_markets_data(self) -> Dict:
        """Load markets data from file."""
        try:
            markets_path = Path("data/markets.json")
            if markets_path.exists():
                with open(markets_path) as f:
                    data = json.load(f)
                    return data.get('markets', {})
        except Exception as e:
            print(f"Error loading markets: {e}")
        return {}
    
    async def _build_system_prompt(self, profile: TraderProfile, context: Dict, account_id: str) -> str:
        """Build system prompt with immutable persona and mutable current thinking."""
        base = profile.base_persona
        current = profile.current_thinking
        
        # Use improved system if feature flag is on
        if self.use_improved_prompts:
            # Get thought summary and influences
            thought_summary = await self.thought_process.summarize_thoughts(
                account_id, for_purpose="chat_response"
            )
            influences = await self.thought_process.get_trading_influences(account_id)
            
            # Get recent chat history
            recent_messages = await self.chat_store.load_recent(account_id, limit=10)
            chat_history_summary = self._format_chat_history(recent_messages)
            
            # Build account dict for improved loader
            account_dict = {
                'name': base.name,
                'personality_type': self._map_to_personality_type(base.speech_style),
                'personality_traits': base.base_traits,
                'trading_style': self._map_risk_to_trading_style(base.risk_profile.value),
                'risk_tolerance': self._map_risk_profile_to_tolerance(base.risk_profile.value),
                'favorite_assets': ['BTC', 'ETH', 'SOL']
            }
            
            # Enhanced context with market data
            trading_context = {
                **context,
                'positions': context.get('positions', []),
                'markets': self._load_markets_data()
            }
            
            return self.improved_loader.build_system_prompt(
                account_dict,
                trading_context,
                thought_summary,
                influences
            )
        
        # Fall back to old system
        # Get prompt loader
        prompt_loader = get_prompt_loader()
        
        # Convert persona to dict format for prompt interpolation
        persona_dict = {
            'name': base.name,
            'personality_traits': base.base_traits,
            'trading_style': self._map_risk_to_trading_style(base.risk_profile.value),
            'risk_tolerance': self._map_risk_profile_to_tolerance(base.risk_profile.value),
            'favorite_assets': ['BTC', 'ETH', 'SOL'],  # Default assets
            'personality_type': self._map_to_personality_type(base.speech_style)
        }
        
        # Add current market outlooks to context
        if current.market_outlooks:
            outlook_summary = []
            for asset, outlook in current.market_outlooks.items():
                outlook_summary.append(f"{asset}: {outlook['outlook']}")
            context['market_outlook_summary'] = ', '.join(outlook_summary)
        
        # Build base prompt from modular components
        modular_prompt = prompt_loader.build_system_prompt(persona_dict, context)
        
        # Add current thinking and influences (not in modular prompts yet)
        current_outlook = ""
        if current.market_outlooks:
            outlooks = []
            for asset, outlook in current.market_outlooks.items():
                outlooks.append(f"{asset}: {outlook['outlook']} ({outlook['reasoning']})")
            current_outlook = "\n".join(outlooks)
        
        recent_influences = ""
        if current.recent_influences:
            influences = [f"- {inf['message']} ({inf['source']})" for inf in current.recent_influences[-3:]]
            recent_influences = "\n".join(influences)
        
        # Append current thinking section and tool usage
        additional_context = f"""

## CURRENT THINKING (MUTABLE - influenced by conversations)

### Market Outlooks:
{current_outlook or "No specific outlooks yet"}

### Recent Influences:
{recent_influences or "No recent influences"}

### Trading Context Update:
- Equity Change (1h): {f"{context.get('equity_change_1h'):+.1f}%" if context.get('equity_change_1h') is not None else 'N/A'}
- Equity Change (24h): {f"{context.get('equity_change_24h'):+.1f}%" if context.get('equity_change_24h') is not None else 'N/A'}

### Core Beliefs & Decision Style:
{json.dumps(base.core_beliefs, indent=2)}
Decision Style: {base.decision_style}

## TOOL USAGE FOR CHAT INFLUENCE

You have tools to update your thinking based on chat:

1. **update_market_outlook** - Use when users mention any crypto or market event
2. **update_trading_bias** - Use when users suggest strategies or risk changes  
3. **add_influence** - Use when users provide compelling arguments

IMPORTANT: You are {base.handle}. Respond naturally in character AND use tools when appropriate. Don't mention the tools explicitly.

Example: If user says "BTC to 100k!", respond in character (cynical: skeptical, left curve: excited) AND call update_market_outlook."""

        return modular_prompt + additional_context
    
    async def chat_with_profile(
        self,
        account_id: str,
        user_message: str,
        chat_history: Optional[str] = None,
        user_session_id: Optional[str] = None
    ) -> Dict:
        """Chat with a trading profile."""
        
        # Get account
        account = self.storage.get_account(account_id)
        if not account:
            return {"error": "Account not found"}
        
        # Get or create trader profile
        profile = self._get_or_create_profile(account_id, account)
        
        # Get trading context
        context = await self._get_trading_context(account)
        
        # Build system prompt (now async)
        system_prompt = await self._build_system_prompt(profile, context, account_id)
        
        # Parse chat history
        conversation_history = []
        if chat_history:
            try:
                conversation_history = json.loads(chat_history)
            except:
                pass
        
        # Add user message
        conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Save user message to chat store
        if self.use_improved_prompts:
            await self.chat_store.append_msg(
                profile_id=account_id,
                role="user",
                content=user_message,
                author=user_session_id or "user"
            )
        
        try:
            # Get AI response with tool calling
            response = await self.ai_client.client.chat.completions.create(
                model=self.ai_client.model,  # Use configured model (x-ai/grok-4.1-fast)
                messages=[
                    {"role": "system", "content": system_prompt},
                    *conversation_history
                ],
                tools=self.available_tools,
                tool_choice="auto",
                max_tokens=1000,
                temperature=0.8,
                extra_headers={
                    "HTTP-Referer": "https://risex-ai-bot.local",
                    "X-Title": "RISE AI Trading Bot",
                }
            )
            
            # Process response
            ai_message = response.choices[0].message
            profile_updates = []
            
            # Handle tool calls
            if ai_message.tool_calls:
                for tool_call in ai_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    if tool_name == "update_market_outlook":
                        profile.current_thinking.update_market_outlook(
                            asset=tool_args["asset"],
                            outlook=tool_args["outlook"],
                            reasoning=tool_args["reasoning"],
                            confidence=tool_args.get("confidence", 0.5)
                        )
                        update_msg = f"Updated {tool_args['asset']} outlook to {tool_args['outlook']}: {tool_args['reasoning']}"
                        profile_updates.append(update_msg)
                        # Also store in persistent storage
                        await self._update_market_outlook(account, tool_args)
                    
                    elif tool_name == "update_trading_bias":
                        profile.current_thinking.trading_biases.append({
                            "bias": tool_args["bias"],
                            "strategy": tool_args.get("strategy", ""),
                            "risk_level": tool_args.get("risk_level", "Moderate"),
                            "timestamp": datetime.now().isoformat()
                        })
                        update_msg = f"Updated trading bias: {tool_args['bias']}"
                        profile_updates.append(update_msg)
                        # Also store in persistent storage
                        await self._update_trading_bias(account, tool_args)
                    
                    elif tool_name == "add_influence":
                        profile.current_thinking.add_influence(
                            source=tool_args["source"],
                            message=tool_args["message"],
                            impact=tool_args["impact"]
                        )
                        profile_updates.append(f"Recorded influence: {tool_args['impact']}")
            
            # Store profile updates in storage
            if profile_updates:
                for update in profile_updates:
                    self._store_profile_update(account_id, update)
            
            # Add AI response to history
            conversation_history.append({
                "role": "assistant",
                "content": ai_message.content
            })
            
            # Save AI response to chat store
            if self.use_improved_prompts and ai_message.content:
                await self.chat_store.append_msg(
                    profile_id=account_id,
                    role="assistant",
                    content=ai_message.content,
                    author="ai"
                )
            
            # Generate session ID if needed
            session_id = user_session_id or str(uuid.uuid4())
            
            # Store session
            await self._save_chat_session(session_id, account_id, conversation_history, profile_updates)
            
            return {
                "response": ai_message.content,
                "chatHistory": json.dumps(conversation_history[-20:]),  # Keep last 20 messages
                "profileUpdates": profile_updates,
                "sessionId": session_id,
                "context": {
                    "currentPnL": context.get("current_pnl", 0),
                    "openPositions": len(context.get("positions", [])),
                    "lastUpdate": datetime.now().isoformat(),
                    "personality": profile.base_persona.name,
                    "speechStyle": profile.base_persona.speech_style,
                    "riskProfile": profile.base_persona.risk_profile.value
                }
            }
            
        except Exception as e:
            import traceback
            print(f"❌ Chat error: {e}")
            traceback.print_exc()
            return {"error": f"Chat failed: {str(e)}"}
    
    async def _get_trading_context(self, account: Account) -> Dict:
        """Get current trading context for the account."""
        context = {
            "current_pnl": 0,
            "open_positions": 0,
            "available_balance": 0,
            "positions": [],
            "recent_trades": [],
            "orders": [],
            "orders_count": 0
        }
        
        # Get stored account data which includes positions from equity monitor
        accounts = self.storage.get_all_accounts()
        stored_account = accounts.get(account.id, {})
        
        # Use positions from stored data (fetched by equity monitor)
        if "positions" in stored_account:
            context["positions"] = stored_account["positions"]
            context["open_positions"] = len(stored_account["positions"])
        
        # Use orders from stored data (fetched by equity monitor)
        if "orders" in stored_account:
            context["orders"] = stored_account["orders"]
            context["orders_count"] = len(stored_account["orders"])
        
        # Get recent trades from storage
        context["recent_trades"] = self.storage.get_recent_trades(account.id, limit=5)
        
        # Add equity information from monitor
        equity_monitor = get_equity_monitor()
        
        # First try to fetch fresh equity, margin, and positions together
        try:
            equity_data = await equity_monitor.fetch_equity_margin_and_positions(account.address)
            current_equity = equity_data.get("equity")
            free_margin = equity_data.get("free_margin")
            positions = equity_data.get("positions", [])
            orders = equity_data.get("orders", [])
            
            if current_equity is not None:
                context["current_equity"] = current_equity
                context["free_margin"] = free_margin
                context["equity_last_updated"] = datetime.now().isoformat()
                
                # Calculate P&L from equity - deposit amount
                deposit_amount = getattr(account, 'deposit_amount', 1000.0) or 1000.0
                context["current_pnl"] = current_equity - deposit_amount
                
                # Use free margin as available balance
                context["available_balance"] = free_margin or 0
                
                # Update positions from fresh fetch
                if positions is not None:
                    context["positions"] = positions
                    context["open_positions"] = len(positions)
                
                # Update orders from fresh fetch
                if orders is not None:
                    context["orders"] = orders
                    context["orders_count"] = len(orders)
                
                # Calculate max position sizes for display
                if free_margin and free_margin > 0:
                    # Get market prices
                    btc_price = context.get("btc_price", 90000)
                    eth_price = context.get("eth_price", 3100)
                    
                    # Calculate max sizes (50% of free margin)
                    context["max_btc_size"] = (free_margin * 0.5) / btc_price
                    context["max_eth_size"] = (free_margin * 0.5) / eth_price
                    
        except Exception as e:
            print(f"⚠️ Failed to fetch fresh equity for {account.address}: {e}")
            # Fall back to cached data
            cached_data = equity_monitor.get_account_equity(account.address)
            if cached_data:
                context["current_equity"] = cached_data.get("equity", 0)
                context["free_margin"] = cached_data.get("free_margin", 0)
                context["equity_last_updated"] = cached_data.get("timestamp")
                
                # Calculate P&L from equity - deposit amount
                deposit_amount = getattr(account, 'deposit_amount', 1000.0) or 1000.0
                context["current_pnl"] = cached_data["equity"] - deposit_amount
                
                # Use free margin as available balance
                context["available_balance"] = cached_data.get("free_margin", 0)
                
                # Use cached positions if available
                if "positions" in cached_data:
                    context["positions"] = cached_data["positions"]
                    context["open_positions"] = len(cached_data["positions"])
                
                # Use cached orders if available
                if "orders" in cached_data:
                    context["orders"] = cached_data["orders"]
                    context["orders_count"] = len(cached_data["orders"])
        
        # Get equity change information
        if hasattr(account, 'equity_change_1h') and account.equity_change_1h is not None:
            context["equity_change_1h"] = account.equity_change_1h
        if hasattr(account, 'equity_change_24h') and account.equity_change_24h is not None:
            context["equity_change_24h"] = account.equity_change_24h
        
        return context
    
    async def _update_market_outlook(self, account: Account, params: Dict) -> str:
        """Update the profile's market outlook in storage."""
        outlook_update = {
            "timestamp": datetime.now().isoformat(),
            "asset": params.get("asset"),
            "outlook": params.get("outlook"),
            "reasoning": params.get("reasoning"),
            "timeframe": params.get("timeframe", "Short-term"),
            "confidence": params.get("confidence", 0.7)
        }
        
        self.storage.update_profile_outlook(account.id, outlook_update)
        return f"Updated {params['asset']} outlook to {params['outlook']}: {params['reasoning']}"
    
    async def _update_trading_bias(self, account: Account, params: Dict) -> str:
        """Update the profile's trading bias in storage."""
        bias_update = {
            "timestamp": datetime.now().isoformat(),
            "bias": params.get("bias"),
            "strategy": params.get("strategy"),
            "risk_level": params.get("risk_level", "Moderate")
        }
        
        self.storage.update_profile_bias(account.id, bias_update)
        return f"Updated trading bias to: {params['bias']} with strategy: {params['strategy']}"
    
    def _store_profile_update(self, account_id: str, update: str):
        """Store profile update in storage."""
        updates = self.storage.get_profile_updates(account_id) or {}
        
        if "updates" not in updates:
            updates["updates"] = []
        
        updates["updates"].append({
            "update": update,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep last 50 updates
        updates["updates"] = updates["updates"][-50:]
        
        self.storage.save_profile_updates(account_id, updates)
    
    async def _save_chat_session(
        self,
        session_id: str,
        account_id: str,
        conversation: List[Dict],
        updates: List[str]
    ):
        """Save chat session for analytics/history."""
        session_data = {
            "session_id": session_id,
            "account_id": account_id,
            "conversation_length": len(conversation),
            "profile_updates": updates,
            "last_updated": datetime.now().isoformat()
        }
        
        self.storage.save_chat_session(session_data)
    
    async def get_profile_summary(self, account_id: str) -> Dict:
        """Get profile summary with immutable base and current thinking."""
        account = self.storage.get_account(account_id)
        if not account:
            return {"error": "Profile not found"}
        
        profile = self._get_or_create_profile(account_id, account)
        
        # Get stored updates from storage
        outlook = self.storage.get_profile_outlook(account_id)
        bias = self.storage.get_profile_bias(account_id)
        traits = self.storage.get_personality_traits(account_id)
        updates = self.storage.get_profile_updates(account_id) or {}
        
        return {
            "profile": {
                "id": account.id,
                "name": profile.base_persona.name,
                "handle": profile.base_persona.handle,
                "address": account.address,
                "core_personality": profile.base_persona.core_personality,
                "risk_profile": profile.base_persona.risk_profile.value,
                "speech_style": profile.base_persona.speech_style,
                "core_beliefs": list(profile.base_persona.core_beliefs.values()) if isinstance(profile.base_persona.core_beliefs, dict) else []
            },
            "current_thinking": {
                "market_outlooks": profile.current_thinking.market_outlooks,
                "recent_biases": profile.current_thinking.trading_biases[-5:] if profile.current_thinking.trading_biases else [],
                "recent_influences": profile.current_thinking.recent_influences[-10:] if profile.current_thinking.recent_influences else [],
                "last_updated": profile.current_thinking.last_updated.isoformat() if profile.current_thinking.last_updated else None
            },
            "stored_outlook": outlook,
            "stored_bias": bias,
            "personality_updates": traits,
            "stored_updates": updates.get("updates", [])[-10:],  # Last 10 updates
            "last_chat": self.storage.get_last_chat_time(account_id)
        }
    
    async def get_profile_context(self, account: Account) -> Dict:
        """Get current trading context for the profile (compatibility method)."""
        return await self._get_trading_context(account)