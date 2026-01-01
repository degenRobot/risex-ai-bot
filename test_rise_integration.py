#!/usr/bin/env python3
"""Test script for RISE API integration."""

import asyncio
import os
from dotenv import load_dotenv
from eth_account import Account as EthAccount

from app.services.rise_client import RiseClient, RiseAPIError

load_dotenv()


async def test_rise_integration():
    """Test basic RISE API functionality."""
    print("🧪 Testing RISE API Integration")
    print("=" * 50)
    
    # Check environment variables
    private_key = os.getenv("PRIVATE_KEY")
    signer_key = os.getenv("SIGNER_PRIVATE_KEY")
    
    if not private_key or not signer_key:
        print("❌ Missing PRIVATE_KEY or SIGNER_PRIVATE_KEY in .env")
        return False
    
    # Get addresses
    account = EthAccount.from_key(private_key)
    signer = EthAccount.from_key(signer_key)
    
    print(f"Account: {account.address}")
    print(f"Signer:  {signer.address}")
    
    if account.address == signer.address:
        print("❌ Account and signer must be different addresses for security")
        return False
    
    print()
    
    async with RiseClient() as client:
        try:
            # Test 1: Get EIP-712 domain
            print("1. Testing EIP-712 domain retrieval...")
            domain = await client.get_eip712_domain()
            print(f"   ✅ Domain: {domain['name']} v{domain['version']}")
            
            # Test 2: Get markets
            print("2. Testing market data...")
            markets = await client.get_markets()
            print(f"   ✅ Found {len(markets)} markets")
            if markets:
                btc_market = next((m for m in markets if m.get("symbol") == "BTC"), None)
                if btc_market:
                    print(f"   📊 BTC Market ID: {btc_market.get('market_id')}")
            
            # Test 3: Check account balance
            print("3. Testing account balance...")
            balance = await client.get_balance(account.address)
            print(f"   ✅ Balance data retrieved: {list(balance.keys())}")
            
            # Test 4: Check positions
            print("4. Testing position data...")
            positions = await client.get_all_positions(account.address)
            print(f"   ✅ Found {len(positions)} positions")
            
            # Test 5: Signer registration (read-only test)
            print("5. Testing signer registration process...")
            try:
                nonce = await client.get_account_nonce(account.address)
                print(f"   ✅ Account nonce: {nonce}")
                
                # Note: We don't actually register to avoid side effects
                print("   ⏭️  Skipping actual registration for safety")
                
            except RiseAPIError as e:
                if "already registered" in str(e).lower():
                    print("   ✅ Signer already registered")
                else:
                    print(f"   ⚠️  Registration check: {e}")
            
            print()
            print("🎉 Basic RISE integration test completed!")
            print("📝 Note: Not testing actual transactions (deposit/orders) to avoid side effects")
            print("📝 To test transactions, ensure you have USDC deposited and markets are active")
            
            return True
            
        except RiseAPIError as e:
            print(f"❌ RISE API Error: {e}")
            if e.status_code:
                print(f"   Status Code: {e.status_code}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False


if __name__ == "__main__":
    print("Starting RISE integration test...")
    print("Ensure you have PRIVATE_KEY and SIGNER_PRIVATE_KEY in .env")
    print()
    
    success = asyncio.run(test_rise_integration())
    
    if success:
        print("\n✅ Integration test passed!")
    else:
        print("\n❌ Integration test failed!")
    
    print("\nNext steps:")
    print("1. Run: poetry install")
    print("2. Set up .env with your keys")
    print("3. Test with actual USDC deposit if needed")