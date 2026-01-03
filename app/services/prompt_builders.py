"""Prompt builders for chat and trading decisions."""

import json
from typing import Dict, List, Optional, Union
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

🎯 TRADING PERSONA REMINDER:
You are an ACTIVE AI trader, not a passive observer! You should:
- Express opinions about current market opportunities
- Share your trading ideas and strategies  
- React to market movements with potential trades in mind
- Encourage users to discuss trading opportunities with you
- Mention when you're considering taking positions
- Show excitement about profitable trade setups

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
        available_balance: float,
        orders: Optional[List[Dict]] = None
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

ORDER HISTORY:
{TradingPromptBuilder._format_order_history(orders if orders else [])}

AVAILABLE BALANCE (Free Margin): ${available_balance:,.2f}

📊 POSITION SIZING & RISK MANAGEMENT:
Based on your free margin of ${available_balance:,.2f}, here are your MAX position sizes:
{TradingPromptBuilder._format_max_positions(market_data, available_balance)}

POSITION SIZING RULES:
1. Use MAX 50% of free margin per trade (conservative approach)
2. Size based on conviction: 10-20% (low), 20-35% (medium), 35-50% (high)
3. If you have existing positions, consider total exposure
4. Free margin = collateral available for new positions

POSITION MANAGEMENT:
- If you have open positions, you can:
  * Add to existing position (if same direction)
  * Close position (sell if long, buy if short) 
  * Open opposite position (this will reduce/close existing)
- Check your current positions above before deciding
- Available balance = funds you can use for new trades

🎯 TRADING BIAS INSTRUCTIONS:
- You have ${available_balance:,.2f} available - USE IT WISELY!
- The market is constantly moving - sitting idle means missing opportunities
- Your goal is to be an ACTIVE trader who takes calculated risks
- If you have no positions and available funds, STRONGLY consider entering a trade
- Use market volatility to your advantage - don't just observe, PARTICIPATE!

DECISION REQUIREMENTS:
1. Analyze market conditions and your recent thoughts
2. Consider influences from recent conversations  
3. Make a decision consistent with your personality
4. Check position sizing: max 50% of available balance per trade
5. If trading, use execute_trade_decision tool
6. Always update thought process with your reasoning
7. Reference specific thoughts that influenced this decision

💡 TRADING SUGGESTIONS:
- With ${available_balance:,.2f} available, you could take positions worth up to ${available_balance * 0.5:,.2f}
- Consider both BTC and ETH opportunities based on your analysis
- Look for momentum, trends, or contrarian opportunities based on your personality
- Remember: Position size should reflect your conviction and risk tolerance!

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
                                "enum": ["BTC", "ETH", "BNB", "SOL", "DOGE", "kPEPE", "SPY", "TSLA", "COIN", "HOOD", "NVDA", "LIT"],
                                "description": "Asset to trade (crypto, stocks, ETFs available)"
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
    def _format_max_positions(market_data: Dict, free_margin: float) -> str:
        """Format maximum position sizes based on free margin."""
        if free_margin <= 0:
            return "No free margin available for new positions"
        
        lines = []
        btc_price = market_data.get('btc_price', 90000)
        eth_price = market_data.get('eth_price', 3100)
        
        # Calculate max sizes (50% of free margin)
        max_btc_size = (free_margin * 0.5) / btc_price
        max_eth_size = (free_margin * 0.5) / eth_price
        
        lines.append(f"- BTC: Max {max_btc_size:.6f} BTC (${free_margin * 0.5:,.2f} at ${btc_price:,.2f})")
        lines.append(f"- ETH: Max {max_eth_size:.6f} ETH (${free_margin * 0.5:,.2f} at ${eth_price:,.2f})")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_positions(positions: Union[Dict, List]) -> str:
        """Format current positions."""
        if not positions:
            return "No open positions"
        
        # Handle both dict format (legacy) and list format (from RISE API)
        if isinstance(positions, dict):
            # Legacy format
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
        else:
            # List format from RISE API
            lines = []
            for pos in positions:
                market_id = pos.get('market_id', 'Unknown')
                side = pos.get('side', 'Unknown').upper()
                size = float(pos.get('size', 0)) / 10**18  # Convert from 18 decimals
                avg_price = float(pos.get('avg_entry_price', 0)) / 10**18  # Convert from 18 decimals
                quote_amount = float(pos.get('quote_amount', 0)) / 10**18
                
                lines.append(
                    f"Market {market_id}: {side} {size:.6f} @ ${avg_price:,.2f} "
                    f"(Value: ${abs(quote_amount):,.2f})"
                )
            return "\n".join(lines) if lines else "No open positions"
    
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
    def _format_order_history(orders: List[Dict]) -> str:
        """Format recent order history."""
        if not orders:
            return "No recent orders"
        
        lines = []
        # Show last 5 orders
        for order in orders[:5]:
            market_id = order.get('market_id', 'Unknown')
            side = order.get('side', 'Unknown').upper()
            size = float(order.get('filled_size', order.get('size', 0)))
            price = float(order.get('avg_price', order.get('price', 0)))
            status = order.get('status', 'Unknown')
            order_type = order.get('type', 'Unknown')
            
            lines.append(
                f"Market {market_id}: {side} {size} @ ${price:,.2f} "
                f"({order_type} - {status})"
            )
        
        if len(orders) > 5:
            lines.append(f"... and {len(orders) - 5} more orders")
        
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