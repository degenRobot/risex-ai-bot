"""Simple JSON file storage for the RISE AI trading bot."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..models import Account, Persona, Trade


class StorageError(Exception):
    """Storage operation error."""
    pass


class JSONStorage:
    """Simple JSON file-based storage system."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Storage file paths
        self.accounts_file = self.data_dir / "accounts.json"
        self.trades_file = self.data_dir / "trades.json"
        self.personas_file = self.data_dir / "personas.json"
    
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