"""Mock social media profiles for testing AI persona generation."""

import random
from datetime import datetime, timedelta
from typing import Dict, List

from ..models import TradingStyle


class MockTradingProfile:
    """Represents a mock trader's social media profile."""
    
    def __init__(
        self,
        handle: str,
        name: str,
        bio: str,
        trading_style: TradingStyle,
        favorite_assets: List[str],
        personality_traits: List[str]
    ):
        self.handle = handle
        self.name = name
        self.bio = bio
        self.trading_style = trading_style
        self.favorite_assets = favorite_assets
        self.personality_traits = personality_traits
        self.tweet_history: List[Dict] = []
    
    def generate_tweet_based_on_market(self, market_data: Dict) -> str:
        """Generate a tweet based on current market conditions and personality."""
        
        btc_change = market_data.get('btc_change', 0)
        eth_change = market_data.get('eth_change', 0)
        btc_price = market_data.get('btc_price', 95000)
        eth_price = market_data.get('eth_price', 3500)
        
        # Tweet templates based on trading style and market conditions
        tweets = self._get_tweet_templates(btc_change, eth_change, btc_price, eth_price)
        
        # Add some randomness
        tweet = random.choice(tweets)
        
        # Store tweet with timestamp
        self.tweet_history.append({
            'text': tweet,
            'timestamp': datetime.now(),
            'market_context': {
                'btc_change': btc_change,
                'eth_change': eth_change,
                'btc_price': btc_price,
                'eth_price': eth_price
            }
        })
        
        return tweet
    
    def _get_tweet_templates(self, btc_change: float, eth_change: float, btc_price: float, eth_price: float) -> List[str]:
        """Get appropriate tweet templates based on trading style and market."""
        
        # Determine market sentiment
        avg_change = (btc_change + eth_change) / 2
        is_bullish = avg_change > 0.02
        is_bearish = avg_change < -0.02
        
        templates = []
        
        if self.trading_style == TradingStyle.AGGRESSIVE:
            if is_bullish:
                templates.extend([
                    f"🚀 BTC breaking ${btc_price:,.0f}! Going all in, this is the rocket ship moment!",
                    f"ETH at ${eth_price:,.0f} and climbing! Leveraging up, fortune favors the bold! 💎",
                    "Market pumping hard! Time to ride this wave to the moon! 🌙",
                    f"BTC +{btc_change:.1%} today! Adding to my position, this bull run is just getting started!",
                ])
            elif is_bearish:
                templates.extend([
                    f"BTC dipping to ${btc_price:,.0f}? BUYING THE DIP! This is free money! 💰",
                    "Market fear = opportunity! Doubling down while others panic sell 📈",
                    f"ETH down {abs(eth_change):.1%}? Perfect entry point! Loading up the bags! 🛍️",
                ])
            else:
                templates.extend([
                    "Sideways action building pressure... big move coming soon! ⚡",
                    "Accumulation phase! Smart money is loading up quietly 🤫",
                ])
        
        elif self.trading_style == TradingStyle.CONSERVATIVE:
            if is_bullish:
                templates.extend([
                    f"BTC looking strong at ${btc_price:,.0f}. Considering a small position increase.",
                    "Nice green day! Sticking to my DCA strategy, slow and steady wins 🐢",
                    f"ETH up {eth_change:.1%}. Good to see some positive momentum in the market.",
                ])
            elif is_bearish:
                templates.extend([
                    "Market volatility today. Glad I'm in cash for now, waiting for clearer signals.",
                    f"BTC down {abs(btc_change):.1%}. Not panicking, just observing. Long-term vision intact 👁️",
                    "Red days are part of the game. Risk management is key to survival.",
                ])
            else:
                templates.extend([
                    "Market consolidation continues. Patience is a virtue in trading.",
                    "Using this quiet period to study charts and plan next moves 📊",
                ])
        
        elif self.trading_style == TradingStyle.DEGEN:
            if is_bullish:
                templates.extend([
                    f"BTC ${btc_price:,.0f}?? YOLO TIME! 100x leverage let's gooooo! 🎲🎲🎲",
                    "ETH PUMPING! Mortgage the house, sell the car! We're going to Lambo land! 🏎️",
                    "TO THE MOON! 🚀🚀🚀 Risk it all for the tendies!",
                    "Number go up! Brain go smooth! Buying more! 🧠📈",
                ])
            elif is_bearish:
                templates.extend([
                    "DIP = OPPORTUNITY! Selling kidneys to buy more crypto! 🫘",
                    "BTFD! Blood in the streets means FEAST TIME! 🩸💰",
                    "Market crashing? Time to leverage UP! What could go wrong? 😂",
                ])
            else:
                templates.extend([
                    "Boring crab market... time to find some 1000x moonshots! 🦀→🚀",
                    "When in doubt, add more leverage! YOLO! 🎰",
                ])
        
        elif self.trading_style == TradingStyle.CONTRARIAN:
            if is_bullish:
                templates.extend([
                    "Everyone's bullish... makes me nervous. Time to take some profits 📉",
                    f"BTC at ${btc_price:,.0f}, euphoria is building. History rhymes... 🔄",
                    "When your barista gives you crypto tips, it might be time to sell 💈",
                ])
            elif is_bearish:
                templates.extend([
                    "Maximum fear in the market! This is when fortunes are made 💪",
                    f"BTC down {abs(btc_change):.1%}. Everyone's panicking, I'm shopping 🛒",
                    "Blood in the streets, time to be greedy when others are fearful 🩸➡️💰",
                ])
            else:
                templates.extend([
                    "Market indecision = opportunity for the patient contrarian 🎯",
                    "While others chase momentum, I'm looking for value 💎",
                ])
        
        elif self.trading_style == TradingStyle.MOMENTUM:
            if is_bullish:
                templates.extend([
                    f"BTC momentum strong at ${btc_price:,.0f}! Following the trend! 📈⬆️",
                    "Trend is your friend! ETH showing beautiful momentum continuation 🌊",
                    f"Higher highs, higher lows on BTC! Riding this trend! +{btc_change:.1%}",
                ])
            elif is_bearish:
                templates.extend([
                    "Downtrend confirmed. Cutting losses and waiting for reversal signals 📉",
                    f"BTC breaking support levels. Momentum shifted bearish {btc_change:.1%}",
                    "Trend has turned, respecting the market direction. Cash is a position too.",
                ])
            else:
                templates.extend([
                    "No clear trend direction yet. Waiting for breakout confirmation 👀",
                    "Sideways chop. Momentum trader stays patient for clear signals ⏳",
                ])
        
        # Add some asset-specific tweets
        if "BTC" in self.favorite_assets:
            templates.extend([
                f"Bitcoin dominance at these levels with BTC at ${btc_price:,.0f}... interesting dynamics",
                "BTC: digital gold, store of value, future of money. Still early! ₿",
            ])
        
        if "ETH" in self.favorite_assets:
            templates.extend([
                f"ETH at ${eth_price:,.0f}. The world computer is just getting started 🖥️",
                "Ethereum ecosystem growing every day. Bullish on utility! ⚡",
            ])
        
        return templates if templates else [
            "Markets are wild today! What a time to be in crypto! 🎢"
        ]
    
    def get_recent_tweets(self, days: int = 7) -> List[str]:
        """Get recent tweets from the last N days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_tweets = [
            tweet['text'] for tweet in self.tweet_history 
            if tweet['timestamp'] > cutoff_date
        ]
        return recent_tweets[-20:]  # Return max 20 recent tweets


class MockSocialClient:
    """Simulates a social media client with predefined trading profiles."""
    
    def __init__(self):
        self.profiles = self._create_mock_profiles()
    
    def _create_mock_profiles(self) -> Dict[str, MockTradingProfile]:
        """Create a set of predefined mock trading profiles."""
        
        profiles = {}
        
        # Aggressive day trader
        profiles["crypto_degen"] = MockTradingProfile(
            handle="crypto_degen",
            name="Max Leverage",
            bio="Day trader | High risk high reward | YOLO mentality | Not financial advice 🚀",
            trading_style=TradingStyle.AGGRESSIVE,
            favorite_assets=["BTC", "ETH"],
            personality_traits=["risk-taker", "optimistic", "impatient", "high-energy"]
        )
        
        # Conservative long-term investor
        profiles["btc_hodler"] = MockTradingProfile(
            handle="btc_hodler",
            name="Diamond Hands Dave",
            bio="Bitcoin maximalist | DCA strategy | 10 year time horizon | Stack sats 💎🙌",
            trading_style=TradingStyle.CONSERVATIVE,
            favorite_assets=["BTC"],
            personality_traits=["patient", "disciplined", "long-term-focused", "risk-aware"]
        )
        
        # Momentum trader
        profiles["trend_master"] = MockTradingProfile(
            handle="trend_master",
            name="Wave Rider",
            bio="Technical analyst | Trend following | Chart patterns | Momentum is king 📈",
            trading_style=TradingStyle.MOMENTUM,
            favorite_assets=["BTC", "ETH"],
            personality_traits=["analytical", "disciplined", "trend-following", "patient"]
        )
        
        # Contrarian trader
        profiles["market_contrarian"] = MockTradingProfile(
            handle="market_contrarian",
            name="Opposite George",
            bio="Contrarian investor | Buy fear, sell greed | Value hunting | Independent thinking 🎯",
            trading_style=TradingStyle.CONTRARIAN,
            favorite_assets=["BTC", "ETH"],
            personality_traits=["independent", "skeptical", "value-focused", "patient"]
        )
        
        # YOLO degen
        profiles["yolo_king"] = MockTradingProfile(
            handle="yolo_king",
            name="Lambo Soon",
            bio="100x or bust | Leverage everything | Moon mission commander | DYOR = Don't Yield On Risk 🎰",
            trading_style=TradingStyle.DEGEN,
            favorite_assets=["BTC", "ETH"],
            personality_traits=["reckless", "optimistic", "high-risk", "meme-focused"]
        )
        
        return profiles
    
    def get_profile(self, handle: str) -> MockTradingProfile:
        """Get a profile by handle."""
        return self.profiles.get(handle)
    
    def list_profiles(self) -> List[str]:
        """List available profile handles."""
        return list(self.profiles.keys())
    
    def simulate_daily_activity(self, market_data: Dict) -> Dict[str, List[str]]:
        """Simulate daily social media activity for all profiles."""
        
        daily_tweets = {}
        
        for handle, profile in self.profiles.items():
            # Each profile posts 1-3 tweets per day
            tweet_count = random.randint(1, 3)
            tweets = []
            
            for _ in range(tweet_count):
                tweet = profile.generate_tweet_based_on_market(market_data)
                tweets.append(tweet)
            
            daily_tweets[handle] = tweets
        
        return daily_tweets
    
    async def get_user_profile(self, handle: str) -> Dict:
        """Simulate fetching a user profile (async to match real API)."""
        profile = self.get_profile(handle)
        if not profile:
            raise ValueError(f"Profile {handle} not found")
        
        return {
            "handle": profile.handle,
            "name": profile.name,
            "bio": profile.bio,
            "tweet_texts": profile.get_recent_tweets(days=7)
        }
    
    async def get_user_tweets(self, handle: str, count: int = 20) -> List[Dict]:
        """Simulate fetching recent tweets (async to match real API)."""
        profile = self.get_profile(handle)
        if not profile:
            return []
        
        recent_tweets = profile.tweet_history[-count:]
        
        return [
            {
                "text": tweet["text"],
                "created_at": tweet["timestamp"].isoformat(),
                "likes": random.randint(0, 100),
                "retweets": random.randint(0, 20)
            }
            for tweet in recent_tweets
        ]