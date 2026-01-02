#!/usr/bin/env python3
"""Test USDC deposit to RISE account."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rise_client import RiseClient
from app.services.storage import JSONStorage
from eth_account import Account as EthAccount


async def test_deposit():
    """Test depositing USDC."""
    rise_client = RiseClient()
    storage = JSONStorage()
    
    print("RISE USDC Deposit Test")
    print("=" * 60)
    
    # Get first account from storage
    accounts = storage.list_accounts()
    
    if not accounts:
        print("No accounts found!")
        return
    
    # Use the first account
    account = accounts[0]
    
    print(f"\nAccount: {account.address}")
    
    # Check current balance first
    print("\nFetching current balance...")
    try:
        balance_data = await rise_client.get_balance(account.address)
        print(f"Current balance data: {json.dumps(balance_data, indent=2)}")
    except Exception as e:
        print(f"Error getting balance: {e}")
    
    # Now let's deposit 1000 USDC
    deposit_amount = 1000.0
    print(f"\nDepositing {deposit_amount} USDC...")
    print(f"Account: {account.address}")
    print(f"Amount: {deposit_amount} USDC")
    
    try:
        # Note: Our current implementation uses 18 decimals
        # But USDC typically uses 6 decimals
        # Let's try with our current implementation first
        result = await rise_client.deposit_usdc(
            account_key=account.private_key,
            amount=deposit_amount
        )
        
        print(f"\n✓ Deposit request submitted successfully!")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        # Wait a bit for the transaction to process
        print("\nWaiting 5 seconds for transaction to process...")
        await asyncio.sleep(5)
        
        # Check balance again
        print("\nFetching updated balance...")
        balance_data = await rise_client.get_balance(account.address)
        print(f"Updated balance data: {json.dumps(balance_data, indent=2)}")
        
    except Exception as e:
        print(f"\n✗ Deposit error: {e}")
        print("\nThis might be because:")
        print("1. The deposit endpoint expects different parameters")
        print("2. USDC decimal places might be incorrect (6 vs 18)")
        print("3. The testnet deposit function might be disabled")
    
    await rise_client.close()


async def test_deposit_with_6_decimals():
    """Test deposit with 6 decimal USDC (standard USDC decimals)."""
    print("\n" + "=" * 60)
    print("Testing with 6 decimal USDC...")
    
    rise_client = RiseClient()
    storage = JSONStorage()
    
    accounts = storage.list_accounts()
    if not accounts:
        return
    
    account = accounts[0]
    
    # Modify the deposit method to use 6 decimals
    # We'll make a direct API call with custom parameters
    domain = await rise_client.get_eip712_domain()
    
    # USDC uses 6 decimals
    deposit_amount = 1000.0
    amount_wei = int(deposit_amount * 1e6)  # 6 decimals for USDC
    
    print(f"Amount: {deposit_amount} USDC = {amount_wei} wei (6 decimals)")
    
    # Create deposit signature
    typed_data = {
        "domain": domain,
        "message": {
            "account": account.address,
            "amount": amount_wei,
        },
        "primaryType": "Deposit",
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "Deposit": [
                {"name": "account", "type": "address"},
                {"name": "amount", "type": "uint256"},
            ]
        }
    }
    
    signature = rise_client._sign_typed_data(typed_data, account.private_key)
    nonce = rise_client._create_client_nonce(account.address)
    deadline = int(time.time()) + 300
    
    # Try with amount in wei format (as string)
    deposit_request = {
        "account": account.address,
        "amount": str(amount_wei),  # Wei format as string
        "permit_params": {
            "account": account.address,
            "signer": account.address,
            "deadline": str(deadline),
            "signature": signature,
            "nonce": str(nonce)
        }
    }
    
    try:
        result = await rise_client._request(
            "POST", "/v1/account/deposit",
            json=deposit_request
        )
        
        print(f"\n✓ Deposit with 6 decimals successful!")
        print(f"Response: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        print(f"\n✗ Deposit with 6 decimals failed: {e}")
    
    await rise_client.close()


if __name__ == "__main__":
    import time
    print(f"Starting deposit test at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run both tests
    asyncio.run(test_deposit())
    asyncio.run(test_deposit_with_6_decimals())