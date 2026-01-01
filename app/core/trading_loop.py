"""Automated trading loop for AI personas."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ..models import Account, TradeDecision, TradingDecisionLog, MarketContext
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
        
        # 4. Make AI trading decision with historical context
        try:
            balance_data = await self.rise_client.get_balance(account.address)
            available_balance = float(balance_data.get("cross_margin_balance", 1000.0))  # Default for testnet
            
            self.logger.info(f"   💰 Available balance: ${available_balance:.2f}")
            
            # Get trading history for decision making
            trading_history = self.storage.get_recent_successful_decisions(account.id, days=7)
            
            # Get recent social posts for context
            recent_posts = await self._get_recent_social_activity(persona.handle)
            
            # Use enhanced AI decision making if we have history or social data
            if trading_history or recent_posts:
                self.logger.info(f"   📚 Using {len(trading_history)} historical insights for decision making")
                decision = await self.ai_client.get_enhanced_trade_decision(
                    persona, market_data, current_positions, available_balance,
                    trading_history=trading_history, recent_posts=recent_posts
                )
            else:
                decision = await self.ai_client.get_trade_decision(
                    persona, market_data, current_positions, available_balance
                )
            
            # Create comprehensive decision log
            import uuid
            decision_log = TradingDecisionLog(
                id=str(uuid.uuid4()),
                account_id=account.id,
                persona_name=persona.name,
                market_context=MarketContext(
                    btc_price=market_data.get('btc_price', 0),
                    eth_price=market_data.get('eth_price', 0),
                    btc_change=market_data.get('btc_change', 0),
                    eth_change=market_data.get('eth_change', 0)
                ),
                available_balance=available_balance,
                current_positions=current_positions,
                total_pnl=total_pnl,
                recent_posts=recent_posts[:5] if recent_posts else [],
                decision=decision,
                executed=False
            )
            
            self.logger.info(f"   🤖 AI Decision: {decision.should_trade}")
            if decision.should_trade:
                self.logger.info(f"      📈 Action: {decision.action} {decision.market}")
                self.logger.info(f"      💵 Size: {decision.size_percent:.1%} of balance")
                self.logger.info(f"      🎯 Confidence: {decision.confidence:.1%}")
            self.logger.info(f"      💭 Reasoning: {decision.reasoning}")
            
            # 5. Execute trade if decision is positive
            if decision.should_trade and decision.confidence > 0.6:
                execution_result = await self._execute_trade_decision(account, decision, available_balance)
                decision_log.executed = bool(execution_result.get('success', False))
                decision_log.execution_details = execution_result
            else:
                if not decision.should_trade:
                    self.logger.info("   ⏭️  No trade action taken")
                else:
                    self.logger.info(f"   🤔 Confidence too low ({decision.confidence:.1%}), skipping trade")
            
            # Save decision log for future learning
            self.storage.save_trading_decision(decision_log)
            
        except AIClientError as e:
            self.logger.error(f"   ❌ AI decision error: {e}")
        except Exception as e:
            self.logger.error(f"   ❌ Unexpected error: {e}")
    
    async def _execute_trade_decision(self, account: Account, decision: TradeDecision, balance: float) -> Dict:
        """Execute a trading decision and return result."""
        if not decision.market or not decision.action:
            self.logger.warning("   ⚠️  Invalid trade decision - missing market or action")
            return {"success": False, "error": "Invalid decision"}
        
        # Get market ID from cache or lookup
        market_id = self.market_cache.get(f"{decision.market.lower()}_market_id")
        
        if not market_id:
            # Try to find in markets list
            for market in self.market_cache.get("markets", []):
                base_asset = market.get("base_asset_symbol", "")
                if "/" in base_asset and base_asset.split("/")[0] == decision.market:
                    market_id = int(market.get("market_id"))
                    break
        
        if not market_id:
            self.logger.warning(f"   ⚠️  Market {decision.market} not found")
            return {"success": False, "error": f"Market {decision.market} not found"}
        
        # Calculate trade size
        price_key = f"{decision.market.lower()}_price"
        trade_size = min(
            balance * decision.size_percent,
            self.max_position_usd / self.market_cache.get(price_key, 50000)  # Fallback price
        )
        
        current_price = self.market_cache.get(price_key, 0)
        
        if self.dry_run:
            self.logger.info(f"   🧪 DRY RUN: Would {decision.action} {trade_size:.6f} {decision.market} at ~${current_price:,.0f}")
            return {
                "success": True, 
                "dry_run": True, 
                "action": decision.action, 
                "market": decision.market,
                "size": trade_size,
                "price": current_price
            }
        
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
                
                return {
                    "success": True,
                    "order_id": order_id,
                    "trade_id": trade.id,
                    "action": decision.action,
                    "market": decision.market,
                    "size": trade_size,
                    "price": current_price
                }
                
            else:
                self.logger.error(f"   ❌ Order failed: {order_response}")
                return {
                    "success": False,
                    "error": "Order placement failed",
                    "response": order_response
                }
                
        except RiseAPIError as e:
            self.logger.error(f"   ❌ Trade execution error: {e}")
            return {"success": False, "error": f"API error: {e}"}
        except Exception as e:
            self.logger.error(f"   ❌ Unexpected trade error: {e}")
            return {"success": False, "error": f"Unexpected error: {e}"}
    
    async def _update_market_cache(self):
        """Update cached market data with real RISE API data."""
        try:
            # Use the enhanced method to get real market data
            enhanced_data = await self.rise_client.get_enhanced_market_data()
            
            # Update cache with real data
            self.market_cache.update(enhanced_data)
            self.market_cache["last_update"] = datetime.now()
            
            # Also get the full markets list for reference
            markets = await self.rise_client.get_markets()
            self.market_cache["markets"] = markets
            
            # Log the real market data
            if enhanced_data.get("btc_price"):
                self.logger.info(f"   📊 Real Market Data - BTC: ${enhanced_data['btc_price']:,.0f} ({enhanced_data.get('btc_change', 0):.1%})")
            if enhanced_data.get("eth_price"):
                self.logger.info(f"   📊 Real Market Data - ETH: ${enhanced_data['eth_price']:,.0f} ({enhanced_data.get('eth_change', 0):.1%})")
            
        except Exception as e:
            self.logger.error(f"Market cache update error: {e}")
            # Fallback to some default values if API fails
            self.market_cache.update({
                "btc_price": 95000,
                "eth_price": 3500,
                "btc_change": 0.0,
                "eth_change": 0.0
            })
    
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
            "btc_price": self.market_cache.get("btc_price", 95000),
            "eth_price": self.market_cache.get("eth_price", 3500),
            "btc_change": self.market_cache.get("btc_change", 0.0),
            "eth_change": self.market_cache.get("eth_change", 0.0),
        }
    
    def _format_positions_for_ai(self, positions: List[Dict]) -> Dict[str, float]:
        """Format positions for AI decision making."""
        formatted = {"BTC": 0.0, "ETH": 0.0}
        
        # Get market ID to symbol mapping from cache
        btc_market_id = self.market_cache.get("btc_market_id", 1)
        eth_market_id = self.market_cache.get("eth_market_id", 2)
        
        for position in positions:
            market_id = int(position.get("market_id", 0))
            size = float(position.get("size", 0))
            
            # Map market ID to symbol using real market data
            if market_id == btc_market_id:
                formatted["BTC"] = size
            elif market_id == eth_market_id:
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