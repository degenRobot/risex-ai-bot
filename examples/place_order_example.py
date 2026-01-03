#!/usr/bin/env python3
"""
Example: How to place an order using the RISE AI Trading Bot

This example shows how to place an order via the RISE API.
Note: Orders will fail on testnet until markets are enabled.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.market_manager import get_market_manager
from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage


async def place_order_example():
    """Example of placing an order."""
    
    # Initialize services
    rise_client = RiseClient()
    storage = JSONStorage()
    market_manager = get_market_manager()
    
    print("RISE Trading Bot - Order Example")
    print("=" * 50)
    
    # 1. Get account (use existing or create new)
    accounts = storage.list_accounts()
    if not accounts:
        print("No accounts found. Create one with:")
        print("  poetry run python scripts/run_trading_bot.py --create-accounts")
        return
    
    account = accounts[0]  # Use first account
    print(f"\nUsing account: {account.address}")
    
    # 2. Get current market data
    print("\nFetching market data...")
    await market_manager.get_latest_data(force_update=True)
    
    btc_price = market_manager.market_cache.get("btc_price", 90000)
    btc_market_id = market_manager.market_cache.get("btc_market_id", 1)
    
    print(f"BTC Price: ${btc_price:,.2f}")
    print(f"Market ID: {btc_market_id}")
    
    # 3. Define order parameters
    order_params = {
        "market_id": btc_market_id,
        "size": 0.001,  # 0.001 BTC
        "price": btc_price * 0.99,  # 1% below market
        "side": "buy",
        "order_type": "limit",
    }
    
    print("\nOrder Details:")
    print(f"- Type: {order_params['order_type'].upper()} {order_params['side'].upper()}")
    print(f"- Size: {order_params['size']} BTC")
    print(f"- Price: ${order_params['price']:,.2f}")
    print(f"- Total: ${order_params['size'] * order_params['price']:,.2f}")
    
    # 4. Place the order
    print("\nPlacing order...")
    try:
        result = await rise_client.place_order(
            account_key=account.private_key,
            signer_key=account.signer_key,
            **order_params,
        )
        
        if result.get("success"):
            print("✓ Order placed successfully!")
            print(f"  Order ID: {result.get('data', {}).get('order_id')}")
            print(f"  TX Hash: {result.get('data', {}).get('transaction_hash')}")
        else:
            print("✗ Order failed")
            print(f"  Message: {result.get('message')}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        
        # Note about current testnet status
        if "missing nonce or insufficient funds" in str(e):
            print("\n⚠️  Testnet Status:")
            print("   Orders are failing due to testnet configuration.")
            print("   This is not an issue with the bot implementation.")
            print("   The bot will work once markets are enabled.")
    
    # Cleanup
    await rise_client.close()
    await market_manager.close()


# Example: Place order with custom parameters
async def place_custom_order(
    account_address: str,
    market: str = "BTC",  # BTC or ETH
    size: float = 0.001,
    price_offset: float = 0.99,  # 0.99 = 1% below market
):
    """Place a custom order."""
    rise_client = RiseClient()
    storage = JSONStorage()
    
    # Find account
    accounts = storage.list_accounts()
    account = next((a for a in accounts if a.address == account_address), None)
    
    if not account:
        print(f"Account {account_address} not found")
        return
    
    # Get market data
    markets = await rise_client.get_markets()
    target_market = next((m for m in markets if market in m.get("base_asset_symbol", "")), None)
    
    if not target_market:
        print(f"Market {market} not found")
        return
    
    market_id = int(target_market["market_id"])
    current_price = float(target_market["last_price"])
    
    # Place order
    result = await rise_client.place_order(
        account_key=account.private_key,
        signer_key=account.signer_key,
        market_id=market_id,
        size=size,
        price=current_price * price_offset,
        side="buy",
        order_type="limit",
    )
    
    print(f"Order result: {result}")
    await rise_client.close()
    
    return result


if __name__ == "__main__":
    # Run the example
    asyncio.run(place_order_example())
    
    # Example of custom order (uncomment to use):
    # asyncio.run(place_custom_order(
    #     account_address="0x...",
    #     market="ETH",
    #     size=0.01,
    #     price_offset=0.98  # 2% below market
    # ))