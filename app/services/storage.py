"""Simple JSON file storage for the RISE AI trading bot."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..models import Account, Persona, Trade, TradingDecisionLog, TradingSession, Position
from ..pending_actions import PendingAction, ActionStatus


class StorageError(Exception):
    """Storage operation error."""
    pass


class JSONStorage:
    """Simple JSON file-based storage system."""
    
    def __init__(self, data_dir: str = None):
        # Use environment variable or default
        if data_dir is None:
            import os
            data_dir = os.environ.get("DATA_DIR", "data")
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Storage file paths
        self.accounts_file = self.data_dir / "accounts.json"
        self.chat_sessions_file = self.data_dir / "chat_sessions.json"
        self.profile_updates_file = self.data_dir / "profile_updates.json"
        self.trades_file = self.data_dir / "trades.json"
        self.personas_file = self.data_dir / "personas.json"
        self.decisions_file = self.data_dir / "trading_decisions.json"
        self.sessions_file = self.data_dir / "trading_sessions.json"
        self.pending_actions_file = self.data_dir / "pending_actions.json"
        self.positions_file = self.data_dir / "positions.json"
    
    def _load_json(self, file_path: Path) -> Dict:
        """Load JSON data from file with error recovery."""
        if not file_path.exists():
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            # Handle corrupted JSON by backing up and resetting
            print(f"WARNING: Corrupted JSON in {file_path.name}: {e}")
            backup_path = file_path.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            try:
                # Backup corrupted file
                import shutil
                shutil.copy2(file_path, backup_path)
                print(f"Backed up corrupted file to: {backup_path}")
                
                # Reset to empty JSON
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
                print(f"Reset {file_path.name} to empty JSON")
                
                return {}
            except Exception as backup_error:
                print(f"ERROR: Failed to backup/reset {file_path.name}: {backup_error}")
                # Return empty dict instead of crashing
                return {}
        except IOError as e:
            print(f"ERROR: IO error loading {file_path.name}: {e}")
            return {}
    
    def _save_json(self, file_path: Path, data: Dict) -> None:
        """Save JSON data to file."""
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write with pretty formatting
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str, ensure_ascii=False)
        except IOError as e:
            raise StorageError(f"Failed to save {file_path.name}: {e}")
    
    # Account management
    def save_account(self, account_id_or_obj, account_data=None) -> None:
        """Save account to storage. Can accept Account object or (account_id, account_dict)."""
        accounts = self._load_json(self.accounts_file)
        
        if isinstance(account_id_or_obj, Account):
            # Account object provided
            accounts[account_id_or_obj.id] = account_id_or_obj.model_dump()
        else:
            # account_id and dict provided
            accounts[account_id_or_obj] = account_data
            
        self._save_json(self.accounts_file, accounts)
    
    def get_account(self, account_id: str) -> Optional[Account]:
        """Get account by ID."""
        accounts = self._load_json(self.accounts_file)
        account_data = accounts.get(account_id)
        
        if not account_data:
            return None
        
        try:
            return Account(**account_data)
        except Exception as e:
            raise StorageError(f"Failed to load account {account_id}: {e}")
    
    def get_all_accounts(self) -> Dict[str, Dict]:
        """Get all accounts as raw dict data."""
        return self._load_json(self.accounts_file)
    
    def list_accounts(self) -> List[Account]:
        """List all accounts."""
        accounts = self._load_json(self.accounts_file)
        
        result = []
        for account_id, account_data in accounts.items():
            try:
                result.append(Account(**account_data))
            except Exception as e:
                print(f"Warning: Skipping corrupted account {account_id}: {e}")
                continue
        
        return result
    
    def delete_account(self, account_id: str) -> bool:
        """Delete account from storage."""
        accounts = self._load_json(self.accounts_file)
        
        if account_id not in accounts:
            return False
        
        del accounts[account_id]
        self._save_json(self.accounts_file, accounts)
        return True
    
    # Trade management
    def save_trade(self, trade: Trade) -> None:
        """Save trade to storage."""
        trades = self._load_json(self.trades_file)
        
        # Organize trades by account_id
        if trade.account_id not in trades:
            trades[trade.account_id] = []
        
        trades[trade.account_id].append(trade.model_dump())
        self._save_json(self.trades_file, trades)
    
    def get_trades(self, account_id: str, limit: int = 50) -> List[Trade]:
        """Get trades for account, most recent first."""
        trades = self._load_json(self.trades_file)
        account_trades = trades.get(account_id, [])
        
        # Sort by timestamp (most recent first) and limit
        sorted_trades = sorted(
            account_trades, 
            key=lambda t: t.get('timestamp', ''), 
            reverse=True
        )
        
        result = []
        for trade_data in sorted_trades[:limit]:
            try:
                result.append(Trade(**trade_data))
            except Exception as e:
                print(f"Warning: Skipping corrupted trade: {e}")
                continue
        
        return result
    
    def get_all_trades(self, limit: int = 100) -> List[Trade]:
        """Get all trades across all accounts."""
        trades = self._load_json(self.trades_file)
        
        all_trades = []
        for account_id, account_trades in trades.items():
            for trade_data in account_trades:
                try:
                    all_trades.append(Trade(**trade_data))
                except Exception as e:
                    print(f"Warning: Skipping corrupted trade: {e}")
                    continue
        
        # Sort by timestamp (most recent first) and limit
        all_trades.sort(key=lambda t: t.timestamp, reverse=True)
        return all_trades[:limit]
    
    # Persona management
    def save_persona(self, persona: Persona) -> None:
        """Save standalone persona."""
        personas = self._load_json(self.personas_file)
        personas[persona.handle] = persona.model_dump()
        self._save_json(self.personas_file, personas)
    
    def get_persona(self, handle: str) -> Optional[Persona]:
        """Get persona by handle."""
        personas = self._load_json(self.personas_file)
        persona_data = personas.get(handle)
        
        if not persona_data:
            return None
        
        try:
            return Persona(**persona_data)
        except Exception as e:
            raise StorageError(f"Failed to load persona {handle}: {e}")
    
    def list_personas(self) -> List[Persona]:
        """List all standalone personas."""
        personas = self._load_json(self.personas_file)
        
        result = []
        for handle, persona_data in personas.items():
            try:
                result.append(Persona(**persona_data))
            except Exception as e:
                print(f"Warning: Skipping corrupted persona {handle}: {e}")
                continue
        
        return result
    
    # Data validation and repair methods
    def validate_json_file(self, file_path: Path) -> bool:
        """Validate that a file contains valid JSON."""
        if not file_path.exists():
            return True  # Non-existent files are "valid"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True
        except Exception:
            return False
    
    def repair_all_data_files(self) -> Dict[str, str]:
        """Check and repair all data files, returning status for each."""
        results = {}
        data_files = [
            self.accounts_file,
            self.chat_sessions_file,
            self.profile_updates_file,
            self.trades_file,
            self.personas_file,
            self.decisions_file,
            self.sessions_file,
            self.pending_actions_file,
            self.positions_file,
            self.data_dir / "equity_snapshots.json",
            self.data_dir / "thought_processes.json",
            self.data_dir / "markets.json"
        ]
        
        for file_path in data_files:
            if not self.validate_json_file(file_path):
                # Force repair by trying to load
                self._load_json(file_path)
                results[file_path.name] = "repaired"
            else:
                results[file_path.name] = "valid"
        
        return results
    
    # Utility methods
    def get_stats(self) -> Dict:
        """Get storage statistics."""
        try:
            accounts = self.list_accounts()
            all_trades = self.get_all_trades()
            personas = self.list_personas()
            
            active_accounts = [a for a in accounts if a.is_active]
            recent_trades = [t for t in all_trades if t.timestamp.date() == datetime.now().date()]
            
            return {
                "total_accounts": len(accounts),
                "active_accounts": len(active_accounts),
                "total_trades": len(all_trades),
                "trades_today": len(recent_trades),
                "total_personas": len(personas),
                "data_files": {
                    "accounts": self.accounts_file.exists(),
                    "trades": self.trades_file.exists(),
                    "personas": self.personas_file.exists(),
                }
            }
        except Exception as e:
            return {"error": str(e)}
    
    def backup_data(self, backup_dir: str = "backups") -> str:
        """Create backup of all data files."""
        backup_path = Path(backup_dir)
        backup_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_subdir = backup_path / f"backup_{timestamp}"
        backup_subdir.mkdir()
        
        # Copy all data files
        files_backed_up = []
        for file_path in [self.accounts_file, self.trades_file, self.personas_file]:
            if file_path.exists():
                backup_file = backup_subdir / file_path.name
                backup_file.write_text(file_path.read_text())
                files_backed_up.append(file_path.name)
        
        return f"Backup created at {backup_subdir} with files: {', '.join(files_backed_up)}"
    
    # Trading decision logging
    def save_trading_decision(self, decision_log: TradingDecisionLog) -> None:
        """Save trading decision with full context."""
        decisions = self._load_json(self.decisions_file)
        
        # Organize by account_id
        if decision_log.account_id not in decisions:
            decisions[decision_log.account_id] = []
        
        decisions[decision_log.account_id].append(decision_log.model_dump())
        self._save_json(self.decisions_file, decisions)
    
    def get_trading_decisions(self, account_id: str, limit: int = 20) -> List[TradingDecisionLog]:
        """Get recent trading decisions for account."""
        decisions = self._load_json(self.decisions_file)
        account_decisions = decisions.get(account_id, [])
        
        # Sort by timestamp (most recent first) and limit
        sorted_decisions = sorted(
            account_decisions, 
            key=lambda d: d.get('timestamp', ''), 
            reverse=True
        )
        
        result = []
        for decision_data in sorted_decisions[:limit]:
            try:
                result.append(TradingDecisionLog(**decision_data))
            except Exception as e:
                print(f"Warning: Skipping corrupted decision: {e}")
                continue
        
        return result
    
    def get_recent_successful_decisions(self, account_id: str, days: int = 7) -> List[TradingDecisionLog]:
        """Get recent successful trading decisions for learning."""
        from datetime import timedelta
        
        decisions = self.get_trading_decisions(account_id, limit=100)
        cutoff_date = datetime.now() - timedelta(days=days)
        
        successful_decisions = []
        for decision in decisions:
            if (decision.timestamp >= cutoff_date and 
                decision.executed and 
                decision.outcome_tracked and 
                decision.outcome_pnl is not None and 
                decision.outcome_pnl > 0):
                successful_decisions.append(decision)
        
        return successful_decisions[:10]  # Return top 10 successful decisions
    
    def update_decision_outcome(self, decision_id: str, pnl: float, reasoning: str) -> bool:
        """Update the outcome of a trading decision."""
        decisions = self._load_json(self.decisions_file)
        
        for account_id, account_decisions in decisions.items():
            for decision_data in account_decisions:
                if decision_data.get('id') == decision_id:
                    decision_data['outcome_tracked'] = True
                    decision_data['outcome_pnl'] = pnl
                    decision_data['outcome_reasoning'] = reasoning
                    self._save_json(self.decisions_file, decisions)
                    return True
        
        return False
    
    # Trading session management
    def save_trading_session(self, session: TradingSession) -> None:
        """Save trading session."""
        sessions = self._load_json(self.sessions_file)
        
        if session.account_id not in sessions:
            sessions[session.account_id] = []
        
        # Update existing session or add new one
        for i, existing_session in enumerate(sessions[session.account_id]):
            if existing_session.get('id') == session.id:
                sessions[session.account_id][i] = session.model_dump()
                self._save_json(self.sessions_file, sessions)
                return
        
        # Add new session
        sessions[session.account_id].append(session.model_dump())
        self._save_json(self.sessions_file, sessions)
    
    def get_trading_sessions(self, account_id: str, limit: int = 10) -> List[TradingSession]:
        """Get recent trading sessions for account."""
        sessions = self._load_json(self.sessions_file)
        account_sessions = sessions.get(account_id, [])
        
        # Sort by start_time (most recent first) and limit
        sorted_sessions = sorted(
            account_sessions, 
            key=lambda s: s.get('start_time', ''), 
            reverse=True
        )
        
        result = []
        for session_data in sorted_sessions[:limit]:
            try:
                result.append(TradingSession(**session_data))
            except Exception as e:
                print(f"Warning: Skipping corrupted session: {e}")
                continue
        
        return result
    
    def get_trading_analytics(self, account_id: str) -> Dict:
        """Get trading analytics for an account."""
        decisions = self.get_trading_decisions(account_id, limit=100)
        sessions = self.get_trading_sessions(account_id, limit=20)
        
        # Calculate decision metrics
        total_decisions = len(decisions)
        executed_decisions = len([d for d in decisions if d.executed])
        tracked_decisions = len([d for d in decisions if d.outcome_tracked])
        profitable_decisions = len([d for d in decisions if d.outcome_tracked and d.outcome_pnl and d.outcome_pnl > 0])
        
        # Calculate session metrics
        total_sessions = len(sessions)
        profitable_sessions = len([s for s in sessions if s.session_pnl > 0])
        
        avg_decision_confidence = sum(d.decision.confidence for d in decisions) / total_decisions if total_decisions > 0 else 0
        avg_session_pnl = sum(s.session_pnl for s in sessions) / total_sessions if total_sessions > 0 else 0
        
        # Success rates
        execution_rate = executed_decisions / total_decisions if total_decisions > 0 else 0
        win_rate = profitable_decisions / tracked_decisions if tracked_decisions > 0 else 0
        session_win_rate = profitable_sessions / total_sessions if total_sessions > 0 else 0
        
        return {
            "total_decisions": total_decisions,
            "executed_decisions": executed_decisions,
            "tracked_decisions": tracked_decisions,
            "profitable_decisions": profitable_decisions,
            "execution_rate": execution_rate,
            "win_rate": win_rate,
            "avg_confidence": avg_decision_confidence,
            "total_sessions": total_sessions,
            "profitable_sessions": profitable_sessions,
            "session_win_rate": session_win_rate,
            "avg_session_pnl": avg_session_pnl,
        }
    
    # Pending actions management
    def save_pending_action(self, action: PendingAction) -> None:
        """Save pending action to storage."""
        actions = self._load_json(self.pending_actions_file)
        
        # Organize by account_id
        if action.account_id not in actions:
            actions[action.account_id] = {}
        
        actions[action.account_id][action.id] = action.model_dump()
        self._save_json(self.pending_actions_file, actions)
    
    def get_pending_action(self, action_id: str) -> Optional[PendingAction]:
        """Get pending action by ID."""
        actions = self._load_json(self.pending_actions_file)
        
        for account_id, account_actions in actions.items():
            if action_id in account_actions:
                try:
                    return PendingAction(**account_actions[action_id])
                except Exception as e:
                    print(f"Warning: Failed to load action {action_id}: {e}")
                    return None
        
        return None
    
    def get_pending_actions(self, account_id: str, status: Optional[ActionStatus] = None) -> List[PendingAction]:
        """Get pending actions for account, optionally filtered by status."""
        actions = self._load_json(self.pending_actions_file)
        account_actions = actions.get(account_id, {})
        
        result = []
        for action_id, action_data in account_actions.items():
            try:
                action = PendingAction(**action_data)
                if status is None or action.status == status:
                    result.append(action)
            except Exception as e:
                print(f"Warning: Skipping corrupted action {action_id}: {e}")
                continue
        
        # Sort by created_at (most recent first)
        result.sort(key=lambda a: a.created_at, reverse=True)
        return result
    
    def get_all_pending_actions(self) -> List[PendingAction]:
        """Get all pending actions across all accounts."""
        actions = self._load_json(self.pending_actions_file)
        
        result = []
        for account_id, account_actions in actions.items():
            for action_id, action_data in account_actions.items():
                try:
                    action = PendingAction(**action_data)
                    if action.status == ActionStatus.PENDING:
                        result.append(action)
                except Exception as e:
                    print(f"Warning: Skipping corrupted action {action_id}: {e}")
                    continue
        
        return result
    
    def update_pending_action_status(self, action_id: str, status: ActionStatus, **kwargs) -> bool:
        """Update pending action status with optional fields."""
        actions = self._load_json(self.pending_actions_file)
        
        for account_id, account_actions in actions.items():
            if action_id in account_actions:
                account_actions[action_id]["status"] = status.value
                
                # Update optional fields
                if status == ActionStatus.TRIGGERED and "triggered_at" not in kwargs:
                    account_actions[action_id]["triggered_at"] = datetime.now().isoformat()
                
                if status == ActionStatus.EXECUTED and "executed_at" not in kwargs:
                    account_actions[action_id]["executed_at"] = datetime.now().isoformat()
                
                for key, value in kwargs.items():
                    if key in ["triggered_at", "executed_at", "error_message", "result"]:
                        account_actions[action_id][key] = value
                
                self._save_json(self.pending_actions_file, actions)
                return True
        
        return False
    
    def cleanup_expired_actions(self, days_old: int = 7) -> int:
        """Remove old expired/cancelled/executed actions."""
        from datetime import timedelta
        
        actions = self._load_json(self.pending_actions_file)
        cutoff_date = datetime.now() - timedelta(days=days_old)
        removed_count = 0
        
        for account_id in list(actions.keys()):
            account_actions = actions[account_id]
            
            for action_id in list(account_actions.keys()):
                try:
                    action = PendingAction(**account_actions[action_id])
                    
                    # Remove old non-pending actions
                    if (action.status in [ActionStatus.EXPIRED, ActionStatus.CANCELLED, 
                                         ActionStatus.EXECUTED, ActionStatus.FAILED] and
                        action.created_at < cutoff_date):
                        del account_actions[action_id]
                        removed_count += 1
                        
                except Exception:
                    # Remove corrupted actions
                    del account_actions[action_id]
                    removed_count += 1
            
            # Remove empty accounts
            if not account_actions:
                del actions[account_id]
        
        self._save_json(self.pending_actions_file, actions)
        return removed_count
    
    # Chat and Profile Update Methods
    
    def save_chat_session(self, session_data: Dict) -> bool:
        """Save chat session data."""
        try:
            sessions = self._load_json(self.chat_sessions_file)
            session_id = session_data["session_id"]
            sessions[session_id] = session_data
            self._save_json(self.chat_sessions_file, sessions)
            return True
        except Exception:
            return False
    
    def get_chat_session(self, session_id: str) -> Optional[Dict]:
        """Get chat session by ID."""
        sessions = self._load_json(self.chat_sessions_file)
        return sessions.get(session_id)
    
    def update_profile_outlook(self, account_id: str, outlook_data: Dict) -> bool:
        """Update profile's market outlook."""
        try:
            updates = self._load_json(self.profile_updates_file)
            
            if account_id not in updates:
                updates[account_id] = {"outlooks": [], "biases": [], "traits": []}
            
            updates[account_id]["outlooks"].append(outlook_data)
            # Keep only last 20 outlooks
            updates[account_id]["outlooks"] = updates[account_id]["outlooks"][-20:]
            
            self._save_json(self.profile_updates_file, updates)
            return True
        except Exception:
            return False
    
    def update_profile_bias(self, account_id: str, bias_data: Dict) -> bool:
        """Update profile's trading bias."""
        try:
            updates = self._load_json(self.profile_updates_file)
            
            if account_id not in updates:
                updates[account_id] = {"outlooks": [], "biases": [], "traits": []}
            
            updates[account_id]["biases"].append(bias_data)
            # Keep only last 10 biases
            updates[account_id]["biases"] = updates[account_id]["biases"][-10:]
            
            self._save_json(self.profile_updates_file, updates)
            return True
        except Exception:
            return False
    
    def add_personality_trait(self, account_id: str, trait_data: Dict) -> bool:
        """Add personality trait update."""
        try:
            updates = self._load_json(self.profile_updates_file)
            
            if account_id not in updates:
                updates[account_id] = {"outlooks": [], "biases": [], "traits": []}
            
            updates[account_id]["traits"].append(trait_data)
            # Keep only last 15 traits
            updates[account_id]["traits"] = updates[account_id]["traits"][-15:]
            
            self._save_json(self.profile_updates_file, updates)
            return True
        except Exception:
            return False
    
    def get_profile_outlook(self, account_id: str) -> List[Dict]:
        """Get profile's market outlook updates."""
        updates = self._load_json(self.profile_updates_file)
        profile_updates = updates.get(account_id, {})
        return profile_updates.get("outlooks", [])
    
    def get_profile_bias(self, account_id: str) -> List[Dict]:
        """Get profile's trading bias updates."""
        updates = self._load_json(self.profile_updates_file)
        profile_updates = updates.get(account_id, {})
        return profile_updates.get("biases", [])
    
    def get_personality_traits(self, account_id: str) -> List[Dict]:
        """Get personality trait updates."""
        updates = self._load_json(self.profile_updates_file)
        profile_updates = updates.get(account_id, {})
        return profile_updates.get("traits", [])
    
    def get_last_chat_time(self, account_id: str) -> Optional[str]:
        """Get last chat time for account."""
        sessions = self._load_json(self.chat_sessions_file)
        
        last_time = None
        for session in sessions.values():
            if session.get("account_id") == account_id:
                session_time = session.get("last_updated")
                if not last_time or (session_time and session_time > last_time):
                    last_time = session_time
        
        return last_time
    
    def get_recent_trades(self, account_id: str, limit: int = 5) -> List[Dict]:
        """Get recent trades for account."""
        trades = self._load_json(self.trades_file)
        
        # Trades are stored as {account_id: [list of trades]}
        account_trades = trades.get(account_id, [])
        
        # Sort by timestamp and return recent ones
        sorted_trades = sorted(
            account_trades, 
            key=lambda x: x.get("timestamp", ""), 
            reverse=True
        )
        return sorted_trades[:limit]
    
    def get_profile_updates(self, account_id: str) -> Optional[Dict]:
        """Get profile updates for account."""
        updates = self._load_json(self.profile_updates_file)
        return updates.get(account_id, {})
    
    def save_profile_updates(self, account_id: str, updates: Dict) -> None:
        """Save profile updates for account."""
        all_updates = self._load_json(self.profile_updates_file)
        all_updates[account_id] = updates
        self._save_json(self.profile_updates_file, all_updates)
    
    # Position tracking methods
    def save_position_snapshot(self, position: Position) -> None:
        """Save a position snapshot for P&L tracking."""
        positions = self._load_json(self.positions_file)
        
        # Organize positions by account_id and timestamp
        if position.account_id not in positions:
            positions[position.account_id] = []
        
        # Add timestamp to make snapshots unique
        position_data = position.model_dump()
        position_data["snapshot_time"] = datetime.utcnow().isoformat()
        
        positions[position.account_id].append(position_data)
        self._save_json(self.positions_file, positions)
    
    def get_latest_positions(self, account_id: str) -> List[Position]:
        """Get the most recent position snapshot for an account."""
        positions = self._load_json(self.positions_file)
        account_positions = positions.get(account_id, [])
        
        if not account_positions:
            return []
        
        # Group by market and get latest for each
        latest_by_market = {}
        for pos_data in account_positions:
            market = pos_data.get("market")
            if market:
                if market not in latest_by_market or \
                   pos_data.get("snapshot_time", "") > latest_by_market[market].get("snapshot_time", ""):
                    latest_by_market[market] = pos_data
        
        # Convert to Position objects
        result = []
        for pos_data in latest_by_market.values():
            try:
                # Remove snapshot_time before creating Position
                pos_data_copy = pos_data.copy()
                pos_data_copy.pop("snapshot_time", None)
                result.append(Position(**pos_data_copy))
            except Exception as e:
                print(f"Warning: Skipping corrupted position: {e}")
        
        return result
    
    def update_trade_with_pnl(self, trade_id: str, account_id: str, pnl: float, realized_pnl: float = None) -> bool:
        """Update a trade with P&L information."""
        trades = self._load_json(self.trades_file)
        
        if account_id in trades:
            for i, trade_data in enumerate(trades[account_id]):
                if trade_data.get("id") == trade_id:
                    trade_data["pnl"] = pnl
                    if realized_pnl is not None:
                        trade_data["realized_pnl"] = realized_pnl
                    trade_data["pnl_updated_at"] = datetime.utcnow().isoformat()
                    
                    trades[account_id][i] = trade_data
                    self._save_json(self.trades_file, trades)
                    return True
        
        return False
    
    def get_total_pnl(self, account_id: str) -> Dict[str, float]:
        """Get total P&L for an account from latest positions."""
        positions = self.get_latest_positions(account_id)
        
        total_unrealized = sum(p.unrealized_pnl for p in positions)
        total_realized = sum(p.realized_pnl for p in positions)
        
        return {
            "unrealized_pnl": total_unrealized,
            "realized_pnl": total_realized,
            "total_pnl": total_unrealized + total_realized
        }
    
    def update_decision_outcome(self, decision_id: str, trade_id: str, pnl: float, status: str) -> None:
        """Update a trading decision with actual outcome."""
        decisions = self._load_json(self.trading_decisions_file)
        
        # Find and update the decision
        for account_id, account_decisions in decisions.items():
            for i, decision in enumerate(account_decisions):
                if decision.get("id") == decision_id:
                    decision["outcome_trade_id"] = trade_id
                    decision["outcome_pnl"] = pnl
                    decision["outcome_status"] = status
                    decision["outcome_timestamp"] = datetime.utcnow().isoformat()
                    decisions[account_id][i] = decision
                    self._save_json(self.trading_decisions_file, decisions)
                    return
    
    # Equity snapshot management
    def save_equity_snapshot(self, account_id: str, snapshot: Dict, limit: int = 200) -> None:
        """Save an equity snapshot for an account with history limit."""
        equity_file = self.data_dir / "equity_snapshots.json"
        snapshots = self._load_json(equity_file)
        
        if account_id not in snapshots:
            snapshots[account_id] = []
        
        # Add new snapshot
        snapshots[account_id].append(snapshot)
        
        # Trim to limit (keep most recent)
        if len(snapshots[account_id]) > limit:
            snapshots[account_id] = snapshots[account_id][-limit:]
        
        self._save_json(equity_file, snapshots)
    
    def get_equity_snapshots(self, account_id: str) -> List[Dict]:
        """Get equity snapshots for an account."""
        equity_file = self.data_dir / "equity_snapshots.json"
        snapshots = self._load_json(equity_file)
        return snapshots.get(account_id, [])
