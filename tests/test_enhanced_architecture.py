#!/usr/bin/env python3
"""Test the enhanced architecture with tool calling and parallel execution."""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.market_manager import get_market_manager
from app.core.parallel_executor import ParallelProfileExecutor
from app.services.storage import JSONStorage
from app.services.ai_tools import TradingTools
from app.services.rise_client import RiseClient
from app.models.pending_actions import (
    PendingAction, ActionType, TriggerCondition, 
    OperatorType, ActionParams
)


async def test_market_manager():
    """Test the global market manager."""
    print("\n🧪 Testing Global Market Manager")
    print("=" * 50)
    
    manager = get_market_manager()
    
    # Test singleton
    manager2 = get_market_manager()
    assert manager is manager2, "Market manager should be singleton"
    print("✅ Singleton pattern working")
    
    # Test market data
    data = await manager.get_latest_data(force_update=True)
    print(f"✅ Market data fetched: {len(data)} fields")
    print(f"   BTC: ${data.get('btc_price', 0):,.0f}")
    print(f"   ETH: ${data.get('eth_price', 0):,.0f}")
    
    # Test specific market lookup
    btc_data = await manager.get_market_by_symbol("BTC")
    if btc_data:
        print(f"✅ BTC market lookup: ${btc_data['price']:,.0f}")
    
    # Test summary
    summary = manager.get_market_summary()
    print(f"✅ Market summary: BTC {summary['btc']}, ETH {summary['eth']}")
    
    await manager.close()


async def test_pending_actions():
    """Test pending actions system."""
    print("\n🧪 Testing Pending Actions System")
    print("=" * 50)
    
    storage = JSONStorage()
    
    # Create test action
    import uuid
    test_action = PendingAction(
        id=str(uuid.uuid4()),
        account_id="test_account",
        persona_name="Test Trader",
        action_type=ActionType.STOP_LOSS,
        condition=TriggerCondition(
            field="price",
            operator=OperatorType.LESS_EQUAL,
            value=85000,
            market="BTC"
        ),
        action_params=ActionParams(
            market="BTC",
            reduce_percent=100
        ),
        reasoning="Test stop loss at $85,000"
    )
    
    # Save action
    storage.save_pending_action(test_action)
    print("✅ Pending action saved")
    
    # Retrieve action
    retrieved = storage.get_pending_action(test_action.id)
    assert retrieved is not None, "Should retrieve saved action"
    assert retrieved.id == test_action.id
    print("✅ Pending action retrieved")
    
    # Test condition evaluation
    # Should not trigger
    context1 = {"btc_price": 90000}
    assert not test_action.should_trigger(context1), "Should not trigger above price"
    print("✅ Condition evaluation (no trigger) correct")
    
    # Should trigger
    context2 = {"btc_price": 84000}
    assert test_action.should_trigger(context2), "Should trigger below price"
    print("✅ Condition evaluation (trigger) correct")
    
    # Get all pending actions
    all_pending = storage.get_all_pending_actions()
    print(f"✅ Found {len(all_pending)} pending actions total")


async def test_tool_schemas():
    """Test AI tool schemas."""
    print("\n🧪 Testing AI Tool Schemas")
    print("=" * 50)
    
    rise_client = RiseClient()
    storage = JSONStorage()
    tools = TradingTools(rise_client, storage)
    
    schemas = tools.tools_schema
    print(f"✅ Found {len(schemas)} tool schemas")
    
    # List all tools
    for tool in schemas:
        func = tool["function"]
        print(f"   • {func['name']}: {func['description']}")
    
    # Verify required tools exist
    tool_names = [t["function"]["name"] for t in schemas]
    required_tools = [
        "place_market_order", "place_limit_order", "close_position",
        "set_stop_loss", "set_take_profit", "schedule_limit_order"
    ]
    
    for required in required_tools:
        assert required in tool_names, f"Missing required tool: {required}"
    
    print("✅ All required tools present")
    
    await rise_client.close()


async def test_parallel_executor():
    """Test parallel executor initialization."""
    print("\n🧪 Testing Parallel Executor")
    print("=" * 50)
    
    executor = ParallelProfileExecutor(dry_run=True)
    
    # Initialize
    await executor.initialize()
    print(f"✅ Executor initialized with {len(executor.active_profiles)} profiles")
    
    # Test market manager is initialized
    assert executor.market_manager is not None
    print("✅ Market manager integrated")
    
    # Test tools are available
    assert executor.trading_tools is not None
    assert len(executor.trading_tools.tools_schema) > 0
    print("✅ Trading tools integrated")
    
    # If we have profiles, test formatting
    if executor.active_profiles:
        test_positions = [
            {"market_id": 1, "size": 0.5, "entry_price": 90000},
            {"market_id": 2, "size": -0.3, "entry_price": 3000}
        ]
        formatted = executor._format_positions(test_positions)
        print(f"✅ Position formatting: {formatted}")
    
    await executor.rise_client.close()


async def test_full_cycle():
    """Test a full execution cycle (dry run)."""
    print("\n🧪 Testing Full Execution Cycle (Dry Run)")
    print("=" * 50)
    
    executor = ParallelProfileExecutor(dry_run=True)
    await executor.initialize()
    
    if not executor.active_profiles:
        print("⚠️  No active profiles, skipping cycle test")
        await executor.rise_client.close()
        return
    
    print(f"📋 Running cycle with {len(executor.active_profiles)} profiles")
    
    # Run one cycle
    await executor.run_cycle()
    
    print("✅ Full cycle completed successfully")
    
    await executor.rise_client.close()


async def main():
    """Run all tests."""
    print("\n🏁 ENHANCED ARCHITECTURE TEST SUITE")
    print("=" * 70)
    
    try:
        # Test each component
        await test_market_manager()
        await test_pending_actions()
        await test_tool_schemas()
        await test_parallel_executor()
        await test_full_cycle()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n❌ Test assertion failed: {e}")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())