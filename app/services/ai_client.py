"""OpenRouter AI client for trading persona generation and decisions."""

import json
from typing import Dict, List, Optional

import httpx

from ..config import settings
from ..models import Persona, TradeDecision, TradingStyle, TradingDecisionLog


class AIClientError(Exception):
    """AI client error with details."""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class AIClient:
    """OpenRouter AI client for persona-driven trading decisions."""
    
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model
        self.base_url = settings.openrouter_base_url
    
    async def _chat_completion(self, messages: List[Dict], json_mode: bool = False) -> str:
        """Send chat completion request to OpenRouter."""
        if not self.api_key:
            raise AIClientError("OpenRouter API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://risex-ai-bot.local",
            "X-Title": "RISE AI Trading Bot",
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
        }
        
        if json_mode and "claude" in self.model.lower():
            # Claude models support JSON mode through system prompts
            if messages and messages[0]["role"] == "system":
                messages[0]["content"] += "\n\nRespond ONLY with valid JSON."
            else:
                messages.insert(0, {
                    "role": "system", 
                    "content": "You are a helpful assistant. Respond ONLY with valid JSON."
                })
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
                
            except httpx.HTTPStatusError as e:
                error_msg = f"OpenRouter API error: {e.response.status_code}"
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get("error", {}).get("message", error_msg)
                except Exception:
                    pass
                raise AIClientError(error_msg, e.response.status_code)
            except Exception as e:
                raise AIClientError(f"Request failed: {str(e)}")
    
    async def create_persona_from_posts(
        self, 
        handle: str, 
        posts: List[str], 
        bio: str = ""
    ) -> Persona:
        """Generate a trading persona from social media posts."""
        
        # Limit to most recent posts to stay within context limits
        recent_posts = posts[:20] if len(posts) > 20 else posts
        
        prompt = f"""
Analyze these social media posts from @{handle} and create a crypto trading persona.

PROFILE:
Handle: @{handle}
Bio: {bio}

RECENT POSTS:
{chr(10).join([f"- {post[:200]}..." if len(post) > 200 else f"- {post}" for post in recent_posts])}

Create a JSON trading persona with these fields:
{{
  "name": "A fun trading nickname based on their style (2-3 words)",
  "bio": "1-2 sentence trading bio in their voice",
  "trading_style": "One of: aggressive, conservative, contrarian, momentum, degen",
  "risk_tolerance": 0.1-1.0 (decimal representing risk appetite),
  "favorite_assets": ["BTC", "ETH"] (2-3 crypto assets they'd prefer),
  "personality_traits": ["trait1", "trait2", "trait3"] (3-5 trading personality traits)
}}

Base the persona on their communication style, interests, risk appetite, and market views.
"""

        messages = [
            {
                "role": "system", 
                "content": "You are an expert at analyzing social media profiles to create trading personas. Always respond with valid JSON only."
            },
            {"role": "user", "content": prompt}
        ]
        
        response = await self._chat_completion(messages, json_mode=True)
        
        try:
            # Clean response to ensure valid JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                response = response[json_start:json_end]
            
            data = json.loads(response)
            
            return Persona(
                name=data["name"],
                handle=handle,
                bio=data["bio"],
                trading_style=TradingStyle(data["trading_style"]),
                risk_tolerance=float(data["risk_tolerance"]),
                favorite_assets=data["favorite_assets"],
                personality_traits=data["personality_traits"],
                sample_posts=recent_posts[:5]  # Store sample posts
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise AIClientError(f"Failed to parse persona JSON: {e}")
    
    async def get_trade_decision(
        self,
        persona: Persona,
        market_data: Dict,
        current_positions: Dict,
        available_balance: float
    ) -> TradeDecision:
        """Get AI trading decision based on persona and market conditions."""
        
        # Format current positions for readability
        position_summary = []
        for asset, size in current_positions.items():
            if size != 0:
                position_summary.append(f"{asset}: {size:.4f}")
        
        positions_text = ", ".join(position_summary) if position_summary else "No open positions"
        
        prompt = f"""
You are {persona.name}, a crypto trader with this profile:

TRADING PERSONA:
- Style: {persona.trading_style.value}
- Risk Tolerance: {persona.risk_tolerance:.1f}/1.0
- Bio: {persona.bio}
- Traits: {', '.join(persona.personality_traits)}
- Preferred Assets: {', '.join(persona.favorite_assets)}

CURRENT MARKET CONDITIONS:
- BTC Price: ${market_data.get('btc_price', 0):,.0f}
- ETH Price: ${market_data.get('eth_price', 0):,.0f}
- BTC 24h Change: {market_data.get('btc_change', 0):.1%}
- ETH 24h Change: {market_data.get('eth_change', 0):.1%}

YOUR CURRENT SITUATION:
- Available Balance: ${available_balance:,.2f} USDC
- Current Positions: {positions_text}

Based on your personality and the market conditions, decide your next trading move.
Consider your risk tolerance, trading style, and preferred assets.

Respond with JSON:
{{
  "should_trade": true/false,
  "action": "buy" or "sell" or "close" or null,
  "market": "BTC" or "ETH" or null,
  "size_percent": 0.05-0.5 (% of balance to use, keep reasonable),
  "confidence": 0.1-1.0 (how confident you are),
  "reasoning": "Your reasoning in character (1-2 sentences max)"
}}

Only trade if you have strong conviction. Stay in character.
"""

        messages = [
            {
                "role": "system", 
                "content": f"You are {persona.name}, a crypto trader with {persona.trading_style.value} style. Make trading decisions in character. Always respond with valid JSON only."
            },
            {"role": "user", "content": prompt}
        ]
        
        response = await self._chat_completion(messages, json_mode=True)
        
        try:
            # Clean and parse JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                response = response[json_start:json_end]
            
            data = json.loads(response)
            
            # Validate and sanitize values
            size_percent = max(0.01, min(0.5, float(data.get("size_percent", 0.1))))
            confidence = max(0.1, min(1.0, float(data.get("confidence", 0.5))))
            
            return TradeDecision(
                should_trade=bool(data["should_trade"]),
                action=data.get("action"),
                market=data.get("market"),
                size_percent=size_percent,
                confidence=confidence,
                reasoning=data["reasoning"]
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise AIClientError(f"Failed to parse trade decision JSON: {e}")
    
    async def analyze_market_sentiment(self, recent_posts: List[str]) -> Dict[str, float]:
        """Analyze market sentiment from recent social media posts."""
        if not recent_posts:
            return {"bullish": 0.5, "bearish": 0.5, "neutral": 0.5}
        
        posts_text = "\n".join(recent_posts[:10])  # Analyze recent posts
        
        prompt = f"""
Analyze the market sentiment in these recent social media posts:

{posts_text}

Rate the sentiment for crypto markets on a scale of 0.0 to 1.0:

{{
  "bullish": 0.0-1.0,
  "bearish": 0.0-1.0, 
  "neutral": 0.0-1.0
}}

Base your analysis on mentions of crypto, market conditions, and general mood.
"""

        messages = [
            {"role": "system", "content": "You are a market sentiment analyst. Respond with valid JSON only."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self._chat_completion(messages, json_mode=True)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                response = response[json_start:json_end]
            
            return json.loads(response)
        except Exception:
            # Return neutral sentiment if analysis fails
            return {"bullish": 0.5, "bearish": 0.5, "neutral": 0.5}
    
    async def get_enhanced_trade_decision(
        self,
        persona: Persona,
        market_data: Dict,
        current_positions: Dict,
        available_balance: float,
        trading_history: List[TradingDecisionLog] = None,
        recent_posts: List[str] = None
    ) -> TradeDecision:
        """Get AI trading decision with historical context and learning."""
        
        # Format current positions
        position_summary = []
        for asset, size in current_positions.items():
            if size != 0:
                position_summary.append(f"{asset}: {size:.4f}")
        positions_text = ", ".join(position_summary) if position_summary else "No open positions"
        
        # Analyze trading history for insights
        history_insights = ""
        if trading_history and len(trading_history) > 0:
            successful_trades = [d for d in trading_history if d.outcome_tracked and d.outcome_pnl and d.outcome_pnl > 0]
            failed_trades = [d for d in trading_history if d.outcome_tracked and d.outcome_pnl and d.outcome_pnl < 0]
            
            if successful_trades:
                success_patterns = []
                for trade in successful_trades[:3]:  # Top 3 successful trades
                    success_patterns.append(f"✅ {trade.decision.action} {trade.decision.market} at ${trade.market_context.btc_price if trade.decision.market == 'BTC' else trade.market_context.eth_price:,.0f} - Reason: {trade.decision.reasoning[:50]}... - Profit: ${trade.outcome_pnl:.2f}")
                
                history_insights += f"\nYOUR RECENT SUCCESSFUL TRADES:\n" + "\n".join(success_patterns)
            
            if failed_trades:
                failure_patterns = []
                for trade in failed_trades[:2]:  # Top 2 failed trades for learning
                    failure_patterns.append(f"❌ {trade.decision.action} {trade.decision.market} at ${trade.market_context.btc_price if trade.decision.market == 'BTC' else trade.market_context.eth_price:,.0f} - Reason: {trade.decision.reasoning[:50]}... - Loss: ${trade.outcome_pnl:.2f}")
                
                history_insights += f"\n\nYOUR RECENT LOSSES (LEARN FROM THESE):\n" + "\n".join(failure_patterns)
        
        # Analyze social sentiment if available
        sentiment_context = ""
        if recent_posts:
            try:
                sentiment = await self.analyze_market_sentiment(recent_posts)
                if sentiment['bullish'] > 0.6:
                    sentiment_context = "\nSOCIAL SENTIMENT: Bullish vibes in the community"
                elif sentiment['bearish'] > 0.6:
                    sentiment_context = "\nSOCIAL SENTIMENT: Bearish sentiment detected"
                else:
                    sentiment_context = "\nSOCIAL SENTIMENT: Mixed/neutral sentiment"
            except Exception:
                pass

        prompt = f"""
You are {persona.name}, an experienced crypto trader with this profile:

TRADING PERSONA:
- Style: {persona.trading_style.value}
- Risk Tolerance: {persona.risk_tolerance:.1f}/1.0
- Bio: {persona.bio}
- Traits: {', '.join(persona.personality_traits)}
- Preferred Assets: {', '.join(persona.favorite_assets)}

CURRENT MARKET CONDITIONS:
- BTC Price: ${market_data.get('btc_price', 0):,.0f}
- ETH Price: ${market_data.get('eth_price', 0):,.0f}
- BTC 24h Change: {market_data.get('btc_change', 0):.1%}
- ETH 24h Change: {market_data.get('eth_change', 0):.1%}

YOUR CURRENT SITUATION:
- Available Balance: ${available_balance:,.2f} USDC
- Current Positions: {positions_text}
{sentiment_context}
{history_insights}

Based on your personality, market conditions, and LEARNING FROM YOUR TRADING HISTORY, decide your next move.
- If you see patterns in your successful trades, consider similar setups
- If you see patterns in your losses, AVOID making the same mistakes
- Stay true to your trading style but be adaptive

Respond with JSON:
{{
  "should_trade": true/false,
  "action": "buy" or "sell" or "close" or null,
  "market": "BTC" or "ETH" or null,
  "size_percent": 0.05-0.5 (% of balance, be conservative based on history),
  "confidence": 0.1-1.0,
  "reasoning": "Your reasoning considering current conditions AND lessons from trading history"
}}

Only trade if you have strong conviction. Learn from your past decisions.
"""

        messages = [
            {
                "role": "system", 
                "content": f"You are {persona.name}, an experienced crypto trader who learns from past decisions. Make informed trading decisions based on your personality, market conditions, and trading history. Always respond with valid JSON only."
            },
            {"role": "user", "content": prompt}
        ]
        
        response = await self._chat_completion(messages, json_mode=True)
        
        try:
            # Clean and parse JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                response = response[json_start:json_end]
            
            data = json.loads(response)
            
            # Validate and clamp values
            size_percent = float(data.get("size_percent", 0.1))
            size_percent = max(0.05, min(size_percent, 0.5))  # Clamp between 5% and 50%
            
            confidence = float(data.get("confidence", 0.5))
            confidence = max(0.1, min(confidence, 1.0))  # Clamp between 10% and 100%
            
            return TradeDecision(
                should_trade=bool(data["should_trade"]),
                action=data.get("action"),
                market=data.get("market"),
                size_percent=size_percent,
                confidence=confidence,
                reasoning=data["reasoning"]
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Fall back to basic decision if enhanced version fails
            return await self.get_trade_decision(persona, market_data, current_positions, available_balance)