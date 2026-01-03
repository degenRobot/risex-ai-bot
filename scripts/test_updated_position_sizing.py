#!/usr/bin/env python3
"""Test updated position sizing with free margin."""

import asyncio
import json
from pathlib import Path
import sys

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.equity_monitor import get_equity_monitor
from app.services.storage import JSONStorage
from app.services.rise_client import RiseClient
from app.services.ai_tools import TradingTools
from app.core.market_manager import get_market_manager


async def test_equity_update():
    """Test the combined equity and margin update."""
    print("=== Testing Combined Equity/Margin Update ===\n")
    
    equity_monitor = get_equity_monitor()
    storage = JSONStorage()
    
    # Update all accounts
    success, total = await equity_monitor.update_all_accounts()
    print(f"Updated {success}/{total} accounts\n")
    
    # Check stored data
    accounts = storage.get_all_accounts()
    for account_id, account_data in accounts.items():
        print(f"{account_data['persona']['name']}:")
        print(f"  Equity: ${account_data.get('latest_equity', 0):,.2f}")
        print(f"  Free Margin: ${account_data.get('free_margin', 0):,.2f}")
        print(f"  Margin Used: ${account_data.get('margin_used', 0):,.2f}")
        print()


async def test_position_sizing_with_tools():
    """Test position sizing with the AI tools."""
    print("\n=== Testing AI Tools with Position Sizing ===\n")
    
    rise_client = RiseClient()
    storage = JSONStorage()
    tools = TradingTools(rise_client, storage, dry_run=False)
    
    # Get Midwit McGee account
    accounts = storage.get_all_accounts()
    midwit = next((acc for acc_id, acc in accounts.items() 
                   if acc['persona']['name'] == "Midwit McGee"), None)
    
    if not midwit:
        print("Midwit McGee account not found")
        return
    
    # Test with different size percentages
    test_sizes = [0.05, 0.25, 0.5]  # 5%, 25%, 50% of available balance
    
    for size_percent in test_sizes:
        print(f"\nTesting with {size_percent*100}% of available balance:")
        
        try:
            result = await tools._place_market_order(
                account_id="VeRw6CY7dOF9SEpFmfU1bA",
                persona_name="Midwit McGee",
                account_key=midwit['private_key'],
                signer_key=midwit['signer_key'],
                market="BTC",
                side="buy",
                size_percent=size_percent
            )
            
            if result.get('success'):
                print(f"  ✅ Success: {result['executed_size']:.6f} BTC")
                print(f"     Order ID: {result['order_id']}")
                # Only test one successful order
                break
            else:
                print(f"  ❌ Failed: {result.get('error')}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    await rise_client.close()


async def test_trading_prompt():
    """Test the trading prompt with position sizing info."""
    print("\n=== Testing Trading Prompt ===\n")
    
    from app.services.prompt_builders import TradingPromptBuilder
    from app.trader_profiles import create_trader_profile
    
    # Create test data
    profile = create_trader_profile("midCurve", "test")
    
    market_data = {
        'btc_price': 89000,
        'eth_price': 3100,
        'btc_change_24h': 0.012,
        'eth_change_24h': 0.044
    }
    
    positions = {
        'BTC': {
            'size': 0.005,
            'avg_price': 90000,
            'current_price': 89000,
            'unrealized_pnl': -50,
            'pnl_percent': -0.011
        }
    }
    
    # Test with different free margins
    test_margins = [100, 1000, 2000]
    
    for margin in test_margins:
        print(f"\n--- Free Margin: ${margin} ---")
        
        prompt = TradingPromptBuilder.build_trading_prompt(
            profile=profile,
            thought_summary="Recent market analysis shows bullish momentum",
            market_data=market_data,
            positions=positions,
            recent_trades=[],
            available_balance=margin
        )
        
        # Extract and print position sizing section
        lines = prompt.split('\n')
        in_sizing = False
        for line in lines:
            if "POSITION SIZING & RISK MANAGEMENT:" in line:
                in_sizing = True
            elif "POSITION MANAGEMENT:" in line:
                in_sizing = False
            elif in_sizing:
                print(line)


async def main():
    """Run all tests."""
    print("=" * 80)
    print("UPDATED POSITION SIZING TEST")
    print("=" * 80)
    
    # Test 1: Update accounts with combined equity/margin
    await test_equity_update()
    
    # Test 2: Test AI tools with proper sizing
    await test_position_sizing_with_tools()
    
    # Test 3: Test trading prompt
    await test_trading_prompt()


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main())