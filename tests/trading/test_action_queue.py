"""Test trading action queue functionality."""

import pytest
import asyncio
import os
import sys
import uuid
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.trading.actions import (
    TradingActionQueue,
    PendingAction,
    ActionType,
    ActionPriority,
    get_action_queue
)


class TestActionQueue:
    """Test the trading action queue."""
    
    @pytest.mark.asyncio
    async def test_add_action(self):
        """Test adding actions to queue."""
        # Clear any existing actions first
        queue = TradingActionQueue(storage_path="data/test_actions.json")
        queue._actions.clear()
        queue._save_actions()
        
        action = PendingAction(
            id=str(uuid.uuid4()),
            profile_id="test-profile-1",
            action_type=ActionType.MARKET_ORDER,
            priority=ActionPriority.NORMAL,
            symbol="BTC",
            side="buy",
            size=0.001,
            reasoning="Test trade"
        )
        
        success = await queue.add_action(action)
        assert success is True
        
        # Test duplicate rejection
        duplicate = PendingAction(
            id=str(uuid.uuid4()),
            profile_id="test-profile-1",
            action_type=ActionType.MARKET_ORDER,
            priority=ActionPriority.NORMAL,
            symbol="BTC",
            side="buy",
            size=0.002,
            reasoning="Duplicate test"
        )
        
        success = await queue.add_action(duplicate)
        assert success is False  # Should reject duplicate
        
    @pytest.mark.asyncio
    async def test_get_ready_actions(self):
        """Test getting actions ready for execution."""
        queue = TradingActionQueue(storage_path="data/test_actions2.json")
        queue._actions.clear()
        queue._save_actions()
        
        # Add immediate action
        immediate = PendingAction(
            id=str(uuid.uuid4()),
            profile_id="test-profile-2",
            action_type=ActionType.MARKET_ORDER,
            priority=ActionPriority.HIGH,
            symbol="ETH",
            side="sell",
            size=0.1
        )
        await queue.add_action(immediate)
        
        # Add delayed action
        delayed = PendingAction(
            id=str(uuid.uuid4()),
            profile_id="test-profile-2", 
            action_type=ActionType.LIMIT_ORDER,
            priority=ActionPriority.NORMAL,
            symbol="SOL",
            side="buy",
            size=5,
            price=150.0,
            not_before=datetime.now() + timedelta(minutes=5)
        )
        await queue.add_action(delayed)
        
        # Get ready actions
        ready = await queue.get_ready_actions("test-profile-2")
        
        assert len(ready) == 1
        assert ready[0].symbol == "ETH"  # Only immediate action is ready
        
    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        """Test actions are returned in priority order."""
        queue = TradingActionQueue(storage_path="data/test_actions3.json")
        queue._actions.clear()
        queue._save_actions()
        
        # Add actions with different priorities
        low = PendingAction(
            id="low-1",
            profile_id="test-profile-3",
            action_type=ActionType.REBALANCE,
            priority=ActionPriority.LOW,
            symbol="LINK",
            side="buy"
        )
        await queue.add_action(low)
        
        critical = PendingAction(
            id="critical-1",
            profile_id="test-profile-3",
            action_type=ActionType.STOP_LOSS,
            priority=ActionPriority.CRITICAL,
            symbol="BTC",
            side="sell"
        )
        await queue.add_action(critical)
        
        normal = PendingAction(
            id="normal-1",
            profile_id="test-profile-3",
            action_type=ActionType.MARKET_ORDER,
            priority=ActionPriority.NORMAL,
            symbol="ETH",
            side="buy"
        )
        await queue.add_action(normal)
        
        # Get actions - should be in priority order
        ready = await queue.get_ready_actions("test-profile-3")
        
        assert len(ready) == 3
        assert ready[0].id == "critical-1"  # Critical first
        assert ready[1].id == "normal-1"    # Then normal
        assert ready[2].id == "low-1"       # Low last
        
    @pytest.mark.asyncio
    async def test_throttling(self):
        """Test action execution throttling."""
        queue = TradingActionQueue(storage_path="data/test_actions4.json")
        queue._actions.clear()
        queue._save_actions()
        queue.min_interval_seconds = 2  # 2 seconds between actions
        
        profile_id = "test-profile-4"
        symbol = "BTC"
        
        # First check should pass
        can_execute = await queue.can_execute_action(profile_id, symbol)
        assert can_execute is True
        
        # Mark as executed
        queue.last_execution_times[f"{profile_id}:{symbol}"] = datetime.now()
        
        # Immediate second check should fail
        can_execute = await queue.can_execute_action(profile_id, symbol)
        assert can_execute is False
        
        # Wait and check again
        await asyncio.sleep(2.1)
        can_execute = await queue.can_execute_action(profile_id, symbol)
        assert can_execute is True
        
    @pytest.mark.asyncio
    async def test_mark_executed(self):
        """Test marking actions as executed."""
        queue = TradingActionQueue(storage_path="data/test_actions5.json")
        queue._actions.clear()
        queue._save_actions()
        
        action = PendingAction(
            id=str(uuid.uuid4()),
            profile_id="test-profile-5",
            action_type=ActionType.MARKET_ORDER,
            priority=ActionPriority.NORMAL,
            symbol="BTC",
            side="buy",
            size=0.001
        )
        
        await queue.add_action(action)
        
        # Mark as successful
        await queue.mark_executed(action.id, success=True)
        
        # Action should be removed
        ready = await queue.get_ready_actions("test-profile-5")
        assert len(ready) == 0
        
    @pytest.mark.asyncio
    async def test_failed_retry(self):
        """Test retry logic for failed actions."""
        queue = TradingActionQueue(storage_path="data/test_actions6.json")
        queue._actions.clear()
        queue._save_actions()
        
        action = PendingAction(
            id=str(uuid.uuid4()),
            profile_id="test-profile-6",
            action_type=ActionType.MARKET_ORDER,
            priority=ActionPriority.NORMAL,
            symbol="ETH",
            side="sell",
            size=0.1
        )
        
        await queue.add_action(action)
        
        # Mark as failed
        await queue.mark_executed(action.id, success=False, error="Test error")
        
        # Should still exist but not be ready (delayed)
        ready = await queue.get_ready_actions("test-profile-6")
        assert len(ready) == 0
        
        # Check it's still in queue
        assert action.id in queue._actions
        assert queue._actions[action.id].attempts == 1
        assert queue._actions[action.id].last_error == "Test error"
        
    def test_queue_stats(self):
        """Test getting queue statistics."""
        queue = TradingActionQueue(storage_path="data/test_actions7.json")
        queue._actions.clear()
        
        # Add some test actions
        for i in range(5):
            action = PendingAction(
                id=f"test-{i}",
                profile_id=f"profile-{i % 2}",  # 2 profiles
                action_type=ActionType.MARKET_ORDER if i % 2 else ActionType.LIMIT_ORDER,
                priority=ActionPriority.NORMAL,
                symbol="BTC",
                side="buy"
            )
            queue._actions[action.id] = action
            
        stats = queue.get_queue_stats()
        
        assert stats['total_actions'] == 5
        assert stats['by_type']['MARKET_ORDER'] == 2
        assert stats['by_type']['LIMIT_ORDER'] == 3
        assert stats['by_priority']['NORMAL'] == 5
        assert len(stats['by_profile']) == 2
        

async def run_async_tests():
    """Run async tests without pytest."""
    print("=" * 60)
    print("Testing Trading Action Queue")
    print("=" * 60)
    
    test = TestActionQueue()
    
    print("\n🔵 Testing add action...")
    await test.test_add_action()
    print("   ✅ Actions added and duplicates rejected")
    
    print("\n🔵 Testing ready actions...")
    await test.test_get_ready_actions()
    print("   ✅ Ready actions filtered correctly")
    
    print("\n🔵 Testing priority ordering...")
    await test.test_priority_ordering()
    print("   ✅ Actions prioritized correctly")
    
    print("\n🔵 Testing throttling...")
    await test.test_throttling()
    print("   ✅ Throttling works correctly")
    
    print("\n🔵 Testing execution marking...")
    await test.test_mark_executed()
    print("   ✅ Execution tracking works")
    
    print("\n🔵 Testing failed retry...")
    await test.test_failed_retry()
    print("   ✅ Retry logic works")
    
    print("\n🔵 Testing queue stats...")
    test.test_queue_stats()
    print("   ✅ Statistics calculated correctly")
    
    # Cleanup test files
    import glob
    for f in glob.glob("data/test_actions*.json"):
        os.remove(f)
    
    print("\n✅ All action queue tests passed!")
    

if __name__ == "__main__":
    asyncio.run(run_async_tests())
    
    print("\n💡 To run pytest tests:")
    print("   poetry run pytest tests/trading/test_action_queue.py -v")