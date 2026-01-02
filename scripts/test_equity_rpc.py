#!/usr/bin/env python3
"""Test RPC-based equity fetching from PerpsManager contract."""

import asyncio
import json
import os
import sys
from decimal import Decimal
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from eth_typing import HexStr
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.exceptions import ContractLogicError

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.storage import JSONStorage

# Load environment
load_dotenv()

# Contract configuration
PERPS_MANAGER_ADDRESS = "0x68cAcD54a8c93A3186BF50bE6b78B761F728E1b4"

# Minimal ABI for getAccountEquity
PERPS_MANAGER_ABI = [
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "getAccountEquity",
        "outputs": [{"name": "", "type": "int256"}],
        "stateMutability": "view",
        "type": "function"
    }
]


class EquityTester:
    """Test RPC equity fetching functionality."""
    
    def __init__(self):
        # Use indexing RPC for better reliability
        rpc_url = os.getenv("BACKEND_RPC_URL", "https://indexing.testnet.riselabs.xyz")
        print(f"🔌 Connecting to RPC: {rpc_url}")
        
        self.w3 = AsyncWeb3(AsyncHTTPProvider(rpc_url))
        self.perps_manager = self.w3.eth.contract(
            address=PERPS_MANAGER_ADDRESS,
            abi=PERPS_MANAGER_ABI
        )
        self.storage = JSONStorage()
    
    async def test_connection(self):
        """Test basic RPC connection."""
        print("\n🧪 Testing RPC Connection...")
        
        try:
            # Check if connected
            is_connected = await self.w3.is_connected()
            print(f"   Connected: {is_connected}")
            
            # Get chain ID
            chain_id = await self.w3.eth.chain_id
            print(f"   Chain ID: {chain_id}")
            
            # Get latest block
            block = await self.w3.eth.get_block("latest")
            print(f"   Latest Block: {block['number']:,}")
            
            # Verify contract exists
            code = await self.w3.eth.get_code(PERPS_MANAGER_ADDRESS)
            print(f"   Contract Code Size: {len(code)} bytes")
            
            return True
            
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    async def fetch_single_equity(self, address: str) -> Dict:
        """Fetch equity for a single account."""
        print(f"\n📊 Fetching equity for {address[:8]}...{address[-6:]}")
        
        try:
            # Call getAccountEquity
            equity_raw = await self.perps_manager.functions.getAccountEquity(address).call()
            
            # Convert from int256 to human readable
            # Assuming 18 decimals (RISE internal) -> 6 decimals (USDC)
            equity_usdc = float(equity_raw) / 10**18
            
            result = {
                "address": address,
                "equity_raw": str(equity_raw),
                "equity_usdc": equity_usdc,
                "success": True
            }
            
            print(f"   ✅ Equity: ${equity_usdc:,.2f} USDC")
            print(f"   Raw value: {equity_raw}")
            
            return result
            
        except ContractLogicError as e:
            print(f"   ⚠️  Contract error: {e}")
            return {
                "address": address,
                "error": str(e),
                "success": False
            }
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return {
                "address": address,
                "error": str(e),
                "success": False
            }
    
    async def test_batch_request(self, addresses: List[str]) -> List[Dict]:
        """Test batch fetching multiple accounts."""
        print(f"\n🔄 Testing batch request for {len(addresses)} accounts...")
        
        # Create tasks for concurrent fetching
        tasks = [self.fetch_single_equity(addr) for addr in addresses]
        
        # Execute concurrently
        start_time = asyncio.get_event_loop().time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = asyncio.get_event_loop().time() - start_time
        
        print(f"\n⏱️  Batch completed in {elapsed:.2f}s")
        
        # Process results
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        print(f"✅ Successful: {successful}/{len(addresses)}")
        
        return results
    
    async def test_with_storage_accounts(self):
        """Test with accounts from storage."""
        print("\n📂 Testing with stored accounts...")
        
        # Load accounts from storage
        accounts_data = self.storage._load_json(self.storage.accounts_file)
        
        if not accounts_data:
            print("   ⚠️  No accounts found in storage")
            return
        
        # Get account addresses
        addresses = []
        for account_id, account_data in accounts_data.items():
            address = account_data.get("address")
            if address:
                addresses.append(address)
                print(f"   Found account: {account_data.get('handle')} ({address[:8]}...)")
        
        if addresses:
            # Test batch fetch
            results = await self.test_batch_request(addresses)
            
            # Save results
            output = {
                "timestamp": asyncio.get_event_loop().time(),
                "rpc_url": os.getenv("BACKEND_RPC_URL", "https://indexing.testnet.riselabs.xyz"),
                "results": results,
                "summary": {
                    "total": len(results),
                    "successful": sum(1 for r in results if isinstance(r, dict) and r.get("success")),
                    "total_equity_usdc": sum(
                        r.get("equity_usdc", 0) 
                        for r in results 
                        if isinstance(r, dict) and r.get("success")
                    )
                }
            }
            
            # Save test results
            test_file = Path("data/test_equity_results.json")
            test_file.parent.mkdir(exist_ok=True)
            
            with open(test_file, "w") as f:
                json.dump(output, f, indent=2)
            
            print(f"\n💾 Results saved to {test_file}")
            print(f"📊 Total equity across accounts: ${output['summary']['total_equity_usdc']:,.2f}")
    
    async def test_error_cases(self):
        """Test error handling."""
        print("\n🧪 Testing error cases...")
        
        # Test with zero address
        await self.fetch_single_equity("0x0000000000000000000000000000000000000000")
        
        # Test with invalid address
        await self.fetch_single_equity("0xinvalid")
    
    async def run_all_tests(self):
        """Run all tests."""
        print("=" * 60)
        print("🚀 Starting RPC Equity Tests")
        print("=" * 60)
        
        # Test connection first
        if not await self.test_connection():
            print("\n❌ Connection failed, aborting tests")
            return
        
        # Test single account (example)
        test_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f7E83C"  # Example address
        await self.fetch_single_equity(test_address)
        
        # Test with storage accounts
        await self.test_with_storage_accounts()
        
        # Test error cases
        await self.test_error_cases()
        
        print("\n✅ All tests completed!")


async def main():
    """Run the equity tester."""
    tester = EquityTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())