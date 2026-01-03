#!/usr/bin/env python3
"""Test minimal order execution to debug the async issue."""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.equity_monitor import get_equity_monitor
from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage


async def test_free_margin():
    """Test fetching free margin directly."""
    print("Testing free margin fetch...")
    
    # Test account
    test_address = "0x41972911b53D5B038c4c35F610e31963F60FaAd5"  # Midwit McGee
    
    equity_monitor = get_equity_monitor()
    
    try:
        # This should work correctly
        free_margin = await equity_monitor.fetch_free_margin(test_address)
        print(f"✅ Free margin: ${free_margin:.2f}")
        return free_margin
    except Exception as e:
        print(f"❌ Error fetching free margin: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_place_order():
    """Test placing a minimal market order."""
    print("\nTesting order placement...")
    
    # Initialize client
    rise_client = RiseClient()

    ## Get account keys from storage
    storage = JSONStorage()
    account_key = storage.get_account_key("Midwit McGee")
    signer_key = storage.get_signer_key("Midwit McGee")
    

    if not account_key or not signer_key:
        print("❌ Missing test keys in environment")
        return
    
    try:
        # Place minimal market order
        result = await rise_client.place_market_order(
            account_key=account_key,
            signer_key=signer_key,
            market_id=1,  # BTC
            size=0.001,   # Minimum size
            side="buy",
            reduce_only=False,
        )
        
        if result.get("success"):
            print("✅ Order placed successfully!")
            print(f"   Order ID: {result['data']['order_id']}")
            print(f"   TX Hash: {result['data']['transaction_hash']}")
        else:
            print(f"❌ Order failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Exception during order: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await rise_client.close()


async def test_ai_tools():
    """Test the AI tools execution path."""
    print("\nTesting AI tools execution...")
    
    from app.services.ai_tools import TradingTools
    from app.services.rise_client import RiseClient
    from app.services.storage import JSONStorage
    
    # Setup
    rise_client = RiseClient()
    storage = JSONStorage()
    tools = TradingTools(rise_client, storage, dry_run=False)
    
    # Test keys
    account_key = "0x4f79817ea2a6ea4021f5591029d69cd56f6b746a4910a8a7ad6e9bf5373cfa7f"
    signer_key = "0x2201953d780f0b4895398f8ec6e0f1e09ce3c45557e508a22851091fb77ae0f8"
    
    try:
        # Execute tool call
        result = await tools._place_market_order(
            account_id="VeRw6CY7dOF9SEpFmfU1bA",
            persona_name="Midwit McGee",
            account_key=account_key,
            signer_key=signer_key,
            market="BTC",
            side="buy",
            size_percent=0.01,  # 1% of balance
        )
        
        print(f"Tool result: {result}")
        
    except Exception as e:
        print(f"❌ Tool execution error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await rise_client.close()


async def main():
    """Run all tests."""
    print("=" * 60)
    print("RISE ORDER EXECUTION TEST")
    print("=" * 60)
    
    # Test 1: Free margin
    margin = await test_free_margin()
    
    # Test 2: Direct order
    if margin and margin > 0:
        await test_place_order()
    
    # Test 3: AI tools path
    await test_ai_tools()


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main())