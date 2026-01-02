#!/usr/bin/env python3
"""Test fresh account flow: generate keys → register signer → deposit USDC."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage


async def test_fresh_account_flow():
    """Test complete fresh account onboarding flow."""
    print("=" * 80)
    print("🧪 FRESH ACCOUNT ONBOARDING TEST")
    print("=" * 80)
    
    # Initialize services
    rise_client = RiseClient()
    storage = JSONStorage()
    
    try:
        # Step 1: Generate completely fresh keys
        print("\n1️⃣  Generating fresh account keys...")
        
        from web3 import Web3
        w3 = Web3()
        
        # Generate main account key
        main_account = w3.eth.account.create()
        print(f"   Main Account: {main_account.address}")
        print(f"   Private Key: {main_account.key.hex()[:10]}...{main_account.key.hex()[-6:]}")
        
        # Generate separate signer key (MUST be different)
        signer_account = w3.eth.account.create()
        print(f"   Signer Account: {signer_account.address}")
        print(f"   Signer Key: {signer_account.key.hex()[:10]}...{signer_account.key.hex()[-6:]}")
        
        # Verify they're different
        assert main_account.address != signer_account.address, "Keys must be different!"
        print("   ✅ Keys are different (required)")
        
        # Step 2: Register signer key
        print("\n2️⃣  Registering signer key...")
        print(f"   Registering {signer_account.address} as signer for {main_account.address}")
        
        try:
            registration_result = await rise_client.register_signer(
                account_key=main_account.key.hex(),
                signer_key=signer_account.key.hex()
            )
            
            print(f"   Registration response: {registration_result}")
            
            # Check nested success in data
            success = registration_result.get("data", {}).get("success") if registration_result else False
            if success:
                print("   ✅ Signer registration successful!")
                
                # Check if we got transaction details
                data = registration_result.get("data", {})
                if "transaction_hash" in data:
                    print(f"   Transaction: {data['transaction_hash']}")
                    print(f"   Block: {data.get('block_number', 'N/A')}")
                    
            else:
                error_msg = registration_result.get("error") if registration_result else "No response"
                print(f"   ⚠️  Registration failed: {error_msg}")
                
                # Continue anyway to test deposit
                print("   Continuing to test deposit...")
                
        except Exception as e:
            print(f"   ❌ Registration error: {e}")
            print("   Continuing to test deposit...")
        
        # Step 3: Test deposit (should mint testnet USDC)
        print("\n3️⃣  Testing USDC deposit (should mint testnet funds)...")
        print(f"   Depositing for account: {main_account.address}")
        
        # Test different amounts
        test_amounts = [100.0, 50.0, 1.0]
        
        for amount in test_amounts:
            print(f"\n   Testing deposit of ${amount}...")
            
            try:
                deposit_result = await rise_client.deposit_usdc(
                    account_key=main_account.key.hex(),
                    amount=amount
                )
                
                print(f"   Deposit response: {deposit_result}")
                
                # Check nested success in data
                deposit_success = deposit_result.get("data", {}).get("success") if deposit_result else False
                if deposit_success:
                    print(f"   ✅ Deposit of ${amount} successful!")
                    
                    # Check transaction details
                    data = deposit_result.get("data", {})
                    if "transaction_hash" in data:
                        print(f"   Transaction: {data['transaction_hash']}")
                        print(f"   Block: {data.get('block_number', 'N/A')}")
                    
                    # Break on first success
                    break
                    
                else:
                    error_msg = deposit_result.get("error") if deposit_result else "No response"
                    print(f"   ⚠️  Deposit of ${amount} failed: {error_msg}")
                    
            except Exception as e:
                print(f"   ❌ Deposit error: {e}")
                
                # Print more details if available
                if hasattr(e, 'details'):
                    print(f"   Error details: {e.details}")
        
        # Step 4: Check account status after operations
        print("\n4️⃣  Checking account status...")
        
        try:
            # Check account info
            account_info = await rise_client.get_account(main_account.address)
            print(f"   Account info: {account_info}")
            
            # Check balance
            balance_info = await rise_client.get_balance(main_account.address)
            print(f"   Balance info: {balance_info}")
            
            if balance_info:
                available_balance = balance_info.get("cross_margin_balance", 0)
                print(f"   Available balance: ${float(available_balance):.2f}")
            
        except Exception as e:
            print(f"   ⚠️  Could not fetch account status: {e}")
        
        # Step 5: Test equity monitoring for this account
        print("\n5️⃣  Testing equity monitoring for fresh account...")
        
        from app.services.equity_monitor import get_equity_monitor
        equity_monitor = get_equity_monitor()
        
        try:
            # Fetch equity directly
            equity = await equity_monitor.fetch_equity(main_account.address)
            
            if equity is not None:
                print(f"   ✅ On-chain equity: ${equity:,.2f}")
            else:
                print("   ⚠️  Could not fetch equity")
                
        except Exception as e:
            print(f"   ❌ Equity fetch error: {e}")
        
        # Step 6: Test a simple market order (if we have balance)
        print("\n6️⃣  Testing market order placement...")
        
        try:
            # Try to place a very small BTC order
            order_result = await rise_client.place_market_order(
                account_key=main_account.key.hex(),
                signer_key=signer_account.key.hex(),
                market_id=1,  # BTC
                side="buy",
                size=0.001,  # Very small size
                time_in_force=3  # IOC
            )
            
            print(f"   Order result: {order_result}")
            
            if order_result and order_result.get("success"):
                print("   ✅ Market order placed successfully!")
                
                if "order_id" in order_result:
                    print(f"   Order ID: {order_result['order_id']}")
            else:
                error_msg = order_result.get("error") if order_result else "No response"
                print(f"   ⚠️  Order failed: {error_msg}")
                
        except Exception as e:
            print(f"   ⚠️  Order error (expected if no balance): {e}")
        
        # Final summary
        print("\n" + "=" * 80)
        print("📊 FRESH ACCOUNT TEST SUMMARY")
        print("=" * 80)
        print(f"Main Account: {main_account.address}")
        print(f"Signer Account: {signer_account.address}")
        
        # Check if we should save this account for further testing
        save_response = input("\nSave this account for further testing? (y/n): ")
        
        if save_response.lower() == 'y':
            # Create a test account entry
            test_account_id = f"fresh_test_{int(datetime.now().timestamp())}"
            
            account_data = {
                "id": test_account_id,
                "address": main_account.address,
                "private_key": main_account.key.hex(),
                "signer_key": signer_account.key.hex(),
                "persona": None,
                "is_active": True,
                "is_registered": True,  # Assume successful if we got here
                "registered_at": datetime.now().isoformat(),
                "has_deposited": False,  # Will be updated based on test results
                "created_at": datetime.now().isoformat()
            }
            
            # Save to storage
            storage.save_account(test_account_id, account_data)
            print(f"   ✅ Account saved as: {test_account_id}")
        
        return {
            "main_address": main_account.address,
            "signer_address": signer_account.address,
            "main_key": main_account.key.hex(),
            "signer_key": signer_account.key.hex()
        }
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        await rise_client.close()


async def main():
    """Run the fresh account test."""
    print("This will test the complete onboarding flow with fresh keys")
    print("Make sure you have internet connection for testnet access")
    
    result = await test_fresh_account_flow()
    
    if result:
        print(f"\n🎯 Test completed with fresh account: {result['main_address']}")
    else:
        print("\n💥 Test failed - check logs above")


if __name__ == "__main__":
    asyncio.run(main())