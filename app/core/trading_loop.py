"""Automated trading loop for AI personas."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ..models import Account, TradeDecision
from ..services.ai_client import AIClient, AIClientError
from ..services.rise_client import RiseClient, RiseAPIError
from ..services.mock_social import MockSocialClient
from ..services.storage import JSONStorage


class TradingBot:
    """Automated trading bot managing multiple AI personas."""
    
    def __init__(
        self,
        interval_seconds: int = 60,
        max_position_usd: float = 100.0,
        dry_run: bool = True
    ):
        self.interval_seconds = interval_seconds
        self.max_position_usd = max_position_usd
        self.dry_run = dry_run
        
        # Initialize services
        self.storage = JSONStorage()
        self.ai_client = AIClient()
        self.rise_client = RiseClient()
        self.mock_social = MockSocialClient()
        
        # Bot state
        self.is_running = False
        self.active_accounts: List[Account] = []
        self.market_cache: Dict = {}
        self.last_social_update = datetime.now()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        if dry_run:
            self.logger.info("🧪 Trading bot initialized in DRY RUN mode")
        else:
            self.logger.info("🚨 Trading bot initialized in LIVE mode")
    
    async def initialize(self):
        """Initialize the trading bot."""
        self.logger.info("🚀 Initializing trading bot...")
        
        # Load active accounts
        all_accounts = self.storage.list_accounts()
        self.active_accounts = [acc for acc in all_accounts if acc.is_active and acc.persona]
        
        self.logger.info(f"📋 Loaded {len(self.active_accounts)} active trading accounts")
        for acc in self.active_accounts:
            self.logger.info(f"   • {acc.persona.name} (@{acc.persona.handle}) - {acc.persona.trading_style.value}")
        
        # Cache market data
        await self._update_market_cache()
        
        self.logger.info("✅ Trading bot initialization complete")
    
    async def run(self):
        """Main trading loop."""
        if self.is_running:
            self.logger.warning("Bot is already running!")
            return
        
        await self.initialize()
        
        if not self.active_accounts:
            self.logger.error("❌ No active accounts found! Create accounts first.")
            return
        
        self.is_running = True
        self.logger.info(f"🔄 Starting trading loop (interval: {self.interval_seconds}s)")
        
        try:
            iteration = 0
            while self.is_running:
                iteration += 1
                start_time = datetime.now()
                
                self.logger.info(f"\n🔄 Trading Loop Iteration #{iteration} - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                self.logger.info("=" * 60)
                
                # Update market data
                await self._update_market_cache()
                
                # Update social activity (every 5 minutes)
                if datetime.now() - self.last_social_update > timedelta(minutes=5):
                    await self._update_social_activity()
                    self.last_social_update = datetime.now()
                
                # Process each account
                for account in self.active_accounts:
                    try:
                        await self._process_account(account)
                    except Exception as e:
                        self.logger.error(f"❌ Error processing account {account.persona.name}: {e}")
                        continue
                
                # Calculate loop duration and sleep
                duration = (datetime.now() - start_time).total_seconds()
                self.logger.info(f"⏱️  Loop iteration completed in {duration:.1f}s")
                
                if self.interval_seconds > duration:
                    sleep_time = self.interval_seconds - duration
                    self.logger.info(f"😴 Sleeping for {sleep_time:.1f}s until next iteration...")
                    await asyncio.sleep(sleep_time)
                
        except KeyboardInterrupt:
            self.logger.info("⚠️  Received interrupt signal")
        except Exception as e:
            self.logger.error(f"❌ Trading loop error: {e}")
        finally:
            self.is_running = False
            await self.cleanup()
    
    async def _process_account(self, account: Account):
        """Process a single trading account."""
        persona = account.persona
        self.logger.info(f"\n👤 Processing {persona.name} (@{persona.handle})")
        
        # 1. Get new social activity
        new_tweets = await self._get_recent_social_activity(persona.handle)
        if new_tweets:
            self.logger.info(f"   📱 New tweets: {len(new_tweets)}")
            for tweet in new_tweets[-2:]:  # Show last 2 tweets
                self.logger.info(f"      💬 \"{tweet[:80]}{'...' if len(tweet) > 80 else ''}\"")
        
        # 2. Get current positions and P&L
        try:
            positions = await self.rise_client.get_all_positions(account.address)
            pnl_data = await self.rise_client.calculate_pnl(account.address)
            
            total_pnl = pnl_data.get("total_pnl", 0.0)
            position_count = len([p for p in positions if float(p.get("size", 0)) != 0])
            
            self.logger.info(f"   📊 Positions: {position_count}, P&L: ${total_pnl:+.2f}")
            
        except RiseAPIError as e:
            if "not found" in str(e).lower():
                self.logger.info("   📊 No positions found (new account)")
                total_pnl = 0.0
                positions = []
            else:
                self.logger.warning(f"   ⚠️  Position check error: {e}")
                return
        
        # 3. Get market data for decision making
        market_data = self._get_current_market_data()
        current_positions = self._format_positions_for_ai(positions)
        
        # 4. Make AI trading decision
        try:
            balance_data = await self.rise_client.get_balance(account.address)
            available_balance = float(balance_data.get("cross_margin_balance", 1000.0))  # Default for testnet
            
            self.logger.info(f"   💰 Available balance: ${available_balance:.2f}")
            
            decision = await self.ai_client.get_trade_decision(
                persona, market_data, current_positions, available_balance
            )
            
            self.logger.info(f"   🤖 AI Decision: {decision.should_trade}")
            if decision.should_trade:
                self.logger.info(f"      📈 Action: {decision.action} {decision.market}")
                self.logger.info(f"      💵 Size: {decision.size_percent:.1%} of balance")
                self.logger.info(f"      🎯 Confidence: {decision.confidence:.1%}")
            self.logger.info(f"      💭 Reasoning: {decision.reasoning}")
            
            # 5. Execute trade if decision is positive
            if decision.should_trade and decision.confidence > 0.6:
                await self._execute_trade_decision(account, decision, available_balance)
            else:
                if not decision.should_trade:
                    self.logger.info("   ⏭️  No trade action taken")
                else:
                    self.logger.info(f"   🤔 Confidence too low ({decision.confidence:.1%}), skipping trade")
            
        except AIClientError as e:
            self.logger.error(f"   ❌ AI decision error: {e}")
        except Exception as e:
            self.logger.error(f"   ❌ Unexpected error: {e}")
    
    async def _execute_trade_decision(self, account: Account, decision: TradeDecision, balance: float):
        """Execute a trading decision."""
        if not decision.market or not decision.action:
            self.logger.warning("   ⚠️  Invalid trade decision - missing market or action")
            return
        
        # Get market ID
        market_id = None
        for market in self.market_cache.get("markets", []):
            if market.get("symbol") == decision.market:
                market_id = int(market.get("market_id"))
                break
        
        if not market_id:
            self.logger.warning(f"   ⚠️  Market {decision.market} not found")
            return
        
        # Calculate trade size
        trade_size = min(
            balance * decision.size_percent,
            self.max_position_usd / self.market_cache.get(f"{decision.market}_price", 50000)  # Fallback price
        )
        
        current_price = self.market_cache.get(f"{decision.market}_price", 0)
        
        if self.dry_run:
            self.logger.info(f"   🧪 DRY RUN: Would {decision.action} {trade_size:.6f} {decision.market} at ~${current_price:,.0f}")
            return
        
        # Execute real trade
        try:
            self.logger.info(f"   📋 Placing {decision.action} order: {trade_size:.6f} {decision.market}")
            
            order_response = await self.rise_client.place_order(
                account_key=account.private_key,
                signer_key=account.signer_key,
                market_id=market_id,
                size=trade_size,
                price=current_price * 1.01 if decision.action == "buy" else current_price * 0.99,  # Small slippage
                side=decision.action,
                order_type="limit"
            )
            
            if order_response.get("success"):
                self.logger.info(f"   ✅ Order placed successfully!")
                order_id = order_response.get("data", {}).get("order_id")
                if order_id:
                    self.logger.info(f"      🆔 Order ID: {order_id}")
                
                # Save trade record
                from ..models import Trade
                import uuid
                trade = Trade(
                    id=str(uuid.uuid4()),
                    account_id=account.id,
                    market_id=market_id,
                    side=decision.action,
                    size=trade_size,
                    price=current_price,
                    reasoning=decision.reasoning,
                    timestamp=datetime.now(),
                    status="submitted"
                )
                self.storage.save_trade(trade)
                
            else:
                self.logger.error(f"   ❌ Order failed: {order_response}")
                
        except RiseAPIError as e:
            self.logger.error(f"   ❌ Trade execution error: {e}")
        except Exception as e:
            self.logger.error(f"   ❌ Unexpected trade error: {e}")
    
    async def _update_market_cache(self):
        """Update cached market data."""
        try:
            markets = await self.rise_client.get_markets()
            self.market_cache["markets"] = markets
            self.market_cache["last_update"] = datetime.now()
            
            # Get latest prices for BTC and ETH
            for market in markets:
                symbol = market.get("symbol")
                market_id = int(market.get("market_id", 0))
                
                if symbol in ["BTC", "ETH"]:
                    try:
                        price = await self.rise_client.get_latest_price(market_id)
                        if price:
                            self.market_cache[f"{symbol}_price"] = price
                            
                            # Calculate 24h change (mock for now)
                            # In production, you'd compare with previous day's data
                            change = (price - 90000) / 90000 if symbol == "BTC" else (price - 3000) / 3000
                            self.market_cache[f"{symbol}_change"] = min(max(change, -0.3), 0.3)  # Cap at ±30%
                    except Exception:
                        pass
            
        except Exception as e:
            self.logger.error(f"Market cache update error: {e}")
    
    async def _update_social_activity(self):
        """Update social media activity for all profiles."""
        market_data = self._get_current_market_data()
        
        self.logger.info("📱 Updating social media activity...")
        social_updates = self.mock_social.simulate_daily_activity(market_data)
        
        # Log some interesting tweets
        for handle, tweets in social_updates.items():
            if tweets:
                self.logger.info(f"   @{handle}: \"{tweets[0][:60]}{'...' if len(tweets[0]) > 60 else ''}\"")
    
    async def _get_recent_social_activity(self, handle: str) -> List[str]:
        """Get recent social activity for a handle."""
        try:
            profile_data = await self.mock_social.get_user_profile(handle)
            return profile_data.get("tweet_texts", [])[-5:]  # Last 5 tweets
        except Exception:
            return []
    
    def _get_current_market_data(self) -> Dict:
        """Format current market data for AI decision making."""
        return {
            "btc_price": self.market_cache.get("BTC_price", 95000),
            "eth_price": self.market_cache.get("ETH_price", 3500),
            "btc_change": self.market_cache.get("BTC_change", 0.0),
            "eth_change": self.market_cache.get("ETH_change", 0.0),
        }
    
    def _format_positions_for_ai(self, positions: List[Dict]) -> Dict[str, float]:
        """Format positions for AI decision making."""
        formatted = {"BTC": 0.0, "ETH": 0.0}
        
        for position in positions:
            market_id = int(position.get("market_id", 0))
            size = float(position.get("size", 0))
            
            # Map market ID to symbol (simplified)
            if market_id == 1:  # Assuming market 1 is BTC
                formatted["BTC"] = size
            elif market_id == 2:  # Assuming market 2 is ETH
                formatted["ETH"] = size
        
        return formatted
    
    async def stop(self):
        """Stop the trading loop."""
        self.logger.info("🛑 Stopping trading bot...")
        self.is_running = False
    
    async def cleanup(self):
        """Cleanup resources."""
        self.logger.info("🧹 Cleaning up trading bot resources...")
        await self.rise_client.close()
        self.logger.info("✅ Trading bot stopped cleanly")
    
    def get_status(self) -> Dict:
        """Get current bot status."""
        return {
            "is_running": self.is_running,
            "active_accounts": len(self.active_accounts),
            "dry_run": self.dry_run,
            "interval_seconds": self.interval_seconds,
            "last_market_update": self.market_cache.get("last_update"),
            "current_prices": {
                "BTC": self.market_cache.get("BTC_price"),
                "ETH": self.market_cache.get("ETH_price"),
            }
        }