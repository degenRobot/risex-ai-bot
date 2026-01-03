"""Parallel executor for trading profiles with tool calling support."""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from ..ai.prompt_loader_improved import get_improved_prompt_loader
from ..core.market_manager import get_market_manager
from ..models import Account
from ..pending_actions import ActionStatus, PendingAction, PendingActionSummary
from ..realtime.bus import publish_event
from ..realtime.events import (
    create_market_update,
    create_trade_decision,
)
from ..services.ai_client import AIClient
from ..services.ai_tools import TradingTools
from ..services.equity_monitor import get_equity_monitor
from ..services.rise_client import RiseClient
from ..services.storage import JSONStorage
from ..services.thought_process import ThoughtProcessManager
from ..trading.actions import ActionType, get_action_queue


class ParallelProfileExecutor:
    """Executes trading logic for multiple profiles in parallel."""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.market_manager = get_market_manager()
        self.equity_monitor = get_equity_monitor()
        self.storage = JSONStorage()
        self.rise_client = RiseClient()
        self.ai_client = AIClient()
        self.trading_tools = TradingTools(self.rise_client, self.storage, dry_run=dry_run)
        self.action_queue = get_action_queue()
        self.improved_loader = get_improved_prompt_loader()
        self.thought_process = ThoughtProcessManager()
        self.logger = logging.getLogger(__name__)
        
        # Log mode
        mode = "DRY RUN" if dry_run else "LIVE TRADING"
        self.logger.info(f"Parallel executor initialized in {mode} mode")
        
        # Execution state
        self.active_profiles: list[Account] = []
        self.is_running = False
        
        # Market rotation settings
        self.markets_per_cycle = 5  # Process 5 markets per cycle
        self.market_rotation_index = 0  # Track which markets to check
    
    async def initialize(self):
        """Initialize the executor with active profiles."""
        # Load active accounts with personas
        all_accounts = self.storage.list_accounts()
        self.active_profiles = [
            acc for acc in all_accounts 
            if acc.is_active and acc.persona
        ]
        
        self.logger.info(f"Loaded {len(self.active_profiles)} active profiles")
        for profile in self.active_profiles:
            self.logger.info(
                f"   - {profile.persona.name} (@{profile.persona.handle}) "
                f"- {profile.persona.trading_style.value}",
            )
        
        # Start background market updates
        await self.market_manager.start_background_updates()
        
        # Start background equity polling
        await self.equity_monitor.start_polling()
    
    async def shutdown(self):
        """Shutdown executor and cleanup background tasks."""
        self.logger.info("Shutting down parallel executor...")
        self.is_running = False
        
        # Stop background services
        await self.market_manager.stop_background_updates()
        await self.equity_monitor.stop_polling()
        
        self.logger.info("Parallel executor shutdown complete")
    
    async def run_cycle(self):
        """Run one complete trading cycle for all profiles."""
        start_time = datetime.now()
        self.logger.info(f"\nTrading Cycle Started - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 70)
        
        try:
            # 1. Get latest market data (shared by all)
            market_data = await self.market_manager.get_latest_data()
            market_summary = self.market_manager.get_market_summary()
            
            self.logger.info(f"Market: BTC {market_summary['btc']}, ETH {market_summary['eth']}")
            
            # Publish market update events
            if market_data.get("btc_price"):
                await publish_event(create_market_update(
                    symbol="BTC",
                    price=market_data.get("btc_price", 0),
                    change_24h=market_data.get("btc_change", 0),
                    volume_24h=market_data.get("btc_volume", 0),
                ))
            
            if market_data.get("eth_price"):
                await publish_event(create_market_update(
                    symbol="ETH",
                    price=market_data.get("eth_price", 0),
                    change_24h=market_data.get("eth_change", 0),
                    volume_24h=market_data.get("eth_volume", 0),
                ))
            
            # 2. Process each profile in parallel
            profile_tasks = []
            for profile in self.active_profiles:
                task = self._process_profile_safe(profile, market_data)
                profile_tasks.append(task)
            
            # Execute all profiles concurrently
            if profile_tasks:
                results = await asyncio.gather(*profile_tasks, return_exceptions=True)
                
                # Log results
                success_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
                error_count = sum(1 for r in results if isinstance(r, Exception))
                
                self.logger.info(
                    f"Profile processing: {success_count} successful, "
                    f"{error_count} errors",
                )
            
            # 3. Check all pending actions across profiles
            await self._check_all_pending_actions(market_data)
            
            # 4. Process trading action queue
            await self._process_action_queue()
            
            # 5. Cleanup old actions periodically
            if datetime.now().hour == 0 and datetime.now().minute < 5:
                removed = self.storage.cleanup_expired_actions()
                if removed > 0:
                    self.logger.info(f"Cleaned up {removed} expired actions")
            
        except Exception as e:
            self.logger.error(f"Trading cycle error: {e}")
            import traceback
            traceback.print_exc()
        
        duration = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"Cycle completed in {duration:.1f}s")
    
    async def _process_profile_safe(self, profile: Account, market_data: dict) -> dict:
        """Process single profile with error handling."""
        try:
            return await self._process_profile(profile, market_data)
        except Exception as e:
            self.logger.error(f"Error processing {profile.persona.name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_profile(self, profile: Account, market_data: dict) -> dict:
        """Process a single trading profile."""
        persona = profile.persona
        self.logger.info(f"\nProcessing {persona.name} (@{persona.handle})")
        
        # 1. Get current positions
        try:
            positions = await self.rise_client.get_all_positions(profile.address)
            position_count = len([p for p in positions if float(p.get("size", 0)) != 0])
            
            # Save position snapshots for tracking
            for pos_data in positions:
                if float(pos_data.get("size", 0)) != 0:  # Only save open positions
                    try:
                        from app.models import Position
                        position = Position(
                            account_id=profile.id,
                            market=pos_data.get("market", ""),
                            side=pos_data.get("side", ""),
                            size=float(pos_data.get("size", 0)),
                            entry_price=float(pos_data.get("avgPrice", 0)),
                            mark_price=float(pos_data.get("markPrice", 0)),
                            notional_value=float(pos_data.get("notionalValue", 0)),
                            unrealized_pnl=float(pos_data.get("unrealizedPnl", 0)),
                            realized_pnl=float(pos_data.get("realizedPnl", 0)),
                        )
                        self.storage.save_position_snapshot(position)
                    except Exception as e:
                        self.logger.warning(f"Failed to save position snapshot: {e}")
            
            # Calculate P&L
            pnl_data = await self.rise_client.calculate_pnl(profile.address)
            total_pnl = pnl_data.get("total_pnl", 0.0)
            
            self.logger.info(f"   Positions: {position_count}, P&L: ${total_pnl:+.2f}")
        except Exception:
            positions = []
            total_pnl = 0.0
            self.logger.info("   No positions found")
        
        # 2. Get pending actions for this profile
        pending_actions = self.storage.get_pending_actions(profile.id, ActionStatus.PENDING)
        action_summary = PendingActionSummary.from_actions(
            profile.id, persona.name, pending_actions,
        )
        
        if action_summary.pending > 0:
            self.logger.info(
                f"   Pending actions: {action_summary.pending} "
                f"({len(action_summary.stop_losses)} SL, "
                f"{len(action_summary.take_profits)} TP, "
                f"{len(action_summary.limit_orders)} limits)",
            )
        
        # 3. Get recent trade history for context
        recent_trades = self.storage.get_trades(profile.id, limit=10)
        recent_decisions = self.storage.get_recent_successful_decisions(profile.id, days=7)
        
        # 4. Get balance and equity
        try:
            balance_data = await self.rise_client.get_balance(profile.address)
            available_balance = float(balance_data.get("cross_margin_balance", 1000.0))
            self.logger.info(f"   Available balance: ${available_balance:.2f}")
        except Exception:
            available_balance = 1000.0  # Testnet default
        
        # Get latest equity from monitor
        equity_summary = self.equity_monitor.get_equity_summary()
        account_equity_data = self.equity_monitor.get_account_equity(profile.address)
        
        if account_equity_data:
            current_equity = account_equity_data["equity"]
            equity_age = (datetime.now() - account_equity_data["timestamp"]).total_seconds() / 60
            self.logger.info(f"   On-chain equity: ${current_equity:,.2f} (updated {equity_age:.0f}m ago)")
        else:
            current_equity = None
        
        # 5. Call AI with tools
        try:
            ai_response = await self._get_ai_decision_with_tools(
                profile=profile,
                market_data=market_data,
                positions=positions,
                pending_actions=action_summary,
                recent_trades=recent_trades,
                recent_decisions=recent_decisions,
                available_balance=available_balance,
                total_pnl=total_pnl,
                current_equity=current_equity,
            )
            
            # 6. Execute tool calls
            tool_results = []
            if hasattr(ai_response, "tool_calls") and ai_response.tool_calls:
                self.logger.info(f"   AI requested {len(ai_response.tool_calls)} tool calls")
                
                for tool_call in ai_response.tool_calls:
                    try:
                        result = await self._execute_tool_call(profile, tool_call)
                        tool_results.append(result)
                        
                        if result.get("success"):
                            self.logger.info(f"      [OK] {tool_call.function.name}: Success")
                        else:
                            self.logger.warning(
                                f"      [WARN] {tool_call.function.name}: "
                                f"{result.get('error', 'Failed')}",
                            )
                    except Exception as e:
                        self.logger.error(f"      [ERROR] Tool call error: {e}")
                        tool_results.append({"success": False, "error": str(e)})
            else:
                self.logger.info("   AI decision: No action needed")
            
            # Log AI reasoning if available
            if hasattr(ai_response, "content") and ai_response.content:
                self.logger.info(f"   Reasoning: {ai_response.content[:200]}...")
            
            return {
                "success": True,
                "profile": persona.handle,
                "tool_calls": len(tool_results),
                "tool_results": tool_results,
            }
            
        except Exception as e:
            self.logger.error(f"   AI decision error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_ai_decision_with_tools(
        self, profile: Account, market_data: dict, positions: list[dict],
        pending_actions: PendingActionSummary, recent_trades: list,
        recent_decisions: list, available_balance: float, total_pnl: float,
        current_equity: Optional[float] = None,
    ):
        """Get AI decision using OpenRouter with tool calling."""
        persona = profile.persona
        
        # Format positions for AI
        position_summary = self._format_positions(positions)
        
        # Format pending actions
        pending_summary = self._format_pending_actions(pending_actions)
        
        # Build equity info
        equity_info = ""
        if current_equity is not None:
            equity_info = f"\n- On-chain Equity: ${current_equity:,.2f} (live from blockchain)"
            # Add equity change info if available
            account = self.storage.get_account(profile.id)
            if account and account.equity_change_1h is not None:
                equity_info += f"\n- Equity Change (1h): {account.equity_change_1h:+.1f}%"
            if account and account.equity_change_24h is not None:
                equity_info += f"\n- Equity Change (24h): {account.equity_change_24h:+.1f}%"
        
        # Build system prompt using improved prompts
        # Get thought summary and influences
        thought_summary = await self.thought_process.summarize_thoughts(
            profile.id, for_purpose="trading_decision",
        )
        influences = await self.thought_process.get_trading_influences(profile.id)
        
        # Convert persona to dict for improved loader
        persona_dict = {
            "name": persona.name,
            "personality_traits": persona.personality_traits,
            "trading_style": persona.trading_style.value,
            "risk_tolerance": persona.risk_tolerance,
            "favorite_assets": persona.favorite_assets,
            "personality_type": self._get_personality_type(persona),
        }
        
        # Enhanced trading context with all data
        trading_context = {
            "current_equity": current_equity,
            "free_margin": available_balance,
            "open_positions": len(positions),
            "current_pnl": total_pnl,
            "btc_price": market_data.get("btc_price", 0),
            "eth_price": market_data.get("eth_price", 0),
            "btc_change": market_data.get("btc_change", 0),
            "eth_change": market_data.get("eth_change", 0),
            "positions": positions,
            "markets": self._load_markets_data(),
            "win_rate": self._calculate_win_rate(recent_trades),
        }
        
        # Get base prompt from improved system
        base_prompt = self.improved_loader.build_system_prompt(
            persona_dict,
            trading_context, 
            thought_summary,
            influences,
        )
        
        # Add specific trading context
        context_addition = f"""

## Current Trading Context

### Market Data:
- BTC: ${market_data.get('btc_price', 0):,.0f} ({market_data.get('btc_change', 0):+.1%} 24h)
- ETH: ${market_data.get('eth_price', 0):,.0f} ({market_data.get('eth_change', 0):+.1%} 24h)
- SOL: ${market_data.get('sol_price', 0):,.2f} ({market_data.get('sol_change', 0):+.1%} 24h)

### Your Portfolio:
- Available Balance: ${available_balance:,.2f}
- Total P&L: ${total_pnl:+.2f}{equity_info}
- Current Positions: {position_summary}
- Pending Actions: {pending_summary}

### Trading Performance:
- Recent Successful Strategies: {len(recent_decisions)} profitable trades in the last 7 days
- Win Rate: {self._calculate_win_rate(recent_trades)}%

### Trading Instructions:
Use the provided tools to execute your trading strategy. Follow the active trading guidelines:
1. Check multiple markets (rotate through BTC, ETH, SOL, etc)
2. Make decisive trades based on your personality and risk tolerance
3. Set stop losses and take profits for risk management
4. Aim for at least 1-2 trades per cycle when opportunities exist

REMEMBER: You are an ACTIVE trader. Don't just observe - TRADE!"""
        
        system_prompt = base_prompt + context_addition
        
        # Call AI with tools
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Analyze the market and make trading decisions based on your style and current portfolio."},
        ]
        
        response = await self.ai_client.client.chat.completions.create(
            model=self.ai_client.model,
            messages=messages,
            tools=self.trading_tools.tools_schema,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=1000,
        )
        
        return response.choices[0].message
    
    async def _execute_tool_call(self, profile: Account, tool_call) -> dict:
        """Execute a single tool call."""
        try:
            # Parse tool call arguments
            import json
            if isinstance(tool_call.function.arguments, str):
                arguments = json.loads(tool_call.function.arguments)
            else:
                arguments = tool_call.function.arguments
            
            # Execute the tool
            result = await self.trading_tools.execute_tool_call(
                tool_name=tool_call.function.name,
                arguments=arguments,
                account_id=profile.id,
                persona_name=profile.persona.name,
                account_key=profile.private_key,
                signer_key=profile.signer_key,
            )
            
            # Publish trade decision events
            if result.get("success") and tool_call.function.name in ["place_market_order", "place_limit_order"]:
                await publish_event(create_trade_decision(
                    profile_id=profile.id,
                    trader_name=profile.persona.name,
                    market=arguments.get("market", "Unknown"),
                    action=arguments.get("side", "Unknown"),
                    size=arguments.get("size", arguments.get("size_percent", 0)),
                    reason=arguments.get("reason", "Trading decision"),
                    confidence=arguments.get("confidence", 0.7),
                ))
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _check_all_pending_actions(self, market_data: dict):
        """Check and execute triggered pending actions."""
        all_pending = self.storage.get_all_pending_actions()
        
        if not all_pending:
            return
        
        self.logger.info(f"\nChecking {len(all_pending)} pending actions...")
        
        # Build trigger context with market data
        trigger_context = {
            "btc_price": market_data.get("btc_price", 0),
            "eth_price": market_data.get("eth_price", 0),
            **market_data,
        }
        
        triggered_count = 0
        for action in all_pending:
            if action.should_trigger(trigger_context):
                triggered_count += 1
                await self._execute_pending_action(action, trigger_context)
        
        if triggered_count > 0:
            self.logger.info(f"   Triggered {triggered_count} actions")
    
    async def _execute_pending_action(self, action: PendingAction, context: dict):
        """Execute a triggered pending action."""
        self.logger.info(
            f"   Executing {action.action_type.value} for "
            f"{action.persona_name}: {action.reasoning}",
        )
        
        # Mark as triggered
        action.mark_triggered()
        self.storage.save_pending_action(action)
        
        try:
            # Get account details
            account = self.storage.get_account(action.account_id)
            if not account:
                raise ValueError("Account not found")
            
            # Execute based on action type
            if action.action_type in ["stop_loss", "take_profit", "close_position"]:
                result = await self._execute_close_action(account, action)
            elif action.action_type in ["limit_order", "market_order"]:
                result = await self._execute_order_action(account, action)
            else:
                result = {"success": False, "error": "Unknown action type"}
            
            if result.get("success"):
                action.mark_executed(result)
                self.logger.info("      Action executed successfully")
            else:
                action.mark_failed(result.get("error", "Unknown error"))
                self.logger.error(f"      Action failed: {result.get('error')}")
            
        except Exception as e:
            action.mark_failed(str(e))
            self.logger.error(f"      Action execution error: {e}")
        
        # Save updated action
        self.storage.save_pending_action(action)
    
    async def _execute_close_action(self, account: Account, action: PendingAction) -> dict:
        """Execute position close action."""
        params = action.action_params
        
        return await self.trading_tools._close_position(
            account_id=account.id,
            persona_name=account.persona.name,
            account_key=account.private_key,
            signer_key=account.signer_key,
            market=params.market,
            percent=params.reduce_percent or 100,
        )
    
    async def _execute_order_action(self, account: Account, action: PendingAction) -> dict:
        """Execute order placement action."""
        params = action.action_params
        
        if action.action_type == "market_order":
            return await self.trading_tools._place_market_order(
                account_id=account.id,
                persona_name=account.persona.name,
                account_key=account.private_key,
                signer_key=account.signer_key,
                market=params.market,
                side=params.side,
                size_percent=params.size_percent,
            )
        else:
            return await self.trading_tools._place_limit_order(
                account_id=account.id,
                persona_name=account.persona.name,
                account_key=account.private_key,
                signer_key=account.signer_key,
                market=params.market,
                side=params.side,
                size_percent=params.size_percent,
                price=params.price,
            )
    
    def _format_positions(self, positions: list[dict]) -> str:
        """Format positions for AI context."""
        if not positions:
            return "No open positions"
        
        active_positions = []
        for pos in positions:
            size = float(pos.get("size", 0))
            if size != 0:
                market_id = pos.get("market_id")
                entry_price = float(pos.get("entry_price", 0))
                # Map market ID to symbol (simplified)
                symbol = "BTC" if market_id == 1 else "ETH" if market_id == 2 else f"Market{market_id}"
                side = "Long" if size > 0 else "Short"
                active_positions.append(f"{symbol} {side} {abs(size):.4f} @ ${entry_price:,.0f}")
        
        return ", ".join(active_positions) if active_positions else "No open positions"
    
    def _format_pending_actions(self, summary: PendingActionSummary) -> str:
        """Format pending actions for AI context."""
        if summary.pending == 0:
            return "None"
        
        parts = []
        if summary.stop_losses:
            parts.append(f"{len(summary.stop_losses)} stop losses")
        if summary.take_profits:
            parts.append(f"{len(summary.take_profits)} take profits")
        if summary.limit_orders:
            parts.append(f"{len(summary.limit_orders)} limit orders")
        if summary.other_actions:
            parts.append(f"{len(summary.other_actions)} other")
        
        return f"{summary.pending} total ({', '.join(parts)})"
    
    def _get_personality_type(self, persona) -> str:
        """Map persona to personality type."""
        # Map based on personality traits or style
        if any(trait in ["skeptical", "contrarian", "analytical"] for trait in persona.personality_traits):
            return "cynical"
        elif any(trait in ["impulsive", "optimistic", "enthusiastic"] for trait in persona.personality_traits):
            return "leftCurve"
        else:
            return "midwit"
    
    def _calculate_win_rate(self, recent_trades: list) -> float:
        """Calculate win rate from recent trades."""
        if not recent_trades:
            return 0.0
        
        winning_trades = sum(1 for trade in recent_trades if trade.get("pnl", 0) > 0)
        return (winning_trades / len(recent_trades)) * 100 if recent_trades else 0.0
    
    def _load_markets_data(self) -> dict:
        """Load markets data from file."""
        try:
            from pathlib import Path
            markets_path = Path("data/markets.json")
            if markets_path.exists():
                import json
                with open(markets_path) as f:
                    data = json.load(f)
                    return data.get("markets", {})
        except Exception as e:
            self.logger.error(f"Error loading markets: {e}")
        return {}
    
    async def _process_action_queue(self):
        """Process pending actions from the trading queue."""
        queue_stats = self.action_queue.get_queue_stats()
        if queue_stats["total_actions"] == 0:
            return
            
        self.logger.info(f"\nProcessing action queue: {queue_stats['ready_count']} ready actions")
        
        for profile in self.active_profiles:
            # Get next action for this profile
            action = await self.action_queue.get_next_action(profile.id)
            
            if action:
                self.logger.info(f"   Executing {action.action_type.value} for {profile.persona.name}: {action.symbol}")
                
                try:
                    # Convert queue action to tool call
                    if action.action_type == ActionType.MARKET_ORDER:
                        result = await self.trading_tools.execute_tool_call(
                            tool_name="place_market_order",
                            arguments={
                                "market": action.symbol,
                                "side": action.side,
                                "size": action.size,
                                "reason": action.reasoning,
                            },
                            account_id=profile.id,
                            persona_name=profile.persona.name,
                            account_key=profile.private_key,
                            signer_key=profile.signer_key,
                        )
                    elif action.action_type == ActionType.LIMIT_ORDER:
                        result = await self.trading_tools.execute_tool_call(
                            tool_name="place_limit_order",
                            arguments={
                                "market": action.symbol,
                                "side": action.side,
                                "size": action.size,
                                "price": action.price,
                                "reason": action.reasoning,
                            },
                            account_id=profile.id,
                            persona_name=profile.persona.name,
                            account_key=profile.private_key,
                            signer_key=profile.signer_key,
                        )
                    elif action.action_type == ActionType.CLOSE_POSITION:
                        result = await self.trading_tools.execute_tool_call(
                            tool_name="close_position",
                            arguments={
                                "market": action.symbol,
                                "reason": action.reasoning,
                            },
                            account_id=profile.id,
                            persona_name=profile.persona.name,
                            account_key=profile.private_key,
                            signer_key=profile.signer_key,
                        )
                    else:
                        result = {"success": False, "error": f"Unsupported action type: {action.action_type}"}
                    
                    # Mark action as executed
                    await self.action_queue.mark_executed(
                        action.id,
                        success=result.get("success", False),
                        error=result.get("error"),
                    )
                    
                    if result.get("success"):
                        self.logger.info("      ✓ Action executed successfully")
                    else:
                        self.logger.warning(f"      ✗ Action failed: {result.get('error')}")
                        
                except Exception as e:
                    self.logger.error(f"      ✗ Error executing action: {e}")
                    await self.action_queue.mark_executed(action.id, success=False, error=str(e))