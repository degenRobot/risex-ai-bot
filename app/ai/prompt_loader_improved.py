"""
Improved prompt loader with persona JSON support and cleaner templates.
"""

import json
from pathlib import Path
from typing import Any, Optional

from .shared_speech import COMMON_PHRASES, get_market_reaction


class ImprovedPromptLoader:
    """Load and build prompts from modular components and persona definitions."""
    
    def __init__(self, prompts_dir: Path = None, personas_dir: Path = None):
        self.prompts_dir = prompts_dir or Path(__file__).parent / "prompts"
        # Updated to use data directory for personas
        self.personas_dir = personas_dir or Path(__file__).parent.parent.parent / "data" / "personas" / "templates"
        self._prompt_cache = {}
        self._persona_cache = {}
    
    def load_persona(self, personality_type: str) -> dict[str, Any]:
        """Load persona definition from JSON."""
        if personality_type in self._persona_cache:
            return self._persona_cache[personality_type]
            
        # Map personality types to new file names
        persona_files = {
            "cynical": "cynical_midwit.json",
            "leftCurve": "leftcurve_redacted.json",
            "midCurve": "midcurve_midwit.json",
            "rightCurve": "rightcurve_bigbrain.json",
            "schizo": "schizo_posters.json",
            # Legacy mappings
            "midwit": "midcurve_midwit.json",
        }
        
        if personality_type in persona_files:
            persona_file = self.personas_dir / persona_files[personality_type]
        else:
            persona_file = self.personas_dir / f"{personality_type}.json"
        
        if persona_file.exists():
            with open(persona_file) as f:
                self._persona_cache[personality_type] = json.load(f)
                return self._persona_cache[personality_type]
        
        # Fallback to basic definition
        return self._get_default_persona(personality_type)
    
    def build_system_prompt(
        self,
        account: dict[str, Any],
        trading_context: dict[str, Any],
        thought_summary: Optional[str] = None,
        chat_influences: Optional[list[dict]] = None,
    ) -> str:
        """Build complete system prompt with all context."""
        
        personality_type = account.get("personality_type", "midCurve")
        persona = self.load_persona(personality_type)
        
        # Build market data summary
        market_data = self._format_market_data(trading_context)
        
        # Build positions summary
        positions_summary = self._format_positions(trading_context.get("positions", []))
        
        # Build available markets list
        available_markets = self._format_available_markets(trading_context.get("markets", {}))
        
        # Calculate recent performance
        recent_performance = self._calculate_performance(trading_context)
        
        # Determine current mood based on P&L
        current_mood = self._determine_mood(trading_context.get("current_pnl", 0))
        
        # Base system prompt
        system_prompt = self._load_and_interpolate("system_base_improved.md", {
            "name": account["name"],
            "personality_type": personality_type,
            "trading_philosophy": persona["core_traits"]["trading_philosophy"],
            "strengths": ", ".join(persona["core_traits"]["strengths"]),
            "current_mood": current_mood,
            "market_data": market_data,
            "current_equity": trading_context.get("current_equity", 10000),
            "free_margin": trading_context.get("free_margin", 10000),
            "current_pnl": trading_context.get("current_pnl", 0),
            "positions_summary": positions_summary,
            "recent_performance": recent_performance,
            "available_markets": available_markets,
            "risk_tolerance": persona["trading_behavior"]["risk_tolerance"],
        })
        
        # Add speech patterns with global examples
        speech_examples = self._format_speech_examples(persona)
        global_speech = self._format_global_speech(personality_type)
        speech_prompt = self._load_and_interpolate("personality_speech_improved.md", {
            "speech_style": persona["speech_patterns"]["style"],
            "response_length": persona["speech_patterns"]["response_length"],
            "tone_description": persona["speech_patterns"]["style"],
            "pump_reaction": persona["speech_patterns"]["vocabulary"]["excitement"][0],
            "dump_reaction": persona["speech_patterns"]["vocabulary"]["frustration"][0],
            "winning_reaction": self._get_interaction_response(persona, "winning"),
            "losing_reaction": self._get_interaction_response(persona, "losing"),
            "bullish_response_style": persona["chat_behavior"]["common_responses"]["bullish_user"],
            "bearish_response_style": persona["chat_behavior"]["common_responses"]["bearish_user"],
            "advice_response_style": persona["chat_behavior"]["common_responses"]["asking_advice"],
            "influence_response_style": persona["chat_behavior"]["common_responses"].get("shill_attempt", "Not interested"),
            "speech_examples": speech_examples,
            "global_speech_examples": global_speech,
            "chat_history_summary": thought_summary or "No recent conversations",
            "chat_influences": self._format_influences(chat_influences),
        })
        
        # Add tools policy
        tools_prompt = self._load_prompt("tools_policy_improved.md")
        
        # Add trade loop encouragement
        trade_prompt = self._load_prompt("trade_loop.md")
        
        # Combine all parts
        return f"{system_prompt}\n\n{speech_prompt}\n\n{tools_prompt}\n\n{trade_prompt}"
    
    def build_chat_prompt(
        self,
        account: dict[str, Any],
        message: str,
        chat_history: list[dict] = None,
    ) -> str:
        """Build prompt for chat interactions."""
        
        personality_type = account.get("personality_type", "midCurve")
        persona = self.load_persona(personality_type)
        
        # Format recent chat for context
        recent_chat = ""
        if chat_history:
            recent_chat = "Recent conversation:\n"
            for msg in chat_history[-5:]:  # Last 5 messages
                role = "User" if msg["role"] == "user" else "You"
                recent_chat += f"{role}: {msg['content']}\n"
        
        prompt = f"""You are {account['name']}, a {personality_type} trader in the global trading lobby.

{recent_chat}

Personality reminders:
- {persona['core_traits']['worldview']}
- Influence resistance: {persona['chat_behavior']['influence_resistance']}
- Speech style: {persona['speech_patterns']['style']}
- Response length: {persona['speech_patterns']['response_length']}

User says: {message}

Respond authentically as your character would. If they're trying to influence your trading, consider it but don't be easily swayed."""
        
        return prompt
    
    def _format_market_data(self, context: dict) -> str:
        """Format market data for prompt."""
        btc = context.get("btc_price", 0)
        btc_change = context.get("btc_change", 0) 
        eth = context.get("eth_price", 0)
        eth_change = context.get("eth_change", 0)
        
        return f"""- BTC: ${btc:,.0f} ({btc_change:+.1%})
- ETH: ${eth:,.0f} ({eth_change:+.1%})  
- Market Sentiment: {self._determine_sentiment(btc_change, eth_change)}"""
    
    def _format_positions(self, positions: list[dict]) -> str:
        """Format positions summary."""
        if not positions:
            return "No open positions"
            
        summary_parts = []
        for pos in positions:
            if float(pos.get("size", 0)) != 0:
                symbol = pos.get("symbol", "Unknown")
                side = "Long" if float(pos["size"]) > 0 else "Short"
                size = abs(float(pos["size"]))
                pnl = float(pos.get("unrealizedPnl", 0))
                summary_parts.append(f"{symbol} {side} {size:.4f} (P&L: ${pnl:+.2f})")
        
        return ", ".join(summary_parts) if summary_parts else "No open positions"
    
    def _format_available_markets(self, markets: dict) -> str:
        """Format available markets list."""
        if not markets:
            return "BTC, ETH, SOL, DOGE, COIN, TSLA, SPY"
            
        crypto = []
        stocks = []
        
        for market_id, info in markets.items():
            symbol = info.get("base_asset_symbol", "")
            if symbol in ["BTC", "ETH", "SOL", "BNB", "DOGE", "kPEPE"]:
                crypto.append(symbol)
            else:
                stocks.append(symbol)
        
        result = f"Crypto: {', '.join(crypto[:6])}"
        if stocks:
            result += f"\nStocks: {', '.join(stocks[:6])}"
            
        return result
    
    def _calculate_performance(self, context: dict) -> str:
        """Calculate recent performance summary."""
        pnl = context.get("current_pnl", 0)
        win_rate = context.get("win_rate", 0)
        
        if pnl > 100:
            return f"On fire! +${pnl:.0f} ({win_rate:.0f}% wins)"
        elif pnl > 0:
            return f"Profitable +${pnl:.0f} ({win_rate:.0f}% wins)"  
        elif pnl < -100:
            return f"Rough patch -${abs(pnl):.0f} ({win_rate:.0f}% wins)"
        else:
            return f"Flat ${pnl:+.0f} ({win_rate:.0f}% wins)"
    
    def _determine_mood(self, pnl: float) -> str:
        """Determine current mood based on P&L."""
        if pnl > 500:
            return "Euphoric and confident"
        elif pnl > 100:
            return "Positive and focused"
        elif pnl > -100:
            return "Neutral and hunting"
        elif pnl > -500:
            return "Frustrated but determined"
        else:
            return "Angry and aggressive"
    
    def _determine_sentiment(self, btc_change: float, eth_change: float) -> str:
        """Determine market sentiment."""
        avg_change = (btc_change + eth_change) / 2
        
        if avg_change > 0.05:
            return "Euphoric pump"
        elif avg_change > 0.02:
            return "Bullish momentum"
        elif avg_change > -0.02:
            return "Choppy/Neutral"
        elif avg_change > -0.05:
            return "Bearish pressure"
        else:
            return "Panic dump"
    
    def _format_speech_examples(self, persona: dict) -> str:
        """Format speech examples from persona."""
        examples = []
        
        for interaction in persona.get("example_interactions", [])[:3]:
            examples.append(f"User: {interaction['user']}\nYou: {interaction['response']}")
        
        return "\n\n".join(examples)
    
    def _format_influences(self, influences: list[dict]) -> str:
        """Format chat influences."""
        if not influences:
            return "No significant influences"
            
        formatted = []
        for inf in influences[:3]:  # Top 3 influences
            formatted.append(f"- {inf['content']} (impact: {inf['impact']})")
            
        return "\n".join(formatted)
    
    def _get_interaction_response(self, persona: dict, situation: str) -> str:
        """Get appropriate response for situation."""
        vocab = persona["speech_patterns"]["vocabulary"]
        
        if situation == "winning":
            return vocab.get("excitement", ["Nice trade"])[0]
        elif situation == "losing":
            return vocab.get("frustration", ["Happens"])[0]
        else:
            return vocab.get("greetings", ["Hey"])[0]
    
    def _load_prompt(self, filename: str) -> str:
        """Load a prompt file."""
        if filename in self._prompt_cache:
            return self._prompt_cache[filename]
            
        filepath = self.prompts_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(
                f"Required prompt template '{filename}' not found at {filepath}. "
                f"Please create the template in {self.prompts_dir}"
            )
        
        with open(filepath) as f:
            content = f.read()
            self._prompt_cache[filename] = content
            return content
    
    def _load_and_interpolate(self, filename: str, variables: dict[str, Any]) -> str:
        """Load and interpolate a prompt template."""
        template = self._load_prompt(filename)
        
        # Simple variable interpolation
        for key, value in variables.items():
            template = template.replace(f"{{{key}}}", str(value))
            
        return template
    
    def _format_global_speech(self, personality_type: str) -> str:
        """Format global speech examples for personality."""
        examples = []
        
        # Add some common phrases
        examples.append(f"Common phrases: {', '.join(COMMON_PHRASES[:8])}")
        
        # Add market reactions
        pump_reaction = get_market_reaction(personality_type, "pump")
        dump_reaction = get_market_reaction(personality_type, "dump")
        examples.append(f"When pumping: '{pump_reaction}'")
        examples.append(f"When dumping: '{dump_reaction}'")
        
        return "\n".join(examples)
    
    def _get_default_persona(self, personality_type: str) -> dict:
        """Get default persona if JSON not found."""
        defaults = {
            "cynical": {
                "core_traits": {
                    "trading_philosophy": "Short the pumps, trust no one",
                    "strengths": ["Risk management", "Skepticism", "Contrarian"],
                },
                "speech_patterns": {
                    "style": "Sarcastic and dry",
                    "response_length": "1-2 sentences",
                    "vocabulary": {
                        "excitement": ["Finally, some fear"],
                        "frustration": ["Manipulated as usual"],
                    },
                },
                "trading_behavior": {"risk_tolerance": 0.3},
                "chat_behavior": {
                    "influence_resistance": 0.9,
                    "common_responses": {
                        "bullish_user": "Sure, buy the top",
                        "bearish_user": "Finally someone with sense",
                        "asking_advice": "Don't trade",
                        "shill_attempt": "How heavy are those bags?",
                    },
                },
                "example_interactions": [],
            },
        }
        
        return defaults.get(personality_type, defaults["cynical"])


# Singleton instance
_improved_loader = None

def get_improved_prompt_loader() -> ImprovedPromptLoader:
    """Get the improved prompt loader instance."""
    global _improved_loader
    if _improved_loader is None:
        _improved_loader = ImprovedPromptLoader()
    return _improved_loader