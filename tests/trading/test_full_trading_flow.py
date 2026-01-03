#!/usr/bin/env python3
"""
Comprehensive test for the full trading flow:
1. Create account with new keys
2. Register signer
3. Deposit USDC
4. Place orders
5. Check positions
6. Update local P&L
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Optional

from eth_account import Account as EthAccount
import httpx

from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage
from app.models import Account, Persona, Trade, Position, TradingStyle


class FullTradingFlowTest:
    """Test the complete trading flow from account creation to P&L tracking."""
    
    def __init__(self):
        self.storage = JSONStorage()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "steps": {},
            "account": None,
            "trades": [],
            "positions": []
        }
    
    async def run_test(self):
        """Run the complete trading flow test."""
        print("🧪 Full Trading Flow Test")
        print("="*60)
        
        # Step 1: Create new account
        account = await self.test_account_creation()
        if not account:
            return
        
        # Step 2: Register signer
        success = await self.test_register_signer(account)
        if not success:
            print("⚠️  Continuing without registration...")
        
        # Step 3: Deposit USDC
        success = await self.test_deposit_usdc(account)
        if not success:
            print("⚠️  Continuing without deposit...")
        
        # Step 4: Place market order
        order_id = await self.test_place_order(account)
        
        # Step 5: Check positions
        positions = await self.test_check_positions(account)
        
        # Step 6: Update local P&L
        await self.test_update_pnl(account, positions)
        
        # Save results
        self.save_results()
        self.print_summary()
    
    async def test_account_creation(self) -> Optional[Account]:
        """Step 1: Create a new account with keys."""
        print("\n📝 Step 1: Creating new account")
        print("-"*40)
        
        try:
            # Generate new keys
            main_account = EthAccount.create()
            signer_account = EthAccount.create()
            
            print(f"✅ Generated main account: {main_account.address}")
            print(f"✅ Generated signer: {signer_account.address}")
            
            # Create persona
            persona = Persona(
                name="Test Flow Trader",
                handle=f"test_flow_{int(time.time())}",
                bio="Automated test trader for full flow testing",
                trading_style=TradingStyle.MOMENTUM,
                risk_tolerance=0.5,
                favorite_assets=["BTC", "ETH"],
                personality_traits=["systematic", "test-driven"],
                sample_posts=["Testing the flow"]
            )
            
            # Create account
            account = Account(
                id=f"test-{int(time.time())}",
                address=main_account.address,
                private_key=main_account.key.hex(),
                signer_key=signer_account.key.hex(),
                persona=persona,
                is_active=True,
                is_registered=False,
                has_deposited=False
            )
            
            # Save to storage
            self.storage.save_account(account)
            
            self.results["account"] = {
                "id": account.id,
                "address": account.address,
                "signer_address": signer_account.address,
                "handle": persona.handle
            }
            
            self.results["steps"]["account_creation"] = {
                "status": "✅ SUCCESS",
                "account_id": account.id,
                "address": account.address
            }
            
            print(f"✅ Account created and saved: {account.id}")
            return account
            
        except Exception as e:
            self.results["steps"]["account_creation"] = {
                "status": "❌ FAILED",
                "error": str(e)
            }
            print(f"❌ Failed to create account: {e}")
            return None
    
    async def test_register_signer(self, account: Account) -> bool:
        """Step 2: Register signer on RISE."""
        print("\n🔐 Step 2: Registering signer")
        print("-"*40)
        
        try:
            async with RiseClient() as client:
                await client.register_signer(
                    account_key=account.private_key,
                    signer_key=account.signer_key
                )
                
                # Update account status
                account.is_registered = True
                account.registered_at = datetime.utcnow()
                self.storage.save_account(account)
                
                self.results["steps"]["register_signer"] = {
                    "status": "✅ SUCCESS",
                    "registered_at": account.registered_at.isoformat()
                }
                
                print("✅ Signer registered successfully")
                return True
                
        except Exception as e:
            self.results["steps"]["register_signer"] = {
                "status": "❌ FAILED",
                "error": str(e)
            }
            print(f"❌ Failed to register signer: {e}")
            return False
    
    async def test_deposit_usdc(self, account: Account) -> bool:
        """Step 3: Deposit USDC to account."""
        print("\n💰 Step 3: Depositing USDC")
        print("-"*40)
        
        try:
            deposit_amount = 100.0
            
            async with RiseClient() as client:
                tx_hash = await client.deposit_usdc(
                    account_key=account.private_key,
                    amount=deposit_amount
                )
                
                # Update account status
                account.has_deposited = True
                account.deposited_at = datetime.utcnow()
                account.deposit_amount = deposit_amount
                self.storage.save_account(account)
                
                self.results["steps"]["deposit_usdc"] = {
                    "status": "✅ SUCCESS",
                    "amount": deposit_amount,
                    "tx_hash": tx_hash,
                    "deposited_at": account.deposited_at.isoformat()
                }
                
                print(f"✅ Deposited {deposit_amount} USDC")
                print(f"   TX: {tx_hash}")
                return True
                
        except Exception as e:
            self.results["steps"]["deposit_usdc"] = {
                "status": "❌ FAILED",
                "error": str(e)
            }
            print(f"❌ Failed to deposit USDC: {e}")
            return False
    
    async def test_place_order(self, account: Account) -> Optional[str]:
        """Step 4: Place a market order."""
        print("\n📈 Step 4: Placing market order")
        print("-"*40)
        
        try:
            async with RiseClient() as client:
                # Use known market ID for BTC
                # Based on docs: BTC = 1, ETH = 2
                market_id = 1  # BTC-USD
                
                # Optional: verify market exists
                markets = await client.get_markets()
                btc_market = next((m for m in markets if int(m.get("market_id", 0)) == market_id), None)
                
                if btc_market:
                    print(f"   Market info: {btc_market.get('symbol', 'BTC-USD')}")
                    print(f"   Last price: ${btc_market.get('last_price', 'N/A')}")
                    print(f"   Available: {btc_market.get('available', False)}")
                else:
                    print(f"   ⚠️  Market ID {market_id} not found, proceeding anyway...")
                
                # Place small market order
                order_size = 0.001  # Small BTC order
                
                print(f"Placing order: BUY {order_size} BTC")
                
                order = await client.place_order(
                    account_key=account.private_key,
                    signer_key=account.signer_key,
                    market_id=market_id,
                    side="buy",
                    size=order_size,
                    price=0,  # Market order
                    order_type="market"
                )
                
                order_id = order.get("orderId", "unknown")
                
                # Save trade record
                trade = Trade(
                    id=f"trade-{int(time.time())}",
                    account_id=account.id,
                    market="BTC-USD",
                    market_id=market_id,
                    side="buy",
                    size=order_size,
                    price=order.get("price", 0),
                    reasoning="Test market order",
                    timestamp=datetime.utcnow(),
                    order_id=order_id,
                    status="submitted"
                )
                
                self.storage.save_trade(trade)
                self.results["trades"].append(trade.model_dump())
                
                self.results["steps"]["place_order"] = {
                    "status": "✅ SUCCESS",
                    "order_id": order_id,
                    "market": "BTC-USD",
                    "side": "buy",
                    "size": order_size
                }
                
                print(f"✅ Order placed: {order_id}")
                
                # Wait for order to fill
                await asyncio.sleep(3)
                
                # Update trade status
                trade.status = "filled"
                trade.filled_size = order_size
                self.storage.save_trade(trade)
                
                return order_id
                
        except Exception as e:
            self.results["steps"]["place_order"] = {
                "status": "❌ FAILED",
                "error": str(e)
            }
            print(f"❌ Failed to place order: {e}")
            return None
    
    async def test_check_positions(self, account: Account) -> list:
        """Step 5: Check account positions."""
        print("\n📊 Step 5: Checking positions")
        print("-"*40)
        
        try:
            async with RiseClient() as client:
                positions = await client.get_all_positions(account.address)
                
                if not positions:
                    print("⚠️  No positions found")
                    self.results["steps"]["check_positions"] = {
                        "status": "⚠️  NO POSITIONS",
                        "count": 0
                    }
                    return []
                
                # Convert to Position models
                position_models = []
                
                for pos_data in positions:
                    position = Position(
                        account_id=account.id,
                        market=f"{pos_data.get('market', 'Unknown')}-USD",
                        side=pos_data.get("side", "long"),
                        size=pos_data.get("size", 0),
                        entry_price=pos_data.get("avgPrice", 0),
                        mark_price=pos_data.get("markPrice", 0),
                        notional_value=pos_data.get("notionalValue", 0),
                        unrealized_pnl=pos_data.get("unrealizedPnl", 0),
                        realized_pnl=pos_data.get("realizedPnl", 0)
                    )
                    
                    position_models.append(position)
                    self.results["positions"].append(position.model_dump())
                    
                    print(f"✅ Position: {position.market}")
                    print(f"   Size: {position.size}")
                    print(f"   Entry: ${position.entry_price:,.2f}")
                    print(f"   Mark: ${position.mark_price:,.2f}")
                    print(f"   Unrealized P&L: ${position.unrealized_pnl:,.2f}")
                
                self.results["steps"]["check_positions"] = {
                    "status": "✅ SUCCESS",
                    "count": len(position_models),
                    "total_unrealized_pnl": sum(p.unrealized_pnl for p in position_models)
                }
                
                return position_models
                
        except Exception as e:
            self.results["steps"]["check_positions"] = {
                "status": "❌ FAILED",
                "error": str(e)
            }
            print(f"❌ Failed to check positions: {e}")
            return []
    
    async def test_update_pnl(self, account: Account, positions: list):
        """Step 6: Update local P&L tracking."""
        print("\n💹 Step 6: Updating P&L")
        print("-"*40)
        
        try:
            # Calculate total P&L
            total_unrealized = sum(p.unrealized_pnl for p in positions)
            total_realized = sum(p.realized_pnl for p in positions)
            total_pnl = total_unrealized + total_realized
            
            # Update trades with P&L
            trades = self.storage.get_trades(account.id)
            
            if trades and positions:
                # Simple P&L attribution to last trade
                last_trade = trades[-1]
                last_trade.pnl = total_unrealized
                last_trade.realized_pnl = total_realized
                self.storage.save_trade(last_trade)
            
            # Get trading analytics
            analytics = self.storage.get_trading_analytics(account.id)
            
            self.results["steps"]["update_pnl"] = {
                "status": "✅ SUCCESS",
                "total_unrealized_pnl": total_unrealized,
                "total_realized_pnl": total_realized,
                "total_pnl": total_pnl,
                "analytics": analytics
            }
            
            print(f"✅ P&L Updated:")
            print(f"   Unrealized: ${total_unrealized:,.2f}")
            print(f"   Realized: ${total_realized:,.2f}")
            print(f"   Total: ${total_pnl:,.2f}")
            
        except Exception as e:
            self.results["steps"]["update_pnl"] = {
                "status": "❌ FAILED",
                "error": str(e)
            }
            print(f"❌ Failed to update P&L: {e}")
    
    def save_results(self):
        """Save test results to file."""
        with open("tests/trading/full_flow_results.json", "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        print("\n💾 Results saved to tests/trading/full_flow_results.json")
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        for step_name, result in self.results["steps"].items():
            status = result.get("status", "Unknown")
            print(f"{status} {step_name}")
        
        # Count results
        statuses = [r.get("status", "") for r in self.results["steps"].values()]
        success_count = sum(1 for s in statuses if "SUCCESS" in s)
        failed_count = sum(1 for s in statuses if "FAILED" in s)
        warning_count = sum(1 for s in statuses if "WARNING" in s or "NO POSITIONS" in s)
        
        print("="*60)
        print(f"Total Steps: {len(self.results['steps'])}")
        print(f"✅ Success: {success_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"⚠️  Warnings: {warning_count}")
        
        if self.results.get("account"):
            print(f"\n📋 Test Account:")
            print(f"   ID: {self.results['account']['id']}")
            print(f"   Address: {self.results['account']['address']}")
            print(f"   Handle: {self.results['account']['handle']}")


async def main():
    """Run the full trading flow test."""
    test = FullTradingFlowTest()
    await test.run_test()


if __name__ == "__main__":
    asyncio.run(main())