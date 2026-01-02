"""Thought process management for AI traders."""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
import uuid

from .storage import JSONStorage


@dataclass
class ThoughtEntry:
    """Single thought process entry."""
    id: str
    account_id: str
    timestamp: datetime
    entry_type: str  # chat_influence, trading_decision, market_observation
    source: str      # user_message, market_analysis, price_action, chat_response
    content: str     # What happened or was realized
    impact: Optional[str] = None  # How it affects future decisions
    confidence: float = 0.5  # Confidence in this thought (0-1)
    details: Optional[Dict] = None  # Additional context
    related_entries: List[str] = None  # IDs of related thoughts
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['related_entries'] = self.related_entries or []
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ThoughtEntry':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class ThoughtProcessManager:
    """Manages shared thought process across chat and trading."""
    
    def __init__(self, storage_path: Path = Path("data")):
        self.storage_path = storage_path
        self.storage_path.mkdir(exist_ok=True)
        self.thoughts_file = self.storage_path / "thought_processes.json"
        self._lock = asyncio.Lock()
        self._thoughts_cache: Dict[str, List[ThoughtEntry]] = {}
        
    async def add_entry(
        self,
        account_id: str,
        entry_type: str,
        source: str,
        content: str,
        impact: Optional[str] = None,
        confidence: float = 0.5,
        details: Optional[Dict] = None,
        related_entries: Optional[List[str]] = None
    ) -> ThoughtEntry:
        """Add new thought process entry."""
        
        thought_id = str(uuid.uuid4())
        entry = ThoughtEntry(
            id=thought_id,
            account_id=account_id,
            timestamp=datetime.utcnow(),
            entry_type=entry_type,
            source=source,
            content=content,
            impact=impact,
            confidence=confidence,
            details=details,
            related_entries=related_entries or []
        )
        
        async with self._lock:
            # Load existing thoughts
            thoughts = await self._load_thoughts()
            
            # Add new entry
            if account_id not in thoughts:
                thoughts[account_id] = []
            thoughts[account_id].append(entry.to_dict())
            
            # Keep last 100 entries per account
            thoughts[account_id] = thoughts[account_id][-100:]
            
            # Save back
            await self._save_thoughts(thoughts)
            
            # Update cache
            self._thoughts_cache[account_id] = [
                ThoughtEntry.from_dict(t) for t in thoughts[account_id]
            ]
        
        return entry
    
    async def get_recent_thoughts(
        self,
        account_id: str,
        hours: int = 24,
        entry_types: Optional[List[str]] = None
    ) -> List[ThoughtEntry]:
        """Get recent thought process entries."""
        
        # Check cache first
        if account_id not in self._thoughts_cache:
            async with self._lock:
                thoughts = await self._load_thoughts()
                if account_id in thoughts:
                    self._thoughts_cache[account_id] = [
                        ThoughtEntry.from_dict(t) for t in thoughts[account_id]
                    ]
                else:
                    self._thoughts_cache[account_id] = []
        
        # Filter by time and type
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent = []
        
        for thought in self._thoughts_cache.get(account_id, []):
            if thought.timestamp >= cutoff_time:
                if entry_types is None or thought.entry_type in entry_types:
                    recent.append(thought)
        
        return recent
    
    async def summarize_thoughts(
        self,
        account_id: str,
        for_purpose: str = "trading_decision",
        max_entries: int = 20
    ) -> str:
        """Summarize recent thoughts for AI context."""
        
        # Get recent thoughts based on purpose
        if for_purpose == "trading_decision":
            # For trading, focus on market insights and recent trades
            thoughts = await self.get_recent_thoughts(
                account_id,
                hours=48,
                entry_types=["chat_influence", "trading_decision", "market_observation"]
            )
        else:  # chat_response
            # For chat, include all recent thoughts
            thoughts = await self.get_recent_thoughts(account_id, hours=24)
        
        # Sort by timestamp (most recent first)
        thoughts.sort(key=lambda t: t.timestamp, reverse=True)
        thoughts = thoughts[:max_entries]
        
        if not thoughts:
            return "No recent thoughts or decisions recorded."
        
        # Build summary
        summary_parts = []
        
        # Group by type for clearer summary
        by_type = {}
        for thought in thoughts:
            if thought.entry_type not in by_type:
                by_type[thought.entry_type] = []
            by_type[thought.entry_type].append(thought)
        
        if "chat_influence" in by_type:
            summary_parts.append("Recent influences from conversations:")
            for t in by_type["chat_influence"][:5]:
                summary_parts.append(f"- {t.content} (confidence: {t.confidence:.1f})")
                if t.impact:
                    summary_parts.append(f"  Impact: {t.impact}")
        
        if "trading_decision" in by_type:
            summary_parts.append("\nRecent trading decisions:")
            for t in by_type["trading_decision"][:5]:
                summary_parts.append(f"- {t.content}")
                if t.details and "outcome" in t.details:
                    summary_parts.append(f"  Outcome: {t.details['outcome']}")
        
        if "market_observation" in by_type:
            summary_parts.append("\nMarket observations:")
            for t in by_type["market_observation"][:5]:
                summary_parts.append(f"- {t.content}")
        
        return "\n".join(summary_parts)
    
    async def get_trading_influences(
        self,
        account_id: str,
        hours: int = 24
    ) -> List[Dict]:
        """Get thoughts that should influence trading decisions."""
        
        thoughts = await self.get_recent_thoughts(account_id, hours=hours)
        
        influences = []
        for thought in thoughts:
            # High confidence thoughts with trading impact
            if thought.confidence >= 0.6 and thought.impact:
                influence_weight = thought.confidence
                
                # Recent thoughts have more influence
                age_hours = (datetime.utcnow() - thought.timestamp).total_seconds() / 3600
                if age_hours < 1:
                    influence_weight *= 1.0
                elif age_hours < 6:
                    influence_weight *= 0.8
                elif age_hours < 12:
                    influence_weight *= 0.6
                else:
                    influence_weight *= 0.4
                
                influences.append({
                    "content": thought.content,
                    "impact": thought.impact,
                    "source": thought.source,
                    "weight": influence_weight,
                    "timestamp": thought.timestamp.isoformat()
                })
        
        # Sort by weight (most influential first)
        influences.sort(key=lambda x: x["weight"], reverse=True)
        
        return influences[:10]  # Top 10 influences
    
    async def link_thoughts(
        self,
        thought_id: str,
        related_thought_ids: List[str]
    ):
        """Link related thoughts together."""
        async with self._lock:
            thoughts = await self._load_thoughts()
            
            # Find and update the thought
            for account_thoughts in thoughts.values():
                for thought in account_thoughts:
                    if thought["id"] == thought_id:
                        if "related_entries" not in thought:
                            thought["related_entries"] = []
                        thought["related_entries"].extend(related_thought_ids)
                        thought["related_entries"] = list(set(thought["related_entries"]))
                        break
            
            await self._save_thoughts(thoughts)
    
    async def _load_thoughts(self) -> Dict[str, List[Dict]]:
        """Load thoughts from storage."""
        if self.thoughts_file.exists():
            with open(self.thoughts_file, 'r') as f:
                return json.load(f)
        return {}
    
    async def _save_thoughts(self, thoughts: Dict[str, List[Dict]]):
        """Save thoughts to storage."""
        with open(self.thoughts_file, 'w') as f:
            json.dump(thoughts, f, indent=2)


# Example thought entry formats for consistency
THOUGHT_EXAMPLES = {
    "chat_influence": {
        "bullish_insight": {
            "content": "User shared insight about Fed rate cuts being bullish for BTC",
            "impact": "Reconsidering bearish stance on BTC, may look for long entries",
            "confidence": 0.7
        },
        "market_warning": {
            "content": "User warned about potential market crash due to regulatory news",
            "impact": "Will be more cautious with position sizing today",
            "confidence": 0.6
        }
    },
    "trading_decision": {
        "open_position": {
            "content": "Opened long BTC at $95k based on Fed news and technical breakout",
            "impact": "Committed to bullish thesis, will hold unless support breaks",
            "details": {
                "action": "buy",
                "asset": "BTC",
                "size": 0.1,
                "price": 95000,
                "stop_loss": 93000
            }
        },
        "close_position": {
            "content": "Closed BTC long at $98k for 3% profit",
            "impact": "Successful Fed-based trade increases confidence in macro plays",
            "details": {
                "action": "sell",
                "asset": "BTC",
                "size": 0.1,
                "price": 98000,
                "pnl": 300,
                "outcome": "profit"
            }
        }
    },
    "market_observation": {
        "price_action": {
            "content": "BTC pumped 5% immediately after Fed announcement",
            "impact": "Validates importance of macro news, will monitor Fed closely",
            "confidence": 0.8
        },
        "technical_signal": {
            "content": "BTC broke key resistance at $95k with high volume",
            "impact": "Bullish signal confirmed, expecting continuation to $100k",
            "confidence": 0.7
        }
    }
}