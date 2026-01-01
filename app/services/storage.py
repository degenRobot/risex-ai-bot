"""Simple JSON file storage for the RISE AI trading bot."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..models import Account, Persona, Trade, TradingDecisionLog, TradingSession
from ..models.pending_actions import PendingAction, ActionStatus


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
        self.trades_file = self.data_dir / "trades.json"
        self.personas_file = self.data_dir / "personas.json"
        self.decisions_file = self.data_dir / "trading_decisions.json"
        self.sessions_file = self.data_dir / "trading_sessions.json"
        self.pending_actions_file = self.data_dir / "pending_actions.json"
    
    def _load_json(self, file_path: Path) -> Dict:
        """Load JSON data from file."""
        if not file_path.exists():
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise StorageError(f"Failed to load {file_path.name}: {e}")
    
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
    def save_account(self, account: Account) -> None:
        """Save account to storage."""
        accounts = self._load_json(self.accounts_file)
        accounts[account.id] = account.model_dump()
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