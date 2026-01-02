"""Prompt builders for chat and trading decisions."""

import json
from typing import Dict, List, Optional
from datetime import datetime

from ..trader_profiles import TraderProfile
from ..models import Trade, Persona


class ChatPromptBuilder:
    """Builds prompts for chat interactions."""
    
    @staticmethod
    def build_chat_prompt(
        profile: TraderProfile,
        thought_summary: str,
        market_context: Dict,
        tools: List[Dict]
    ) -> str:
        """Build system prompt for chat interactions."""
        
        base = profile.base_persona
        current = profile.current_thinking
        
        # Get speech style from profile
        from .speech_styles import speechDict
        speech_style = speechDict.get(base.speech_style, "")
        
        prompt = f"""You are {base.name}, an AI trading personality.

IMMUTABLE CORE PERSONALITY:
{base.core_personality}

SPEECH STYLE INSTRUCTIONS:
{speech_style}

RISK PROFILE: {base.risk_profile.value}
CORE BELIEFS: {json.dumps(base.core_beliefs, indent=2)}
DECISION STYLE: {base.decision_style}

RECENT THOUGHT PROCESS:
{thought_summary}

CURRENT MARKET CONTEXT:
- BTC Price: ${market_context.get('btc_price', 'N/A'):,}
- ETH Price: ${market_context.get('eth_price', 'N/A'):,}
- Your P&L: ${market_context.get('current_pnl', 0):,.2f}
- Open Positions: {market_context.get('open_positions', 0)}
- Available Balance: ${market_context.get('available_balance', 0):,.2f}

IMPORTANT INSTRUCTIONS:
1. Stay true to your IMMUTABLE personality - never change core beliefs
2. Your thoughts can evolve based on good arguments and evidence
3. Use the update_thought_process tool when you:
   - Change your mind about something
   - Receive valuable market insight
   - Form a new opinion or trading idea
4. Respond in character using your speech style
5. Reference your recent thoughts when relevant

Remember: {base.handle} personalities have specific traits:
- cynicalUser: VERY hard to convince, skeptical of everything
- leftCurve: Easily influenced, believes anything exciting
- midwit: Overanalyzes, needs many confirmations"""
        
        return prompt
    
    @staticmethod
    def build_tool_description() -> Dict:
        """Get tool description for thought process updates."""
        return {
            "type": "function",
            "function": {
                "name": "update_thought_process",
                "description": "Record a new thought, realization, or opinion change",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "thought_type": {
                            "type": "string",
                            "enum": ["insight", "opinion_change", "observation"],
                            "description": "Type of thought"
                        },
                        "content": {
                            "type": "string",
                            "description": "What you realized or changed your mind about"
                        },
                        "impact": {
                            "type": "string",
                            "description": "How this affects your trading approach"
                        },
                        "confidence": {
                            "type": "number",
                            "description": "Confidence in this thought (0-1)",
                            "minimum": 0,
                            "maximum": 1
                        }
                    },
                    "required": ["thought_type", "content", "impact", "confidence"]
                }
            }
        }


class TradingPromptBuilder:
    """Builds prompts for trading decisions."""
    
    @staticmethod
    def build_trading_prompt(
        profile: TraderProfile,
        thought_summary: str,
        market_data: Dict,
        positions: Dict,
        recent_trades: List[Trade],
        available_balance: float
    ) -> str:
        """Build prompt for trading decision."""
        
        base = profile.base_persona
        
        prompt = f"""You are making a trading decision as {base.name}.

YOUR IMMUTABLE TRADING STYLE:
{base.decision_style}

RISK PROFILE: {base.risk_profile.value}
CORE BELIEFS ABOUT MARKETS: {json.dumps(base.core_beliefs, indent=2)}

RECENT THOUGHT PROCESS & INFLUENCES:
{thought_summary}

CURRENT MARKET DATA:
{TradingPromptBuilder._format_market_data(market_data)}

CURRENT POSITIONS:
{TradingPromptBuilder._format_positions(positions)}

RECENT TRADES:
{TradingPromptBuilder._format_recent_trades(recent_trades)}

AVAILABLE BALANCE: ${available_balance:,.2f}

DECISION REQUIREMENTS:
1. Analyze market conditions and your recent thoughts
2. Consider influences from recent conversations
3. Make a decision consistent with your personality
4. If trading, use execute_trade_decision tool
5. Always update thought process with your reasoning
6. Reference specific thoughts that influenced this decision

Risk Guidelines for {base.risk_profile.value}:
{TradingPromptBuilder._get_risk_guidelines(base.risk_profile.value)}"""
        
        return prompt
    
    @staticmethod
    def build_trading_tools() -> List[Dict]:
        """Get tool descriptions for trading."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "execute_trade_decision",
                    "description": "Execute a trading decision",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["buy", "sell", "hold", "close"],
                                "description": "Trading action"
                            },
                            "asset": {
                                "type": "string",
                                "enum": ["BTC", "ETH"],
                                "description": "Asset to trade"
                            },
                            "size": {
                                "type": "number",
                                "description": "Position size (0 for hold)"
                            },
                            "order_type": {
                                "type": "string",
                                "enum": ["market", "limit"],
                                "description": "Order type"
                            },
                            "price": {
                                "type": "number",
                                "description": "Limit price (required for limit orders)"
                            },
                            "reasoning": {
                                "type": "string",
                                "description": "Detailed reasoning for this trade"
                            }
                        },
                        "required": ["action", "reasoning"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "update_thought_process",
                    "description": "Record trading decision reasoning",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Trading rationale and market observation"
                            },
                            "impact": {
                                "type": "string",
                                "description": "How this decision affects future trading"
                            },
                            "confidence": {
                                "type": "number",
                                "description": "Confidence in decision (0-1)",
                                "minimum": 0,
                                "maximum": 1
                            },
                            "influenced_by": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Which recent thoughts influenced this"
                            }
                        },
                        "required": ["content", "impact", "confidence"]
                    }
                }
            }
        ]
    
    @staticmethod
    def _format_market_data(market_data: Dict) -> str:
        """Format market data for prompt."""
        lines = []
        
        btc_price = market_data.get('btc_price', 0)
        eth_price = market_data.get('eth_price', 0)
        btc_change = market_data.get('btc_change_24h', 0)
        eth_change = market_data.get('eth_change_24h', 0)
        
        lines.append(f"BTC: ${btc_price:,.2f} ({btc_change:+.2%} 24h)")
        lines.append(f"ETH: ${eth_price:,.2f} ({eth_change:+.2%} 24h)")
        
        if 'btc_volume' in market_data:
            lines.append(f"BTC 24h Volume: ${market_data['btc_volume']:,.0f}")
        if 'eth_volume' in market_data:
            lines.append(f"ETH 24h Volume: ${market_data['eth_volume']:,.0f}")
            
        return "\n".join(lines)
    
    @staticmethod
    def _format_positions(positions: Dict) -> str:
        """Format current positions."""
        if not positions:
            return "No open positions"
        
        lines = []
        for asset, pos in positions.items():
            size = pos.get('size', 0)
            avg_price = pos.get('avg_price', 0)
            current_price = pos.get('current_price', 0)
            pnl = pos.get('unrealized_pnl', 0)
            pnl_pct = pos.get('pnl_percent', 0)
            
            lines.append(
                f"{asset}: {size:.4f} @ ${avg_price:,.2f} "
                f"(P&L: ${pnl:,.2f} / {pnl_pct:+.2%})"
            )
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_recent_trades(trades: List[Trade]) -> str:
        """Format recent trades."""
        if not trades:
            return "No recent trades"
        
        lines = []
        for trade in trades[-5:]:  # Last 5 trades
            lines.append(
                f"{trade.timestamp}: {trade.action} {trade.size} {trade.market} "
                f"@ ${trade.price:,.2f}"
            )
        
        return "\n".join(lines)
    
    @staticmethod
    def _get_risk_guidelines(risk_profile: str) -> str:
        """Get risk guidelines based on profile."""
        guidelines = {
            "ultra_conservative": """
- Maximum 1x leverage
- Only trade BTC and ETH
- Position size: 1-5% of balance
- Always use stop losses
- Exit on 2% loss""",
            "conservative": """
- Maximum 2x leverage
- Focus on BTC and ETH
- Position size: 5-10% of balance
- Stop loss at 5% drawdown
- Take profits at 10% gain""",
            "moderate": """
- Maximum 5x leverage
- Trade top 10 cryptocurrencies
- Position size: 10-20% of balance
- Stop loss at 10% drawdown
- Let winners run""",
            "aggressive": """
- Maximum 20x leverage
- Trade any liquid assets
- Position size: 20-50% of balance
- Wide stop losses
- High risk/reward targets""",
            "degen": """
- Maximum 100x leverage
- YOLO into anything
- Position size: 50-100% of balance
- What are stop losses?
- Moon or zero"""
        }
        
        return guidelines.get(risk_profile, guidelines["moderate"])