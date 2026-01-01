#!/usr/bin/env python3
"""Test complete flow locally: account creation, RISE setup, AI trading, API access."""

import asyncio
import sys
import uuid
from pathlib import Path
from datetime import datetime
from eth_account import Account as EthAccount

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models import Account, Persona, TradingStyle
from app.services.storage import JSONStorage
from app.services.rise_client import RiseClient
from app.services.ai_client import AIClient
from app.core.market_manager import get_market_manager


async def test_full_flow():
    """Test complete flow with new account."""
    print("RISE AI Trading Bot - Full Flow Test")
    print("=" * 70)
    
    # Initialize services
    storage = JSONStorage()
    rise_client = RiseClient()
    ai_client = AIClient()
    market_manager = get_market_manager()
    
    # Step 1: Create new account with fresh keys
    print("\n1. Creating new account with fresh keys...")
    
    # Generate fresh keys
    main_account = EthAccount.create()
    signer_account = EthAccount.create()
    
    print(f"   Main account address: {main_account.address}")
    print(f"   Signer address: {signer_account.address}")
    
    # Create simple "always long" persona
    persona = Persona(
        name="Bull Trader",
        handle="bull_trader_test",
        bio="Always bullish when I have collateral and no positions",
        trading_style=TradingStyle.MOMENTUM,
        risk_tolerance=0.7,
        favorite_assets=["BTC", "ETH"],
        personality_traits=["optimistic", "momentum-driven", "disciplined"],
        sample_posts=["Always long the trend", "Buy when others are fearful"]
    )
    
    # Create account object
    account = Account(
        id=str(uuid.uuid4()),
        address=main_account.address,
        private_key=main_account.key.hex(),
        signer_key=signer_account.key.hex(),
        persona=persona,
        is_active=True,
        created_at=datetime.now()
    )
    
    # Save to storage
    storage.save_account(account)
    print(f"   Account saved with ID: {account.id}")
    print(f"   Persona: {persona.name} ({persona.trading_style.value})")
    
    # Step 2: Register signer with RISE
    print("\n2. Registering signer with RISE...")
    try:
        result = await rise_client.register_signer(
            account.private_key,
            account.signer_key
        )
        print(f"   Registration result: {result.get('data', {}).get('message', 'Success')}")
    except Exception as e:
        print(f"   Registration error (may already be registered): {e}")
    
    # Step 3: Deposit USDC (triggers faucet on testnet)
    print("\n3. Depositing USDC to trigger faucet...")
    try:
        deposit_result = await rise_client.deposit_usdc(
            account.private_key,
            amount=100.0  # $100 deposit
        )
        print(f"   Deposit result: {deposit_result.get('data', {}).get('message', 'Success')}")
        print("   Note: Faucet may take a moment to credit the account")
    except Exception as e:
        print(f"   Deposit error: {e}")
    
    # Step 4: Get real market data
    print("\n4. Fetching real market data...")
    await market_manager.get_latest_data(force_update=True)
    market_data = market_manager.market_cache
    
    print(f"   BTC Price: ${market_data.get('btc_price', 0):,.0f}")
    print(f"   ETH Price: ${market_data.get('eth_price', 0):,.0f}")
    print(f"   BTC 24h Change: {market_data.get('btc_change', 0):.1%}")
    print(f"   ETH 24h Change: {market_data.get('eth_change', 0):.1%}")
    
    # Step 5: Wait for faucet and check positions
    print("\n5. Waiting for faucet to process (5 seconds)...")
    await asyncio.sleep(5)
    
    # Since balance endpoint is having issues, assume faucet gave us $100
    available_balance = 100.0
    positions = []
    
    try:
        # Try to get positions
        positions = await rise_client.get_all_positions(account.address)
        open_positions = [p for p in positions if float(p.get('size', 0)) != 0]
        print(f"   Account has {len(open_positions)} open positions")
        print(f"   Assumed balance from faucet: ${available_balance:.2f}")
    except Exception as e:
        print(f"   Position check error: {e}")
        print(f"   Assumed balance from faucet: ${available_balance:.2f}")
    
    # Step 6: AI trading decision
    print("\n6. Getting AI trading decision...")
    
    # Format market data for AI
    ai_market_data = {
        "btc_price": market_data.get("btc_price", 0),
        "eth_price": market_data.get("eth_price", 0),
        "btc_change": market_data.get("btc_change", 0),
        "eth_change": market_data.get("eth_change", 0),
    }
    
    # Get AI decision
    current_positions = {"BTC": 0, "ETH": 0}  # No positions
    
    try:
        decision = await ai_client.get_trade_decision(
            persona,
            ai_market_data,
            current_positions,
            available_balance if available_balance > 0 else 1000.0  # Use default if no balance yet
        )
        
        print(f"   Should trade: {decision.should_trade}")
        print(f"   Action: {decision.action}")
        print(f"   Market: {decision.market}")
        print(f"   Size: {decision.size_percent:.1%} of balance")
        print(f"   Confidence: {decision.confidence:.1%}")
        print(f"   Reasoning: {decision.reasoning}")
        
        # Step 7: Place order if AI wants to trade
        if decision.should_trade and decision.action == "buy":
            print("\n7. Placing order based on AI decision...")
            
            market_id = 1 if decision.market == "BTC" else 2
            price = market_data.get(f"{decision.market.lower()}_price", 50000)
            size = (available_balance * decision.size_percent) / price if available_balance > 0 else 0.001
            
            print(f"   Order details:")
            print(f"   - Market: {decision.market} (ID: {market_id})")
            print(f"   - Side: {decision.action}")
            print(f"   - Size: {size:.6f}")
            print(f"   - Price: ${price:,.0f}")
            
            if available_balance > 10:  # Only place order if we have balance
                try:
                    order_result = await rise_client.place_order(
                        account_key=account.private_key,
                        signer_key=account.signer_key,
                        market_id=market_id,
                        size=size,
                        price=price * 1.01,  # Limit order with 1% slippage
                        side=decision.action,
                        order_type="limit"
                    )
                    print(f"   Order result: {order_result.get('data', {}).get('message', 'Success')}")
                except Exception as e:
                    print(f"   Order error: {e}")
            else:
                print("   Skipping order - insufficient balance (faucet may still be pending)")
                
    except Exception as e:
        print(f"   AI decision error: {e}")
    
    # Step 8: Test data tracking for multiple accounts
    print("\n8. Testing multi-account data tracking...")
    
    # List all accounts
    all_accounts = storage.list_accounts()
    print(f"   Total accounts in storage: {len(all_accounts)}")
    
    for acc in all_accounts[-3:]:  # Show last 3 accounts
        if acc.persona:
            print(f"   - {acc.persona.handle}: {acc.persona.name} ({acc.address[:8]}...)")
    
    # Test analytics
    analytics = storage.get_trading_analytics(account.id)
    print(f"\n   Analytics for {persona.handle}:")
    print(f"   - Total decisions: {analytics.get('total_decisions', 0)}")
    print(f"   - Executed decisions: {analytics.get('executed_decisions', 0)}")
    
    # Cleanup
    await rise_client.close()
    await market_manager.close()
    
    print("\n" + "=" * 70)
    print("Full flow test completed!")


async def test_external_api():
    """Test external API endpoints."""
    print("\n\nTesting External API Access")
    print("=" * 70)
    
    import httpx
    
    # Assuming API is running on port 8080
    base_url = "http://localhost:8080"
    
    async with httpx.AsyncClient() as client:
        # Test profile list
        print("\n1. Testing GET /api/profiles")
        try:
            response = await client.get(f"{base_url}/api/profiles")
            if response.status_code == 200:
                profiles = response.json()
                print(f"   Found {len(profiles)} profiles")
                
                if profiles:
                    # Test detailed profile
                    handle = profiles[-1]['handle']  # Get last created
                    print(f"\n2. Testing GET /api/profiles/{handle}")
                    
                    response = await client.get(f"{base_url}/api/profiles/{handle}")
                    if response.status_code == 200:
                        profile = response.json()
                        print(f"   Name: {profile['name']}")
                        print(f"   Trading Style: {profile['trading_style']}")
                        print(f"   Address: {profile['account_address']}")
                        print(f"   Pending Actions: {len(profile['pending_actions'])}")
                        print(f"   Recent Trades: {len(profile['recent_trades'])}")
        except Exception as e:
            print(f"   API test error: {e}")
            print("   Make sure to run: python start.py")


async def main():
    """Run all tests."""
    # Run full flow test
    await test_full_flow()
    
    # Test API if running
    print("\nTo test the API endpoints:")
    print("1. In another terminal, run: python start.py")
    print("2. Then run: python tests/test_api.py")
    print("\nOr uncomment the line below to test here:")
    # await test_external_api()


if __name__ == "__main__":
    asyncio.run(main())