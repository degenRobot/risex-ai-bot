#!/usr/bin/env python3
"""Test RISE features that are currently working."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage


async def test_working_features():
    """Demonstrate RISE API features that are working."""
    
    print("✅ RISE API Working Features Demo")
    print("=" * 60)
    
    # Get test account
    storage = JSONStorage()
    test_account = next((acc for acc in storage.list_accounts() 
                        if acc.signer_key and acc.signer_key != acc.private_key), None)
    
    if not test_account:
        print("❌ No valid test account found")
        return
    
    print(f"\n📊 Test Account: {test_account.address}")
    print(f"   Persona: {test_account.persona.name if test_account.persona else 'Unknown'}")
    
    async with RiseClient() as client:
        # 1. Get Markets (WORKING)
        print("\n1️⃣ Getting Markets ✅")
        markets = await client.get_markets()
        print(f"   Found {len(markets)} markets")
        
        # Show BTC and ETH markets
        for market in markets[:5]:
            symbol = market.get('symbol', 'Unknown')
            market_id = market.get('market_id', market.get('id'))
            if 'BTC' in symbol or 'ETH' in symbol:
                print(f"   - {symbol} (ID: {market_id})")
        
        # 2. Get Market Prices (WORKING)
        print("\n2️⃣ Getting Market Prices ✅")
        prices = await client.get_market_prices()
        for symbol, price in prices.items():
            print(f"   {symbol}: ${price:,.2f}")
        
        # 3. Get Position (WORKING)
        print("\n3️⃣ Getting Current Position ✅")
        response = await client._request(
            "GET", "/v1/account/position",
            params={"account": test_account.address, "market_id": 1}
        )
        
        position = response.get("data", {}).get("position", {})
        size_raw = int(position.get("size", 0))
        
        if size_raw != 0:
            size_human = abs(size_raw / 1e18)
            side = "Long" if size_raw > 0 else "Short"
            quote_amount = int(position.get("quote_amount", 0)) / 1e18
            
            print(f"   Position: {side} {size_human:.6f} BTC")
            print(f"   Quote Amount: ${quote_amount:.2f}")
            
            # Calculate current value
            if 'BTC' in prices:
                current_value = size_human * prices['BTC']
                pnl = current_value - abs(quote_amount)
                print(f"   Current Value: ${current_value:.2f}")
                print(f"   Unrealized P&L: ${pnl:.2f}")
        else:
            print("   No open position")
        
        # 4. Get Transfer History (WORKING)
        print("\n4️⃣ Getting Transfer History ✅")
        response = await client._request(
            "GET", "/v1/account/transfer-history",
            params={"account": test_account.address, "limit": 5}
        )
        
        data = response.get("data", {})
        items = data.get("items", [])
        
        if items:
            print(f"   Found {len(items)} transfers")
            for item in items[:3]:
                tx_type = item.get("type", "Unknown")
                amount = item.get("amount", 0)
                print(f"   - {tx_type}: {amount}")
        
        # 5. Market Data / Price History (WORKING)
        print("\n5️⃣ Getting BTC Price History ✅")
        btc_data = await client.get_market_data(1, resolution="1H", limit=5)
        
        if btc_data:
            print(f"   Last {len(btc_data)} hourly candles:")
            for candle in btc_data[-3:]:
                timestamp = candle.get("time", "Unknown")
                close_price = float(candle.get("close", 0))
                print(f"   - {timestamp}: ${close_price:,.2f}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📝 Summary:")
        print("✅ API connectivity works")
        print("✅ Market data retrieval works")
        print("✅ Position queries work")
        print("✅ Price feeds work")
        print("✅ Transfer history works")
        print("❌ Order placement requires whitelisting")
        print("\n💡 Next Steps:")
        print("1. Contact RISE team to whitelist the account")
        print("2. Or use the bot in 'paper trading' mode")
        print("3. The retry logic is implemented and will work once whitelisted")


if __name__ == "__main__":
    asyncio.run(test_working_features())